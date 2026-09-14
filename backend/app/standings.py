"""Standings calculation: derives each team's record and points from the
recorded matches using classic 3-1-0 scoring (win=3, draw=1 each, loss=0).
"""

from .models import Match, StandingsRow, Team


def compute_standings(teams: list[Team], matches: list[Match]) -> list[StandingsRow]:
    stats = {
        team.id: {
            "team": team,
            "played": 0,
            "won": 0,
            "drawn": 0,
            "lost": 0,
            "points": 0,
        }
        for team in teams
    }

    for match in matches:
        home = stats.get(match.home_team_id)
        away = stats.get(match.away_team_id)
        if home is None or away is None:
            # Match references a team not in `teams`; ignore defensively
            # rather than raising, since standings is a read-only view.
            continue

        home["played"] += 1
        away["played"] += 1

        if match.home_score > match.away_score:
            home["won"] += 1
            home["points"] += 3
            away["lost"] += 1
        elif match.home_score < match.away_score:
            away["won"] += 1
            away["points"] += 3
            home["lost"] += 1
        else:
            home["drawn"] += 1
            away["drawn"] += 1
            home["points"] += 1
            away["points"] += 1

    rows = [StandingsRow(**row) for row in stats.values()]
    rows.sort(key=lambda row: row.points, reverse=True)
    return rows
