# Contas, papéis e permissões

Implementação em 2026-11-11, branch `feat/mvp-web`. A migração 004 foi aplicada
no remoto após aprovação específica do proprietário. O bootstrap da conta do
proprietário também foi executado, somente depois da confirmação do UUID ativo
e de uma segunda aprovação específica. Há um ADMIN e nenhum moderador designado.

## Modelo e matriz de acesso

O login é o mesmo para todos. USER é o acesso padrão de qualquer conta, inclusive
enquanto falta completar o perfil. A atribuição de MODERATOR pertence a uma ou
mais comunidades. ADMIN é global e já inclui acesso à moderação de todas elas;
o proprietário usa uma única conta pessoal, sem login administrativo compartilhado.
O papel retornado é o de maior alcance; vínculos de comunidade são retornados
separadamente. Remover ADMIN preserva eventuais vínculos de moderação existentes.

| Operação | USER | MODERATOR | ADMIN |
| --- | --- | --- | --- |
| Navegação comum e registro autenticado | Sim, após perfil | Sim | Sim |
| Consultar disputa e decisões | Não | Comunidades vinculadas | Todas as comunidades |
| Resolver disputa | Não | Escopo próprio, sem envolvimento | Qualquer comunidade, sem envolvimento |
| Consultar perfis/papéis administrativos | Não | Não | Sim |
| Designar/remover moderador | Não | Não | Sim, com justificativa |
| Consultar auditoria global | Não | Não | Sim |
| Conceder/remover ADMIN | Não | Não | Somente operador de banco, procedimento separado |

Os privilégios especiais são registros privados no banco, não campos escolhidos
no cadastro nem metadados do usuário/JWT. O FastAPI valida o token com Supabase
Auth e recebe desse serviço o UUID confiável. Todas as rotas protegidas consultam
novamente a identidade no banco; as funções SQL verificam novamente o ator e seu
escopo. Revogar acesso tem efeito na próxima verificação sem esperar expirar JWT.

No React, foco da janela, retorno à aba e navegação reconsultam a identidade.
Chamadas simultâneas compartilham uma consulta; respostas antigas não substituem
um login/logout posterior. Ocultar links é somente apresentação. A autorização
efetiva permanece no FastAPI/PostgreSQL. Sem sessão válida: 401. Sem permissão:
403. Escritas por cookies continuam exigindo Origin confiável. Tokens não vão
para localStorage/sessionStorage. Confirmação de e-mail e recuperação permanecem.

## Migração versionada e impacto

`supabase/migrations/20261111000400_account_permissions_and_moderation.sql`
acrescenta três tabelas no schema privado já existente `soe_private`:

- `platform_admin`: atribuição global por profile.id e data de concessão.
- `community_moderator`: profile.id + community.id, quem atribuiu e quando.
- `security_audit`: ator autenticado, operador SQL, alvo, comunidade/partida,
  ação, valores anteriores/posteriores, justificativa e data do banco.

Todas têm RLS habilitada e nenhuma política cliente, portanto default deny.
Nenhum privilégio direto nessas tabelas é concedido a anon/authenticated/service_role.
Somente as funções específicas de aplicação são executáveis por service_role;
essa chave fica exclusivamente no backend. Funções SECURITY DEFINER têm
search_path fixo; helpers e bootstrap não são executáveis pelas roles clientes.
Não se confunde o papel ADMIN da aplicação com a role técnica service_role.

A migração amplia a identidade com papel/escopos e cria seis capacidades de
administração/moderação, índices e trigger que recusa UPDATE/DELETE da auditoria.
Não apaga dados, promove contas, preenche horários, altera RLS das tabelas antigas
ou modifica min_players/max_players. Não implementa DROP das colunas legadas.
USER implícito dispensa backfill. As tabelas são adicionadas vazias.

Mudanças de permissões obtêm um advisory lock exclusivo; operações protegidas
obtêm lock compartilhado antes de consultar privilégios. Uma operação já autorizada
pode concluir antes de a revogação conseguir seu lock; depois do commit da
revogação, as próximas operações são negadas. READ COMMITTED é exigido nesse
caminho. Não se promete cancelar uma transação que já concluiu.

