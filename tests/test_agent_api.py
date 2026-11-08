from datetime import date

import httpx
from fastapi.testclient import TestClient

from app.agent import agent as agent_module
from app.config import Settings
from app.data import hpd_client
from app.main import app


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


def candidate(*parts):
    return {"candidates": [{"content": {"role": "model", "parts": list(parts)}}]}


def configure_gemini(monkeypatch, responses):
    settings = Settings(
        _env_file=None,
        llm_api_key="test-key",
        llm_model="gemini-test",
    )
    monkeypatch.setattr(agent_module, "get_settings", lambda: settings)
    requests = []

    class AsyncClient:
        def __init__(self, *, timeout):
            assert timeout == 30

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, *, headers, json):
            requests.append({"url": url, "headers": headers, "json": json})
            result = responses.pop(0)
            if isinstance(result, Exception):
                raise result
            return FakeResponse(result)

    monkeypatch.setattr(agent_module.httpx, "AsyncClient", AsyncClient)
    return requests


def test_ask_endpoint_answers_overdue_question_using_building_data(
    monkeypatch, hpd_rows
):
    requests = configure_gemini(
        monkeypatch,
        [
            candidate(
                {
                    "functionCall": {
                        "name": "check_deadlines",
                        "args": {"bin": "3000001"},
                    }
                }
            ),
            candidate({"text": "One open violation is overdue."}),
        ],
    )
    requested_bins = []

    async def get_open_violations(bin_):
        requested_bins.append(bin_)
        return hpd_client.parse_violations(hpd_rows)

    monkeypatch.setattr(hpd_client, "get_open_violations", get_open_violations)

    response = TestClient(app).post(
        "/agent/ask",
        json={"message": "What's overdue in my building?", "bin": "3000001"},
    )

    assert response.status_code == 200
    assert response.json() == {"answer": "One open violation is overdue."}
    assert requested_bins == ["3000001"]
    tool_results = requests[1]["json"]["contents"][-1]["parts"]
    assert tool_results[0]["functionResponse"]["response"]["result"][0] == {
        "id": "15001001",
        "status": "overdue",
        "deadline": "2026-01-11",
        "days_overdue": (date.today() - date(2026, 1, 11)).days,
    }


def test_ask_endpoint_answers_class_c_question(monkeypatch):
    configure_gemini(
        monkeypatch,
        [candidate({"text": "Class C means Immediately hazardous."})],
    )

    response = TestClient(app).post(
        "/agent/ask",
        json={"message": "What does Class C mean?"},
    )

    assert response.status_code == 200
    assert response.json() == {"answer": "Class C means Immediately hazardous."}


def test_ask_endpoint_answers_overdue_question_in_spanish(monkeypatch, hpd_rows):
    requests = configure_gemini(
        monkeypatch,
        [
            candidate(
                {
                    "functionCall": {
                        "name": "check_deadlines",
                        "args": {"bin": "3000001"},
                    }
                }
            ),
            candidate({"text": "Hay una violación abierta vencida."}),
        ],
    )
    requested_bins = []

    async def get_open_violations(bin_):
        requested_bins.append(bin_)
        return hpd_client.parse_violations(hpd_rows)

    monkeypatch.setattr(hpd_client, "get_open_violations", get_open_violations)

    response = TestClient(app).post(
        "/agent/ask",
        json={
            "message": "¿Qué está vencido en mi edificio?",
            "bin": "3000001",
            "lang": "es",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"answer": "Hay una violación abierta vencida."}
    assert requested_bins == ["3000001"]
    assert requests[0]["json"]["systemInstruction"]["parts"][0]["text"] == (
        agent_module.system_prompt("es")
    )
    assert requests[0]["json"]["contents"][0]["parts"][0]["text"].startswith(
        "¿Qué está vencido en mi edificio?"
    )


def test_ask_endpoint_answers_class_c_question_in_spanish(monkeypatch):
    requests = configure_gemini(
        monkeypatch,
        [candidate({"text": "La Clase C significa Inmediatamente peligrosa."})],
    )

    response = TestClient(app).post(
        "/agent/ask",
        json={"message": "¿Qué significa la Clase C?", "lang": "es"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "La Clase C significa Inmediatamente peligrosa."
    }
    assert requests[0]["json"]["systemInstruction"]["parts"][0]["text"] == (
        agent_module.system_prompt("es")
    )


def test_ask_endpoint_validates_bin():
    response = TestClient(app).post(
        "/agent/ask",
        json={"message": "What's overdue?", "bin": "bad-bin"},
    )

    assert response.status_code == 422


def test_ask_endpoint_returns_gateway_timeout_when_gemini_times_out(monkeypatch):
    configure_gemini(monkeypatch, [httpx.ReadTimeout("Gemini request timed out")])

    response = TestClient(app).post(
        "/agent/ask",
        json={"message": "What does Class C mean?"},
    )

    assert response.status_code == 504
    assert response.json() == {"detail": "Gemini request timed out"}
