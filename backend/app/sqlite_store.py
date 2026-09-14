"""SQLite implementation of the Store interface (see storage.py). Data is
persisted to a file, so it survives process restarts. A single connection
is kept open for the lifetime of the store and guarded by a lock, since
FastAPI runs sync endpoints in a threadpool and sqlite3 connections aren't
safe to use concurrently from multiple threads without one.

Swapping this for Postgres later means writing a PostgresStore that
implements the same Store interface (e.g. with psycopg) - the API layer in
main.py only depends on that interface, not on SQLite specifically.
"""

import sqlite3
import threading
from datetime import date as date_type

from .models import Match, Team
from .storage import Store

_SCHEMA = """
CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    home_team_id INTEGER NOT NULL REFERENCES teams(id),
    away_team_id INTEGER NOT NULL REFERENCES teams(id),
    home_score INTEGER NOT NULL,
    away_score INTEGER NOT NULL,
    date TEXT NOT NULL,
    matchday INTEGER NOT NULL
);
"""


class SqliteStore(Store):
    def __init__(self, db_path: str) -> None:
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock, self._conn:
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def list_teams(self) -> list[Team]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, name FROM teams ORDER BY id"
            ).fetchall()
        return [Team(id=row["id"], name=row["name"]) for row in rows]

    def create_team(self, name: str) -> Team:
        with self._lock, self._conn:
            cursor = self._conn.execute(
                "INSERT INTO teams (name) VALUES (?)", (name,)
            )
            team_id = cursor.lastrowid
        return Team(id=team_id, name=name)

    def get_team(self, team_id: int) -> Team | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT id, name FROM teams WHERE id = ?", (team_id,)
            ).fetchone()
        return Team(id=row["id"], name=row["name"]) if row else None

    def team_name_exists(self, name: str) -> bool:
        with self._lock:
            row = self._conn.execute(
                "SELECT 1 FROM teams WHERE lower(name) = lower(?)", (name,)
            ).fetchone()
        return row is not None

    def list_matches(self) -> list[Match]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, home_team_id, away_team_id, home_score, away_score, "
                "date, matchday FROM matches ORDER BY id"
            ).fetchall()
        return [self._row_to_match(row) for row in rows]

    def create_match(
        self,
        home_team_id: int,
        away_team_id: int,
        home_score: int,
        away_score: int,
        match_date: date_type,
        matchday: int,
    ) -> Match:
        date_str = match_date.isoformat()
        with self._lock, self._conn:
            cursor = self._conn.execute(
                "INSERT INTO matches "
                "(home_team_id, away_team_id, home_score, away_score, date, matchday) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (home_team_id, away_team_id, home_score, away_score, date_str, matchday),
            )
            match_id = cursor.lastrowid
        return Match(
            id=match_id,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            home_score=home_score,
            away_score=away_score,
            date=match_date,
            matchday=matchday,
        )

    @staticmethod
    def _row_to_match(row: sqlite3.Row) -> Match:
        return Match(
            id=row["id"],
            home_team_id=row["home_team_id"],
            away_team_id=row["away_team_id"],
            home_score=row["home_score"],
            away_score=row["away_score"],
            date=date_type.fromisoformat(row["date"]),
            matchday=row["matchday"],
        )
