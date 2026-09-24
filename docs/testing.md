# Testing

The backend has two test suites. Both are written in pytest and both drive
the app through its HTTP API with FastAPI's `TestClient`. They differ in
what sits behind the API.

| Suite | Location | Storage behind the API | Needs external services? |
| --- | --- | --- | --- |
| Unit | `backend/tests/*.py` | `InMemoryStore` (and `SqliteStore` directly) | No |
| Integration | `backend/tests/integration/` | Real SQLite file, plus real Postgres when configured | Only for the Postgres run |

The behavior under test comes from [product-spec.md](../product-spec.md)
and the contract in [openapi.yaml](../openapi.yaml).

## Unit tests

These are fast, isolated checks of the business rules. The `client`
fixture in `tests/conftest.py` builds a new app with its own
`InMemoryStore` for every test, so no test can affect another.

| File | Covers |
| --- | --- |
| `test_teams.py` | Creating and listing teams; blank names rejected; duplicate names rejected (including case-insensitive matches) |
| `test_matches.py` | Recording and listing matches; rejects the same team on both sides, negative scores, `matchday < 1`, and unknown team ids |
| `test_standings.py` | 3-1-0 scoring (win, draw, away win), played/won/drawn/lost totals, ranking by points, teams with no matches shown with zeroed stats |
| `test_sqlite_store.py` | `SqliteStore` persistence: teams, matches, and name uniqueness survive a store or app restart on the same file |

## Integration tests

These run the whole stack, HTTP → FastAPI → Store → database, with no
mocks. They check full user flows rather than single rules:

| File | Flow |
| --- | --- |
| `test_team_setup_flow.py` | Created teams persist and are listed; duplicate names are rejected; a new team shows a zeroed standings row |
| `test_match_recording_flow.py` | Recorded matches persist and appear in history; invalid matches are rejected **and not persisted** |
| `test_standings_end_to_end.py` | A full season produces the correct ranked table; standings are recomputed on every request |

`tests/integration/conftest.py` parametrizes the `store` fixture by
backend:

- **SQLite** always runs, with a new temp file for each test.
- **Postgres** also runs when `TEST_DATABASE_URL` is set. Before each test
  it drops the tables so that `PostgresStore` recreates them through the
  same `CREATE TABLE IF NOT EXISTS` code that runs on startup in
  production.

So each integration test runs once or twice, and shows up as
`test_x[sqlite]` and `test_x[postgres]`.

## Running tests locally

From `backend/`, with dependencies installed
(`pip install -r requirements.txt`):

```sh
# Everything that needs no external services (unit + integration on SQLite)
pytest

# Unit tests only
pytest tests --ignore=tests/integration

# Integration tests only (SQLite)
pytest tests/integration

# Integration tests against Postgres as well - start the db from the repo root:
docker compose up -d db
TEST_DATABASE_URL=postgresql://scoreboard:scoreboard@localhost:5432/scoreboard \
  pytest tests/integration -v
```

In PowerShell, set the variable first:
`$env:TEST_DATABASE_URL = "postgresql://scoreboard:scoreboard@localhost:5432/scoreboard"`.

The Postgres run drops and recreates `teams` and `matches`. Only point
`TEST_DATABASE_URL` at a throwaway database, **never** at production.

Lint the same way CI does:

```sh
pip install ruff
ruff check .
```

## Tests in CI

`.github/workflows/ci.yml` runs on every push to any branch and on every
pull request:

1. Starts a `postgres:16-alpine` service container and waits for its
   health check.
2. Installs dependencies with Python 3.13.
3. Runs `ruff check .`.
4. Runs the unit tests: `pytest tests --ignore=tests/integration`.
5. Runs the integration tests with
   `TEST_DATABASE_URL=postgresql://scoreboard:scoreboard@localhost:5432/scoreboard`,
   so every integration test runs on both SQLite **and** Postgres.
6. In a separate job, builds the Docker image from `backend/Dockerfile`.

Render auto-deploys `main` without waiting for CI, so run CI on the pull
request and check it's green before merging. A green CI run on `main`
then triggers the post-deploy smoke test, and a red one means rolling
back. See [release-process.md](./release-process.md).

## Adding tests

- **A new business rule or validation:** add a unit test next to the
  related tests (`test_teams.py`, `test_matches.py`, `test_standings.py`).
- **A new user-facing flow, or anything touching storage:** add an
  integration test under `tests/integration/`. Use the `client` fixture
  and it runs against every configured backend automatically.
- **A new `Store` implementation:** add it to `_BACKENDS` and `store` in
  `tests/integration/conftest.py` so the whole integration suite covers
  it.
