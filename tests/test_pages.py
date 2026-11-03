"""Page tests with the Open Data clients stubbed out."""

import pytest
from fastapi.testclient import TestClient

from app.data import hpd_client, nyc311_client
from app.data.cache import cache
from app.main import app


@pytest.fixture
def client(monkeypatch, hpd_rows, complaint_rows):
    cache.clear()

    async def fake_violations(bin_, limit=500):
        return hpd_client.parse_violations(hpd_rows)

    async def fake_complaints(bbl, days=365, limit=200):
        return nyc311_client.parse_complaints(complaint_rows)

    monkeypatch.setattr(hpd_client, "get_open_violations", fake_violations)
    monkeypatch.setattr(nyc311_client, "get_recent_complaints", fake_complaints)
    return TestClient(app)


def test_home_heading_is_a_question(client):
    assert "What&#39;s wrong in your building?" in client.get("/").text
    assert "Qué problemas hay en su edificio" in client.get("/?lang=es").text


def test_report_leads_with_overdue_summary_and_address(client):
    html = client.get(
        "/building/3000001", params={"bbl": "3012340001", "address": "123 Sample St, Brooklyn"}
    ).text
    assert "123 Sample St, Brooklyn" in html
    assert "1 repair is overdue" in html
    assert "What can I do?" in html
    # IDs are tucked away, not shown as the heading.
    assert "<summary>Building IDs</summary>" in html
    # Friendly dates.
    assert "Fix by Jan 11, 2026" in html


def test_report_cards_link_to_a_letter(client):
    html = client.get("/building/3000001").text
    assert "/building/3000001/letter?" in html
    assert "violation=15001001" in html


def test_report_in_spanish(client):
    html = client.get("/building/3000001", params={"lang": "es"}).text
    assert "1 reparación está vencida" in html
    assert "11 de ene. de 2026" in html


def test_letter_page(client):
    resp = client.get(
        "/building/3000001/letter",
        params={"address": "123 Sample St", "apartment": "4B", "name": "Ana Diaz"},
    )
    assert resp.status_code == 200
    assert "Violation #15001001" in resp.text
    assert "Ana Diaz" in resp.text
    assert 'data-copy="#letter"' in resp.text


def test_letter_rejects_bad_violation_id(client):
    resp = client.get("/building/3000001/letter", params={"violation": "abc"})
    assert resp.status_code == 422
