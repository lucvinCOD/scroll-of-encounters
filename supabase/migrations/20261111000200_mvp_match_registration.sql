-- EXPAND. Não altera dados antigos, RLS, permissões de tabelas ou colunas legadas.
-- As funções públicas são capacidades restritas ao backend (service_role).
CREATE SCHEMA IF NOT EXISTS soe_private;

CREATE INDEX IF NOT EXISTS soe_participant_player_match_idx
    ON public.match_participant (player_id, match_id);
CREATE INDEX IF NOT EXISTS soe_match_start_idx
    ON public.game_match ((match_date + approximate_start_time))
    WHERE approximate_start_time IS NOT NULL AND status IN ('PENDING','VERIFIED','DISPUTED');

CREATE OR REPLACE FUNCTION soe_private.assert_actor(p_actor uuid)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM public.profile WHERE id=p_actor AND status='ACTIVE') THEN
        RAISE EXCEPTION 'SOE_ACTOR_FORBIDDEN' USING ERRCODE='42501';
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION soe_private.lock_players(p_players bigint[])
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE p bigint;
BEGIN
    -- O backend usa READ COMMITTED. Recusar snapshots fixos evita write skew.
    IF current_setting('transaction_isolation') <> 'read committed' THEN
        RAISE EXCEPTION 'SOE_RETRY_TRANSACTION' USING ERRCODE='40001';
    END IF;
    FOR p IN SELECT DISTINCT unnest(p_players) ORDER BY 1 LOOP
        PERFORM pg_advisory_xact_lock(hashtextextended('soe/player/' || p::text, 0));
    END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION soe_private.check_start(
    p_players bigint[], p_match bigint, p_date date, p_start time, p_status text
) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE conflict_id bigint;
BEGIN
    PERFORM soe_private.lock_players(p_players);
    IF p_start IS NULL OR p_status='CANCELLED' THEN RETURN; END IF;
    SELECT m.id INTO conflict_id
    FROM public.game_match m JOIN public.match_participant mp ON mp.match_id=m.id
    WHERE mp.player_id=ANY(p_players) AND m.id IS DISTINCT FROM p_match
      AND m.status IN ('PENDING','VERIFIED','DISPUTED')
      AND m.approximate_start_time IS NOT NULL
      AND (m.match_date+m.approximate_start_time) > (p_date+p_start)-interval '10 minutes'
      AND (m.match_date+m.approximate_start_time) < (p_date+p_start)+interval '10 minutes'
    ORDER BY m.id LIMIT 1;
    IF conflict_id IS NOT NULL THEN
        RAISE EXCEPTION 'SOE_TEMPORAL_CONFLICT' USING ERRCODE='23P01', DETAIL=conflict_id::text;
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION soe_private.guard_match_start()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE ids bigint[];
BEGIN
    IF TG_OP='INSERT' AND NEW.approximate_start_time IS NULL THEN
        RAISE EXCEPTION 'SOE_START_REQUIRED' USING ERRCODE='22023';
    END IF;
    IF TG_OP='UPDATE' AND OLD.approximate_start_time IS NOT NULL AND NEW.approximate_start_time IS NULL THEN
        RAISE EXCEPTION 'SOE_START_REQUIRED' USING ERRCODE='22023';
    END IF;
    SELECT array_agg(player_id ORDER BY player_id) INTO ids
    FROM public.match_participant WHERE match_id=NEW.id;
    PERFORM soe_private.check_start(coalesce(ids,'{}'::bigint[]),NEW.id,
        NEW.match_date,NEW.approximate_start_time,NEW.status);
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION soe_private.guard_participant_start()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE m public.game_match%ROWTYPE;
BEGIN
    IF TG_OP='DELETE' THEN
        PERFORM 1 FROM public.game_match WHERE id=OLD.match_id FOR UPDATE;
        PERFORM soe_private.lock_players(ARRAY[OLD.player_id]);
        RETURN OLD;
    END IF;
    IF TG_OP='UPDATE' THEN
        PERFORM 1 FROM public.game_match WHERE id IN (OLD.match_id,NEW.match_id) ORDER BY id FOR UPDATE;
    END IF;
    SELECT * INTO m FROM public.game_match WHERE id=NEW.match_id FOR UPDATE;
    PERFORM soe_private.check_start(ARRAY[NEW.player_id],m.id,m.match_date,m.approximate_start_time,m.status);
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION soe_private.assert_result(p_match bigint)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE total integer; wins integer; draws integer; minimum integer; maximum integer;
BEGIN
    SELECT f.min_players,f.max_players INTO minimum,maximum
    FROM public.game_match m JOIN public.format f ON f.id=m.format_id WHERE m.id=p_match;
    IF NOT FOUND THEN RETURN; END IF;
    SELECT count(*),count(*) FILTER(WHERE result='WIN'),count(*) FILTER(WHERE result='DRAW')
      INTO total,wins,draws FROM public.match_participant WHERE match_id=p_match;
    IF total<minimum OR (maximum IS NOT NULL AND total>maximum) THEN
        RAISE EXCEPTION 'SOE_PARTICIPANT_COUNT' USING ERRCODE='23514';
    END IF;
    IF NOT ((wins=1 AND draws=0) OR (wins=0 AND draws=total)) THEN
        RAISE EXCEPTION 'SOE_INVALID_RESULT' USING ERRCODE='23514';
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION soe_private.guard_result()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
    IF TG_TABLE_NAME='game_match' THEN
        PERFORM soe_private.assert_result(NEW.id);
    ELSE
        IF TG_OP<>'DELETE' THEN PERFORM soe_private.assert_result(NEW.match_id); END IF;
        IF TG_OP<>'INSERT' THEN PERFORM soe_private.assert_result(OLD.match_id); END IF;
    END IF;
    RETURN NULL;
