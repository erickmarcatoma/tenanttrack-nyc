"""HPD Housing Maintenance Code Violations (NYC Open Data wvxf-dwi5)."""

from dataclasses import dataclass
from datetime import date, datetime

import httpx

from app.config import get_settings
from app.data.cache import cache

DATASET_ID = "wvxf-dwi5"


@dataclass
class Violation:
    violation_id: str
    bin: str
    apartment: str
    violation_class: str
    description: str
    status: str  # "Open" or "Close"
    issued_date: date | None
    correct_by: date | None


def _to_date(value: str | None) -> date | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "")).date()


def parse_violations(rows: list[dict]) -> list[Violation]:
    return [
        Violation(
            violation_id=row.get("violationid", ""),
            bin=row.get("bin", ""),
            apartment=row.get("apartment", ""),
            violation_class=row.get("class", "").upper(),
            description=row.get("novdescription", ""),
            status=row.get("violationstatus", ""),
            issued_date=_to_date(row.get("novissueddate")),
            correct_by=_to_date(row.get("newcorrectbydate") or row.get("originalcorrectbydate")),
        )
        for row in rows
    ]


async def get_open_violations(bin_: str, limit: int = 500) -> list[Violation]:
    key = f"hpd:{bin_}"
    if (cached := cache.get(key)) is not None:
        return cached

    settings = get_settings()
    headers = {}
    if settings.nyc_open_data_app_token:
        headers["X-App-Token"] = settings.nyc_open_data_app_token
    params = {
        "bin": bin_,
        "violationstatus": "Open",
        "$order": "novissueddate DESC",
        "$limit": limit,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{settings.nyc_open_data_base_url}/{DATASET_ID}.json",
            params=params,
            headers=headers,
        )
        resp.raise_for_status()
        violations = parse_violations(resp.json())

    cache.set(key, violations)
    return violations
