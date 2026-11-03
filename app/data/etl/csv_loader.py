"""Load violations from a CSV export and normalize column names."""

import csv
from pathlib import Path

from app.data.hpd_client import Violation, parse_violations

# Map messy header variants to the Open Data field names.
COLUMN_ALIASES = {
    "violation id": "violationid",
    "violation_id": "violationid",
    "bin": "bin",
    "apt": "apartment",
    "apartment": "apartment",
    "class": "class",
    "description": "novdescription",
    "status": "violationstatus",
    "issued": "novissueddate",
    "correct by": "originalcorrectbydate",
}


def load_csv(path: Path) -> list[Violation]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = []
        for raw in reader:
            row = {}
            for key, value in raw.items():
                field = COLUMN_ALIASES.get((key or "").strip().lower())
                if field:
                    row[field] = (value or "").strip()
            rows.append(row)
    return parse_violations(rows)
