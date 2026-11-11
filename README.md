# Scroll of Encounters

Uma plataforma de comunidades para guardar histórias de partidas de jogos de
mesa. MVP com React + TypeScript + Vite + Tailwind, FastAPI e Supabase/PostgreSQL.

Arquivos, contrato HTTP, decisões e evidências: [entrega do MVP](docs/MVP_DELIVERY.md).

## Executar localmente

Requisitos: Node.js 24.12+ e Python 3.14 (ambiente atual). Na raiz:

```powershell
npm.cmd ci
.\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
```

Se o ambiente Python ainda não existir, criar com `python -m venv backend/.venv`.
Configurar `backend/.env` a partir de `backend/.env.example`, sem substituir uma
configuração existente. A chave privada Supabase pertence somente ao backend.

Terminal 1, a partir de backend/:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Terminal 2, a partir de frontend/:

```powershell
npm.cmd ci
npm.cmd run dev
```

Abrir http://127.0.0.1:5173. Documentação HTTP em http://127.0.0.1:8000/docs.
O proxy `/api` permite a comunicação no mesmo domínio do navegador. Em produção,
usar HTTPS, `COOKIE_SECURE=true`, origens explícitas em `TRUSTED_ORIGINS` e proxy
reverso equivalente. Não expor o servidor de desenvolvimento à internet.

## Fluxo do MVP

- Navegação por início, comunidades, jogadores, histórico e registro de partidas.
- Leituras públicas passam pelo FastAPI; a chave Supabase nunca vai ao navegador.
- Em `#/entrar`, criar conta com seu próprio e-mail e senha, confirmar o e-mail e
  escolher nome público e comunidade principal em `#/perfil`. Perfil e jogador
  são criados juntos e uma repetição não sobrescreve identidades existentes.
- Quem já possui conta pode entrar ou solicitar recuperação de senha.
  Não há contas administrativas automáticas nem autor informado pelo formulário.
- O backend valida a sessão com Supabase Auth a cada escrita. Cookies de sessão
  são HttpOnly e SameSite=Lax; requisições com cookies exigem origem confiável.
- Selecionar comunidade, formato, data, início, identidades persistentes e vencedor
  único ou empate. Convidados são registros reutilizáveis em player, não nomes soltos.
- O registro nasce PENDING. Não há limites de quantidade de partidas ou dias retroativos.
- Os horários são referências locais de Brasília. Não se usa término ou duração.
- Apenas partidas VERIFIED entram no contador de partidas verificadas. Confirmação,
  contestação e moderação por participantes são a próxima etapa, não são simuladas.

## Integridade e arquitetura

Frontend → FastAPI → funções Supabase específicas → PostgreSQL.
O esquema remoto foi inspecionado; nomes de comunidades são apresentados a partir
de subdivision/city, porque a tabela existente não possui coluna name.

`soe_register_match` grava partida e participantes em uma transação. Locks por
identidade, adquiridos em ordem, protegem a checagem de inícios separados por menos
de dez minutos. Exatamente dez minutos é permitido. Triggers também revalidam
mudanças de data/início/status e participantes. PENDING, VERIFIED e DISPUTED
conflitam; CANCELLED não. Transações com snapshot fixo são recusadas nesse caminho.

Duplicidades em até duas horas são avisos separados. Históricos sem início são
preservados e geram aviso quando relevantes à data; seu horário não é inventado.
Resultados e quantidade de participantes são verificados também por constraints
deferidas. Falhas não deixam partida ou participantes parcialmente gravados.

As seis funções públicas novas são SECURITY DEFINER com search_path fixo e
somente service_role pode executá-las. Helpers ficam em schema privado. Nenhuma
política RLS ou permissão de tabela é ampliada. As migrações 002 e 003 foram
aplicadas com aprovação pela interface; os acessos foram conferidos no remoto.

O retorno de confirmação/recuperação recebe tokens temporariamente pelo fragmento
do endereço, remove-os antes de renderizar e os troca por cookies HttpOnly pelo
backend. Não há armazenamento de tokens em localStorage/sessionStorage.
O fluxo segue o [retorno de autenticação do Supabase](https://supabase.com/docs/guides/auth/sessions/implicit-flow).

**Aplicado em 2026-11-11 após aprovação específica do proprietário:** a URL de
retorno remoto passou de `http://localhost:3000` para `http://127.0.0.1:5173`.
A verificação posterior confirmou zero diferenças declaradas e as outras dez
propriedades comparadas inalteradas, incluindo confirmação de e-mail e MFA.
O retorno local requer o frontend em execução neste computador; abrir o link
no celular apontará ao próprio celular. Ainda não há confirmação de entrega
dos e-mails nem de gravação autenticada em produção. Não compartilhar links de acesso.

Migrações oficiais em `supabase/migrations/`. Nunca rodar db reset no remoto.
Remoção de término/cota diária permanece fora das migrações executáveis até a
aprovação destrutiva e preservação apropriada dos valores históricos.

## Testes

Da raiz:

```powershell
.\backend\.venv\Scripts\python.exe -B -m unittest discover -s backend/tests -p "test_*.py" -v
.\backend\.venv\Scripts\python.exe -B scripts/check_secrets.py
```

De frontend/:

```powershell
npm.cmd test
npm.cmd run build
```

Os testes novos de SQL usam PostgreSQL 17 local, com sessões reais separadas,
inclusive a corrida de dois registros conflitantes. No Windows os binários são
uma dependência opcional de tooling; no Linux instalar initdb/postgres no PATH.
O PostgreSQL fica restrito a loopback e os dados descartáveis ficam em diretório
temporário verificado. Eles nunca aceitam DSN de produção. As fixtures não são
seeds remotas. Os testes de API simulam autenticação/transportes; os de Scryfall
simulam respostas externas. Verificações reais são registradas separadamente.
