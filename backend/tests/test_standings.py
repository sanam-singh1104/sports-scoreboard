from datetime import date

from app.models import Match, Team
from app.standings import compute_standings


def record(client, home, away, home_score, away_score, matchday, day="01"):
    return client.post(
        "/api/matches",
        json={
            "homeTeamId": home,
            "awayTeamId": away,
            "homeScore": home_score,
            "awayScore": away_score,
            "date": f"2026-08-{day}",
            "matchday": matchday,
        },
    )


# --- Unit tests directly against compute_standings ---


def test_team_with_no_matches_has_zeroed_stats():
    teams = [Team(id=1, name="Riverside FC")]
    rows = compute_standings(teams, [])

    assert len(rows) == 1
    row = rows[0]
    assert row.played == row.won == row.drawn == row.lost == row.points == 0


def test_win_awards_three_points_to_winner_only():
    teams = [Team(id=1, name="A"), Team(id=2, name="B")]
    matches = [
        Match(
            id=1, home_team_id=1, away_team_id=2, home_score=3, away_score=1,
            date=date(2026, 8, 2), matchday=1,
        )
    ]
    rows = {r.team.id: r for r in compute_standings(teams, matches)}

    assert rows[1].won == 1
    assert rows[1].lost == 0
    assert rows[1].drawn == 0
    assert rows[1].points == 3
    assert rows[2].won == 0
    assert rows[2].lost == 1
    assert rows[2].points == 0


def test_draw_awards_one_point_each():
    teams = [Team(id=1, name="A"), Team(id=2, name="B")]
    matches = [
        Match(
            id=1, home_team_id=1, away_team_id=2, home_score=2, away_score=2,
            date=date(2026, 8, 2), matchday=1,
        )
    ]
    rows = {r.team.id: r for r in compute_standings(teams, matches)}

    assert rows[1].drawn == 1
    assert rows[1].points == 1
    assert rows[2].drawn == 1
    assert rows[2].points == 1


def test_away_win_credited_correctly():
    teams = [Team(id=1, name="A"), Team(id=2, name="B")]
    matches = [
        Match(
            id=1, home_team_id=1, away_team_id=2, home_score=0, away_score=2,
            date=date(2026, 8, 2), matchday=1,
        )
    ]
    rows = {r.team.id: r for r in compute_standings(teams, matches)}

    assert rows[2].won == 1
    assert rows[2].points == 3
    assert rows[1].lost == 1
    assert rows[1].points == 0


def test_played_count_accumulates_across_matches():
    teams = [Team(id=1, name="A"), Team(id=2, name="B"), Team(id=3, name="C")]
    matches = [
        Match(id=1, home_team_id=1, away_team_id=2, home_score=1, away_score=0, date=date(2026, 8, 2), matchday=1),
        Match(id=2, home_team_id=1, away_team_id=3, home_score=2, away_score=2, date=date(2026, 8, 9), matchday=2),
    ]
    rows = {r.team.id: r for r in compute_standings(teams, matches)}

    assert rows[1].played == 2
    assert rows[1].won == 1
    assert rows[1].drawn == 1
    assert rows[1].points == 4


def test_ranked_by_points_highest_first():
    teams = [Team(id=1, name="A"), Team(id=2, name="B"), Team(id=3, name="C")]
    matches = [
        # A beats B, A beats C -> A: 6 pts
        Match(id=1, home_team_id=1, away_team_id=2, home_score=2, away_score=0, date=date(2026, 8, 2), matchday=1),
        Match(id=2, home_team_id=1, away_team_id=3, home_score=1, away_score=0, date=date(2026, 8, 9), matchday=2),
        # B draws C -> B: 1 pt, C: 1 pt
        Match(id=3, home_team_id=2, away_team_id=3, home_score=1, away_score=1, date=date(2026, 8, 16), matchday=3),
    ]
    rows = compute_standings(teams, matches)

    assert [r.team.id for r in rows] == [1, 2, 3]
    assert [r.points for r in rows] == [6, 1, 1]


# --- Integration tests through the API ---


def test_standings_endpoint_includes_team_with_no_matches(client_with_teams):
    resp = client_with_teams.get("/api/standings")
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 3
    assert all(r["played"] == 0 and r["points"] == 0 for r in rows)


def test_standings_endpoint_ranked_by_points(client_with_teams):
    # Riverside FC (1) beats Oakwood United (2): 3-1 -> Riverside 3 pts
    record(client_with_teams, 1, 2, 3, 1, matchday=1, day="02")
    # Oakwood United (2) draws Harbor City (3): 1-1 -> 1 pt each
    record(client_with_teams, 2, 3, 1, 1, matchday=2, day="09")

    resp = client_with_teams.get("/api/standings")
    rows = resp.json()

    points_by_name = {r["team"]["name"]: r["points"] for r in rows}
    assert points_by_name == {
        "Riverside FC": 3,
        "Oakwood United": 1,
        "Harbor City": 1,
    }
    # Highest points first
    assert rows[0]["team"]["name"] == "Riverside FC"
    assert [r["points"] for r in rows] == sorted(
        [r["points"] for r in rows], reverse=True
    )


def test_standings_played_won_drawn_lost_totals(client_with_teams):
    record(client_with_teams, 1, 2, 3, 1, matchday=1, day="02")  # Riverside win
    record(client_with_teams, 1, 3, 2, 2, matchday=2, day="09")  # Riverside draw

    resp = client_with_teams.get("/api/standings")
    rows = {r["team"]["name"]: r for r in resp.json()}

    riverside = rows["Riverside FC"]
    assert riverside["played"] == 2
    assert riverside["won"] == 1
    assert riverside["drawn"] == 1
    assert riverside["lost"] == 0
    assert riverside["points"] == 4

    oakwood = rows["Oakwood United"]
    assert oakwood["played"] == 1
    assert oakwood["lost"] == 1
    assert oakwood["points"] == 0
