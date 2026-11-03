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
- Hosting: Render or Fly.io (TBD). Build from the `Dockerfile`.
- Set secrets in the host: `NYC_OPEN_DATA_APP_TOKEN`, `GEOCLIENT_API_KEY`, `DATABASE_URL`, `LLM_API_KEY`.

## Roll back

Redeploy the previous image or revert the commit on `main`.

## Common incidents

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Report page returns 502 | NYC Open Data outage or rate limit | Check data.cityofnewyork.us status; confirm app token; cached reports still serve |
| Every search says "not found" | Geoclient key missing or expired | Check `GEOCLIENT_API_KEY` |
| Assistant returns 501 | `LLM_API_KEY` missing | Set the key |
| No alerts sent | Cron job failing or SMTP/SMS not set | Check the "Daily alerts" workflow logs |
