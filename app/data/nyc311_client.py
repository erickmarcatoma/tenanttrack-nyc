"""311 Service Requests (NYC Open Data erm2-nwe9), filtered to HPD housing complaints."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta

import httpx

from app.config import get_settings
from app.data.cache import cache

DATASET_ID = "erm2-nwe9"
DATASET_NAME = "311 Service Requests"


@dataclass
class Complaint:
    unique_key: str
    complaint_type: str
    descriptor: str
    status: str
    created: date | None
    closed: date | None


def _to_date(value: str | None) -> date | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "")).date()


def parse_complaints(rows: list[dict]) -> list[Complaint]:
    return [
        Complaint(
            unique_key=row.get("unique_key", ""),
            complaint_type=row.get("complaint_type", ""),
            descriptor=row.get("descriptor", ""),
            status=row.get("status", ""),
            created=_to_date(row.get("created_date")),
            closed=_to_date(row.get("closed_date")),
        )
        for row in rows
    ]


async def get_recent_complaints(bbl: str, days: int = 365, limit: int = 200) -> list[Complaint]:
    if not bbl.isdigit() or len(bbl) != 10:
        raise ValueError("BBL must be 10 digits")
    key = f"311:{bbl}:{days}"
    if (cached := cache.get(key)) is not None:
        return cached

    settings = get_settings()
    since = (date.today() - timedelta(days=days)).isoformat()
    headers = {}
    if settings.nyc_open_data_app_token:
        headers["X-App-Token"] = settings.nyc_open_data_app_token
    params = {
        "$where": f"bbl='{bbl}' AND agency='HPD' AND created_date >= '{since}'",
        "$order": "created_date DESC",
        "$limit": limit,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{settings.nyc_open_data_base_url}/{DATASET_ID}.json",
            params=params,
            headers=headers,
        )
        resp.raise_for_status()
        complaints = parse_complaints(resp.json())

    cache.set(key, complaints)
    return complaints
