-- Somente leitura. Preparado localmente; não executado no Supabase.
-- Capturar o resultado antes da expansão e repetir após cada etapa autorizada.
BEGIN TRANSACTION READ ONLY;

-- Baseline parcial: não pressupõe tipo/default do limite diário.
WITH requested(table_name, column_name) AS (
    VALUES
        ('game_match', 'approximate_end_time'),
        ('game_match', 'approximate_start_time'),
        ('game_match', 'match_date'),
        ('game_match', 'id'),
        ('game_match', 'status'),
        ('format', 'daily_participation_limit'),
        ('format', 'min_players'),
        ('format', 'max_players')
)
SELECT
    'public' AS schema_name,
    r.table_name,
    r.column_name,
    a.attnum IS NOT NULL AS found,
    pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type,
    a.attnotnull AS not_null,
    a.attidentity AS identity_kind,
    a.attgenerated AS generated_kind,
    pg_catalog.pg_get_expr(d.adbin, d.adrelid) AS default_or_generation_expression
FROM requested AS r
LEFT JOIN pg_catalog.pg_namespace AS n ON n.nspname = 'public'
LEFT JOIN pg_catalog.pg_class AS c
    ON c.relnamespace = n.oid AND c.relname = r.table_name
    AND c.relkind IN ('r', 'p')
LEFT JOIN pg_catalog.pg_attribute AS a
    ON a.attrelid = c.oid AND a.attname = r.column_name
    AND a.attnum > 0 AND NOT a.attisdropped
LEFT JOIN pg_catalog.pg_attrdef AS d
    ON d.adrelid = a.attrelid AND d.adnum = a.attnum
ORDER BY r.table_name, r.column_name;

-- Todas as constraints locais; DROP COLUMN pode eliminar algumas automaticamente.
SELECT
    c.relname AS table_name,
    con.conname AS constraint_name,
    con.contype AS type_code,
    con.convalidated AS validated,
    pg_catalog.pg_get_constraintdef(con.oid, false) AS definition
FROM pg_catalog.pg_constraint AS con
JOIN pg_catalog.pg_class AS c ON c.oid = con.conrelid
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relname IN ('game_match', 'format')
ORDER BY c.relname, con.conname;

-- Dependências de coluna e também de tabela inteira (triagem conservadora).
WITH targets AS (
    SELECT c.oid AS table_oid, c.relname AS table_name,
           a.attnum, a.attname AS column_name
    FROM pg_catalog.pg_class AS c
    JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
    JOIN pg_catalog.pg_attribute AS a ON a.attrelid = c.oid
    WHERE n.nspname = 'public' AND a.attnum > 0 AND NOT a.attisdropped
      AND (
          (c.relname = 'game_match' AND a.attname = 'approximate_end_time')
          OR (c.relname = 'format' AND a.attname = 'daily_participation_limit')
      )
)
SELECT
    t.table_name, t.column_name, d.deptype AS dependency_type,
    d.refobjsubid = 0 AS whole_table_dependency,
    pg_catalog.pg_describe_object(d.classid, d.objid, d.objsubid) AS dependent_object
FROM targets AS t
JOIN pg_catalog.pg_depend AS d
    ON d.refclassid = 'pg_catalog.pg_class'::pg_catalog.regclass
    AND d.refobjid = t.table_oid AND d.refobjsubid IN (0, t.attnum)
ORDER BY t.table_name, t.column_name, dependent_object;

-- Índices, triggers e políticas: evidência para revisão, não alteração.
SELECT schemaname, tablename, indexname, indexdef
FROM pg_catalog.pg_indexes
WHERE schemaname = 'public' AND tablename IN ('game_match', 'format')
ORDER BY tablename, indexname;

SELECT c.relname AS table_name, t.tgname AS trigger_name,
       pg_catalog.pg_get_triggerdef(t.oid, false) AS definition
FROM pg_catalog.pg_trigger AS t
JOIN pg_catalog.pg_class AS c ON c.oid = t.tgrelid
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relname IN ('game_match', 'format')
  AND NOT t.tgisinternal
ORDER BY c.relname, t.tgname;

SELECT schemaname, tablename, policyname, roles, cmd, qual, with_check
FROM pg_catalog.pg_policies
WHERE schemaname = 'public' AND tablename IN ('game_match', 'format')
ORDER BY tablename, policyname;

-- Triagem textual em rotinas e views não sistêmicas; incluir "format" também
-- encontra leituras genéricas da tabela, com possíveis falsos positivos.
-- Não cobre SQL dinâmico, fragmentos, jobs nem consumidores externos.
SELECT n.nspname AS schema_name, p.proname AS routine_name,
       pg_catalog.pg_get_function_identity_arguments(p.oid) AS arguments,
       p.prosrc AS body_for_review
FROM pg_catalog.pg_proc AS p
JOIN pg_catalog.pg_namespace AS n ON n.oid = p.pronamespace
WHERE n.nspname !~ '^pg_' AND n.nspname <> 'information_schema'
  AND p.prokind IN ('f', 'p')
  AND p.prosrc ~* '(approximate_end_time|daily_participation_limit|game_match|format)'
ORDER BY n.nspname, p.proname, arguments;

SELECT schemaname, viewname AS object_name, definition
FROM pg_catalog.pg_views
WHERE schemaname !~ '^pg_' AND schemaname <> 'information_schema'
  AND definition ~* '(approximate_end_time|daily_participation_limit|game_match|format)'
UNION ALL
SELECT schemaname, matviewname AS object_name, definition
FROM pg_catalog.pg_matviews
WHERE schemaname !~ '^pg_' AND schemaname <> 'information_schema'
  AND definition ~* '(approximate_end_time|daily_participation_limit|game_match|format)'
ORDER BY schemaname, object_name;

COMMIT;
