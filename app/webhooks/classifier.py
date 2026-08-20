from __future__ import annotations

from typing import Any


EVENT_TYPE_UNKNOWN = "unknown"
EVENT_TYPE_MESSAGE_RECEIVED = "message.received"
EVENT_TYPE_MESSAGE_SENT = "message.sent"
EVENT_TYPE_MESSAGE_DELIVERED = "message.delivered"
EVENT_TYPE_MESSAGE_READ = "message.read"
EVENT_TYPE_CONNECTION_UPDATE = "connection.update"
EVENT_TYPE_SEND_ERROR = "send.error"

FORWARDABLE_EVENTS = {
    EVENT_TYPE_MESSAGE_RECEIVED,
    EVENT_TYPE_CONNECTION_UPDATE,
    EVENT_TYPE_SEND_ERROR,
}

# Status values from Evolution API messages.update
_DELIVERY_STATUSES = {"DELIVERY_ACK", "SERVER_ACK", "2"}
_READ_STATUSES = {"READ", "3", "PLAYED"}
_ERROR_STATUSES = {"ERROR", "5"}


def classify(payload: dict[str, Any]) -> str:
    event = payload.get("event", "").upper().replace(".", "_")
    data = payload.get("data", {})

    if event == "MESSAGES_UPSERT":
        key = data.get("key", {})
        from_me = key.get("fromMe", False)
        return EVENT_TYPE_MESSAGE_RECEIVED if not from_me else EVENT_TYPE_MESSAGE_SENT

    if event == "MESSAGES_UPDATE":
        updates = data if isinstance(data, list) else [data]
        if updates:
            status = str(updates[0].get("update", {}).get("status", "")).upper()
            if status in _ERROR_STATUSES:
                return EVENT_TYPE_SEND_ERROR
            if status in _READ_STATUSES:
                return EVENT_TYPE_MESSAGE_READ
            if status in _DELIVERY_STATUSES:
                return EVENT_TYPE_MESSAGE_DELIVERED
        return EVENT_TYPE_MESSAGE_DELIVERED

    if event in ("CONNECTION_UPDATE",):
        return EVENT_TYPE_CONNECTION_UPDATE

    if event in ("SEND_ACK", "SEND_MESSAGE"):
        data_status = str(data.get("status", "")).upper()
        if data_status in _ERROR_STATUSES:
            return EVENT_TYPE_SEND_ERROR

    return EVENT_TYPE_UNKNOWN


def is_forwardable(event_type: str) -> bool:
    return event_type in FORWARDABLE_EVENTS
