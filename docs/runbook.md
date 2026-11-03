# Runbook

## Run locally

```bash
cp .env.example .env
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Health check: `GET /healthz` returns `{"status": "ok"}`.

## Deploy

- Merges to `main` run CI (lint, tests, accessibility).
- Hosting: Render. The repo includes a `render.yaml` config that builds from the `Dockerfile` and checks `/healthz`.
- Set secrets in the host: `NYC_OPEN_DATA_APP_TOKEN`, `GEOCLIENT_API_KEY`, `DATABASE_URL`, `LLM_API_KEY`, and optional `LLM_MODEL`, `SMTP_URL`, `SMS_API_KEY`.

### Render setup

1. Create a new Web Service in Render and connect this repo.
2. Choose the Docker runtime; Render will use the repo's `Dockerfile`.
3. Set the health check path to `/healthz`.
4. Add the environment variables above in the Render dashboard.
5. Deploy the service and confirm `/healthz` returns `{"status": "ok"}`.

## Roll back

Redeploy the previous image or revert the commit on `main`.

## Common incidents

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Report page returns 502 | NYC Open Data outage or rate limit | Check data.cityofnewyork.us status; confirm app token; cached reports still serve |
| Every search says "not found" | Geoclient key missing or expired | Check `GEOCLIENT_API_KEY` |
| Assistant returns 501 | `LLM_API_KEY` missing | Set the key |
| No alerts sent | Cron job failing or SMTP/SMS not set | Check the "Daily alerts" workflow logs |
