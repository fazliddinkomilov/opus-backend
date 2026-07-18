"""SMS delivery for OTP codes.

Provider abstraction with an Eskiz.uz implementation (the most common SMS
gateway in Uzbekistan) plus a console fallback used in dev / dry-run mode.

The concrete provider is chosen from settings at call time so the same code
path works locally (console) and in production (Eskiz) without branching in
callers.
"""

from __future__ import annotations

import logging
from typing import Protocol

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger("mastergo.sms")

# Eskiz login tokens are valid for ~30 days; refresh well before that.
_ESKIZ_TOKEN_CACHE_KEY = "sms:eskiz:token"
_ESKIZ_TOKEN_TTL_SECONDS = 20 * 24 * 60 * 60  # 20 days
_HTTP_TIMEOUT_SECONDS = 12


class SmsError(Exception):
    """Raised when an SMS could not be delivered."""


class SmsProvider(Protocol):
    def send(self, phone: str, text: str) -> None: ...


def normalize_phone(phone: str) -> str:
    """Return an Eskiz-friendly MSISDN: digits only, Uzbekistan country code.

    Accepts ``+998 90 123 45 67``, ``998901234567``, ``901234567`` etc.
    """
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) == 9:  # local number without country code
        digits = f"998{digits}"
    elif digits.startswith("00998"):
        digits = digits[2:]
    return digits


class ConsoleSmsProvider:
    """Logs the message instead of sending it. Used for dev / dry-run."""

    def send(self, phone: str, text: str) -> None:
        logger.info("[SMS dry-run] to=%s text=%s", normalize_phone(phone), text)


class EskizSmsProvider:
    """Eskiz.uz REST client with cached auth token.

    Docs: https://documenter.getpostman.com/view/663428/RzfmES4z
    """

    def __init__(self, *, email: str, password: str, base_url: str, sender: str):
        if not email or not password:
            raise SmsError("eskiz_not_configured")
        self._email = email
        self._password = password
        self._base_url = base_url.rstrip("/")
        self._sender = sender

    def _login(self) -> str:
        resp = requests.post(
            f"{self._base_url}/auth/login",
            data={"email": self._email, "password": self._password},
            timeout=_HTTP_TIMEOUT_SECONDS,
        )
        if resp.status_code != 200:
            raise SmsError(f"eskiz_login_failed:{resp.status_code}")
        token = (resp.json().get("data") or {}).get("token")
        if not token:
            raise SmsError("eskiz_login_no_token")
        cache.set(_ESKIZ_TOKEN_CACHE_KEY, token, timeout=_ESKIZ_TOKEN_TTL_SECONDS)
        return token

    def _token(self, *, force_refresh: bool = False) -> str:
        if not force_refresh:
            cached = cache.get(_ESKIZ_TOKEN_CACHE_KEY)
            if cached:
                return cached
        return self._login()

    def send(self, phone: str, text: str) -> None:
        payload = {
            "mobile_phone": normalize_phone(phone),
            "message": text,
            "from": self._sender,
        }
        # One retry with a fresh token if the cached one was rejected.
        for attempt in range(2):
            token = self._token(force_refresh=attempt == 1)
            resp = requests.post(
                f"{self._base_url}/message/sms/send",
                data=payload,
                headers={"Authorization": f"Bearer {token}"},
                timeout=_HTTP_TIMEOUT_SECONDS,
            )
            if resp.status_code == 401 and attempt == 0:
                continue
            if resp.status_code not in (200, 201):
                raise SmsError(f"eskiz_send_failed:{resp.status_code}:{resp.text[:200]}")
            return
        raise SmsError("eskiz_send_failed:unauthorized")


def get_sms_provider() -> SmsProvider:
    if getattr(settings, "SMS_DRY_RUN", False):
        return ConsoleSmsProvider()
    provider = getattr(settings, "SMS_PROVIDER", "eskiz")
    if provider == "eskiz":
        return EskizSmsProvider(
            email=getattr(settings, "ESKIZ_EMAIL", ""),
            password=getattr(settings, "ESKIZ_PASSWORD", ""),
            base_url=getattr(settings, "ESKIZ_BASE_URL", "https://notify.eskiz.uz/api"),
            sender=getattr(settings, "ESKIZ_SENDER", "4546"),
        )
    raise SmsError(f"unknown_sms_provider:{provider}")


def send_otp_sms(phone: str, code: str) -> None:
    """Render the OTP template and hand it to the active provider."""
    template = getattr(
        settings,
        "OTP_SMS_TEMPLATE",
        "MasterGo: tasdiqlash kodi {code}. Hech kimga bermang.",
    )
    get_sms_provider().send(phone, template.format(code=code))
