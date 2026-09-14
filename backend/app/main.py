"""FastAPI app implementing the API defined in openapi.yaml."""

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import Match, MatchCreate, StandingsRow, Team, TeamCreate
from .sqlite_store import SqliteStore
from .standings import compute_standings
from .storage import InMemoryStore, Store


def create_app(store: Store | None = None) -> FastAPI:
    """Factory so tests (and callers) can inject a fresh, isolated store
    instead of sharing the process-wide default.
    """
    app = FastAPI(title="Sports League Scoreboard API", version="0.1.0")
    app.state.store = store or InMemoryStore()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def get_store() -> Store:
        return app.state.store

    @app.get("/api/teams", response_model=list[Team])
    def list_teams() -> list[Team]:
        return get_store().list_teams()

    @app.post("/api/teams", response_model=Team, status_code=201)
    def create_team(payload: TeamCreate) -> Team:
        name = payload.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Team name must not be blank")

        store = get_store()
        if store.team_name_exists(name):
            raise HTTPException(
                status_code=409, detail=f'A team named "{name}" already exists'
            )
        return store.create_team(name)

    @app.get("/api/matches", response_model=list[Match])
    def list_matches() -> list[Match]:
        return get_store().list_matches()

    @app.post("/api/matches", response_model=Match, status_code=201)
    def create_match(payload: MatchCreate) -> Match:
        store = get_store()

        if payload.home_team_id == payload.away_team_id:
            raise HTTPException(
                status_code=400,
                detail="awayTeamId must be different from homeTeamId",
            )
        if payload.home_score < 0 or payload.away_score < 0:
            raise HTTPException(
                status_code=400, detail="Scores must be non-negative"
            )
        if payload.matchday < 1:
            raise HTTPException(
                status_code=400, detail="matchday must be at least 1"
            )
        if store.get_team(payload.home_team_id) is None:
            raise HTTPException(
                status_code=400,
                detail=f"homeTeamId {payload.home_team_id} does not exist",
            )
        if store.get_team(payload.away_team_id) is None:
            raise HTTPException(
                status_code=400,
                detail=f"awayTeamId {payload.away_team_id} does not exist",
            )

        return store.create_match(
            home_team_id=payload.home_team_id,
            away_team_id=payload.away_team_id,
            home_score=payload.home_score,
            away_score=payload.away_score,
            match_date=payload.date,
            matchday=payload.matchday,
        )

    @app.get("/api/standings", response_model=list[StandingsRow])
    def get_standings() -> list[StandingsRow]:
        store = get_store()
        return compute_standings(store.list_teams(), store.list_matches())

    return app


def _default_db_path() -> str:
    """Resolved relative to this file (backend/scoreboard.db) rather than
    the process's cwd, so it doesn't matter where uvicorn is launched from.
    Override with SCOREBOARD_DB_PATH, e.g. to point at a different file.
    """
    env_path = os.environ.get("SCOREBOARD_DB_PATH")
    if env_path:
        return env_path
    return str(Path(__file__).resolve().parent.parent / "scoreboard.db")


app = create_app(SqliteStore(_default_db_path()))
