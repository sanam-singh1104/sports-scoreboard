"""End-to-end coverage of product-spec.md Feature 2 (Record matches), driven
through the HTTP API against a real SQLite file.
"""


def _create_team(client, name):
    return client.post("/api/teams", json={"name": name}).json()["id"]


def test_recorded_match_persists_and_appears_in_history(client):
    home_id = _create_team(client, "Riverside FC")
    away_id = _create_team(client, "Oakwood United")

    resp = client.post(
        "/api/matches",
        json={
            "homeTeamId": home_id,
            "awayTeamId": away_id,
            "homeScore": 3,
            "awayScore": 1,
            "date": "2026-08-02",
            "matchday": 1,
        },
    )
    assert resp.status_code == 201
    match_id = resp.json()["id"]

    history = client.get("/api/matches").json()
    assert len(history) == 1
    match = history[0]
    assert match["id"] == match_id
    assert match["homeTeamId"] == home_id
    assert match["awayTeamId"] == away_id
    assert match["homeScore"] == 3
    assert match["awayScore"] == 1
    assert match["date"] == "2026-08-02"
    assert match["matchday"] == 1


def test_match_referencing_unknown_team_rejected_and_not_persisted(client):
    home_id = _create_team(client, "Riverside FC")

    resp = client.post(
        "/api/matches",
        json={
            "homeTeamId": home_id,
            "awayTeamId": 9999,
            "homeScore": 1,
            "awayScore": 0,
            "date": "2026-08-02",
            "matchday": 1,
        },
    )
    assert resp.status_code == 400
    assert client.get("/api/matches").json() == []


def test_match_with_same_team_on_both_sides_rejected(client):
    team_id = _create_team(client, "Riverside FC")

    resp = client.post(
        "/api/matches",
        json={
            "homeTeamId": team_id,
            "awayTeamId": team_id,
            "homeScore": 2,
            "awayScore": 0,
            "date": "2026-08-02",
            "matchday": 1,
        },
    )
    assert resp.status_code == 400
