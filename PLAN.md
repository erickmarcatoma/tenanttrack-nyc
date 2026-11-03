# TenantTrack NYC — Project Plan

Solo build, about 8 weeks. Goal: a live, tested, accessible MVP, then v2, with docs and user research that match the NYC OTI Senior Product Engineer JD.

## Milestones

| Phase | Weeks | Deliverable | Done when |
| --- | --- | --- | --- |
| 0. Setup | 0 | Repo, README, plan, PRD | Repo is public with docs |
| 1. MVP | 1–3 | Address lookup → building report | Any NYC address shows open violations and 311 complaints |
| 2. Rules engine | 4 | Overdue flags by violation class | 50 hand-checked violations flagged correctly; ≥ 90% test coverage |
| 3. CI/CD + observability | 5 | GitHub Actions, logging, monitoring | Every push runs lint, tests, and axe checks; uptime monitor live |
| 4. AI agent | 6–7 | Explain violations + draft letters (EN/ES) | Agent uses tools for all facts; drafts reviewed in both languages |
| 5. v2 | 8 | Alerts, offline mode, audits | Alerts fire on status change; WCAG audit and privacy note published |
| Ongoing | 1–8 | User research + docs | 5 tenant interviews written up; runbook and architecture doc done |

## Phase details

### Phase 1: MVP (weeks 1–3)
- [ ] Scaffold FastAPI app, config, Dockerfile
- [ ] Geoclient client: address → BBL/BIN
- [ ] HPD violations client (`wvxf-dwi5`)
- [ ] 311 client (`erm2-nwe9`), filtered to HPD housing complaints
- [ ] Postgres cache for API responses
- [ ] HTMX pages: search, building report
- [ ] English/Spanish i18n
- [ ] Deploy to Render or Fly.io

### Phase 2: Rules engine (week 4)
- [ ] Confirm current legal correction periods for class A, B, C violations from HPD rules
- [ ] `rules/deadlines.py`: deadline per class
- [ ] `rules/overdue.py`: overdue / due soon / on time
- [ ] pytest suite with fixtures and edge cases
- [ ] Show overdue flags on the report page

### Phase 3: CI/CD + observability (week 5)
- [ ] `ci.yml`: ruff, pytest, coverage, axe-core
- [ ] Structured logging
- [ ] Error tracking and uptime monitoring
- [ ] Auto-deploy on merge to main

### Phase 4: AI agent (weeks 6–7)
- [ ] Choose the LLM API
- [ ] Agent loop with three tools: `lookup_violations`, `check_deadlines`, `draft_letter`
- [ ] Prompts in English and Spanish
- [ ] Guardrails: no legal advice, cite only tool data, link to legal aid
- [ ] Tests for tool calls and draft output

### Phase 5: v2 (week 8)
- [ ] Daily alert job: status diff, email/SMS
- [ ] One-tap unsubscribe that deletes contact info
- [ ] Service worker for offline report viewing
- [ ] Messy CSV/PDF feed ingestion (cut first if time runs short)
- [ ] Owner view: other buildings by the same landlord

### Ongoing: research and docs
- [ ] Recruit 5 tenants (tenant associations, legal-aid clinics)
- [ ] Interview guide, notes, findings in `docs/user-research.md`
- [ ] `docs/architecture.md` with diagram
- [ ] `docs/runbook.md`: deploy, rollback, data outages
- [ ] `docs/privacy.md` and `docs/accessibility-audit.md`

## Success metrics

| Goal | Metric | Target |
| --- | --- | --- |
| Understandable data | Testers explain their violations correctly | 4 of 5 |
| Act on overdue repairs | Draft rate on reports with overdue items | ≥ 30% |
| Bilingual parity | Task completion gap, ES vs EN | ≤ 5 points |
| Low-end performance | Lighthouse mobile, slow 4G | ≥ 90; report < 3 s |
| Accessibility | axe critical/serious issues | 0 |
| Correct deadlines | Hand-checked sample of 50 violations | 100% |

## Scope cuts if time runs short

1. Messy CSV/PDF feed
2. Alerts (keep the report and the agent)
3. Owner portfolio view

Keep the rules engine, AI agent, and tenant interviews. These map most closely to the JD.

## Risks

| Risk | Mitigation |
| --- | --- |
| Open Data API rate limits or outages | Cache responses; app token; show last-updated time |
| LLM states wrong deadlines | Deadlines come only from the rules engine tool |
| Hard to recruit tenants | Start outreach in week 1 |
| Solo scope creep | Follow the cut list above |
