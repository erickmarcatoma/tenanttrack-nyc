# Privacy

TenantTrack NYC is built to collect as little as possible.

## What we store

- **Nothing** for address lookups. Addresses are sent to NYC Geoclient to find the building and are not saved.
- **Alert contact only** (email or phone), the building ID, and language, when a tenant subscribes to alerts.

## What we never store

- Names, apartment numbers, or letter contents. Letters are drafted in the browser session and the tenant copies them.
- Accounts, passwords, or tracking cookies.

## Deletion

Every alert includes a one-tap unsubscribe link. Unsubscribing **deletes** the contact, not just deactivates it.

## Third parties

- NYC Open Data and Geoclient (public city APIs)
- LLM provider: receives the question and violation data only, never contact info
- Email/SMS provider: receives the contact only to send alerts

## Security

- HTTPS only
- Secrets kept in environment variables, never in the repo
- Inputs validated (BIN, BBL, field lengths) before use in queries
