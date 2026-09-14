"""Tests for the SQLite storage backend, especially that data survives a
process restart (a fresh SqliteStore instance opening the same db file).
"""

from datetime import date

from fastapi.testclient import TestClient

from app.main import create_app
from app.sqlite_store import SqliteStore
from app.standings import compute_standings


def test_teams_and_matches_persist_across_store_restarts(tmp_path):
    db_path = str(tmp_path / "scoreboard.db")

    store1 = SqliteStore(db_path)
    home = store1.create_team("Riverside FC")
    away = store1.create_team("Oakwood United")
    store1.create_match(
        home_team_id=home.id,
        away_team_id=away.id,
        home_score=3,
        away_score=1,
        match_date=date(2026, 8, 2),
        matchday=1,
    )
    store1.close()

    # Simulate a backend restart: a brand new store instance pointed at the
    # same db file, with no in-memory state carried over.
    store2 = SqliteStore(db_path)

    teams = store2.list_teams()
    matches = store2.list_matches()

    assert [t.name for t in teams] == ["Riverside FC", "Oakwood United"]
    assert len(matches) == 1
    assert matches[0].home_team_id == home.id
    assert matches[0].away_team_id == away.id
    assert matches[0].home_score == 3
    assert matches[0].away_score == 1
    assert matches[0].date == date(2026, 8, 2)
    assert matches[0].matchday == 1

    store2.close()


def test_standings_computed_correctly_from_persisted_data(tmp_path):
    db_path = str(tmp_path / "scoreboard.db")

    store1 = SqliteStore(db_path)
    home = store1.create_team("A")
    away = store1.create_team("B")
    store1.create_match(home.id, away.id, 2, 0, date(2026, 8, 2), 1)
    store1.close()

    store2 = SqliteStore(db_path)
    rows = {r.team.name: r for r in compute_standings(store2.list_teams(), store2.list_matches())}

    assert rows["A"].points == 3
    assert rows["A"].won == 1
    assert rows["B"].points == 0
    assert rows["B"].lost == 1

    store2.close()


def test_api_persists_data_across_app_restarts(tmp_path):
    db_path = str(tmp_path / "scoreboard.db")

    store1 = SqliteStore(db_path)
    client1 = TestClient(create_app(store1))
    client1.post("/api/teams", json={"name": "Riverside FC"})
    client1.post("/api/teams", json={"name": "Oakwood United"})
    client1.post(
        "/api/matches",
        json={
            "homeTeamId": 1,
            "awayTeamId": 2,
            "homeScore": 2,
            "awayScore": 1,
            "date": "2026-08-02",
            "matchday": 1,
        },
    )
    store1.close()

    # New store + new app instance against the same file simulates the
    # backend process being restarted.
    store2 = SqliteStore(db_path)
    client2 = TestClient(create_app(store2))

    teams = client2.get("/api/teams").json()
    matches = client2.get("/api/matches").json()
    standings = client2.get("/api/standings").json()

    assert [t["name"] for t in teams] == ["Riverside FC", "Oakwood United"]
    assert len(matches) == 1
    assert standings[0]["team"]["name"] == "Riverside FC"
    assert standings[0]["points"] == 3

    store2.close()


def test_team_name_uniqueness_persists_across_restarts(tmp_path):
    db_path = str(tmp_path / "scoreboard.db")

    store1 = SqliteStore(db_path)
    store1.create_team("Riverside FC")
    store1.close()

    store2 = SqliteStore(db_path)
    assert store2.team_name_exists("riverside fc") is True
    assert store2.team_name_exists("Harbor City") is False
    store2.close()
