# Migrações — estado atual do MVP

Atualizado em 2026-11-11. **Supabase CLI é o único versionamento.** As três
versões abaixo foram aplicadas no projeto vinculado `ikmadcldfxvnupajxdwm`.

| Versão | Efeito e validação |
| --- | --- |
| `20261111000100` | Término opcional, sem apagar seus valores. Início já existia manualmente como TIME NULL. |
| `20261111000200` | Registro atômico PENDING, catálogo, histórico, convidados e identidade. Triggers de resultados/participantes/inícios e locks por jogador. Funções de aplicação executáveis somente por service_role, aprovadas na interface. |
| `20261111000300` | Criação atômica/idempotente de profile e player para uma conta Supabase autenticada. Usa a FK já existente para auth.users. Nenhuma conta ou perfil foi criado durante a aplicação. Acesso restrito aprovado na interface. |

Pós-verificação remota de 003: colunas, RLS, políticas e ACL das tabelas iguais
às de antes. As seis capacidades públicas têm EXECUTE somente para service_role
(além do proprietário); anon/authenticated não podem chamá-las. A chave privada
fica exclusivamente no backend. A partida id=1 foi preservada com início NULL,
término 10:30, data 2026-09-15 e status PENDING. Não houve backfill.

A regra bloqueante usa data + início, diferença estritamente inferior a dez
minutos, incluindo virada de dia, convidados e PENDING/VERIFIED/DISPUTED.
CANCELLED não conflita. Exatamente dez minutos é permitido. Advisory locks por
jogador e triggers protegem requisições concorrentes e alterações posteriores.
Resultados são validados no commit. Não há cotas de criação nem limite retroativo.
Duplicidades em aproximadamente duas horas geram avisos separados. Histórico sem
início não permite calcular conflito; permanece intacto e pode gerar aviso.

`approximate_end_time` e `daily_participation_limit` permanecem no banco, mas os
fluxos do MVP não os utilizam. O catálogo não expõe cota diária. A inspeção de
dependências encontrou somente o CHECK local da cota (duas entradas de catálogo)
e nenhuma dependência catalogada do término. Isso não elimina consumidores
externos/SQL dinâmico. Não há DROP pendente em migrations/. `min_players` e
`max_players` continuam sendo regras do tamanho da mesa e não foram alterados.

Testes atuais: unittest em `backend/tests/test_*.py`; os testes de 001 usam PGlite
em memória. `test_match_database.py` usa PostgreSQL 17.11 local descartável,
incluindo duas sessões concorrentes, reaplicação, atomicidade e acesso por roles.
As fixtures locais não são baseline nem seeds do remoto. Instalar
`backend/requirements-dev.txt` e `npm ci` na raiz antes da suíte completa.
No Windows os binários de teste são uma dependência opcional; em Linux configure
initdb/postgres no PATH. API e Scryfall também têm testes com transportes simulados.

Fluxo para qualquer **nova** versão, da raiz:

```powershell
npm.cmd run supabase -- migration list --remote
npm.cmd run supabase -- db push --remote --skip-vault --dry-run
```

Revisar somente as novas versões previstas, destino e preservação. Nunca editar
versões aplicadas ou reparar o ledger para forçar reaplicação. Aplicação de versão
não destrutiva revisada segue AGENTS.md; mudança de segurança/destrutiva exige
aprovação específica pela interface antes de `db push --remote --skip-vault --yes`.
`--yes` responde ao CLI **depois** da aprovação, não a substitui.

**Configuração de autenticação pendente:** `supabase/config.toml` declara
site_url `http://127.0.0.1:5173`; o remoto ainda usa `http://localhost:3000`.
`config diff --remote` confirmou uma única atualização declarada. `config push
--remote --yes` foi rejeitado pela revisão automática por afetar autenticação em
produção; aguarda aprovação específica do proprietário. Não desativar confirmação
de e-mail/MFA nem ampliar a allowlist como atalho. Configuração não é migração SQL.

As evidências de inspeção ficam em `supabase/.temp/mvp-audit/`, ignoradas pelo Git.
Validação de escrita autenticada real e entrega de e-mails ainda pendentes.

## Histórico da adoção inicial (001)

O registro abaixo preserva a documentação da etapa 001. Afirmações sobre ausência
de endpoints, regras ainda futuras ou versões pendentes descrevem **aquela etapa**;
o estado atual é a tabela e as orientações acima.

