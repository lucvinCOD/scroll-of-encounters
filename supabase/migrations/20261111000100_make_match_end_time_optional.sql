-- EXPAND: somente a obrigatoriedade do término muda.
-- O início foi criado manualmente e é uma pré-condição, não um backfill.
-- Uma única instrução DO mantém validação e DDL atômicos, inclusive fora do CLI.
DO $migration$
DECLARE
    start_column record;
    end_column record;
    previous_lock_timeout text := pg_catalog.current_setting('lock_timeout');
BEGIN
    PERFORM pg_catalog.set_config('lock_timeout', '5s', true);
    LOCK TABLE public.game_match IN ACCESS EXCLUSIVE MODE;

    SELECT a.atttypid, a.attnotnull, a.attidentity, a.attgenerated
    INTO start_column
    FROM pg_catalog.pg_attribute AS a
    WHERE a.attrelid = 'public.game_match'::pg_catalog.regclass
      AND a.attname = 'approximate_start_time'
      AND a.attnum > 0 AND NOT a.attisdropped;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Pré-condição ausente: approximate_start_time deve existir antes desta migração.';
    END IF;
    IF start_column.atttypid <> 'time without time zone'::pg_catalog.regtype
       OR start_column.attnotnull
       OR start_column.attidentity <> '' OR start_column.attgenerated <> '' THEN
        RAISE EXCEPTION 'Schema divergente: approximate_start_time deve ser TIME nullable e não gerado.';
    END IF;

    SELECT a.atttypid, a.attnotnull, a.attidentity, a.attgenerated
    INTO end_column
    FROM pg_catalog.pg_attribute AS a
    WHERE a.attrelid = 'public.game_match'::pg_catalog.regclass
      AND a.attname = 'approximate_end_time'
      AND a.attnum > 0 AND NOT a.attisdropped;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Pré-condição ausente: approximate_end_time deve existir antes desta migração.';
    END IF;
    IF end_column.atttypid <> 'time without time zone'::pg_catalog.regtype
       OR end_column.attidentity <> '' OR end_column.attgenerated <> '' THEN
        RAISE EXCEPTION 'Schema divergente: approximate_end_time deve ser TIME e não gerado.';
    END IF;

    -- Reaplicação não executa novo ALTER nem modifica registros existentes.
    IF end_column.attnotnull THEN
        ALTER TABLE public.game_match
            ALTER COLUMN approximate_end_time DROP NOT NULL;
    END IF;

    PERFORM pg_catalog.set_config('lock_timeout', previous_lock_timeout, true);
END;
$migration$;
