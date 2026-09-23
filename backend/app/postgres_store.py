"""PostgreSQL implementation of the Store interface (see storage.py). Used
in place of SqliteStore when DATABASE_URL is set (see main.py) - e.g. by the
`backend` service in docker-compose.yml, which points it at the `db`
service by name rather than localhost.

Table setup (equivalent to a migration for this project's simple, additive
schema) runs on every startup via CREATE TABLE IF NOT EXISTS, the same
approach sqlite_store.py uses - idempotent, so it's safe to run every time
the container starts.

A single connection (autocommit) is kept open for the lifetime of the store
and guarded by a lock, mirroring SqliteStore, since FastAPI runs sync
endpoints in a threadpool.
"""

import threading
import time
from datetime import date as date_type

import psycopg
from psycopg.rows import DictRow, dict_row

from .models import Match, Team
from .storage import Store

_SCHEMA = """
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    home_team_id INTEGER NOT NULL REFERENCES teams(id),
    away_team_id INTEGER NOT NULL REFERENCES teams(id),
    home_score INTEGER NOT NULL,
    away_score INTEGER NOT NULL,
    date DATE NOT NULL,
    matchday INTEGER NOT NULL
);
"""

# The db container may still be starting (or restarting) when the backend
# tries to connect even after compose's healthcheck-gated startup order, so
# retry for a while rather than crashing on the first attempt.
_CONNECT_RETRIES = 10
_CONNECT_RETRY_DELAY_SECONDS = 1.0


class PostgresStore(Store):
    def __init__(self, dsn: str) -> None:
        self._lock = threading.Lock()
        self._conn = self._connect_with_retry(dsn)
        with self._lock:
            self._conn.execute(_SCHEMA)

    @staticmethod
    def _connect_with_retry(dsn: str) -> psycopg.Connection:
        last_error: Exception | None = None
        for attempt in range(_CONNECT_RETRIES):
            try:
                return psycopg.connect(dsn, autocommit=True, row_factory=dict_row)
            except psycopg.OperationalError as exc:
                last_error = exc
                if attempt < _CONNECT_RETRIES - 1:
                    time.sleep(_CONNECT_RETRY_DELAY_SECONDS)
        raise ConnectionError(
            f"Could not connect to Postgres after {_CONNECT_RETRIES} attempts"
        ) from last_error

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
        with self._lock:
            row = self._conn.execute(
                "INSERT INTO teams (name) VALUES (%s) RETURNING id", (name,)
            ).fetchone()
        return Team(id=row["id"], name=name)

    def get_team(self, team_id: int) -> Team | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT id, name FROM teams WHERE id = %s", (team_id,)
            ).fetchone()
        return Team(id=row["id"], name=row["name"]) if row else None

    def team_name_exists(self, name: str) -> bool:
        with self._lock:
            row = self._conn.execute(
                "SELECT 1 FROM teams WHERE lower(name) = lower(%s)", (name,)
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
        with self._lock:
            row = self._conn.execute(
                "INSERT INTO matches "
                "(home_team_id, away_team_id, home_score, away_score, date, matchday) "
                "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                (home_team_id, away_team_id, home_score, away_score, match_date, matchday),
            ).fetchone()
        return Match(
            id=row["id"],
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            home_score=home_score,
            away_score=away_score,
            date=match_date,
            matchday=matchday,
        )

    @staticmethod
    def _row_to_match(row: DictRow) -> Match:
        return Match(
            id=row["id"],
            home_team_id=row["home_team_id"],
            away_team_id=row["away_team_id"],
            home_score=row["home_score"],
            away_score=row["away_score"],
            date=row["date"],
            matchday=row["matchday"],
        )
