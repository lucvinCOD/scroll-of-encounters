# Contração futura — não é uma migração executável

Os rascunhos SQL numerados de 2026-11-09 foram substituídos por este plano.
Somente `supabase/migrations/` participa do histórico do Supabase CLI.
Nenhuma remoção é aplicada pelo próximo `db push`.

## Remover daily_participation_limit

Verificado no MVP de 2026-11-11: backend/frontend não usam essa cota.
`soe_catalog` consulta format, mas seleciona campos explícitos e omite o limite.
`soe_register_match` e as constraints usam min_players/max_players, preservados.
Isso não confirma ausência de dependências no banco ou em consumidores externos.

A inspeção remota do MVP encontrou somente o CHECK local da cota e nenhuma
dependência catalogada do término. Não foi removido qualquer objeto. As duas
entradas de pg_depend para a cota apontam ao mesmo CHECK; não são duas regras
de produto distintas. Rotinas com SQL dinâmico e consumidores externos continuam
dependendo de análise. A remoção não faz parte das migrações 001, 002 ou 003.

Na verificação remota de 2026-11-11, observou-se `integer NOT NULL`, sem default,
e CHECK `daily_participation_limit > 0`. Os dados e definições de format foram
preservados durante a expansão do término. Isso é uma inspeção parcial: ainda
não houve levantamento completo de referências, consumidores e recuperação,
portanto a remoção continua pendente e fora da pasta de migrações executáveis.

Antes de criar uma migração executável:

1. Executar, com autorização de leitura, `checks/001_schema_and_dependencies.sql`.
   Capturar tipo exato, nullability, default, constraints, índices, dependências,
   funções, triggers e políticas. A inspeção inclui `min_players` e `max_players`.
2. Revisar funções com `SELECT *`, SQL dinâmico, jobs, relatórios e consumidores
   externos. A triagem textual e `pg_depend` não são prova completa de ausência.
3. Retirar o uso da cota dos consumidores antes da contração, preservando as
   regras de quantidade de participantes por mesa (`min_players`/`max_players`).
4. Obter backup protegido da definição, valores e dependências e testar a
   recuperação. Não colocar dados/credenciais no Git. Não presumir INTEGER,
   default ou CHECK para a coluna antiga.
5. Registrar a análise e obter aprovação explícita para a remoção/perda desses
   valores. Uma coluna recriada não restaura seus dados ou dependências.
6. Criar uma nova migração com `npm.cmd run supabase -- migration new
   remove_daily_participation_limit`, em um único comando. Revisar o SQL gerado.

A intenção, somente depois dessas etapas, é remover exclusivamente
`public.format.daily_participation_limit`, usando `RESTRICT`, sem `CASCADE` e sem
qualquer alteração em `min_players` ou `max_players`. Mesmo `RESTRICT` permite
remoção automática de certos índices/constraints locais; revisar esses objetos
antes. Comparar snapshots completos de `format` e definições das duas colunas
protegidas antes/depois, descontando apenas a coluna removida e dependências
explicitamente aprovadas.

## Remover approximate_end_time

A próxima migração mantém a coluna e seus valores. Uma futura remoção requer
migrar consumidores, inspecionar dependências e definir retenção/arquivamento ou
autorizar perda dos términos. A partida id=1 contém término 10:30; não apagar,
editar ou fabricar seu início para liberar essa etapa.

## Reversão da expansão

Não há mais arquivo `.down.sql` paralelo. Se for necessário restaurar `NOT NULL`
no término, criar uma NOVA migração Supabase corretiva, depois de confirmar que
nenhuma linha contém término nulo. O PostgreSQL deverá rejeitar a mudança caso
existam nulos; não os preencher para forçar a reversão. Preservar a coluna de
início, que já existia manualmente. Corrigir progressivamente quando a reversão
for incompatível com registros novos. Não marcar versões como revertidas para
obrigar sua reaplicação e não editar uma migração já aplicada.
