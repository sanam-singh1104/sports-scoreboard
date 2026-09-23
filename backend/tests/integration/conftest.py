"""Fixtures for the integration suite: these drive the app through the real
HTTP -> FastAPI -> SqliteStore -> sqlite3-file stack, using a temp file per
test (fast, isolated, no mocks). This shadows the top-level tests/conftest.py
`client` fixture (which is backed by InMemoryStore) for everything under
tests/integration/, since the point here is to exercise the real database.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.sqlite_store import SqliteStore


@pytest.fixture
def store(tmp_path):
    s = SqliteStore(str(tmp_path / "scoreboard.db"))
    yield s
    s.close()


@pytest.fixture
def client(store):
    return TestClient(create_app(store))
