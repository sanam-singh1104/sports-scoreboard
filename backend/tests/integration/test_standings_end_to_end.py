"""End-to-end coverage of product-spec.md Features 3 & 4 (standings
calculation and standings view): a full mini-season, entered exactly as the
frontend would (create teams, then post match results one by one), verified
through the /api/standings and /api/matches endpoints against a real SQLite
file - not a mock or the in-memory store used elsewhere in the unit suite.
"""


def _create_team(client, name):
    return client.post("/api/teams", json={"name": name}).json()["id"]


def _record(client, home, away, home_score, away_score, matchday, day):
    resp = client.post(
        "/api/matches",
        json={
            "homeTeamId": home,
            "awayTeamId": away,
            "homeScore": home_score,
            "awayScore": away_score,
            "date": f"2026-08-{day:02d}",
            "matchday": matchday,
        },
    )
    assert resp.status_code == 201
    return resp.json()


def test_full_season_flow_produces_correct_ranked_standings(client):
    """Mirrors the openapi.yaml /standings example: a team that has won all
    of its matches sits top with 12 points, and a team with no matches yet
    still appears in the table with all-zero stats.
    """
    riverside = _create_team(client, "Riverside FC")
    oakwood = _create_team(client, "Oakwood United")
    harbor = _create_team(client, "Harbor City")
    iron_bridge = _create_team(client, "Iron Bridge")

    _record(client, riverside, oakwood, 3, 1, matchday=1, day=2)
    _record(client, riverside, harbor, 2, 0, matchday=2, day=9)
    _record(client, oakwood, harbor, 1, 1, matchday=2, day=9)
    _record(client, riverside, oakwood, 2, 1, matchday=3, day=16)
    _record(client, riverside, harbor, 4, 2, matchday=4, day=23)

    standings = client.get("/api/standings").json()
    by_name = {row["team"]["name"]: row for row in standings}

    assert len(standings) == 4

    riverside_row = by_name["Riverside FC"]
    assert riverside_row["played"] == 4
    assert riverside_row["won"] == 4
    assert riverside_row["drawn"] == 0
    assert riverside_row["lost"] == 0
    assert riverside_row["points"] == 12

    oakwood_row = by_name["Oakwood United"]
    assert oakwood_row["played"] == 3
    assert oakwood_row["won"] == 0
    assert oakwood_row["drawn"] == 1
    assert oakwood_row["lost"] == 2
    assert oakwood_row["points"] == 1

    harbor_row = by_name["Harbor City"]
    assert harbor_row["played"] == 3
    assert harbor_row["drawn"] == 1
    assert harbor_row["lost"] == 2
    assert harbor_row["points"] == 1

    iron_bridge_row = by_name["Iron Bridge"]
    assert iron_bridge_row["played"] == 0
    assert iron_bridge_row["points"] == 0

    # Ranked by total points, highest first
    assert [row["points"] for row in standings] == sorted(
        (row["points"] for row in standings), reverse=True
    )
    assert standings[0]["team"]["name"] == "Riverside FC"

    # Match history is visible and complete for sharing the league state
    history = client.get("/api/matches").json()
    assert len(history) == 5
    assert {m["matchday"] for m in history} == {1, 2, 3, 4}


def test_standings_recomputed_fresh_on_every_request(client):
    """Standings must always be derived from recorded matches, not cached -
    each additional match changes the response on the very next GET.
    """
    a = _create_team(client, "A")
    b = _create_team(client, "B")

    before = {r["team"]["name"]: r["points"] for r in client.get("/api/standings").json()}
    assert before == {"A": 0, "B": 0}

    _record(client, a, b, 2, 0, matchday=1, day=2)

    after = {r["team"]["name"]: r["points"] for r in client.get("/api/standings").json()}
    assert after == {"A": 3, "B": 0}
