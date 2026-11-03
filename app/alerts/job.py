"""Daily alert job: compare today's violation status with the last snapshot and notify.

Run with: python -m app.alerts.job
"""

import logging
from dataclasses import dataclass

from app.config import get_settings

log = logging.getLogger(__name__)


@dataclass
class Change:
    violation_id: str
    kind: str  # "opened" | "closed" | "became_overdue"


def diff(previous: dict[str, str], current: dict[str, str]) -> list[Change]:
    """Compare {violation_id: status} maps and return what changed."""
    changes = []
    for vid, status in current.items():
        before = previous.get(vid)
        if before is None:
            changes.append(Change(vid, "opened"))
        elif before != "overdue" and status == "overdue":
            changes.append(Change(vid, "became_overdue"))
    for vid in previous:
        if vid not in current:
            changes.append(Change(vid, "closed"))
    return changes


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    if not settings.database_url:
        log.info("DATABASE_URL not set; alert job skipped.")
        return 0
    # TODO (Phase 5): load subscriptions and snapshots, fetch current status,
    # run diff(), send notifications, save new snapshots.
    log.info("Alert job not implemented yet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
