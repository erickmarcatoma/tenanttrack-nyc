"""Overdue logic: is the landlord past the legal repair deadline?"""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from app.rules.deadlines import deadline_for

DUE_SOON_DAYS = 7


class RepairStatus(StrEnum):
    OVERDUE = "overdue"
    DUE_SOON = "due_soon"
    ON_TIME = "on_time"
    CLOSED = "closed"
    UNKNOWN = "unknown"


@dataclass
class Evaluation:
    status: RepairStatus
    deadline: date | None
    days_overdue: int = 0


def evaluate(
    violation_class: str,
    issued_date: date | None,
    correct_by: date | None = None,
    is_open: bool = True,
    today: date | None = None,
) -> Evaluation:
    today = today or date.today()
    deadline = deadline_for(violation_class, issued_date, correct_by)

    if not is_open:
        return Evaluation(RepairStatus.CLOSED, deadline)
    if deadline is None:
        return Evaluation(RepairStatus.UNKNOWN, None)
    if today > deadline:
        return Evaluation(RepairStatus.OVERDUE, deadline, (today - deadline).days)
    if (deadline - today).days <= DUE_SOON_DAYS:
        return Evaluation(RepairStatus.DUE_SOON, deadline)
    return Evaluation(RepairStatus.ON_TIME, deadline)


def evaluate_violation(violation, today: date | None = None) -> Evaluation:
    """Evaluate an hpd_client.Violation."""
    return evaluate(
        violation.violation_class,
        violation.issued_date,
        violation.correct_by,
        is_open=violation.status.lower() == "open",
        today=today,
    )
