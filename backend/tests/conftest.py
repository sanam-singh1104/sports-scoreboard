import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    """A fresh app backed by a fresh, isolated in-memory store per test."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def client_with_teams(client):
    """Client with three teams already created: Riverside FC, Oakwood
    United, Harbor City (ids 1, 2, 3 respectively).
    """
    for name in ["Riverside FC", "Oakwood United", "Harbor City"]:
        client.post("/api/teams", json={"name": name})
    return client