Auditoria e mutação ficam na mesma transação. Falha na auditoria desfaz a mudança.
O operador/proprietário do banco continua sendo uma fronteira de confiança:
superusuários podem alterar a própria infraestrutura; RLS não protege contra
comprometimento da chave privada ou do proprietário. Nenhuma permissão ampla é
concedida para contornar isso. Leituras administrativas são paginadas/no-store,
sem e-mails, senhas, tokens ou dados brutos de auth.users. A listagem de contas
inclui perfis concluídos; cadastro ainda sem perfil tem USER, mas não é listado ali.

## Regra de resolução de disputas

A fila contém somente partidas DISPUTED das comunidades autorizadas. Detalhes
incluem data/início, comunidade, formato, autor público, participantes, resultados
e decisões anteriores. A tabela atual não contém justificativa original de
contestação: a interface informa essa ausência; não fabrica motivos. A criação
de contestações/confirmacões por participantes é uma etapa posterior, fora desta
missão de contas. Partidas DISPUTED existentes já podem ser analisadas.

Após consultar as informações e os envolvidos, o responsável escolhe:

- **VERIFY:** manter os resultados relatados e marcar VERIFIED após análise.
  O banco revalida resultado e quantidade de participantes. É uma confirmação
  por decisão de moderação; passa a contar nas estatísticas de partidas verificadas.
- **CANCEL:** marcar CANCELLED e manter a partida/participantes para histórico.
  Não conta nas estatísticas e não bloqueia registros pela regra de início.
  Permite invalidar inclusive registros legados com resultado incompleto.

As duas decisões exigem justificativa de 10 a 2000 caracteres. Não permitem
trocar vencedor, participantes, comunidade, formato ou horário. Corrigir conteúdo
e invalidar confirmações exigirá um fluxo futuro específico, não edição implícita.

Quem participou **ou publicou** a partida não pode decidir. Esta proteção também
vale para ADMIN: outro responsável autorizado e não envolvido precisa analisar.
O bloqueio usa profile_id dos participantes e created_by, nunca nomes ou campos
de autoria enviados pelo cliente. Convidados não recebem voto nem moderação.

A identificação automática da participação depende do vínculo player.profile_id.
Participação antiga como convidado ainda sem vínculo com uma conta não permite
identificar com certeza a mesma pessoa. Não se faz associação por nome ou
homônimos; esse vínculo histórico exige um fluxo futuro de comprovação. O
responsável também deve declarar seu impedimento quando reconhecer envolvimento
que ainda não esteja registrado, encaminhando o caso a outra pessoa autorizada.

A partida fica bloqueada durante a decisão, serializando com os triggers de
participantes existentes. Duas decisões simultâneas não podem ambas concluir;
a segunda recebe 409. A auditoria armazena o estado analisado, resultado da
decisão, UUID/nome do responsável, justificativa e horário do banco. Dados
históricos e a regra estrita de conflito de início inferior a dez minutos são
preservados. Exatamente dez minutos continua permitido; não há cotas diárias.

## Rotas e telas

| Método e rota | Acesso |
| --- | --- |
| GET /auth/permissions | Própria identidade autenticada |
| GET /admin/users?q=&limit=20&offset=0 | ADMIN, perfis e escopos sem e-mail |
| POST /admin/moderators | ADMIN, conceder/revogar vínculo com justificativa |
| GET /admin/audit?limit=20&offset=0 | ADMIN |
| GET /moderation/matches?community_id=1&limit=20&offset=0 | MODERATOR no escopo ou ADMIN |
| GET /moderation/matches/{id} | MODERATOR no escopo ou ADMIN |
| POST /moderation/matches/{id}/resolution | Responsável autorizado, não envolvido |

Telas: `#/administracao`, `#/moderacao` e `#/moderacao?match=ID`. Possuem
carregamento, erro, vazio, acesso negado e resultados reais das rotas acima.
Nenhum papel/partida fictício é colocado no frontend para demonstrar privilégios.

Exemplo de contrato de vínculo, não executado em conta real:

```json
{"profile_id":"UUID_DO_PERFIL","community_id":1,"enabled":true,"reason":"Responsável designado para a comunidade."}
```

Para remover, enviar enabled false. Para decidir uma disputa:

```json
{"decision":"VERIFY","reason":"Resultado conferido com os participantes envolvidos."}
```

O ator vem exclusivamente da sessão. Campos extras (role, actor, permissões no
cadastro, alterações de participantes na decisão) são rejeitados.

## Aprovação e aplicação remota

