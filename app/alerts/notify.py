"""Send alert notifications by email or SMS."""

import logging

from app.config import get_settings

log = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> bool:
    if not get_settings().smtp_url:
        log.info("SMTP not configured; skipping email.")
        return False
    # TODO (Phase 5): send via SMTP provider.
    raise NotImplementedError


def send_sms(to: str, body: str) -> bool:
    if not get_settings().sms_api_key:
        log.info("SMS not configured; skipping SMS.")
        return False
    # TODO (Phase 5): send via SMS provider.
    raise NotImplementedError
