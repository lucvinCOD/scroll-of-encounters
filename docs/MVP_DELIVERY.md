# Entrega local do MVP — 2026-11-11

Este documento registra a etapa inicial do MVP. A evolução posterior de contas,
permissões, migração 004, bootstrap aprovado e confirmação das áreas pelo usuário
está em [Contas e permissões](ACCOUNTS_AND_PERMISSIONS.md). As pendências de conta
do proprietário e acesso administrativo descritas nesta etapa já foram resolvidas.

Branch: `feat/mvp-web`. Alterações preexistentes foram preservadas no commit
`c34abbb`. Nenhum push, merge ou reescrita de histórico foi realizado.

## Funcionalidades

Home, comunidades, jogadores com busca/filtro, histórico com paginação/filtro e
registro de partidas. Layout responsivo com pergaminho, verde profundo, dourado,
brasão SVG e navegação funcional. Estados de carregamento, falha, vazio e sucesso.
Sem dados fictícios nas telas: todas as listagens vêm do FastAPI/Supabase.

Cadastro/entrada, recuperação de senha e perfil inicial. E-mail/senha são
informados pelo próprio usuário. Supabase Auth valida o usuário; o cliente não
escolhe o autor. Tokens ficam em cookies HttpOnly; escritas com cookies exigem
Origin confiável. Confirmação por e-mail e MFA não foram desativados.

Registro recebe comunidade, formato, data, início local de Brasília, IDs de
participantes persistentes e vencedor ou empate. Resultado inicial PENDING;
somente VERIFIED é contado como verificado. Convidados podem ser criados e
reutilizados. Nenhuma cota diária ou janela retroativa é aplicada.

## Contrato HTTP

Leituras: `GET /catalog`, `/communities/`, `/formats/`, `/games/`, `/players/`,
`/matches/?limit=20&offset=0&community_id=1` (filtro opcional) e `/cards/search`.
Limite de paginação não é limite de registro de partidas.

Escritas: `POST /players/guests`, `/matches` e rotas `/auth/*`, descritas em
`http://127.0.0.1:8000/docs`. Exemplo de contrato, não uma partida a inserir:

```json
{
  "community_id": 1,
  "format_id": 1,
  "match_date": "2001-01-01",
  "approximate_start_time": "10:00",
  "participant_ids": [1, 2],
  "result": {"type": "winner", "winner_player_id": 1}
}
```

Para empate: `"result": {"type": "draw"}`. O backend rejeita campos extras,
participantes repetidos/inexistentes, vencedor externo à mesa e resultados
incompatíveis. Resposta 201: `{id, status: "PENDING", warnings: [...]}`.
Conflito temporal é HTTP 409; avisos de duplicidade não impedem a gravação.

## Arquivos da implementação

| Área | Arquivos |
| --- | --- |
| Configuração/segurança | `.gitignore`, `scripts/check_secrets.py`, `backend/.env.example`, `backend/app/config.py`, `backend/app/db.py`, `backend/app/auth.py`, `backend/app/models.py` |
| API | `backend/app/main.py`, `routers/auth.py`, `routers/matches.py`, `routers/games.py`, `routers/player.py`, `services/matches.py`, `services/game.py`, `services/player.py`, `services/scryfall.py` (routers/services dentro de backend/app) |
| Banco | `supabase/migrations/20261111000200_mvp_match_registration.sql`, `20261111000300_verified_account_onboarding.sql`, `supabase/config.toml`, `backend/migrations/README.md`, `backend/migrations/plans/contract_legacy_columns.md` |
| Testes/tooling | `backend/requirements-dev.txt`, `backend/tests/local_postgres.py`, `fixtures/mvp_schema.sql`, `test_match_database.py`, `test_match_api.py`, `test_scryfall.py`, `package.json`, `package-lock.json` |
| Frontend | `frontend/src/App.tsx`, `main.tsx`, `index.css`, `types.ts`, `state/AppContext.tsx`, `hooks/useResource.ts`, `components/BrandHeader.tsx`, `components/layout/AppShell.tsx`, `components/MatchCard.tsx`, `components/ResourceState.tsx` |
| Páginas | `frontend/src/pages/{Home,Communities,Players,History,RegisterMatch,Login,Profile,Password}Page.tsx` |
| Frontend/testes | `frontend/package.json`, `src/services/authCallback.ts`, `src/services/authCallback.test.ts`, `tests/dev-server.test.mjs` |
| Documentação | `README.md`, `frontend/README.md`, este arquivo |

