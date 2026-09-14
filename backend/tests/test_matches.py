def test_list_matches_empty(client):
    resp = client.get("/api/matches")
    assert resp.status_code == 200
    assert resp.json() == []


def test_record_match(client_with_teams):
    resp = client_with_teams.post(
        "/api/matches",
        json={
            "homeTeamId": 1,
            "awayTeamId": 2,
            "homeScore": 3,
            "awayScore": 1,
            "date": "2026-08-02",
            "matchday": 1,
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["homeTeamId"] == 1
    assert body["awayTeamId"] == 2
    assert body["homeScore"] == 3
    assert body["awayScore"] == 1
    assert body["date"] == "2026-08-02"
    assert body["matchday"] == 1
    assert isinstance(body["id"], int)


def test_recorded_match_appears_in_history(client_with_teams):
    client_with_teams.post(
        "/api/matches",
        json={
            "homeTeamId": 1,
            "awayTeamId": 2,
            "homeScore": 3,
            "awayScore": 1,
            "date": "2026-08-02",
            "matchday": 1,
        },
    )
    resp = client_with_teams.get("/api/matches")
    matches = resp.json()
    assert len(matches) == 1
    assert matches[0]["homeTeamId"] == 1


def test_match_same_team_twice_rejected(client_with_teams):
    resp = client_with_teams.post(
        "/api/matches",
        json={
            "homeTeamId": 1,
            "awayTeamId": 1,
            "homeScore": 2,
            "awayScore": 0,
            "date": "2026-08-02",
            "matchday": 1,
        },
    )
    assert resp.status_code == 400


def test_match_negative_score_rejected(client_with_teams):
    resp = client_with_teams.post(
        "/api/matches",
        json={
            "homeTeamId": 1,
            "awayTeamId": 2,
            "homeScore": -1,
            "awayScore": 0,
            "date": "2026-08-02",
            "matchday": 1,
        },
    )
    assert resp.status_code == 400


def test_match_invalid_matchday_rejected(client_with_teams):
    resp = client_with_teams.post(
        "/api/matches",
        json={
            "homeTeamId": 1,
            "awayTeamId": 2,
            "homeScore": 1,
            "awayScore": 0,
            "date": "2026-08-02",
            "matchday": 0,
        },
    )
    assert resp.status_code == 400


def test_match_unknown_team_rejected(client_with_teams):
    resp = client_with_teams.post(
        "/api/matches",
        json={
            "homeTeamId": 1,
            "awayTeamId": 999,
            "homeScore": 1,
            "awayScore": 0,
            "date": "2026-08-02",
            "matchday": 1,
        },
    )
    assert resp.status_code == 400
