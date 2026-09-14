def test_list_teams_empty(client):
    resp = client.get("/api/teams")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_team(client):
    resp = client.post("/api/teams", json={"name": "Riverside FC"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Riverside FC"
    assert isinstance(body["id"], int)


def test_created_team_appears_in_list(client):
    client.post("/api/teams", json={"name": "Riverside FC"})
    client.post("/api/teams", json={"name": "Oakwood United"})

    resp = client.get("/api/teams")
    names = [t["name"] for t in resp.json()]
    assert names == ["Riverside FC", "Oakwood United"]


def test_create_team_blank_name_rejected(client):
    resp = client.post("/api/teams", json={"name": "   "})
    assert resp.status_code == 400


def test_create_team_duplicate_name_rejected(client):
    client.post("/api/teams", json={"name": "Riverside FC"})
    resp = client.post("/api/teams", json={"name": "Riverside FC"})
    assert resp.status_code == 409


def test_create_team_duplicate_name_case_insensitive(client):
    client.post("/api/teams", json={"name": "Riverside FC"})
    resp = client.post("/api/teams", json={"name": "riverside fc"})
    assert resp.status_code == 409