END;
$$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='soe_match_start_guard' AND tgrelid='public.game_match'::regclass) THEN
        CREATE TRIGGER soe_match_start_guard BEFORE INSERT OR UPDATE OF match_date,approximate_start_time,status
        ON public.game_match FOR EACH ROW EXECUTE FUNCTION soe_private.guard_match_start();
        CREATE TRIGGER soe_participant_start_guard BEFORE INSERT OR UPDATE OR DELETE
        ON public.match_participant FOR EACH ROW EXECUTE FUNCTION soe_private.guard_participant_start();
        CREATE CONSTRAINT TRIGGER soe_match_result_guard AFTER INSERT OR UPDATE OF format_id
        ON public.game_match DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION soe_private.guard_result();
        CREATE CONSTRAINT TRIGGER soe_participant_result_guard AFTER INSERT OR UPDATE OR DELETE
        ON public.match_participant DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION soe_private.guard_result();
    END IF;
END $$;

CREATE OR REPLACE FUNCTION public.soe_catalog()
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path = '' AS $$
SELECT jsonb_build_object(
 'games',coalesce((SELECT jsonb_agg(jsonb_build_object('id',id,'name',name) ORDER BY name) FROM public.game),'[]'),
 'formats',coalesce((SELECT jsonb_agg(jsonb_build_object('id',id,'game_id',game_id,'name',name,
    'min_players',min_players,'max_players',max_players,'match_type',match_type) ORDER BY name) FROM public.format),'[]'),
 'communities',coalesce((SELECT jsonb_agg(jsonb_build_object('id',id,'city',city,'state_code',state_code,
    'subdivision',subdivision,'description',description) ORDER BY city,id) FROM public.community),'[]'),
 'players',coalesce((SELECT jsonb_agg(jsonb_build_object('id',id,'display_name',display_name,
    'community_id',community_id,'is_guest',profile_id IS NULL) ORDER BY display_name,id) FROM public.player),'[]'),
 'verified_matches',(SELECT count(*) FROM public.game_match WHERE status='VERIFIED')
);
$$;

