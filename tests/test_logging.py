import json
import logging
from io import StringIO

import httpx
import pytest

from app.data import geoclient, hpd_client, nyc311_client


@pytest.fixture
def capture_json_logs():
    handlers = []

    def capture(logger_name):
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        from app.logging_config import JsonLogFormatter

        handler.setFormatter(JsonLogFormatter())
        logger = logging.getLogger(logger_name)
        logger.addHandler(handler)
        handlers.append((logger, handler))
        return stream

    yield capture

    for logger, handler in handlers:
        logger.removeHandler(handler)


def _upstream_error(status_code):
    request = httpx.Request("GET", "https://example.test/data")
    response = httpx.Response(status_code, request=request)
    return httpx.HTTPStatusError("upstream failure", request=request, response=response)


def test_request_logs_are_json_without_query_parameters(capture_json_logs):
    from fastapi.testclient import TestClient

    from app.main import app

    stream = capture_json_logs("app.request")
    response = TestClient(app).get("/?lang=es&address=private")

    [record] = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert response.status_code == 200
    assert record["event"] == "http_request"
    assert record["method"] == "GET"
    assert record["path"] == "/"
    assert record["status_code"] == 200
    assert isinstance(record["duration_ms"], (int, float))
    assert record["duration_ms"] >= 0
    assert "private" not in stream.getvalue()


def test_hpd_error_log_has_dataset_and_status(capture_json_logs, monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import app

    async def fail(_bin):
        raise _upstream_error(503)

    monkeypatch.setattr(hpd_client, "get_open_violations", fail)
    stream = capture_json_logs("app.api.routes_report")

    response = TestClient(app).get("/building/3000001", params={"address": "private address"})

    [record] = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert response.status_code == 502
    assert record["dataset"] == hpd_client.DATASET_NAME
    assert record["dataset_id"] == hpd_client.DATASET_ID
    assert record["status_code"] == 503
    assert record["error_type"] == "HTTPStatusError"
    assert "private address" not in stream.getvalue()


def test_311_error_log_has_dataset_and_status(
    hpd_rows, capture_json_logs, monkeypatch
):
    from fastapi.testclient import TestClient

    from app.data.cache import cache
    from app.main import app

    async def provide_violations(_bin, limit=500):
        return hpd_client.parse_violations(hpd_rows)

    async def fail(_bbl, days=365, limit=200):
        raise _upstream_error(429)

    cache.clear()
    monkeypatch.setattr(hpd_client, "get_open_violations", provide_violations)
    monkeypatch.setattr(nyc311_client, "get_recent_complaints", fail)
    stream = capture_json_logs("app.api.routes_report")

    response = TestClient(app).get("/building/3000001", params={"bbl": "3012340001"})

    [record] = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert response.status_code == 200
    assert record["dataset"] == nyc311_client.DATASET_NAME
    assert record["dataset_id"] == nyc311_client.DATASET_ID
    assert record["status_code"] == 429


def test_geoclient_error_log_has_name_and_status(capture_json_logs, monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import app

    async def fail(_address):
        raise _upstream_error(401)

    monkeypatch.setattr(geoclient, "search", fail)
    stream = capture_json_logs("app.api.routes_search")

    response = TestClient(app).get(
        "/search", params={"address": "private address"}, follow_redirects=False
    )

    [record] = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert response.status_code == 303
    assert record["dataset"] == "NYC Geoclient"
    assert record["status_code"] == 401
    assert record["error_type"] == "HTTPStatusError"
    assert "private address" not in stream.getvalue()


def test_agent_tool_log_has_tool_name_and_step(capture_json_logs):
    stream = capture_json_logs("app.agent.agent")
    logger = logging.getLogger("app.agent.agent")

    logger.info(
        "Agent tool call started",
        extra={
            "event": "agent_tool_started",
            "tool_name": "lookup_violations",
            "step": 2,
        },
    )

    [record] = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert record["event"] == "agent_tool_started"
    assert record["tool_name"] == "lookup_violations"
    assert record["step"] == 2
