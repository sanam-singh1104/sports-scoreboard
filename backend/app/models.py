"""Pydantic schemas matching the shapes defined in openapi.yaml."""

from datetime import date as date_type

from pydantic import BaseModel, ConfigDict, Field


class Team(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str


class TeamCreate(BaseModel):
    name: str


class Match(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    home_team_id: int = Field(alias="homeTeamId")
    away_team_id: int = Field(alias="awayTeamId")
    home_score: int = Field(alias="homeScore")
    away_score: int = Field(alias="awayScore")
    date: date_type
    matchday: int


class MatchCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    home_team_id: int = Field(alias="homeTeamId")
    away_team_id: int = Field(alias="awayTeamId")
    home_score: int = Field(alias="homeScore")
    away_score: int = Field(alias="awayScore")
    date: date_type
    matchday: int


class StandingsRow(BaseModel):
    team: Team
    played: int
    won: int
    drawn: int
    lost: int
    points: int
