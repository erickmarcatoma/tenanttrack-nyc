# TenantTrack NYC

**Live app:** [tenanttrack-nyc.vercel.app](https://tenanttrack-nyc.vercel.app/)

Bilingual, mobile-first web app that shows NYC tenants open HPD violations and 311 complaints, flags overdue repairs, and drafts complaints with an AI assistant. Built on NYC Open Data.

> Status: deployed; features remain in development. See [PLAN.md](PLAN.md) for the roadmap.

## The problem

NYC renters living with unrepaired housing violations can't easily see what is open in their building, whether the landlord is past the legal repair deadline, or what to do next. The data is public, but it is split across 311 and HPD datasets, written in code-level language, and English-only in practice.

## What it does

1. **Look up a building.** Enter any NYC address, with no login required.
2. **See the report.** Open HPD violations, recent 311 complaints, and the landlord's record, in plain English or Spanish.
3. **Spot overdue repairs.** A rules engine flags every violation past its legal correction deadline, based on its class (A, B, C).
4. **Take action.** An AI assistant explains each violation and drafts an HPD complaint or a landlord letter in English or Spanish.
5. **Stay updated.** Optional email or SMS alerts when a violation opens, closes, or becomes overdue.

## Architecture

```
PWA frontend (HTMX, offline cache)
        │
        ▼
FastAPI backend
 ├── Data pipeline ──► NYC Open Data (311, HPD) + Geoclient
 ├── Rules engine      (deadlines by violation class)
 ├── AI agent ───────► LLM API (explain + draft, EN/ES)
 └── Alert job ──────► Email / SMS
        │
        ▼
Postgres (cache, alert subscriptions)
```

- **One AI agent, three tools:** `lookup_violations`, `check_deadlines`, `draft_letter`. Deadlines come from tested Python code, not from the LLM.
- **No accounts.** The only personal data kept is a contact for alerts, and users can delete it with one tap.

## Tech stack

| Layer | Choice |
| --- | --- |
| Backend | Python 3.12, FastAPI |
| Frontend | HTMX, server-rendered templates, PWA (service worker) |
| Database | Postgres |
| AI | LLM API with tool calling |
| CI/CD | GitHub Actions (lint, pytest, axe accessibility checks) |
| Hosting | Vercel |

## Data sources

| Dataset | ID | Use |
| --- | --- | --- |
| [311 Service Requests](https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9) | `erm2-nwe9` | Housing complaints per building |
| [HPD Housing Maintenance Code Violations](https://data.cityofnewyork.us/Housing-Development/Housing-Maintenance-Code-Violations/wvxf-dwi5) | `wvxf-dwi5` | Open violations, class, status |
| NYC Geoclient API | — | Address → BBL / BIN |

## Project structure

```
app/
  api/        routes: search, report, agent, alerts
  data/       NYC Open Data + Geoclient clients, cache, ETL
  rules/      violation deadlines and overdue logic
  agent/      AI agent, tools, prompts (en/es)
  alerts/     daily status diff + notifications
  db/         models and migrations
  templates/  HTMX pages
  static/     css, js, service worker, manifest
  i18n/       en.json, es.json
tests/        unit and integration tests, fixtures
docs/         PRD, architecture, runbook, privacy, accessibility audit, user research
```

## Getting started

> Setup steps will be finalized as the MVP lands.

```bash
git clone https://github.com/erickmarcatoma/tenanttrack-nyc.git
cd tenanttrack-nyc
cp .env.example .env          # add your API keys
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Run tests:

```bash
pytest
```

## Accessibility and privacy

- Targets **WCAG 2.1 AA**. The audit report will live in `docs/accessibility-audit.md`.
- Built for low-end phones and slow connections: lightweight pages, offline support.
- No accounts and no tracking. See `docs/privacy.md`.

## Disclaimer

TenantTrack NYC is an independent project and is not affiliated with the City of New York, HPD, or 311. It explains public data and tenant rights, but it does not give legal advice. For legal help, contact a tenant legal-aid organization.

## License

MIT
