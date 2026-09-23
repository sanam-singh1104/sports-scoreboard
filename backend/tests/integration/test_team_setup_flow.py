"""End-to-end coverage of product-spec.md Feature 1 (Team setup), driven
through the HTTP API against a real SQLite file.
"""


def test_created_team_persists_and_appears_in_list(client):
    resp = client.post("/api/teams", json={"name": "Riverside FC"})
    assert resp.status_code == 201
    team_id = resp.json()["id"]

    listed = client.get("/api/teams").json()
    assert listed == [{"id": team_id, "name": "Riverside FC"}]


def test_team_with_no_matches_shows_zeroed_standings_row(client):
    client.post("/api/teams", json={"name": "Iron Bridge"})

    rows = client.get("/api/standings").json()
    assert len(rows) == 1
    row = rows[0]
    assert row["team"]["name"] == "Iron Bridge"
    assert (
        row["played"] == row["won"] == row["drawn"] == row["lost"] == row["points"] == 0
    )


def test_duplicate_team_name_rejected_case_insensitively(client):
    client.post("/api/teams", json={"name": "Riverside FC"})
    resp = client.post("/api/teams", json={"name": "riverside fc"})
    assert resp.status_code == 409

    # Rejected duplicate must not have been persisted
    listed = client.get("/api/teams").json()
    assert len(listed) == 1
