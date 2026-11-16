-- Somente leitura. Não gera início nem altera a partida de teste.
-- Comparar a evidência antes/depois em ambiente com visibilidade adequada.
BEGIN TRANSACTION READ ONLY;

SELECT
    count(*) AS visible_matches,
    count(*) FILTER (WHERE approximate_start_time IS NULL) AS unknown_starts,
    count(*) FILTER (WHERE approximate_end_time IS NULL) AS unknown_ends,
    count(*) FILTER (WHERE approximate_end_time IS NOT NULL) AS recorded_ends
FROM public.game_match;

-- O cast evita presumir que o identificador seja inteiro ou UUID.
-- Não transforma os valores da linha em uma asserção sobre o tipo físico.
SELECT id, match_date, approximate_start_time, approximate_end_time, status
FROM public.game_match
WHERE id::text = '1';

-- Snapshot dos formatos antes/depois, sem presumir tipo de identificador.
-- Inclui min_players/max_players e permite conferir a preservação de tudo.
SELECT pg_catalog.to_jsonb(f) AS format_snapshot
FROM public.format AS f
ORDER BY pg_catalog.to_jsonb(f)::text;

COMMIT;
