"""NYC Geoclient: free-text address -> BBL / BIN."""

from dataclasses import dataclass

import httpx

from app.config import get_settings


@dataclass
class Location:
    address: str
    borough: str
    bbl: str
    bin: str


def parse_search_response(payload: dict) -> list[Location]:
    """Turn a Geoclient /search.json response into Location results."""
    results = []
    for item in payload.get("results", []):
        resp = item.get("response", {})
        bbl = resp.get("bbl")
        bin_ = resp.get("buildingIdentificationNumber")
        if not bbl or not bin_:
            continue
        house = resp.get("houseNumber", "")
        street = resp.get("firstStreetNameNormalized", "")
        results.append(
            Location(
                address=f"{house} {street}".strip(),
                borough=resp.get("firstBoroughName", ""),
                bbl=bbl,
                bin=bin_,
            )
        )
    return results


async def search(address: str) -> list[Location]:
    settings = get_settings()
    if not settings.geoclient_api_key:
        raise RuntimeError("GEOCLIENT_API_KEY is not set")
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{settings.geoclient_base_url}/search.json",
            params={"input": address},
            headers={"Ocp-Apim-Subscription-Key": settings.geoclient_api_key},
        )
        resp.raise_for_status()
        return parse_search_response(resp.json())
