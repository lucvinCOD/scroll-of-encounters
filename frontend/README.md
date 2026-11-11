# Frontend — Scroll of Encounters

MVP com React, TypeScript, Vite e Tailwind CSS. Home, comunidades, jogadores,
histórico e registro usam o FastAPI real. Cadastro, confirmação por e-mail,
recuperação de senha e conclusão de perfil usam Supabase Auth pelo backend.
Veja o estado remoto e as pendências em [README da raiz](../README.md).

As áreas `#/moderacao` e `#/administracao` usam permissões verificadas no backend
e PostgreSQL. Os links dependem da identidade atual: USER vê a navegação comum;
MODERATOR vê moderação; ADMIN vê ambas. A migração 004 já foi aplicada após
aprovação; o bootstrap da conta do proprietário também foi executado após
aprovação específica do UUID. Não há modo demonstrativo com
privilégios fictícios. Consulte [contas e permissões](../docs/ACCOUNTS_AND_PERMISSIONS.md).

## Desenvolvimento

Requer Node.js 24.12+; o ambiente usado tem Node.js 24.19.0. As versões diretas
estão fixadas no package.json e package-lock.json: React 19.3.1, TypeScript 7.0.2,
Vite 8.3.8 e Tailwind CSS 4.3.5. Os comandos são executados em `frontend/`:

```powershell
npm.cmd ci
npm.cmd run dev
```

Acesse `http://127.0.0.1:5173`. O Vite atualiza a página durante a edição dos
componentes. Se a porta estiver ocupada, encerre a instância apropriada ou
informe outra porta com `npm.cmd run dev -- --port 5174`.

## Verificação e build

```powershell
npm.cmd run check
npm.cmd test
npm.cmd run build
npm.cmd run preview
```

`check` verifica os tipos. `build` verifica os tipos e gera os arquivos de
produção em `dist/`. `preview` serve esse build em `http://127.0.0.1:4173`
para conferência local; não é um servidor de produção.

`test` usa o runner nativo do Node.js, sem framework adicional. Verifica respostas
JSON, cabeçalhos e opções, erros HTTP, corpo vazio, falhas de rede e o proxy com
um backend simulado em porta local temporária. Nenhum teste acessa Supabase ou
a API real. Ainda não há testes de interação/renderização no navegador.

## Ambiente e comunicação com FastAPI

Os valores padrão funcionam sem criar arquivo de ambiente. Para personalizá-los,
copie `.env.example` para `.env.local` somente se este ainda não existir e ajuste
os valores locais. Arquivos de ambiente reais são ignorados pelo Git.

| Variável | Padrão | Uso |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `/api` | URL pública usada pelo cliente HTTP, relativa à origem ou absoluta. |
| `API_PROXY_TARGET` | `http://127.0.0.1:8000` | Destino do proxy do servidor Vite, sem exposição pelo prefixo VITE_. |

No desenvolvimento, uma chamada para `/api/cards/search` é encaminhada a
`http://127.0.0.1:8000/cards/search`. Assim o navegador chama sua própria origem,
sem exigir alteração de CORS no backend para esse fluxo. O backend precisa estar
em execução para chamadas reais; o frontend pode iniciar independentemente dele.

Reinicie o Vite depois de alterar variáveis. `VITE_*` é incorporado ao cliente
durante o build; para produção, configure a URL antes do build e um proxy reverso
para `/api` no servidor de hospedagem, ou use uma URL absoluta com CORS apropriado
na API. O proxy local do Vite não é a infraestrutura de produção.

Exemplo de uso do cliente, a partir de `src/`:

```typescript
import { api } from "./services/api";

const health = await api.request<{ message: string }>("/");
```

`api.request` aceita opções padrão de fetch, incluindo método, cabeçalhos, corpo
e AbortSignal. Para enviar JSON, usar JSON.stringify e Content-Type apropriado.
Respostas 204 retornam undefined; ApiError contém status e detalhes de erros JSON.
Falhas de rede são propagadas. A tipagem genérica não valida o JSON em runtime.

O navegador não recebe cliente ou credenciais Supabase. Nunca colocar segredos
em `VITE_*`; manter o acesso ao banco e as regras de integridade no backend.

## Arquivos principais

- `index.html`: documento HTML, título, idioma e elemento raiz.
- `src/main.tsx`: inicializa o React e importa o CSS global.
- `src/App.tsx`: navegação por fragmentos de URL, sem biblioteca adicional.
- `src/components/`: componentes compartilhados; `layout/AppShell.tsx` contém o layout.
- `src/pages/`: início, comunidades, jogadores, histórico, registro e acesso.
- `src/state/AppContext.tsx`: catálogo e restauração da sessão via cookies HttpOnly.
- `src/hooks/useResource.ts`: carregamento, erro, cancelamento e nova tentativa.
- `src/services/authCallback.ts`: remove tokens da URL e estabelece sessão pelo backend.
- `src/services/api.ts`: instância do cliente com `VITE_API_BASE_URL`.
- `src/services/apiClient.ts`: requisições HTTP e tratamento de respostas/erros.
- `src/services/apiClient.test.ts`: testes unitários do cliente, com fetch simulado.
- `tests/dev-server.test.mjs`: teste HTTP do Vite, Tailwind, ambiente e proxy.
- `src/vite-env.d.ts`: tipos das variáveis públicas de ambiente.
- `src/index.css`: importa o Tailwind; suas classes são usadas nos componentes.
- `vite.config.ts`: registra os plugins React e Tailwind e configura o servidor local.
- `tsconfig.json`: configura a verificação de tipos TypeScript.

As dependências e o lockfile do frontend ficam nesta pasta. O `package.json`
da raiz continua dedicado às ferramentas de migração do banco.

## Próximas etapas

Validar o fluxo com conta real e implementar confirmação/contestação das partidas.
As páginas possuem estados de carregamento, erro e ausência de dados. Somente
partidas verificadas entram no contador oficial. A sessão não guarda tokens no
armazenamento do navegador. A verificação visual automatizada não foi concluída.

Na configuração local padrão, use sempre `http://127.0.0.1:5173` para o fluxo de
acesso. Outra porta ou domínio exige revisar TRUSTED_ORIGINS no backend e a URL
de retorno do Supabase. O preview em 4173 não possui o proxy de desenvolvimento;
para integração nesse modo, fornecer infraestrutura de proxy apropriada.

Referências: [React com Vite](https://react.dev/learn/build-a-react-app-from-scratch)
e [Tailwind com Vite](https://tailwindcss.com/docs/installation/using-vite).
Consulte também [variáveis do Vite](https://vite.dev/guide/env-and-mode.html)
e [TypeScript no Node.js](https://nodejs.org/api/typescript.html).


### Creator & Development

**Scroll of Encounters** is an independent tabletop gaming platform created and maintained by **Lucas Ângelo**, a Software Engineering student and developer.

The project was conceived to help gaming communities register matches, preserve their histories, and track player participation.

Its architecture combines React, TypeScript, FastAPI, Python, and PostgreSQL through Supabase.

Development incorporates AI-assisted engineering workflows using OpenAI Codex, with product requirements, architectural decisions, implementation review, and project direction managed by the creator.
