"""HPD correction periods by violation class and condition."""

from datetime import date, timedelta

# Days allowed to correct, counted from the date the notice of violation was issued.
CORRECTION_DAYS: dict[str, int] = {
    "A": 90,  # non-hazardous
    "B": 30,  # hazardous
    "C": 1,  # Other immediately hazardous violations: 24 hours.
}

# HPD lists these Class C periods separately from the class-wide defaults.
# Source: https://www.nyc.gov/site/hpd/services-and-information/report-a-maintenance-issue.page
CLASS_C_CONDITION_DAYS: tuple[tuple[tuple[str, ...], int], ...] = (
    (("lead based paint", "lead paint"), 21),
    (("window guard", "mold", "mice", "mouse", "cockroach", "roach", "rat"), 21),
    (("self-closing door", "self closing door", "selfclosing door"), 14),
    (("heat", "hot water"), 0),
)

CLASS_LABELS: dict[str, dict[str, str]] = {
    "A": {"en": "Non-hazardous", "es": "No peligrosa"},
    "B": {"en": "Hazardous", "es": "Peligrosa"},
    "C": {"en": "Immediately hazardous", "es": "Inmediatamente peligrosa"},
    "I": {"en": "Information / order", "es": "Información / orden"},
}


def deadline_for(
    violation_class: str,
    issued_date: date | None,
    correct_by: date | None = None,
    description: str = "",
) -> date | None:
    """Return an estimated deadline, preferring HPD's record-specific date."""
    if correct_by is not None:
        return correct_by
    normalized_class = violation_class.upper()
    days = CORRECTION_DAYS.get(normalized_class)
    if normalized_class == "C":
        normalized_description = description.casefold().replace("-", " ")
        for phrases, condition_days in CLASS_C_CONDITION_DAYS:
            if any(phrase in normalized_description for phrase in phrases):
                days = condition_days
                break
    if days is None or issued_date is None:
        return None
    return issued_date + timedelta(days=days)


def class_label(violation_class: str, lang: str = "en") -> str:
    labels = CLASS_LABELS.get(violation_class.upper())
    if labels is None:
        return violation_class
    return labels.get(lang, labels["en"])
