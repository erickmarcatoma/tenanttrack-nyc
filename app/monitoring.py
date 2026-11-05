"""Optional error monitoring with sensitive request data removed."""

from urllib.parse import urlsplit, urlunsplit

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.types import Event, Hint


def before_send(event: Event, hint: Hint) -> Event:
    request = event.get("request")
    if request is not None:
        url = request.get("url")
        if isinstance(url, str):
            parts = urlsplit(url)
            request["url"] = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
        for field in ("query_string", "data", "headers", "cookies", "env"):
            request.pop(field, None)

    event.pop("user", None)
    event.pop("extra", None)
    return event


def init_sentry(dsn: str) -> bool:
    if not dsn:
        return False

    sentry_sdk.init(
        dsn=dsn,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0,
        data_collection={"user_info": False},
        before_send=before_send,
        before_breadcrumb=lambda breadcrumb, hint: None,
        max_breadcrumbs=0,
    )
    return True
