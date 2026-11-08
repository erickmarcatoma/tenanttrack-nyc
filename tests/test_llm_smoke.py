import pytest

from app.config import Settings
from app.llm_smoke_test import API_URL, TEST_PROMPT, extract_output_text, run_smoke_test


def test_extract_output_text_skips_non_message_items():
    payload = {
        "output": [
            {"type": "reasoning", "summary": []},
            {
                "type": "message",
                "content": [
                    {"type": "output_text", "text": "TenantTrack"},
                    {"type": "refusal", "refusal": "not used"},
                    {"type": "output_text", "text": " works."},
                ],
            },
        ]
    }

    assert extract_output_text(payload) == "TenantTrack\n works."


def test_smoke_test_posts_to_responses_api(monkeypatch):
    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": "Connection works."}],
                    }
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
            assert url == API_URL
            assert headers == {"Authorization": "Bearer test-key"}
            assert json == {
                "model": "gpt-5.4-mini",
                "input": TEST_PROMPT,
                "max_output_tokens": 64,
            }
            return Response()

    monkeypatch.setattr("app.llm_smoke_test.httpx.Client", Client)
    settings = Settings(_env_file=None, llm_api_key="test-key", llm_model="gpt-5.4-mini")

    assert run_smoke_test(settings) == "Connection works."


@pytest.mark.parametrize(
    ("api_key", "model", "message"),
    [
        ("", "gpt-5.4-mini", "LLM_API_KEY"),
        ("test-key", "", "LLM_MODEL"),
    ],
)
def test_smoke_test_requires_configuration(api_key, model, message):
    settings = Settings(_env_file=None, llm_api_key=api_key, llm_model=model)

    with pytest.raises(RuntimeError, match=message):
        run_smoke_test(settings)
