# Repository Guidelines

## Product Context

Scroll of Encounters is a community-oriented platform for recording and tracking
tabletop game matches. The initial supported game is Magic: The Gathering,
with Commander as the primary format.

The project is not primarily a tournament manager. Its core purpose is to
maintain trustworthy match history, community rankings, player statistics,
and match validation.

Although Magic: The Gathering and Commander are the initial focus, the domain
architecture should remain extensible to other tabletop games and formats.

The product name is **Scroll of Encounters**.

"Community" remains a domain concept inside the application and should not be
renamed merely because the product was previously called Communities.

Current architecture:

Frontend → FastAPI → Supabase/PostgreSQL

Scryfall is used as an external Magic: The Gathering card data source.

### Future Tournament Integration

Tournament management is not part of the current implementation scope.

Scroll of Encounters should, however, remain architecturally capable of supporting a tournament module in the future.

A future tournament system may reuse existing platform concepts such as users, players, communities, games, formats, and match records rather than creating a separate parallel ecosystem.

Matches created within tournaments should, where practical, remain compatible with the platform's general match model while carrying additional tournament context.

Do not implement tournament-specific entities, scoring, pairings, standings, or tournament workflows until their requirements are explicitly defined.

## Core Domain Concepts

The main domain entities include:

- profiles
- players
- communities
- games
- formats
- matches
- match participants
- Commander-specific participant data

A player has one primary community but may participate in matches hosted by
other communities.

Do not introduce game-specific fields into generic match entities when the
information belongs to a specific game or format.

## Match Integrity Rules

Match records are subject to validation.

- Creating a match does not automatically make it valid for rankings.
- Only confirmed matches count toward rankings and statistics.
- Participants may confirm or contest a match.
- A contest requires a reason.
- A disputed match does not count toward rankings or statistics until resolved.
- Relevant edits to a match invalidate previous confirmations.
- Guest players may participate but do not vote on confirmation.
- Guest identities should be reusable.
- Do not impose arbitrary daily limits on match creation or player participation.
- The platform should encourage interaction, persistent player data, and recreational use rather than restrict legitimate activity.
- Match integrity should be protected through validation and anti-abuse mechanisms instead of simple posting limits.
- Potential duplicate matches should be detected and flagged rather than automatically rejected.
- Duplicate detection should consider an approximately two-hour window.
- Future anti-abuse mechanisms may consider suspicious activity patterns, participant confirmation, duplicate detection, and other evidence of fraudulent match records.

## Match Results

The current version of Scroll of Encounters does not use a point-based scoring system.

- Do not implement Commander ranking points or placement-based scoring at this stage.
- When registering a match, the user should report either one winner or a table draw.
- A match with a winner records that player as the winner of the match.
- A table draw represents a match with no single winner.
- Rankings and statistics, when implemented, should derive from confirmed match results rather than from a predefined point system.
- More complex outcomes, such as partial draws, simultaneous eliminations, or placement-based results, are intentionally out of scope for the current version.
- The match result model should remain extensible so these cases can be supported later without requiring a complete redesign.


## Project Structure & Module Organization

- `backend/app/main.py` creates the FastAPI application and registers routers.
- `backend/app/db.py` configures the Supabase client using environment variables.
- `backend/app/routers/cards.py` exposes the Scryfall card search endpoint.
- `backend/app/routers/games.py` exposes game-related HTTP endpoints.
- `backend/app/routers/player.py` exposes player-related HTTP endpoints.
- `backend/app/services/scryfall.py` integrates with the Scryfall API.
- `backend/app/services/game.py` contains game data access logic.
- `backend/app/services/player.py` contains player data access logic.
- `backend/requirements.txt` declares Python dependencies.
- `frontend/` contains the React and TypeScript application, built with Vite
  and styled with Tailwind CSS. See `frontend/README.md` for setup instructions.

Current backend architecture:

HTTP Request
    → FastAPI Router
    → Service
    → Supabase Client
    → Supabase Data API
    → PostgreSQL

Scryfall integration follows a separate external API flow.

Keep HTTP route definitions in `routers/`.
Keep data access and external API integration in `services/`.
Keep shared Supabase client configuration in `db.py`.

