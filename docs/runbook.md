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
- Set required environment variables in the Vercel project settings: `NYC_OPEN_DATA_APP_TOKEN`, `GEOCLIENT_API_KEY`, `DATABASE_URL`, and `LLM_API_KEY`. Set `LLM_MODEL` to `gpt-5.4-mini` for the OpenAI Responses API integration. Other optional variables: `SMTP_URL`, `SMS_API_KEY`.

### OpenAI API smoke test

Set `LLM_API_KEY` and `LLM_MODEL=gpt-5.4-mini` in the local `.env` file, then run `py -m app.llm_smoke_test` from the repository root. The script sends a fixed, non-sensitive test prompt and prints the model response. It never prints the API key. Configure the same variables in Vercel when deploying the AI integration; do not commit `.env` or paste keys into source control.

### Vercel operations

1. Connect the GitHub repository to a Vercel project and configure the production branch.
2. Add environment variables in the Vercel project settings, then redeploy for changes to take effect.
3. Confirm the production URL and `/healthz` return successfully after deployment.

## Roll back

In the Vercel project dashboard, promote a previous healthy deployment. If the issue came from a code change, revert that change on the production branch and redeploy.

## Alerts and dashboards

### Sentry

The app initializes Sentry only when `SENTRY_DSN` is configured. Create a Python project in Sentry, copy its DSN into the Vercel project's `SENTRY_DSN` environment variable for Production, then redeploy. Do not commit the DSN. Error events omit query strings, request data, headers, cookies, user data, and breadcrumbs to avoid collecting tenant addresses or contact details. If the DSN is unset, error reporting is disabled.

To verify a deployment, use Sentry's **Send a test event** option or a controlled test event in a non-production environment, then confirm the event appears in the project's **Issues** view. Do not trigger an intentional production exception on a tenant-facing route. A local test event only verifies the local `.env` configuration; it does not verify production.

### UptimeRobot

Create an HTTPS monitor in UptimeRobot with:

- **Monitor type:** HTTP(s)
- **URL:** `https://tenanttrack-nyc.vercel.app/healthz`
- **Monitoring interval:** 5 minutes
- **Alert contact:** a contact method you control

Save the monitor, verify that it reports the endpoint as up, and use UptimeRobot's **Test Notification** action to confirm notifications reach your contact. The `/healthz` route reports application availability; it does not check NYC APIs or database dependencies.

## Common incidents

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Report page returns 502 | NYC Open Data outage or rate limit | Check data.cityofnewyork.us status; confirm app token; cached reports still serve |
| Every search says "not found" | Geoclient key missing or expired | Check `GEOCLIENT_API_KEY` |
| Assistant returns 501 | `LLM_API_KEY` missing | Set the key |
| No alerts sent | Cron job failing or SMTP/SMS not set | Check the "Daily alerts" workflow logs |
| No application errors appear in Sentry | `SENTRY_DSN` is missing, invalid, or the deployment predates its configuration | Check the Vercel Production environment variable, redeploy, then verify with a non-production test event |
