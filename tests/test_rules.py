from datetime import date

import pytest

from app.rules.deadlines import class_label, deadline_for
from app.rules.overdue import RepairStatus, evaluate

TODAY = date(2026, 11, 2)


@pytest.mark.parametrize(
    ("cls", "issued", "expected"),
    [
        ("A", date(2026, 1, 1), date(2026, 4, 1)),
        ("B", date(2026, 1, 1), date(2026, 1, 31)),
        ("C", date(2026, 1, 1), date(2026, 1, 2)),
        ("c", date(2026, 1, 1), date(2026, 1, 2)),
    ],
)
def test_deadline_by_class(cls, issued, expected):
    assert deadline_for(cls, issued) == expected


def test_dataset_correct_by_date_wins():
    assert deadline_for("A", date(2026, 1, 1), date(2026, 2, 1)) == date(2026, 2, 1)


def test_unknown_class_has_no_deadline():
    assert deadline_for("I", date(2026, 1, 1)) is None


def test_missing_issue_date_has_no_deadline():
    assert deadline_for("B", None) is None


def test_overdue():
    ev = evaluate("C", date(2026, 10, 1), today=TODAY)
    assert ev.status == RepairStatus.OVERDUE
    assert ev.days_overdue == 31


def test_due_soon():
    ev = evaluate("B", date(2026, 10, 7), today=TODAY)  # due Nov 6
    assert ev.status == RepairStatus.DUE_SOON


def test_on_time():
    ev = evaluate("A", date(2026, 10, 1), today=TODAY)
    assert ev.status == RepairStatus.ON_TIME
    assert ev.days_overdue == 0


def test_due_today_is_not_overdue():
    ev = evaluate("B", date(2026, 10, 3), today=TODAY)  # due Nov 2
    assert ev.status == RepairStatus.DUE_SOON


def test_closed_violation():
    ev = evaluate("C", date(2026, 1, 1), is_open=False, today=TODAY)
    assert ev.status == RepairStatus.CLOSED


def test_unknown_status_without_deadline():
    ev = evaluate("I", date(2026, 1, 1), today=TODAY)
    assert ev.status == RepairStatus.UNKNOWN


def test_class_labels_are_bilingual():
    assert class_label("C", "en") == "Immediately hazardous"
    assert class_label("C", "es") == "Inmediatamente peligrosa"
    assert class_label("Z", "en") == "Z"