Do not assume that every database table requires its own router.
Create endpoints according to application use cases.

The database schema already contains tables for games, formats,
communities, players, profiles, matches, match participants,
and Commander-specific participant data.

Inspect existing implementations before creating or changing files.


## Build, Test, and Development Commands

Run these commands in PowerShell from `backend/`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Create the virtual environment only if it does not already exist.

The remaining commands install dependencies and start the development API at
`http://127.0.0.1:8000`.

Use `/docs` for interactive endpoint checks and `/` for the basic health
response.

Run these frontend commands in PowerShell from `frontend/`:

```powershell
npm.cmd ci
npm.cmd run dev
npm.cmd run check
npm.cmd test
npm.cmd run build
npm.cmd run preview
```

The frontend development server runs at `http://127.0.0.1:5173`.
Use Node.js 24.12+ for the frontend and its native Node.js test runner.
The build command checks TypeScript and writes production assets to `dist/`.
Configure the public API URL with `VITE_API_BASE_URL`; the development proxy
target is `API_PROXY_TARGET`. See `frontend/.env.example` and `frontend/README.md`.
Frontend dependencies are managed separately from the root migration tooling.
No CI pipeline is currently configured.

## Coding Style & Naming Conventions

Use four-space indentation, snake_case for Python modules and functions, and
UPPER_SNAKE_CASE for constants such as `SCRYFALL_URL`.

Follow existing double-quoted strings and grouped imports.

Add type hints to new function parameters.

Keep network operations asynchronous using `httpx.AsyncClient`; avoid blocking
calls in async routes.

No formatter or linter is currently configured.

## Testing Guidelines

Backend migration tests use unittest under `backend/tests/`; see
`backend/migrations/README.md`. Frontend HTTP client and development proxy tests
use the native Node.js runner through `npm.cmd test` in `frontend/`.
No coverage threshold is currently established.

For API changes, verify `/` and `/cards/search` through `/docs` and record the
results.

When introducing automated tests:

- use `backend/tests/test_*.py`
- document the runner and dependencies
- mock Scryfall responses
- cover successful searches
- cover upstream errors
- cover missing images
- cover double-faced cards

## Commit & Pull Request Guidelines

This project uses Git with `main` as the primary branch.

Use Conventional Commit-style messages when practical:

- `feat:` for new features
- `fix:` for bug fixes
- `refactor:` for internal code changes without behavior changes
- `docs:` for documentation changes
- `test:` for test-related changes
- `chore:` for maintenance and repository configuration

Keep commits focused on a single logical change.

Pull request descriptions should explain behavior changes, reference related
issues when available, and list validation performed.

Include request/response examples for API changes and screenshots for future
UI changes.

### Player Profile

Each registered user should have a player profile that acts as a persistent representation of their activity on the platform.

The profile should support:

- Player statistics derived from valid match history.
- Percentage-based statistics, such as win rate and other future performance metrics.
- A user-written profile text or biography.
- A collection of the player's registered Commander decks.
- Visual presentation of each registered commander using card data and images when available.
- An optional decklist link for each registered Commander deck.

Commander deck registration is platform data and must not be treated as merely a Scryfall card record.

Scryfall may provide external card information such as card ID, name, image, and other card metadata, while Scroll of Encounters stores the relationship between the player and their registered deck, including platform-specific information such as an optional decklist URL.

Exact database tables and field names for player profiles and registered Commander decks have not yet been defined and should not be assumed before database modeling.

## Security & Configuration

Keep secrets in local environment configuration.

Never commit:

- `.env`
- `.venv/`
- `__pycache__/`

Document new configuration variables with nonsecret examples.

Preserve Scryfall request headers when modifying its integration.


## AI-Assisted Development Workflow

The project owner is learning software engineering while building
a real application intended for a professional portfolio.

AI agents must prioritize working software, maintainability,
security, and technical understanding.

### Autonomy and Approvals

Within the scope of the requested task, agents are authorized to:

- Create, edit, organize, and remove local files generated by the agent,
  while preserving preexisting changes.
- Install necessary development dependencies and run local commands,
  tests, and builds.
