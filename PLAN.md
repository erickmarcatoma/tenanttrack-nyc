# TenantTrack NYC: Day-by-Day Plan

Solo hobby build. **1 day = one work session of about 2 hours.** At 5 sessions a week, the plan takes about **8 weeks** (40 days). Skipped a day? Just continue with the next unchecked one.

**How to use this plan**

1. Find the first unchecked day below. That's today's work.
2. Switch to its branch: `git checkout <branch> && git merge main`
3. Tick the boxes as you go. End each day with a commit and push.
4. On the branch's last day, open a PR, wait for green CI, merge, and delete the branch.

## Progress

**Days done: 7 of 40** · Current: **Day 8** (start recruiting tenants) · Next: **Day 9** (`feat/observability`)

| Branch | Days | Status |
| --- | --- | --- |
| `feat/rules-verify` | 1–4 | ✅ Merged and deleted |
| `chore/deploy` | 5–7 | ✅ Live and merged (delete branch) |
| `docs/research-and-audit` | 8 | ⬜ |
| `feat/observability` | 9–11 | ⬜ |
| `feat/ai-agent` | 12–19 | ⬜ |
| `feat/chat-ui` | 20–24 | ⬜ |
| `feat/alerts` | 25–30 | ⬜ |
| `feat/offline-pwa` | 31–33 | ⬜ |
| `docs/research-and-audit` | 34–40 | ⬜ |

Already done on `main`: project scaffold, search page, building report, letter page, rules engine (with draft deadlines), CI, and docs templates.

## Overview

| Week | Days | Branch | Result |
| --- | --- | --- | --- |
| 1 | 1–4 | `feat/rules-verify` | Correct, sourced repair deadlines |
| 1–2 | 5–7 | `chore/deploy` | Live public URL |
| 2 | 8 | `docs/research-and-audit` | Interview recruiting started |
| 2–3 | 9–11 | `feat/observability` | Logs, errors, and uptime monitoring |
| 3–4 | 12–19 | `feat/ai-agent` | Working AI agent with 3 tools |
| 5 | 20–24 | `feat/chat-ui` | Chat screen in the app |
| 6 | 25–30 | `feat/alerts` | Email alerts on status changes |
| 7 | 31–33 | `feat/offline-pwa` | Installable, works offline |
| 7–8 | 34–40 | `docs/research-and-audit` | 5 interviews, accessibility audit, launch |

---

## Week 1: `feat/rules-verify`

**Day 1: Research the rules**
- [x] Find HPD's official correction periods for class A, B, and C violations
- [x] Note special cases (lead paint, window guards, heat, mold) and their periods
- [x] Save source links in `docs/rules-sources.md`

**Day 2: Update the rules engine**
- [x] Update `CORRECTION_DAYS` in `app/rules/deadlines.py` and add a source comment
- [x] Add special-case handling if any differ from the class default
- [x] Add a test for each special case in `tests/test_rules.py`

**Day 3: Check against real data**
- [x] Get an Open Data app token and a Geoclient key, then put them in `.env`
- [x] Run the app locally and look up 3 real buildings
- [x] Hand-check 15 violations: does the app's status match the dataset's correct-by date?
- [x] Write the results as a table in `docs/rules-sources.md`

