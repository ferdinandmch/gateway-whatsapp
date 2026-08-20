from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ForwardResult:
    def __init__(self, success: bool, status_code: int | None, response: dict[str, Any] | None) -> None:
        self.success = success
        self.status_code = status_code
        self.response = response


def _is_valid_http_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


async def forward_to_n8n(url: str, payload: dict[str, Any]) -> ForwardResult:
    if not _is_valid_http_url(url):
        logger.warning("webhook.forward_to_n8n.invalid_url", extra={"url": url})
        return ForwardResult(success=False, status_code=None, response={"error": "invalid_url"})

    settings = get_settings()
    try:
        async with httpx.AsyncClient(
            timeout=settings.N8N_FORWARD_TIMEOUT,
            follow_redirects=True,
        ) as client:
            resp = await client.post(url, json=payload)
        try:
            response_body = resp.json()
        except Exception:
            response_body = {"raw": resp.text[:500]}
        success = resp.is_success
        logger.info(
            "webhook.forward_to_n8n",
            extra={"url": url, "status_code": resp.status_code, "success": success},
        )
        return ForwardResult(success=success, status_code=resp.status_code, response=response_body)
    except httpx.TimeoutException:
        logger.warning("webhook.forward_to_n8n.timeout", extra={"url": url})
        return ForwardResult(success=False, status_code=None, response={"error": "timeout"})
    except Exception as exc:
        logger.error("webhook.forward_to_n8n.error", extra={"url": url, "error": str(exc)})
        return ForwardResult(success=False, status_code=None, response={"error": str(exc)})
