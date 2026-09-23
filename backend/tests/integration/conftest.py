"""Fixtures for the integration suite: these drive the app through the real
HTTP -> FastAPI -> Store -> database stack (no mocks).

By default only SqliteStore is exercised (a fresh temp file per test - fast,
needs no external services, safe to run on every push). Setting
TEST_DATABASE_URL additionally parametrizes every test in this file's scope
to run the same flows against a real Postgres too - e.g. the `db` service
from docker-compose.yml (see the repo root docker-compose.yml and README for
the exact command). This shadows the top-level tests/conftest.py `client`
fixture (backed by InMemoryStore) for everything under tests/integration/.
"""

import os

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.sqlite_store import SqliteStore

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

_BACKENDS = ["sqlite"] + (["postgres"] if TEST_DATABASE_URL else [])


def _make_postgres_store():
    from app.postgres_store import PostgresStore

    # Clean slate per test: drop the tables so PostgresStore's own startup
    # schema setup (CREATE TABLE IF NOT EXISTS) recreates them fresh - the
    # same idempotent path it takes in production on every restart.
    with psycopg.connect(TEST_DATABASE_URL, autocommit=True) as conn:
        conn.execute("DROP TABLE IF EXISTS matches, teams CASCADE")
    return PostgresStore(TEST_DATABASE_URL)


@pytest.fixture(params=_BACKENDS)
def store(request, tmp_path):
    if request.param == "sqlite":
        s = SqliteStore(str(tmp_path / "scoreboard.db"))
    else:
        s = _make_postgres_store()
    yield s
    s.close()


@pytest.fixture
def client(store):
    return TestClient(create_app(store))
