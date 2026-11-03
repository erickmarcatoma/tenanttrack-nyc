# TenantTrack NYC — Product Requirements (summary)

The full PRD is kept as a shared doc. This is the short version.

## Problem

NYC renters living with unrepaired housing violations can't easily see what is open in their building, whether the landlord is past the legal repair deadline, or what to do next. The data is public but split across 311 and HPD datasets, written in code-level language, and English-only in practice.

## Solution

A bilingual, mobile-first web app. Enter an address, see open HPD violations and 311 complaints, get overdue flags based on legal deadlines, and have an AI assistant explain violations and draft a complaint or landlord letter in English or Spanish.

## Users

- **Primary:** NYC renters in older, rent-stabilized buildings; often on low-end phones and slow connections; many prefer Spanish.
- **Secondary:** Tenant organizers and legal-aid advocates.

## MVP value props

- **Vitamin:** Every open violation and 311 complaint for any address, in plain language.
- **Painkiller:** Automatic overdue flags from the legal deadline for each violation class.
- **Steroid:** A one-tap, ready-to-send letter in English or Spanish.

## Goals

- Tenants understand their building's violations without reading HPD codes.
- Tenants know which repairs are overdue and act on them.
- Spanish speakers get the same experience as English speakers.
- Works on low-end phones and slow connections.
- Production quality: tested, monitored, accessible, documented.

## Non-goals (MVP)

- User accounts and logins
- Filing directly into 311/HPD systems
- Languages beyond English and Spanish
- Legal advice or court filings

## Success metrics

See [PLAN.md](../PLAN.md#success-metrics).

## Requirements (P0)

- Search by address without logging in
- Switch between English and Spanish
- See open violations with class, plain-language description, and deadline
- See which violations are overdue
- See recent 311 housing complaints
- Ask the assistant to explain a violation
- Generate, edit, and copy a complaint or landlord letter