A inspeção de leitura confirmou oito tabelas públicas com RLS ativo, sem tabelas
de papéis/disputas e somente uma política pública de SELECT em game. Histórico
remoto sincronizado até 003. Dry-run da nova etapa listou somente 004, sem
seeds/roles adicionais. Evidências privadas ignoradas: `.temp/permissions-audit`
dentro de supabase/. Nunca colocar snapshots de dados/credenciais no Git.

Fluxo revisado e executado, após aprovação específica pela interface:

```powershell
npm.cmd run supabase -- migration list --remote
npm.cmd run supabase -- db push --remote --skip-vault --dry-run
# Conferir projeto ikmadcldfxvnupajxdwm e somente a versao 20261111000400.
# SOMENTE DEPOIS DA APROVACAO:
npm.cmd run supabase -- db push --remote --skip-vault --yes
```

Verificação posterior: histórico/dry-run sincronizados, nenhuma migração pendente;
RLS habilitada e nenhum acesso direto das roles clientes nas três novas tabelas.
As doze capacidades públicas continuam restritas a service_role; o bootstrap
não é executável por essa role. Hashes/contagens dos dados e definições das oito
tabelas antigas, RLS/ACL/políticas e linha histórica id=1 ficaram iguais.
Contagens imediatamente após a migração: zero ADMINs, zero moderadores, zero eventos. Evidências ignoradas
em supabase/.temp/permissions-audit/{pre-apply,post-apply,empty-assignments}.json.
Aplicação da migração e promoção de uma conta são aprovações distintas.
Não editar versões já aplicadas
nem usar migration repair para forçar reaplicação. Reaplicar localmente preserva
atribuições/auditoria; o CLI também controla o histórico. Rollback deve ser uma
correção versionada revisada, preservando auditoria, não um DROP automático.

## Configurar a primeira conta ADMIN com segurança

1. O proprietário cria e confirma sua própria conta e conclui seu perfil.
   O UUID é o retornado por GET /auth/me, também disponível na identificação
   da própria conta em `#/perfil`. Conferir o mesmo UUID no Supabase Auth/perfil
   pelo operador. Não usar apenas e-mail, nome público ou ordem de cadastro.
2. Após aplicar 004, gerar uma operação **somente para revisão**, da raiz:

   ```powershell
   .\backend\.venv\Scripts\python.exe backend/scripts/admin_operation.py --operation bootstrap --profile-id "UUID_CONFIRMADO" --reason "Bootstrap solicitado e aprovado pelo proprietário."
   ```

   O gerador valida o UUID/justificativa e grava SQL em
   `supabase/.temp/permission-operations/`, ignorado pelo Git. Nunca conecta ao
   Supabase nem aplica a operação. Não aceita UUID nulo, primeiro usuário ou e-mail.
3. Conferir projeto vinculado, UUID, SQL e justificativa. Solicitar aprovação
   específica **para promover esse UUID real**. Com o operador autenticado e a
   aprovação concedida, executar o comando exato impresso pelo gerador:

   ```powershell
   npm.cmd run supabase -- db query --remote --file "CAMINHO_DO_SQL_REVISADO" --yes
   ```

   Esse comando é de escrita, não usar --read-only. Foi executado nesta tarefa
   somente para o UUID do proprietário, após aprovação específica da promoção.
   O SQL chama soe_private.manage_admin apenas como operador/proprietário. O
   backend/service_role não pode executar esse procedimento. Bootstrap só funciona
   quando não existe ADMIN; não há fallback automático para promover outra conta.
4. Reconsultar /auth/me ou atualizar o navegador: role ADMIN; aparecem as duas
   áreas. Conferir evento BOOTSTRAP_ADMIN na auditoria. Nenhuma senha ou token
   deve ser enviado no chat ou incluído na justificativa do operador.

Para novos ADMINs ou revogação futura, o mesmo gerador tem --operation grant ou
revoke. Exigem novas aprovações específicas e operador; não há endpoint de
autopromoção nem botão público. Não é permitido remover o último ADMIN.

## Designar o primeiro MODERATOR

Com a conta ADMIN configurada: abrir Administração, localizar um perfil concluído,
selecionar a conta e a comunidade, escolher Designar moderador e justificar.
Conferir o evento MODERATOR_GRANTED e reconsultar a sessão da pessoa designada.
Para uma segunda comunidade, repetir o vínculo; isso não concede ADMIN.
Para revogar, selecionar a mesma conta/comunidade e Remover vínculo de moderação.
A pessoa continua USER e conserva os outros vínculos. ADMIN já modera globalmente,
portanto o proprietário não precisa criar uma segunda conta de moderador.