- Create branches and local commits, and prepare pull requests.
  Keep commits focused on task-related changes and preserve unrelated work.
- Query Supabase and apply previously reviewed, non-destructive migrations
  that preserve existing data. Verify the target project, migration history,
  and dry-run before applying migrations.
- Perform read-only Git checks and operations without requesting textual
  authorization.

Operation-specific approval is required before:

- Pushing to `main`.
- Deleting real data.
- Changing security permissions or Row Level Security (RLS).
- Performing destructive operations in production.

When approval is necessary, present the concrete operation and use the
confirmation mechanism available in the interface. Never require the user
to write a literal phrase such as "EU AUTORIZO". Do not request approval again
for an operation already authorized unless its scope or risk has changed.
Tool-level sandbox and security confirmations still apply.

After each task, briefly report what was implemented, what was tested and
the results, and what remains pending.

### Before Editing

- Inspect relevant existing files before proposing changes.
- Reuse established project patterns when appropriate.
- Identify dependencies and possible side effects.
- Prefer the smallest coherent change that delivers value.
- Do not introduce new frameworks without a clear justification.
- Do not rewrite working functionality unnecessarily.

### Explaining Code Changes

For each implementation task:

1. State the objective briefly.
2. Identify files that will be modified.
3. Implement the requested change.
4. Explain the main technical decisions.
5. Report tests executed and their results.
6. Identify remaining risks or limitations.

When explaining unfamiliar code, identify:

- Functions and methods.
- Classes and instantiated objects.
- Variables and their origins.
- Imported libraries and modules.
- Important HTTP, database, and security concepts.

Write explanations in Brazilian Portuguese.

Use concise, useful comments above non-obvious code when they
improve understanding. Avoid excessive comments explaining
self-evident syntax.

When giving manual editing instructions, explicitly use:

- SUBSTITUA: replace existing code.
- ACRESCENTE: add new code.
- REMOVA: delete existing code.
- NÃO ALTERE: preserve existing code.

### Safety and Database Changes

- Never reveal, log, or commit credentials.
- Never expose the Supabase secret key to frontend code.
- Do not disable Row Level Security to bypass permission errors.
- Do not grant unrestricted database privileges as a shortcut.
- Follow the operation-specific approval requirements in Autonomy and Approvals.
- Explain proposed SQL migrations before applying them.
- Respect the distinction between SQL privileges and RLS policies.
- Preserve existing production data when applying authorized non-destructive migrations.

### Validation

- Run relevant available tests after changes.
- Do not claim a test passed unless it was executed successfully.
- Use mocks when appropriate for external services.
- Report when live Supabase or Scryfall integration was not tested.
- Prefer incremental implementation over large unverified changes.

### Product Priorities

Community first.

Prioritize:

1. Fast match registration.
2. Persistent player identity.
3. Community participation.
4. Validated match history.
5. Commander-specific features.

Do not prioritize tournaments, complex scoring systems,
or real-time chat for the current MVP.


### Unlimited Match Registration

Scroll of Encounters must not impose arbitrary limits on match registration.

- Users may register any number of matches per day.
- Users may register historical matches without a retroactive time limit.
- Store the match date separately from the registration timestamp.
- Do not block registration solely because of high activity.
- Potential duplicates may generate non-blocking warnings.
- Match confirmation remains separate from match registration.
- Unconfirmed or disputed matches must not contribute to official statistics.
- Do not introduce daily quotas, cooldowns, or historical registration windows without an explicit product decision.

The platform prioritizes freedom of registration and user experience.



### Player Scheduling Conflict Prevention

Match start times are approximate, user-reported references.

- Only the reported match start time is relevant.
- Match end times and durations are not tracked.
- A player cannot participate in two different matches
  with reported start times less than 10 minutes apart.
- Exactly 10 minutes of separation is allowed.
- The restriction applies to all participants, including guests.
- Validate conflicts against existing relevant matches,
  including those pending confirmation.
- Historical registrations must follow the same rule.
- Editing a match's start time or participants must
  trigger conflict validation again.
- Conflict checks must be safe against concurrent requests.
- No daily, weekly, or monthly registration limits exist.
- Do not infer actual match duration from start times.
