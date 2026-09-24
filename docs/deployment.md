# Deploying to Render

The backend deploys to [Render](https://render.com) from a Blueprint:
[`render.yaml`](../render.yaml) at the repo root. It describes the whole
setup as code, so Render creates everything in one step:

| Resource | Name | What it is |
| --- | --- | --- |
| Web service | `sports-scoreboard-api` | The FastAPI backend, built from `backend/Dockerfile` |
| Postgres | `sports-scoreboard-db` | A managed Postgres 16 database |

## How the pieces fit together

- **Database connection.** The Blueprint sets `DATABASE_URL` on the web
  service from the database's `connectionString` (its internal URL).
  `app/main.py` uses `PostgresStore` whenever `DATABASE_URL` is set, and
  falls back to SQLite when it isn't.
- **Port.** Render tells the service which port to listen on through the
  `PORT` environment variable. The Dockerfile's `CMD` passes `$PORT` to
  uvicorn. The Dockerfile sets `PORT=8000` as the default, so
  docker-compose and a plain `docker run` work without it.
- **Tables.** On every startup, `PostgresStore` runs
  `CREATE TABLE IF NOT EXISTS` for `teams` and `matches`. This is safe to
  repeat, so there's no separate migration step. The first deploy creates
  the schema, and later deploys leave the existing data alone. If the
  database is still starting up, `PostgresStore` retries the connection
  for about 10 seconds before giving up.
- **Health check.** Render polls `GET /api/teams` (`healthCheckPath`) and
  only sends traffic to a new deploy once it returns 200.

## Prerequisites

- A Render account (the free tier is enough).
- The repo pushed to GitHub (or GitLab/Bitbucket), with `render.yaml` on
  the branch you want to deploy (`main`).

## Step-by-step

1. **Push the code.** Make sure `render.yaml` and the current
   `backend/Dockerfile` are pushed to `main`.

2. **Create the Blueprint.** In the Render Dashboard, click **New +** →
   **Blueprint**.

3. **Connect the repo.** Authorize Render's GitHub app if you haven't yet,
   then select the `sports-scoreboard` repository and the `main` branch.

4. **Review the plan.** Render reads `render.yaml` and lists the resources
   it will create: the `sports-scoreboard-api` web service and the
   `sports-scoreboard-db` database. Give the Blueprint a name (for example,
   `sports-scoreboard`) and click **Apply**.

5. **Wait for provisioning.** Render creates the database first, then
   builds the Docker image and starts the web service. Follow the progress
   in the web service's **Logs** tab. A successful start looks like:

   ```
   INFO:     Uvicorn running on http://0.0.0.0:10000 (Press CTRL+C to quit)
   INFO:     ... "GET /api/teams HTTP/1.1" 200 OK
   ```

6. **Check the deploy.** Copy the service URL from the top of its page
   (for example, `https://sports-scoreboard-api.onrender.com`) and try it:

   ```sh
   curl https://sports-scoreboard-api.onrender.com/api/teams
   # []

   curl -X POST https://sports-scoreboard-api.onrender.com/api/teams \
     -H "Content-Type: application/json" \
     -d '{"name": "Tigers"}'

   curl https://sports-scoreboard-api.onrender.com/api/standings
   ```

   The interactive API docs are at `/docs` on the same URL.

7. **Confirm the data persists.** Trigger a restart (**Manual Deploy** →
   **Deploy latest commit**), then run `GET /api/teams` again. Teams you
   created before the restart should still be listed, because they're
   stored in Postgres and not in the container.

## Redeploying

Render's auto-deploy is off (`autoDeploy: false`). A push to `main`
deploys only after CI passes: `.github/workflows/deploy.yml` then triggers
Render through the service's Deploy Hook. That workflow needs a one-time
setup of GitHub secrets. See [release-process.md](./release-process.md)
for the setup, the full release flow, and how to roll back.

To change the infrastructure (plans, region, env vars), edit `render.yaml`
and push. Render syncs Blueprint changes automatically.

## Connecting the frontend

`frontend/app.js` currently points at `http://localhost:8000/api`
(`API_BASE`). To use the deployed backend, change `API_BASE` to your
service URL plus `/api`. CORS is already open (`allow_origins=["*"]`).

## Troubleshooting

| Symptom | Likely cause / fix |
| --- | --- |
| Deploy fails with "no open ports detected" | The app isn't binding to `$PORT`. Check that the Dockerfile's `CMD` is the shell form that uses `"$PORT"`. |
| `ConnectionError: Could not connect to Postgres` in logs | The database isn't ready or `DATABASE_URL` is missing. Check that the database status is **Available** and that the web service's **Environment** tab lists `DATABASE_URL`, then redeploy. |
| Data disappears after a restart | `DATABASE_URL` wasn't set, so the app fell back to SQLite inside the container. Check the env var as above. |
| First request takes about 30–60 seconds | Free web services spin down when idle and have to start again. Use a paid plan to keep the service running. |
| Database gone after about 30 days | Free Render Postgres databases expire. Upgrade the plan in `render.yaml` (for example, `plan: basic-256mb`) for anything long-lived. |

## Local equivalent

`docker compose up --build` runs the same setup locally: the same
Dockerfile, a Postgres 16 container, and `DATABASE_URL` wired between
them. See [`docker-compose.yml`](../docker-compose.yml).
