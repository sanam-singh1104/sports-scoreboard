# Sports League Scoreboard — Product Spec

## Overview
A web app for running a sports league. An organizer sets up the league's
teams, records match results, and the app calculates and displays an
up-to-date standings table using classic 3-1-0 scoring.

## Target user
A league organizer (e.g. someone running a small amateur or hobby league)
who wants results and standings in one place, without spreadsheets.

## Core concept
Matches are the input; the standings table is the output. The app derives
each team's record and points from the recorded matches, rather than anyone
editing the table by hand.

## Features & user stories

### 1. Team setup
- As an organizer, I want to add teams to the league so that I can record
  matches between them.
- Acceptance criteria:
  - I can add a team by name.
  - Added teams persist and appear in a list.
  - A team with no matches yet still exists and shows in the standings with
    zeroed stats.

### 2. Record matches
- As an organizer, I want to record a match result so that the standings
  update automatically.
- Acceptance criteria:
  - I pick two (different) teams from the existing teams.
  - I enter a score for each team, a date, and a matchday/round number.
  - On save, the match is stored and appears in the match history.

### 3. Standings calculation
- As an organizer, I want points calculated automatically so that the table
  is always correct.
- Acceptance criteria:
  - For each match: higher score = win (3 pts), equal = draw (1 pt each),
    lower = loss (0 pts).
  - Each team's row shows played, won, drawn, lost, and total points.
  - Totals are computed from all recorded matches, not entered by hand.

### 4. Standings view
- As an organizer, I want to see the ranked league table and match history
  so that I can share the current state of the league.
- Acceptance criteria:
  - The standings table is ranked by total points (highest first).
  - A list of recorded matches (with teams, score, date, matchday) is
    visible.

## Non-goals (deliberately out of scope)
- No per-player statistics (goals, assists, cards).
- No user accounts, logins, or permissions.
- No live/in-progress scoring — only final results.
- No fixtures/scheduling of future matches.
- No multi-league support — one league.
- No tie-breaker rules beyond total points (fine for now).

## Tech (per Module 2)
- Frontend: browser UI (prototype tool TBD).
- Backend: FastAPI.
- Contract: OpenAPI (openapi.yaml) as the source of truth between them.
- Storage: SQLite, kept swappable so Postgres can replace it later.
- Tests covering the spec's behavior.
