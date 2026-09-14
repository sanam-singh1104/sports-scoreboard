# Sports League Scoreboard

A web app for running a sports league. An organizer adds teams, records
match results, and the app automatically calculates and displays an
up-to-date standings table using classic 3-1-0 scoring (win / draw / loss).

Matches are the input; the standings table is the output — team records and
points are derived from recorded matches rather than edited by hand.

See [product-spec.md](./product-spec.md) for the full product spec.

## Tech stack
- **Backend:** FastAPI (Python)
- **Frontend:** browser UI (prototype tool TBD)
- **Contract:** OpenAPI (`openapi.yaml`) as the source of truth between frontend and backend
- **Storage:** SQLite, kept swappable so Postgres can replace it later
- **Tests:** covering the spec's behavior

## Status
Early setup — see `product-spec.md` for the features being built.
