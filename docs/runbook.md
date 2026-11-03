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
- Production URL: https://tenanttrack-nyc.vercel.app/
- Hosting: Vercel, connected to the GitHub repository. The deployment's `/healthz` endpoint has been verified.
- Set required environment variables in the Vercel project settings: `NYC_OPEN_DATA_APP_TOKEN`, `GEOCLIENT_API_KEY`, `DATABASE_URL`, and `LLM_API_KEY`. Optional variables: `LLM_MODEL`, `SMTP_URL`, `SMS_API_KEY`.

### Vercel operations

1. Connect the GitHub repository to a Vercel project and configure the production branch.
2. Add environment variables in the Vercel project settings, then redeploy for changes to take effect.
3. Confirm the production URL and `/healthz` return successfully after deployment.

## Roll back

In the Vercel project dashboard, promote a previous healthy deployment. If the issue came from a code change, revert that change on the production branch and redeploy.

## Common incidents

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Report page returns 502 | NYC Open Data outage or rate limit | Check data.cityofnewyork.us status; confirm app token; cached reports still serve |
| Every search says "not found" | Geoclient key missing or expired | Check `GEOCLIENT_API_KEY` |
| Assistant returns 501 | `LLM_API_KEY` missing | Set the key |
| No alerts sent | Cron job failing or SMTP/SMS not set | Check the "Daily alerts" workflow logs |
