from app.monitoring import before_send, init_sentry


def test_sentry_is_disabled_without_dsn():
    assert init_sentry("") is False


def test_sentry_event_removes_sensitive_request_data():
    event = {
        "request": {
            "url": "https://tenanttrack.example/search?address=123%20Main%20St",
            "query_string": "address=123%20Main%20St",
            "data": {"name": "Tenant Name"},
            "headers": {"Cookie": "session=secret"},
            "cookies": {"session": "secret"},
            "env": {"REMOTE_ADDR": "192.0.2.1"},
            "method": "GET",
        },
        "user": {"email": "tenant@example.com"},
        "extra": {"address": "123 Main St"},
    }

    sanitized = before_send(event, {})

    assert sanitized["request"] == {
        "url": "https://tenanttrack.example/search",
        "method": "GET",
    }
    assert "user" not in sanitized
    assert "extra" not in sanitized