**Day 4: Fix and merge**
- [x] Check Day 3 results for mismatches (none found)
- [x] Check the rules coverage: `pytest --cov=app/rules` (target ≥ 90%; achieved 100%)
- [x] Fix Class C keyword matching to use whole words (e.g. "decorate" ≠ "rat")
- [x] Open a PR → green CI → merge ([PR #1](https://github.com/erickmarcatoma/tenanttrack-nyc/pull/1))
- [x] Delete the `feat/rules-verify` branch

✅ **Done when:** deadlines match HPD's rules and are backed by sources.

---

## Weeks 1–2: `chore/deploy`

**Day 5: Choose hosting and deploy**
- [x] Deploy to Vercel: https://tenanttrack-nyc.vercel.app/
- [x] Add `NYC_OPEN_DATA_APP_TOKEN` and `GEOCLIENT_API_KEY` to Vercel Production and redeploy

**Day 6: Make it reliable**
- [x] Health check: `/healthz` exists (Vercel has no health-check setting; the uptime monitor on Day 10 will ping it)
- [x] Auto-deploy when `main` changes (on by default with Vercel's GitHub integration)
- [x] Test on your phone over mobile data: search → report → letter

**Day 7: Document and merge**
- [x] Add the live URL to the top of `README.md`
- [x] Update `docs/runbook.md` with the real deploy and rollback steps
- [x] PR → green CI → merge ([PR #2](https://github.com/erickmarcatoma/tenanttrack-nyc/pull/2))
- [ ] Delete the `chore/deploy` branch

✅ **Done when:** a public link works on your phone.

---

## Week 2: `docs/research-and-audit` (part 1)

**Day 8: Start recruiting early**
- [ ] List 5–10 tenant associations, legal-aid clinics, or community groups
- [ ] Send a short message asking for 5 tenants for 30-minute interviews
- [ ] Finalize the interview guide in `docs/user-research.md`
- [ ] Commit and push (don't merge yet; you'll come back to this branch)

✅ **Done when:** outreach is sent.

---

## Weeks 2–3: `feat/observability`

**Day 9: Structured logging**
- [ ] Switch to JSON logs (one line per request: path, status, duration)
- [ ] Log Open Data and Geoclient errors with the dataset name and status code

**Day 10: Error tracking and uptime**
- [ ] Add free error tracking (e.g. Sentry) and set `SENTRY_DSN` in the host
- [ ] Add an uptime monitor (e.g. UptimeRobot) pinging `/healthz` every 5 minutes

**Day 11: Document and merge**
- [ ] Add an "Alerts and dashboards" section to `docs/runbook.md`
- [ ] Trigger a test error and confirm it shows up
- [ ] PR → merge → delete the branch

✅ **Done when:** you'd hear about an outage before a user tells you.

---

## Weeks 3–4: `feat/ai-agent`

**Day 12: Pick the LLM**
- [ ] Choose an LLM API that supports tool calling
- [ ] Add `LLM_API_KEY` and `LLM_MODEL` to `.env` and the host
- [ ] Make one simple API call from a script to confirm it works

**Day 13: Tool definitions**
- [ ] Write the JSON schema for `lookup_violations`, `check_deadlines`, and `draft_letter`
- [ ] Make `check_deadlines` accept a BIN (fetch, then evaluate)

**Day 14: The agent loop**
- [ ] Build the loop in `app/agent/agent.py`: send a message, run the tool calls, send the results, repeat (max 6 steps)
- [ ] Log each tool call

**Day 15: Connect the endpoint**
- [ ] Make `POST /agent/ask` return a real answer
- [ ] Test: "What's overdue in my building?" and "What does Class C mean?"

**Day 16: Spanish**
- [ ] Test the same questions with `lang=es`
- [ ] Fix any wording in `prompts/es.md`

**Day 17: Guardrails**
- [ ] The agent never states a date the tools didn't return
- [ ] It refuses legal advice and points to legal aid
- [ ] It uses HPD's class names exactly

**Day 18: Tests**
- [ ] Mock the LLM and test the tool-calling loop
- [ ] Test the max-steps limit and errors (missing key, LLM timeout)

**Day 19: Merge**
- [ ] Update `docs/architecture.md` with the agent flow
- [ ] PR → merge → delete the branch

✅ **Done when:** the agent answers correctly in English and Spanish using only tool data.

---

## Week 5: `feat/chat-ui`

**Day 20: Chat page**
- [ ] Add a `chat.html` template: message list, input box, send button
- [ ] Add a route `GET /building/{bin}/chat`

**Day 21: Make it work with HTMX**
- [ ] Send messages with HTMX and add the reply to the list without a page reload
- [ ] Show a "thinking…" state while waiting

**Day 22: Chat button**
- [ ] Add a floating chat button on the report page (bottom right)
- [ ] Add "Ask about this" on each violation card to open chat with that violation

**Day 23: Accessibility**
- [ ] New messages are announced to screen readers (`aria-live`)
- [ ] Keyboard-only test: open chat, type, send, close
- [ ] Check contrast and 44px tap targets

**Day 24: Merge**
- [ ] Add tests for the chat route
- [ ] Phone test on the live site
- [ ] PR → merge → delete the branch

✅ **Done when:** a tenant can ask a question from the report page on their phone.

---

## Week 6: `feat/alerts`

**Day 25: Database**
- [ ] Add a Postgres database in the host and set `DATABASE_URL`
- [ ] Set up Alembic and create the first migration from `app/db/models.py`

**Day 26: Subscribe and unsubscribe**
- [ ] Build `POST /alerts/subscribe` (email only for now)
- [ ] Build `GET /alerts/unsubscribe/{token}` so it **deletes** the contact
- [ ] Add a sign-up form on the report page

**Day 27: Daily job**
- [ ] `app/alerts/job.py`: load subscriptions, fetch current status, run `diff()`, save snapshots
- [ ] Run it locally against a test building

**Day 28: Send emails**
- [ ] Pick an email provider and set `SMTP_URL`
- [ ] Write simple English and Spanish email templates with an unsubscribe link

**Day 29: Schedule it**
- [ ] Add secrets to GitHub Actions and run `alerts-cron.yml` manually
- [ ] Confirm that you receive a real email

**Day 30: Merge**
- [ ] Add tests for subscribe, unsubscribe deletion, and the job
- [ ] Update `docs/privacy.md` if anything changed
- [ ] PR → merge → delete the branch

✅ **Done when:** you get an email when a test building's violation changes.

---

## Week 7: `feat/offline-pwa`

**Day 31: Installable app**
- [ ] Create app icons (192px and 512px) and add them to `manifest.json`
- [ ] Check that "Add to Home Screen" works on Android and iPhone

**Day 32: Offline**
- [ ] Recently viewed reports open with no connection
- [ ] Show a small "You're offline: showing saved data" note

**Day 33: Performance and merge**
- [ ] Run Lighthouse (mobile, slow 4G): target ≥ 90 performance and < 3 s for the report
- [ ] Fix the biggest issues
- [ ] PR → merge → delete the branch

✅ **Done when:** the app installs, opens offline, and scores ≥ 90.

---

## Weeks 7–8: `docs/research-and-audit` (part 2)

**Day 34: Interviews 1–2**
- [ ] Run 2 interviews using the live app
- [ ] Fill in the interview table the same day

**Day 35: Interviews 3–5**
- [ ] Run 3 more interviews
- [ ] Note quotes and pain points

**Day 36: Findings**
- [ ] Write the top 3–5 findings in `docs/user-research.md`
- [ ] List product changes and pick the 2 most important

**Day 37: Act on the research**
- [ ] Make the top 2 changes (on a small `fix/` branch if they're code)

**Day 38: Accessibility audit**
- [ ] Make the axe check in CI required (remove `continue-on-error`)
- [ ] Run manual checks: keyboard, VoiceOver, TalkBack, 200% zoom
- [ ] Fill in `docs/accessibility-audit.md`

**Day 39: Fix audit issues**
- [ ] Fix every critical or serious issue
- [ ] Re-run the checks and mark them fixed

**Day 40: Launch**
- [ ] Update the README with screenshots, the live link, and what you learned
- [ ] Merge the branch and delete it
- [ ] Share the link on LinkedIn and in your job application 🎉

✅ **Done when:** you've run 5 interviews, the audit is published, and the README is ready for recruiters.

---

## If you fall behind

Cut in this order and keep everything else:

1. Spanish emails in alerts (send English only)
2. The whole `feat/alerts` branch
3. Performance work beyond a score of 80

**Never cut** the rules engine, the AI agent, or the tenant interviews. They match the JD most closely.

## Success metrics

| Goal | Metric | Target |
| --- | --- | --- |
| Understandable data | Testers explain their violations correctly | 4 of 5 |
| Act on overdue repairs | Draft rate on reports with overdue items | ≥ 30% |
| Bilingual parity | Task completion gap, ES vs EN | ≤ 5 points |
| Low-end performance | Lighthouse mobile, slow 4G | ≥ 90; report < 3 s |
| Accessibility | axe critical or serious issues | 0 |
| Correct deadlines | Hand-checked sample of violations | 100% |

## Risks

| Risk | Mitigation |
| --- | --- |
| Open Data rate limits or outages | Cache responses, use an app token, show the last-updated time |
| The LLM states wrong deadlines | Deadlines come only from the rules engine tool |
| Hard to recruit tenants | Outreach starts on Day 8 |
| Losing motivation | Small daily tasks, and a live link early (Day 7) so progress is visible |