Atualizado em 2026-11-11. A versão `20261111000100` foi aplicada após autorização
explícita do proprietário no projeto remoto Scroll of Encounters
(`ikmadcldfxvnupajxdwm`, produção). O repositório está vinculado localmente ao
projeto; esse estado e os snapshots de verificação ficam ignorados pelo Git.
O PostgreSQL remoto foi identificado como 17.11. Não houve reparação manual do
histórico, alteração de dados ou mudança de RLS/permissões das tabelas verificadas.

## Estado remoto: manual versus pendente

| Item | Estado conhecido |
| --- | --- |
| `public.game_match.approximate_start_time` | Já adicionada manualmente como `TIME NULL`; data/comando exato dessa execução não informados. |
| `public.game_match.approximate_end_time` | Agora `TIME NULL`, alterada pela migração `20261111000100`; valores anteriores preservados. |
| Partida `id=1` | Verificada antes/depois: 2026-09-15, início NULL, término 10:30, status `PENDING`; linha preservada. |
| `public.format.daily_participation_limit` | Verificada como `integer NOT NULL`, sem default, com CHECK `> 0`; mantida intacta. Análise completa de dependências ainda pendente. |
| `format.min_players` / `format.max_players` | Definições e valores preservados; nenhuma alteração. |
| Histórico do CLI no remoto | Versão local e remota `20261111000100` sincronizadas; dry-run final sem pendências. |
| Versão `20261111000100` | Aplicada em 2026-11-11, com autorização, e registrada pelo próprio CLI. |

Nenhum início histórico será deduzido de término, duração ou criação do registro.
A existência manual de `approximate_start_time` não significa que a nova versão
já foi aplicada: ela altera a obrigatoriedade de OUTRA coluna.

## Estrutura única

```text
supabase/
  config.toml
  migrations/
    20261111000100_make_match_end_time_optional.sql
backend/migrations/
  README.md
  checks/
    001_schema_and_dependencies.sql
    002_match_history.sql
  plans/
    contract_legacy_columns.md
backend/tests/
  test_migrations.py
  pglite_bridge.mjs
package.json
package-lock.json
```

Somente `supabase/migrations/<timestamp_de_14_dígitos>_<nome>.sql` é executável
pelo versionamento. O CLI controla versões em
`supabase_migrations.schema_migrations`; não existe ledger próprio, runner
Python de produção, sequência `backend/migrations/versions` ou sistema `up/down`.
Os testes executam o SQL em memória, sem gerenciar histórico de implantação.

O Supabase CLI está fixado em 3.1.0 e o PGlite em 0.5.16 como devDependencies.
Node.js 20+ é necessário. Isso é tooling de banco, não um frontend ou nova
dependência do backend em produção. Usar `npm ci` para respeitar o lockfile.
O estado local do CLI, dependências e caches estão no `.gitignore`.

Revisão dos oito arquivos anteriores:

| Arquivo anterior | Destino/decisão |
| --- | --- |
| README | Substituído por este fluxo único. |
| checks/001 | Mantido e ampliado para inspecionar min_players/max_players. |
| checks/002 | Mantido e ampliado com snapshot de format. |
| versions/001_expand...up.sql | Substituído pela versão CLI 20261111000100, sem recriar início ausente. |
| versions/002_migrate...sql | Removido da sequência: não há transformação de dados; as leituras continuam em checks/002. |
| rollbacks/001_expand...down.sql | Substituído por plano de correção progressiva mediante nova versão CLI. |
| drafts/003_contract...sql | Convertido em plano não executável. |
| drafts/004_contract...sql | Convertido em plano não executável. |

## Expand: migração aplicada

`20261111000100_make_match_end_time_optional.sql` faz exclusivamente
`ALTER COLUMN approximate_end_time DROP NOT NULL`, condicionado ao catálogo.
A coluna de início deve existir como TIME nullable, não gerada. O término deve
existir como TIME não gerado. Ausência/tipo divergente interrompe a operação;
não há tentativa de reconstruir esquema desconhecido.

Validação e alteração ficam em uma única instrução `DO`, atômica. Um lock
exclusivo impede que outro DDL altere as pré-condições durante a operação.
O `lock_timeout` de 5 segundos limita a espera pelo lock e é restaurado ao final.
É um limite operacional de DDL, não de partidas. Planejar janela apropriada.

