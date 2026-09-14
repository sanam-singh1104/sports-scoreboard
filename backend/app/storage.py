"""Storage layer, kept behind an abstract interface so the in-memory
implementation can be swapped for a SQLite (or other) implementation later
without changing the API layer in main.py.
"""

from abc import ABC, abstractmethod
from datetime import date as date_type

from .models import Match, Team


class Store(ABC):
    @abstractmethod
    def list_teams(self) -> list[Team]: ...

    @abstractmethod
    def create_team(self, name: str) -> Team: ...

    @abstractmethod
    def get_team(self, team_id: int) -> Team | None: ...

    @abstractmethod
    def team_name_exists(self, name: str) -> bool: ...

    @abstractmethod
    def list_matches(self) -> list[Match]: ...

    @abstractmethod
    def create_match(
        self,
        home_team_id: int,
        away_team_id: int,
        home_score: int,
        away_score: int,
        match_date: date_type,
        matchday: int,
    ) -> Match: ...


class InMemoryStore(Store):
    """Keeps teams and matches in plain dicts, in process memory only."""

    def __init__(self) -> None:
        self._teams: dict[int, Team] = {}
        self._matches: dict[int, Match] = {}
        self._next_team_id = 1
        self._next_match_id = 1

    def list_teams(self) -> list[Team]:
        return list(self._teams.values())

    def create_team(self, name: str) -> Team:
        team = Team(id=self._next_team_id, name=name)
        self._teams[team.id] = team
        self._next_team_id += 1
        return team

    def get_team(self, team_id: int) -> Team | None:
        return self._teams.get(team_id)

    def team_name_exists(self, name: str) -> bool:
        return any(t.name.lower() == name.lower() for t in self._teams.values())

    def list_matches(self) -> list[Match]:
        return list(self._matches.values())

    def create_match(
        self,
        home_team_id: int,
        away_team_id: int,
        home_score: int,
        away_score: int,
        match_date: date_type,
        matchday: int,
    ) -> Match:
        match = Match(
            id=self._next_match_id,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            home_score=home_score,
            away_score=away_score,
            date=match_date,
            matchday=matchday,
        )
        self._matches[match.id] = match
        self._next_match_id += 1
        return match
