import asyncio
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.data.geoclient import parse_search_response
from app.data.hpd_client import parse_violations
from app.data.nyc311_client import get_recent_complaints, parse_complaints
from app.main import app


def test_parse_violations(hpd_rows):
    violations = parse_violations(hpd_rows)
    assert len(violations) == 3
    first = violations[0]
    assert first.violation_class == "C"
    assert first.issued_date == date(2026, 1, 10)
    assert first.correct_by == date(2026, 1, 11)
    assert violations[1].correct_by is None
    assert violations[2].violation_class == "A"  # normalized to upper case
    assert violations[2].correct_by == date(2025, 9, 15)  # newcorrectbydate preferred


def test_parse_complaints(complaint_rows):
    complaints = parse_complaints(complaint_rows)
    assert complaints[0].complaint_type == "HEAT/HOT WATER"
    assert complaints[0].closed == date(2026, 1, 12)
    assert complaints[1].closed is None


def test_parse_geoclient(geoclient_payload):
    [loc] = parse_search_response(geoclient_payload)
    assert loc.bin == "3000001"
    assert loc.bbl == "3012340001"
    assert loc.borough == "BROOKLYN"


def test_311_rejects_bad_bbl():
    with pytest.raises(ValueError):
        asyncio.run(get_recent_complaints("1' OR '1'='1"))


def test_home_page_renders_in_both_languages():
    client = TestClient(app)
    en = client.get("/")
    es = client.get("/?lang=es")
    assert en.status_code == 200 and "Check my building" in en.text
    assert es.status_code == 200 and "Revisar mi edificio" in es.text


def test_healthz():
    assert TestClient(app).get("/healthz").json() == {"status": "ok"}


def test_report_rejects_invalid_bin():
    assert TestClient(app).get("/building/abc").status_code == 422
