from datetime import date

from app.agent.tools import check_deadlines, draft_letter
from app.alerts.job import diff
from app.data.hpd_client import parse_violations

TODAY = date(2026, 11, 2)


def test_check_deadlines(hpd_rows):
    results = {r["id"]: r for r in check_deadlines(parse_violations(hpd_rows), today=TODAY)}
    assert results["15001001"]["status"] == "overdue"
    assert results["15001002"]["status"] == "on_time"
    assert results["15001003"]["status"] == "closed"


def test_draft_letter_lists_only_overdue_items(hpd_rows):
    letter = draft_letter(
        "123 Sample Street, Brooklyn",
        parse_violations(hpd_rows),
        apartment="4B",
        today=TODAY,
    )
    assert "123 Sample Street, Brooklyn, apt. 4B" in letter
    assert "#15001001" in letter
    assert "#15001002" not in letter
    assert "[Your name]" in letter


def test_draft_letter_in_spanish(hpd_rows):
    letter = draft_letter("123 Sample Street", parse_violations(hpd_rows), lang="es", today=TODAY)
    assert "Atentamente" in letter
    assert "Inmediatamente peligrosa" in letter


def test_unknown_language_falls_back_to_english(hpd_rows):
    letter = draft_letter("123 Sample Street", parse_violations(hpd_rows), lang="fr", today=TODAY)
    assert "Sincerely" in letter


def test_alert_diff():
    previous = {"1": "on_time", "2": "on_time", "3": "overdue"}
    current = {"1": "overdue", "3": "overdue", "4": "on_time"}
    kinds = {(c.violation_id, c.kind) for c in diff(previous, current)}
    assert kinds == {("1", "became_overdue"), ("4", "opened"), ("2", "closed")}