CREATE OR REPLACE FUNCTION public.soe_identity(p_actor uuid)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = '' AS $$
BEGIN
    PERFORM soe_private.assert_actor(p_actor);
    RETURN (SELECT jsonb_build_object('id',p.id,'username',p.username,
        'player_id',(SELECT id FROM public.player WHERE profile_id=p.id))
        FROM public.profile p WHERE p.id=p_actor);
END;
$$;

CREATE OR REPLACE FUNCTION public.soe_match_history(p_limit integer DEFAULT 30,p_offset integer DEFAULT 0,p_community bigint DEFAULT NULL)
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path = '' AS $$
SELECT jsonb_build_object('total',(SELECT count(*) FROM public.game_match WHERE p_community IS NULL OR community_id=p_community),
'items',coalesce((SELECT jsonb_agg(item ORDER BY match_date DESC, approximate_start_time DESC NULLS LAST,id DESC) FROM (
 SELECT m.id,m.match_date,m.approximate_start_time,jsonb_build_object(
   'id',m.id,'community_id',m.community_id,'format_id',m.format_id,'match_date',m.match_date,
   'approximate_start_time',m.approximate_start_time,'status',m.status,'created_at',m.created_at,
   'author',p.username,'format_name',f.name,
   'participants',coalesce((SELECT jsonb_agg(jsonb_build_object('player_id',mp.player_id,
      'display_name',pl.display_name,'is_guest',pl.profile_id IS NULL,'result',mp.result) ORDER BY mp.id)
      FROM public.match_participant mp JOIN public.player pl ON pl.id=mp.player_id WHERE mp.match_id=m.id),'[]')
 ) AS item FROM public.game_match m JOIN public.format f ON f.id=m.format_id
 LEFT JOIN public.profile p ON p.id=m.created_by
 WHERE p_community IS NULL OR m.community_id=p_community
 ORDER BY m.match_date DESC,m.approximate_start_time DESC NULLS LAST,m.id DESC
 LIMIT least(greatest(p_limit,1),100) OFFSET greatest(p_offset,0)
) records),'[]'));
$$;

CREATE OR REPLACE FUNCTION public.soe_create_guest(p_actor uuid,p_name text,p_community bigint)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE v_id bigint;
BEGIN
    PERFORM soe_private.assert_actor(p_actor);
    IF p_name IS NULL OR length(btrim(p_name)) NOT BETWEEN 2 AND 80 THEN
        RAISE EXCEPTION 'SOE_GUEST_NAME' USING ERRCODE='22023';
    END IF;
    INSERT INTO public.player(display_name,community_id,profile_id)
    VALUES(btrim(p_name),p_community,NULL) RETURNING id INTO v_id;
    RETURN jsonb_build_object('id',v_id,'display_name',btrim(p_name),'community_id',p_community,'is_guest',true);
END;
$$;