## Arquivos e verificação

- Banco: migração 004; nenhum arquivo de migração aplicado foi reescrito.
- Backend: app/permissions.py, routers/governance.py, services/governance.py;
  registro em main.py, contratos em models.py e erros seguros em db.py.
- Operador: backend/scripts/admin_operation.py (gera SQL, não executa).
- Frontend: PermissionGate, AdminPage, ModerationPage, services/permissions.ts;
  tipos, navegação, AppContext e estilos existentes ampliados.
- Testes: test_permissions_database.py (PostgreSQL local real),
  test_permissions_api.py (Auth/transportes simulados) e permissions.test.ts.

Executar da raiz a suíte unittest documentada no README; em frontend/, npm test
e npm run build. Os testes cobrem USER padrão, seleção de papel rejeitada,
autopromoção negada, escopo de múltiplas comunidades, autoria/participação,
decisão e auditoria atômicas, bootstrap único, último ADMIN, escaping do SQL do
operador, revogação concorrente, RLS default deny e reaplicação sem perda de dados.
Testes locais não significam implantação remota ou promoção de contas reais.

Resultados executados nesta etapa:

- **79 testes do backend passaram**, incluindo 15 de permissões em PostgreSQL
  local real e 10 de autorização HTTP com Auth/transportes simulados. As 54
  verificações anteriores de partidas, migrações, acesso e Scryfall continuam passando.
- **15 testes do frontend passaram**, incluindo apresentação por papel e remoção
  da navegação após receber permissões revogadas.
- **npm run build concluiu**, TypeScript e Vite, 38 módulos.
- HTTP real pelo proxy Vite: /api/admin/users, /api/moderation/matches e
  /api/auth/permissions retornaram 401 sem sessão. Token inválido também retornou
  401 após consulta ao Supabase Auth real. Nenhum registro foi criado nesse teste.
- /, /docs, /catalog, /matches/ e a busca real de Sol Ring retornaram 200;
  o proxy /api/catalog continuou funcionando.
- Após aplicar 004, a nova RPC de consulta administrativa no Supabase real
  rejeitou um ator inexistente com HTTP 403; o cache da API reconheceu a função.
  A chave privada não foi encontrada nos arquivos do build frontend.
- Scanner de arquivos versionáveis sem segredos e git diff --check sem erros.
  Starlette mantém o aviso conhecido de depreciação httpx nos testes, sem falhas.

Bootstrap remoto concluído após a segunda aprovação específica: um ADMIN,
um evento BOOTSTRAP_ADMIN para o UUID aprovado e zero vínculos de MODERATOR.
A identidade retornada pela Supabase Data API é ADMIN. Consultas reais via RPC
de usuários, auditoria e fila de disputas passaram; nenhuma disputa foi decidida
nem moderador real designado para testar. Evidências privadas em
supabase/.temp/permissions-audit/bootstrap-{target,post}.json; SQL executado
permanece ignorado em supabase/.temp/permission-operations/.

Os logs HTTP da sessão real do usuário também confirmaram: recuperação aceita
(202), estabelecimento da sessão (200), troca de senha (204), novo login (200)
e consultas /auth/me, /admin/users, /admin/audit e /moderation/matches com 200.
Isso valida a comunicação navegador → FastAPI → Supabase Auth/PostgreSQL para
as leituras administrativas; não é somente um teste RPC com autenticação simulada.
Senhas/tokens/cookies não foram lidos ou registrados nesta verificação.

O proprietário confirmou na interface: **Administração e Moderação abrem
normalmente**. A validação manual da sessão e das duas áreas foi concluída.
Na listagem de contas, ADMIN apresenta alcance global de moderação, mesmo sem
vínculos individuais de comunidade.

Pendências: primeiro vínculo real de MODERATOR (depende de uma pessoa/perfil e
comunidade escolhidos pelo administrador). Não houve screenshot ou validação
visual automatizada; houve validação HTTP da sessão real e confirmação manual
do usuário conforme registrado acima. Cadastro de uma nova pessoa, atribuição real de
MODERATOR e resolução de uma disputa real permanecem não executados nesta etapa.

Referências técnicas: [funções Supabase](https://supabase.com/docs/guides/database/functions),
[metadados de usuários](https://supabase.com/docs/guides/auth/users),
[RLS PostgreSQL 17](https://www.postgresql.org/docs/17/ddl-rowsecurity.html).
