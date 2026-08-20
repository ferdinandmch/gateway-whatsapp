from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.schemas.webhook import NormalizedEvent
from app.webhooks.classifier import (
    EVENT_TYPE_CONNECTION_UPDATE,
    EVENT_TYPE_MESSAGE_DELIVERED,
    EVENT_TYPE_MESSAGE_READ,
    EVENT_TYPE_MESSAGE_RECEIVED,
    EVENT_TYPE_MESSAGE_SENT,
    EVENT_TYPE_SEND_ERROR,
    EVENT_TYPE_UNKNOWN,
)

_CONTENT_TYPE_KEYS = {
    "conversation": "text",
    "extendedTextMessage": "text",
    "imageMessage": "image",
    "audioMessage": "audio",
    "documentMessage": "document",
    "videoMessage": "video",
    "stickerMessage": "unknown",
}

_CONNECTION_STATE_MAP = {
    "open": "connected",
    "connecting": "connecting",
    "qrcode": "connecting",
    "close": "disconnected",
    "disconnected": "disconnected",
    "error": "error",
}


def _extract_message_type(message: dict[str, Any]) -> str:
    for key, msg_type in _CONTENT_TYPE_KEYS.items():
        if key in message:
            return msg_type
    return "unknown"


def _extract_content(message: dict[str, Any], message_type: str) -> str | None:
    if message_type == "text":
        return (
            message.get("conversation")
            or (message.get("extendedTextMessage") or {}).get("text")
        )
    if message_type == "image":
        return (message.get("imageMessage") or {}).get("caption")
    if message_type == "video":
        return (message.get("videoMessage") or {}).get("caption")
    if message_type == "document":
        return (message.get("documentMessage") or {}).get("caption")
    return None


def _extract_media_url(message: dict[str, Any], message_type: str) -> str | None:
    key_map = {
        "image": "imageMessage",
        "audio": "audioMessage",
        "document": "documentMessage",
        "video": "videoMessage",
    }
    msg_key = key_map.get(message_type)
    if msg_key:
        return (message.get(msg_key) or {}).get("url")
    return None


def _parse_timestamp(ts: Any) -> datetime | None:
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return None


def normalize(
    payload: dict[str, Any],
    event_type: str,
    instance_id: uuid.UUID | None = None,
    client_id: uuid.UUID | None = None,
) -> NormalizedEvent:
    provider_instance_name = payload.get("instance")
    data = payload.get("data", {})

    base = NormalizedEvent(
        event_type=event_type,
        provider="evolution",
        client_id=client_id,
        instance_id=instance_id,
        provider_instance_name=provider_instance_name,
    )

    if event_type in (EVENT_TYPE_MESSAGE_RECEIVED, EVENT_TYPE_MESSAGE_SENT):
        key = data.get("key", {})
        message = data.get("message", {})
        remote_jid: str = key.get("remoteJid", "")
        from_number = remote_jid.split("@")[0] if remote_jid else None
        message_type = _extract_message_type(message)
        ts = data.get("messageTimestamp") or data.get("messageTimestamp")

        base.remote_jid = remote_jid
        base.from_number = from_number if not key.get("fromMe") else None
        base.message_type = message_type
        base.content = _extract_content(message, message_type)
        base.media_url = _extract_media_url(message, message_type)
        base.provider_message_id = key.get("id")
        base.timestamp = _parse_timestamp(ts)

    elif event_type in (EVENT_TYPE_MESSAGE_DELIVERED, EVENT_TYPE_MESSAGE_READ):
        updates = data if isinstance(data, list) else [data]
        if updates:
            update = updates[0]
            base.provider_message_id = (update.get("key") or {}).get("id")
        base.timestamp = datetime.now(timezone.utc)

    elif event_type == EVENT_TYPE_SEND_ERROR:
        if isinstance(data, list) and data:
            key = data[0].get("key") or {}
        elif isinstance(data, dict):
            key = data.get("key") or {}
        else:
            key = {}
        base.provider_message_id = key.get("id")
        base.timestamp = datetime.now(timezone.utc)

    elif event_type == EVENT_TYPE_CONNECTION_UPDATE:
        raw_state = str(data.get("state", data.get("connection", ""))).lower()
        base.connection_state = _CONNECTION_STATE_MAP.get(raw_state, raw_state) or raw_state
        base.timestamp = datetime.now(timezone.utc)

    elif event_type == EVENT_TYPE_UNKNOWN:
        base.timestamp = datetime.now(timezone.utc)

    return base