A migração preserva valores, defaults, precisão de TIME, início nullable, colunas
de formato, políticas e permissões. Não contém DML, seed, remoção de colunas ou
mudança de RLS. Defaults existentes são inspecionados, mas não reescritos.

Há duas proteções contra reaplicação: o histórico do CLI evita reaplicar versões
registradas, e o SQL não executa novo ALTER quando o término já está nullable.
Não editar versões aplicadas, apagar histórico ou usar `migration repair` para
forçar uma nova execução. A reparação do histórico remoto também é escrita e
exige aprovação própria.

## Migrate e Contract

Migrate, nesta mudança, é uma decisão explícita de não fazer backfill. Históricos
desconhecidos permanecem assim; não adicionar NOT NULL global ao início.
Consumidores futuros devem exigir início informado para novos registros sem
fabricar término. Não há endpoint de partidas implementado nesta tarefa.

`plans/contract_legacy_columns.md` prepara a remoção futura do limite diário e,
separadamente, do término. Nenhuma dessas remoções está em migrations/ e nenhuma
será executada no próximo push. O tipo/default do limite foi observado, mas
as demais definições e dependências ainda precisam de análise completa.
Backup/recuperação, dependências e aprovação destrutiva continuam pendentes.
`min_players` e `max_players` não devem ser modificados.

Não há referência às colunas antigas nem consulta a format em `backend/app`.
Os services atuais consultam somente game/player. Isso não elimina dependências
remotas ou externas: revisar catálogo, rotinas, triggers, views, jobs e clientes.
`pg_depend` e busca textual são triagens incompletas. `DROP COLUMN ... RESTRICT`
também pode remover índices/constraints locais e não substitui essa análise.

Se precisar restaurar NOT NULL no término, usar nova migração corretiva após
verificar ausência de términos nulos; não preencher nulos para forçar reversão.
A coluna de início manual deve continuar preservada.

## Baseline de um banco existente

Esta é uma adoção incremental: não há DDL completo suficiente para recriar
o projeto vazio. Não foi inventada baseline nem criada migração vazia marcada
como aplicada. Não executar `db reset`, `start` ou reconstrução do banco a partir
somente desta pasta esperando obter o esquema completo.

Antes do primeiro push, inspecionar o histórico remoto. Se houver versões
remotas ausentes localmente, recuperar e revisar as migrações reais no mesmo
histórico CLI, sem apagá-las ou usar `--include-all` para contornar divergências.
Não fabricar entradas em `schema_migrations`. Para reconstrução completa futura,
capturar uma baseline real do banco e planejar sua reconciliação separadamente.
`db pull` pode propor escrita no histórico remoto; não tratá-lo como leitura
incondicional nem executá-lo com aceitação automática.

## Comandos e aprovação

Da raiz do repositório, instalar tooling e rodar testes exclusivamente locais:

```powershell
npm.cmd ci --no-fund --no-audit
.\backend\.venv\Scripts\python.exe -B -m unittest discover -s backend/tests -p "test_*.py" -v
npm.cmd run supabase -- --version
npm.cmd run supabase -- db push --help
```

Os testes usam unittest da biblioteca padrão e PostgreSQL 18.6/WASM via PGlite,
em memória, sem Docker, servidor, DSN, .env ou acesso remoto. Fixtures descartáveis
não são DDL/seed da aplicação. Cobrem preservação de linhas e formatos,
nullable, defaults/precisão, reaplicação com novos términos nulos, schema
incompatível, rollback transacional e execução das consultas de inspeção.
O CLI também aceitou a configuração num teste de criação de migração em pasta
temporária, sem banco. Não cobrem comportamento de
rede, lock entre sessões, permissões/RLS reais ou o ledger remoto do CLI.
A versão real do PostgreSQL remoto foi confirmada como 17.11 na aplicação.

Antes de qualquer aplicação remota: revisar backup, resultado dos checks e o
projeto de destino, autenticar via `npm.cmd run supabase -- login` e vincular via
`npm.cmd run supabase -- link --project-ref <referência-confirmada>`. O vínculo
foi realizado nesta aplicação, depois do login pelo proprietário.
Não colocar senha/token na linha de comando
ou no Git; usar o fluxo seguro do CLI. Evitar `--debug` com credenciais.

