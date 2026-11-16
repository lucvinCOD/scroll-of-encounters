-- Conta Supabase já autenticada: identidade recebida somente do backend.
-- Não modifica usuários existentes, políticas RLS ou permissões de tabelas.
CREATE OR REPLACE FUNCTION public.soe_identity(p_actor uuid)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = '' AS $$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM public.profile WHERE id=p_actor) THEN
        RETURN jsonb_build_object('id',p_actor,'username','','player_id',NULL,'needs_profile',true);
    END IF;
    PERFORM soe_private.assert_actor(p_actor);
    RETURN (SELECT jsonb_build_object('id',p.id,'username',p.username,
        'player_id',(SELECT id FROM public.player WHERE profile_id=p.id),'needs_profile',false)
        FROM public.profile p WHERE p.id=p_actor);
END;
$$;

CREATE OR REPLACE FUNCTION public.soe_complete_profile(p_actor uuid,p_username text,p_community bigint)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
    PERFORM pg_advisory_xact_lock(hashtextextended('soe/profile/'||p_actor::text,0));
    IF EXISTS(SELECT 1 FROM public.profile WHERE id=p_actor) THEN
        PERFORM soe_private.assert_actor(p_actor);
        RETURN public.soe_identity(p_actor);
    END IF;
    IF p_username IS NULL OR length(btrim(p_username)) NOT BETWEEN 3 AND 40 THEN
        RAISE EXCEPTION 'SOE_PROFILE_NAME' USING ERRCODE='22023';
    END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended('soe/username/'||lower(btrim(p_username)),0));
    IF EXISTS(SELECT 1 FROM public.profile WHERE lower(username)=lower(btrim(p_username))) THEN
        RAISE EXCEPTION 'SOE_USERNAME_UNAVAILABLE' USING ERRCODE='23505';
    END IF;
    -- A FK existente profile.id -> auth.users.id impede identidades inexistentes.
    INSERT INTO public.profile(id,username) VALUES(p_actor,btrim(p_username));
    INSERT INTO public.player(display_name,profile_id,community_id) VALUES(btrim(p_username),p_actor,p_community);
    RETURN public.soe_identity(p_actor);
END;
$$;
REVOKE ALL ON FUNCTION public.soe_complete_profile(uuid,text,bigint) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.soe_complete_profile(uuid,text,bigint) TO service_role;
