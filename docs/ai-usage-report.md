# AI Usage Report

This project was built using Claude Code (Anthropic's CLI coding agent) as
a hands-on collaborator, working through the app one layer at a time. This
report describes how it was actually used.

## Spec
`product-spec.md` was written by the project owner and handed to Claude
Code to save as-is — the file itself wasn't AI-drafted content, but it
became the single source of truth Claude Code was pointed back to at every
later step ("based on product-spec.md...", "matches the spec"), which kept
the frontend, the API contract, and the backend consistent with each other
without the owner having to restate requirements each time.

## Frontend prototype
Claude Code built the UI (`frontend/`) in plain HTML/CSS/JS directly from
the spec's user stories, with hardcoded mock data standing in for a
backend that didn't exist yet. This let the owner see and approve the UX
(standings table, add-team form, record-match form, match history) before
any API or storage decisions were locked in.

## API contract
Before backend code was written, Claude Code produced `openapi.yaml`,
deliberately kept aligned with the data shapes the frontend prototype was
already using (`Team`, `Match`, `StandingsRow`). This meant the backend
had a concrete contract to implement against, and the frontend needed no
reshaping later when it was switched from mock data to real HTTP calls.

## Backend
Claude Code implemented a FastAPI backend (`backend/`) against the OpenAPI
contract, using an in-memory store behind an abstract `Store` interface
from the start, so a later swap to real persistence wouldn't touch the API
layer. Pytest tests were written alongside the implementation, not after.

## SQLite persistence
When asked to add persistence, Claude Code added a `SqliteStore`
implementing the same `Store` interface, and pointed the running app at it
while leaving the interface (and therefore the endpoints) unchanged — the
swappability designed in at the backend step paid off here.

## Review-at-each-step workflow
Each layer (frontend, contract, backend, integration, SQLite) was built,
tested, and left uncommitted until the owner reviewed it and explicitly
said to commit. Nothing was pushed to GitHub automatically or bundled into
a later commit — every push corresponds to one reviewed, approved unit of
work with its own commit message.

## Testing
- Backend logic (team/match validation, standings calculation, and
  persistence across simulated restarts) is covered by an automated
  pytest suite (26 tests as of the SQLite change), run and shown to the
  owner after each backend change rather than just claimed to pass.
- Claude Code also ran live smoke tests beyond the automated suite:
  starting the real `uvicorn` server and hitting it with `curl`, serving
  the frontend and confirming it called the live backend correctly, and
  actually killing and restarting the backend process to confirm SQLite
  data survived the restart, rather than just restarting a store object
  in a test.
- One honest limitation: the frontend was verified via code review and
  HTTP-level checks (served files, live API responses), not by an AI
  agent clicking through it in a real browser — browser automation was
  offered and declined for this project, so actual in-browser UX checks
  are still the owner's to do.

## Net effect
AI tooling moved fast within a structure the owner controlled: the spec
and the review gate at each step were both human-driven, and Claude Code's
role was to implement each reviewed layer quickly, keep it consistent with
the contract and spec, and prove it worked (tests plus live checks) before
asking for the next green light.
