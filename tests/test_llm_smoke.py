import pytest

from app.config import Settings
from app.llm_smoke_test import (
    API_URL,
    DEFAULT_MODEL,
    TEST_PROMPT,
    extract_output_text,
    run_smoke_test,
)


def test_extract_output_text_reads_candidate_parts():
    payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": "TenantTrack"},
                        {"functionCall": {"name": "lookup_violations"}},
                        {"text": " works."},
                    ]
                }
            }
        ]
    }

    assert extract_output_text(payload) == "TenantTrack\n works."


def test_extract_output_text_handles_missing_candidates():
    assert extract_output_text({}) == ""
    assert extract_output_text({"candidates": [{"content": {"parts": []}}]}) == ""


def test_smoke_test_posts_to_gemini_api(monkeypatch):
    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "candidates": [
                    {"content": {"parts": [{"text": "Connection works."}]}}
                ]
            }

    class Client:
        def __init__(self, *, timeout):
            assert timeout == 30

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def post(self, url, *, headers, json):
            assert url == f"{API_URL}/{DEFAULT_MODEL}:generateContent"
            assert headers == {"x-goog-api-key": "test-key"}
            assert json == {
                "contents": [{"parts": [{"text": TEST_PROMPT}]}],
                "generationConfig": {"maxOutputTokens": 64},
            }
            return Response()

    monkeypatch.setattr("app.llm_smoke_test.httpx.Client", Client)
    settings = Settings(_env_file=None, llm_api_key="test-key", llm_model=DEFAULT_MODEL)

    assert run_smoke_test(settings) == "Connection works."


@pytest.mark.parametrize(
    ("api_key", "model", "message"),
    [
        ("", DEFAULT_MODEL, "LLM_API_KEY"),
        ("test-key", "", "LLM_MODEL"),
    ],
)
def test_smoke_test_requires_configuration(api_key, model, message):
    settings = Settings(_env_file=None, llm_api_key=api_key, llm_model=model)

    with pytest.raises(RuntimeError, match=message):
        run_smoke_test(settings)
