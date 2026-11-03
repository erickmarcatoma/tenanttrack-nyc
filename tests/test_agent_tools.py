from datetime import date

from app.agent.tools import check_deadlines, draft_letter
from app.alerts.job import diff
from app.data.hpd_client import parse_violations
from app.i18n.dates import format_date

TODAY = date(2026, 11, 2)


def test_check_deadlines(hpd_rows):
    results = {r["id"]: r for r in check_deadlines(parse_violations(hpd_rows), today=TODAY)}
    assert results["15001001"]["status"] == "overdue"
    assert results["15001002"]["status"] == "on_time"
    assert results["15001003"]["status"] == "closed"


def test_letter_has_date_address_ids_and_deadline(hpd_rows):
    letter = draft_letter(
        "123 Sample Street, Brooklyn",
        parse_violations(hpd_rows),
        apartment="4B",
        tenant_name="Ana Diaz",
        today=TODAY,
    )
    assert letter.startswith("Nov 2, 2026")
    assert "Re: Open HPD violations at 123 Sample Street, Brooklyn, apt. 4B" in letter
    assert "Violation #15001001 (Class C, Immediately hazardous), apt. 4B" in letter
    assert "Legal correction date was Jan 11, 2026 (295 days overdue)" in letter
    assert "#15001002" not in letter  # not overdue, so not listed by default
    assert letter.rstrip().endswith("Ana Diaz")


def test_letter_for_one_selected_violation(hpd_rows):
    letter = draft_letter(
        "123 Sample Street",
        parse_violations(hpd_rows),
        violation_ids={"15001002"},
        today=TODAY,
    )
    assert "#15001002" in letter
    assert "#15001001" not in letter
    assert "Must be corrected by Nov 19, 2026" in letter


def test_letter_placeholders_when_details_missing(hpd_rows):
    letter = draft_letter("", parse_violations(hpd_rows), today=TODAY)
    assert "[Building address]" in letter
    assert "[Your name]" in letter


def test_letter_in_spanish(hpd_rows):
    letter = draft_letter("123 Sample Street", parse_violations(hpd_rows), lang="es", today=TODAY)
    assert letter.startswith("2 de nov. de 2026")
    assert "Violación n.º 15001001 (Clase C, Inmediatamente peligrosa)" in letter
    assert "Atentamente" in letter


def test_unknown_language_falls_back_to_english(hpd_rows):
    letter = draft_letter("123 Sample Street", parse_violations(hpd_rows), lang="fr", today=TODAY)
    assert "Sincerely" in letter


def test_format_date():
    assert format_date(date(2026, 1, 11), "en") == "Jan 11, 2026"
    assert format_date(date(2026, 1, 11), "es") == "11 de ene. de 2026"
    assert format_date(None) == ""


def test_alert_diff():
    previous = {"1": "on_time", "2": "on_time", "3": "overdue"}
    current = {"1": "overdue", "3": "overdue", "4": "on_time"}
    kinds = {(c.violation_id, c.kind) for c in diff(previous, current)}
    assert kinds == {("1", "became_overdue"), ("4", "opened"), ("2", "closed")}
