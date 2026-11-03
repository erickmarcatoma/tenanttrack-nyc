import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture
def hpd_rows():
    return load_fixture("hpd_violations.json")


@pytest.fixture
def complaint_rows():
    return load_fixture("nyc311_complaints.json")


@pytest.fixture
def geoclient_payload():
    return load_fixture("geoclient_search.json")