CREATE OR REPLACE FUNCTION public.soe_register_match(
    p_actor uuid,p_community bigint,p_format bigint,p_date date,p_start time,
    p_players bigint[],p_winner bigint DEFAULT NULL,p_draw boolean DEFAULT false
) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE ids bigint[]; minimum integer; maximum integer; v_id bigint; duplicate_ids jsonb; warnings jsonb:='[]';
BEGIN
    PERFORM soe_private.assert_actor(p_actor);
    IF p_start IS NULL OR p_date IS NULL THEN RAISE EXCEPTION 'SOE_START_REQUIRED' USING ERRCODE='22023'; END IF;
    IF p_players IS NULL OR cardinality(p_players)=0 OR array_position(p_players,NULL) IS NOT NULL THEN
        RAISE EXCEPTION 'SOE_INVALID_PARTICIPANTS' USING ERRCODE='22023';
    END IF;
    SELECT array_agg(DISTINCT x ORDER BY x) INTO ids FROM unnest(p_players) x;
    IF cardinality(ids)<>cardinality(p_players) THEN RAISE EXCEPTION 'SOE_DUPLICATE_PLAYER' USING ERRCODE='22023'; END IF;
    IF p_draw IS NULL OR (p_draw AND p_winner IS NOT NULL) OR (NOT p_draw AND (p_winner IS NULL OR NOT p_winner=ANY(ids))) THEN
        RAISE EXCEPTION 'SOE_INVALID_RESULT' USING ERRCODE='22023';
    END IF;
    SELECT min_players,max_players INTO minimum,maximum FROM public.format WHERE id=p_format;
    IF NOT FOUND THEN RAISE EXCEPTION 'SOE_FORMAT_NOT_FOUND' USING ERRCODE='22023'; END IF;
    IF cardinality(ids)<minimum OR (maximum IS NOT NULL AND cardinality(ids)>maximum) THEN
        RAISE EXCEPTION 'SOE_PARTICIPANT_COUNT' USING ERRCODE='22023';
    END IF;
    IF (SELECT count(*) FROM public.player WHERE id=ANY(ids))<>cardinality(ids) THEN
        RAISE EXCEPTION 'SOE_INVALID_PARTICIPANTS' USING ERRCODE='22023';
    END IF;
    PERFORM soe_private.check_start(ids,NULL,p_date,p_start,'PENDING');
    SELECT coalesce(jsonb_agg(m.id),'[]') INTO duplicate_ids FROM public.game_match m
      WHERE m.status<>'CANCELLED' AND m.community_id=p_community AND m.format_id=p_format
      AND m.approximate_start_time IS NOT NULL
      AND abs(extract(epoch FROM ((m.match_date+m.approximate_start_time)-(p_date+p_start))))<=7200
      AND (SELECT array_agg(player_id ORDER BY player_id) FROM public.match_participant WHERE match_id=m.id)=ids;
    IF jsonb_array_length(duplicate_ids)>0 THEN
        warnings:=warnings||jsonb_build_array(jsonb_build_object('code','possible_duplicate','match_ids',duplicate_ids,
            'message','Há partidas com os mesmos participantes próximas deste horário. Confira o histórico.'));
    END IF;
    IF EXISTS(SELECT 1 FROM public.game_match m JOIN public.match_participant mp ON mp.match_id=m.id
        WHERE mp.player_id=ANY(ids) AND m.match_date=p_date AND m.approximate_start_time IS NULL AND m.status<>'CANCELLED') THEN
        warnings:=warnings||jsonb_build_array(jsonb_build_object('code','unknown_historical_start',
            'message','Há partidas históricas sem início informado nesta data; esses conflitos não podem ser verificados.'));
    END IF;
    INSERT INTO public.game_match(community_id,format_id,created_by,match_date,approximate_start_time,context_type,status)
    VALUES(p_community,p_format,p_actor,p_date,p_start,'CASUAL','PENDING') RETURNING id INTO v_id;
    INSERT INTO public.match_participant(match_id,player_id,result)
    SELECT v_id,x,CASE WHEN p_draw THEN 'DRAW' WHEN x=p_winner THEN 'WIN' ELSE 'LOSS' END FROM unnest(ids) x;
    RETURN jsonb_build_object('id',v_id,'status','PENDING','warnings',warnings);
END;
$$;

-- Capacidades novas, não GRANTs de tabelas. Alteração de acesso exige aprovação.
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA soe_private FROM PUBLIC,anon,authenticated,service_role;
REVOKE ALL ON FUNCTION public.soe_catalog() FROM PUBLIC,anon,authenticated;
REVOKE ALL ON FUNCTION public.soe_identity(uuid) FROM PUBLIC,anon,authenticated;
REVOKE ALL ON FUNCTION public.soe_match_history(integer,integer,bigint) FROM PUBLIC,anon,authenticated;
REVOKE ALL ON FUNCTION public.soe_create_guest(uuid,text,bigint) FROM PUBLIC,anon,authenticated;
REVOKE ALL ON FUNCTION public.soe_register_match(uuid,bigint,bigint,date,time,bigint[],bigint,boolean) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.soe_catalog(),public.soe_identity(uuid),
 public.soe_match_history(integer,integer,bigint),public.soe_create_guest(uuid,text,bigint),
 public.soe_register_match(uuid,bigint,bigint,date,time,bigint[],bigint,boolean) TO service_role;