O arquivo local ignorado `backend/.env` recebeu chave privada exclusiva do
servidor após validação do projeto; seu conteúdo não foi exibido nem versionado.
Migrações já aplicadas não foram reescritas. A versão 001 é da etapa anterior.

## Decisões e evidências

As colunas reais foram consultadas antes da implementação. Community não possui
name: a interface apresenta subdivision ou city. Profile.id referencia
auth.users.id; convidado é player com profile_id NULL. Resultados existentes
WIN/LOSS/DRAW foram reutilizados, sem placares ou novas colunas fictícias.

Uma chamada RPC PostgreSQL salva partida e participantes na mesma transação.
Locks transacionais por player, em ordem, serializam conflitos entre autores,
comunidades e convidados. Triggers também revalidam edições; operações em
participantes bloqueiam a partida para serializar com a mudança de início.
READ COMMITTED é exigido para obter leituras atualizadas depois da espera.
Constraints deferidas validam o resultado final e o tamanho da mesa no commit.

A consulta usa diferença estrita de dez minutos entre data + início: 09:50 e
10:10 são permitidos em torno de 10:00; 09:50:01 e 10:09:59 conflitam. A virada
de dia é considerada. PENDING/VERIFIED/DISPUTED bloqueiam, CANCELLED não.
Duplicidades com o mesmo conjunto de participantes em aproximadamente duas
horas geram aviso. Dados históricos sem início permanecem desconhecidos.

Migrações 002 e 003 aplicadas no remoto após revisão e aprovação pela interface.
Dry-run final: nenhuma versão pendente. A inspeção posterior confirmou colunas,
ACL de tabelas e RLS preservadas, além da partida histórica id=1 intacta.
As seis funções de aplicação são SECURITY DEFINER com search_path fixo,
EXECUTE restrito a service_role; helpers não são acessíveis pelas roles clientes.
Não foram concedidos privilégios genéricos de tabela. Evidências locais ignoradas:
`supabase/.temp/mvp-audit/`.

Leituras reais HTTP 200: frontend 5173, proxy `/api/catalog`, `/api/matches/`,
FastAPI `/`, `/docs`, `/catalog`, `/communities/`, `/formats/`, `/players/`,
`/matches/` e Scryfall `/cards/search?name=Sol%20Ring`.

## Pendências e validação manual

1. **Concluído em 2026-11-11:** o proprietário aprovou especificamente a alteração
   de auth.site_url em produção após a rejeição inicial da revisão automática.
   `npm.cmd run supabase -- config push --remote --yes` alterou somente
   localhost:3000 → 127.0.0.1:5173. Diff posterior: zero diferenças declaradas;
   outras dez propriedades comparadas inalteradas, incluindo confirmação de
   e-mail/MFA. Usar o link de e-mail no mesmo computador com frontend em execução.
2. O proprietário cria/recupera sua própria conta na tela Entrar. Confirmar
   recebimento do e-mail; entrega/SMTP não foram validados. Não enviar senha,
   token ou link de acesso pelo chat. Completar perfil e comunidade principal.
3. Registrar uma partida real com dados informados pelo usuário e conferir seu
   ID no histórico. A escrita autenticada remota ainda não foi testada.
4. Verificação visual no navegador não concluída: Computer Use interrompido pela
   política da ferramenta ao não conseguir determinar com confiança a URL.
   Não há screenshot nem afirmação de teste visual aprovado.
5. Próxima melhoria de produto: confirmação/contestação por participantes,
   mantendo PENDING/DISPUTED fora de rankings. Não há ranking ou torneios fictícios.
6. Remoção destrutiva futura de término e cota exige análise/backup/aprovação.
   Ambos permanecem no banco; min_players/max_players não foram alterados.

Comandos de execução e testes no [README](../README.md).

## Resultados executados

- Suíte completa do backend: **54 testes passaram** (37,866 s).
- Frontend: **12 testes passaram**; `npm run build` concluiu, 34 módulos.
- `git diff --check`: sem erros; avisos locais de LF/CRLF não impedem o build.
- Scanner de arquivos versionáveis: zero ocorrências de segredos/gerados privados.
- Chave privada do backend: não encontrada nos arquivos do build frontend.
- POST não autenticado pelo proxy real: HTTP 401, sem inserção de partida.
- Auth remoto: cadastro por e-mail habilitado, confirmação automática desabilitada.
- Há um aviso de depreciação Starlette/httpx nos testes; a suíte passa. Não foi
  ocultado nem tratado como falha de integração.
- Testes de sessão/registro usam autenticação simulada e PostgreSQL local real.
  Eles não substituem a validação final com a conta e a partida reais do usuário.
