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
- A disputed match does not count toward statistics until resolved.
- Relevant edits to a match invalidate previous confirmations.
- Guest players may participate but do not vote on confirmation.
- Potential duplicate matches should be detected rather than blindly
  accepted as separate matches.
- Duplicate detection considers approximately a two-hour window.
- A user may create at most 5 match records per day.
- Commander participation is limited to 10 matches per match date.
- Creation limits and participation limits are separate concepts.

## Commander Scoring

The ranking system rewards winning and survival.

For a standard four-player table:

- 1st place: 3 points
- 2nd place: 2 points
- 3rd place: 1 point
- 4th place: 0 points

For a three-player table:

- 1st place: 3 points
- 2nd place: 2 points
- 3rd place: 0 points

General rules:

- The winner receives 3 points.
- The first eliminated player or first simultaneously eliminated group
  receives 0 points.
- Simultaneously eliminated players receive the score corresponding to the
  worst placement occupied by that group.
- If time expires with two surviving players, each receives 2 points.
- If time expires with three or more surviving players, each receives 1 point.
- Players eliminated before time expires retain the score determined by their
  elimination position.

Scoring rules should be implemented as domain logic rather than duplicated
inside HTTP routes or frontend code.

## Project Structure & Module Organization

- `backend/app/main.py` creates the FastAPI application and registers routers.
- `backend/app/routers/cards.py` exposes `GET /cards/search?name=...`.
- `backend/app/services/scryfall.py` handles asynchronous Scryfall requests and
  normalizes card data, including images for double-faced cards.
- `backend/requirements.txt` pins Python dependencies.
- `frontend/` is currently empty; no frontend tooling or asset structure is
  established.

Keep HTTP routes in `routers/` and external API integration logic in
`services/`.

There is currently no test directory or database implementation in the
repository, although database libraries are listed as dependencies.

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

No build pipeline or frontend commands are currently configured.

## Coding Style & Naming Conventions

Use four-space indentation, snake_case for Python modules and functions, and
UPPER_SNAKE_CASE for constants such as `SCRYFALL_URL`.

Follow existing double-quoted strings and grouped imports.

Add type hints to new function parameters.

Keep network operations asynchronous using `httpx.AsyncClient`; avoid blocking
calls in async routes.

No formatter or linter is currently configured.

## Testing Guidelines

No automated test framework, test command, or coverage threshold is currently
established.

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

## Security & Configuration

Keep secrets in local environment configuration.

Never commit:

- `.env`
- `.venv/`
- `__pycache__/`

Document new configuration variables with nonsecret examples.

Preserve Scryfall request headers when modifying its integration.