Após autorizar acesso de leitura, executar os dois arquivos de checks no SQL
Editor, um por vez, e obter a comparação antes/depois. Verificar visibilidade
adequada sem desabilitar RLS. Nunca considerar uma contagem parcial como prova
de preservação global. Preservar snapshots fora do Git.

Com o projeto correto vinculado e acesso autorizado, revisar histórico e plano:

```powershell
npm.cmd run supabase -- migration list --remote
npm.cmd run supabase -- db push --remote --skip-vault --dry-run
```

Interromper se houver histórico incompatível ou qualquer migração pendente além
de `20261111000100`. Não incluir seeds/roles nem executar reparos automaticamente.
O dry-run não aplica a migração, mas conecta ao remoto. Nesta aplicação ele foi
executado antes e depois, confirmando respectivamente uma versão e zero pendências.

**Comando de escrita que requer aprovação explícita**, após esses pré-requisitos:

```powershell
npm.cmd run supabase -- db push --remote --skip-vault
```

`--remote` aponta ao projeto vinculado; `--skip-vault` evita sincronização de
segredos do Vault. As flags foram conferidas na ajuda do CLI 3.1.0 instalado.
Não usar `--yes` para antecipar a aprovação. O push aplica migrações pendentes
e registra a versão no histórico CLI, não apenas o DDL da coluna.

Depois, repetir checks/001 e checks/002 e listar o histórico. Conferir término
nullable, início inalterado, linha id=1 e formatos preservados. Um segundo
dry-run deve indicar ausência de migrações pendentes.

Revisar também se CHECKs ou triggers existentes impõem término obrigatório;
esta migração não remove restrições desconhecidas para contorná-las.

## Registro da aplicação — 2026-11-11

- O proprietário autorizou a aplicação. Projeto ativo confirmado por nome e
  referência; vínculo local realizado com o CLI.
- Histórico prévio e dry-run listaram somente a versão `20261111000100` pendente.
- Consulta remota somente de leitura confirmou TIME nullable no início,
  TIME NOT NULL no término e ausência de trigger de usuário ou CHECK exigindo
  término. Havia uma partida e um formato.
- O primeiro push sem `--yes` foi recusado pelo próprio CLI em modo agente;
  nada foi aplicado nessa tentativa. A autorização já existente permitiu
  confirmar a mesma operação, sem ampliar seu escopo, com:

  ```powershell
  npm.cmd run supabase -- db push --remote --skip-vault --yes
  ```

- A aplicação terminou com sucesso, sem seeds ou roles adicionais. O histórico
  remoto passou a registrar `20261111000100`; dry-run posterior retornou
  `upToDate: true` e nenhuma migração pendente.
- Comparação antes/depois confirmou como única diferença de esquema inspecionada
  `approximate_end_time.not_null: true -> false`. Contagens e hashes dos dados
  completos de game_match e format foram iguais. A linha 1 permaneceu intacta.
- Defaults, precisão/tipos, demais colunas, constraints, triggers, políticas,
  configurações de RLS e ACL das duas tabelas permaneceram iguais.
- Evidências locais da comparação ficam em
  `supabase/.temp/migration-verification/`, ignorado pelo Git. São evidências
  pontuais de verificação, não uma baseline nem backup completo do banco.
- Não houve commit/push Git, remoção de coluna, preenchimento de início ou
  alteração de min_players/max_players/daily_participation_limit.

## Requisitos futuros preservados

Registro ilimitado, inclusive retroativo. Conflitos bloqueantes com diferença
absoluta entre data + início inferior a 10 minutos para qualquer participante,
inclusive convidado persistente e partidas pendentes; exatamente 10 minutos é
permitido. Revalidar edições de data/início/participantes, com checagem e gravação
atômicas e proteção entre sessões concorrentes em todos os caminhos de escrita.
Não usar término/duração. Possível duplicidade em aproximadamente duas horas
continua aviso não bloqueante separado.

Essa regra ainda não está implementada. Confirmar esquema dos participantes,
convenção de fuso (TIME sozinho não identifica um instante global), estados
relevantes e tratamento dos históricos sem início antes de liberar POST /matches.

Referências oficiais: [Supabase CLI](https://supabase.com/docs/reference/cli/supabase-db-push),
[migrações](https://supabase.com/docs/guides/local-development/database-migrations),
[ALTER TABLE](https://www.postgresql.org/docs/16/sql-altertable.html) e
[PGlite em memória](https://pglite.dev/docs/).
