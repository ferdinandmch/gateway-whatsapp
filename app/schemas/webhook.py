from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class WebhookResponse(BaseModel):
    received: bool
    event_id: uuid.UUID
    event_type: str
    processing_status: str
    forwarded_to_n8n: bool


class NormalizedEvent(BaseModel):
    event_type: str
    provider: str
    client_id: uuid.UUID | None = None
    instance_id: uuid.UUID | None = None
    provider_instance_name: str | None = None
    remote_jid: str | None = None
    from_number: str | None = None
    to_number: str | None = None
    message_type: str | None = None
    content: str | None = None
    media_url: str | None = None
    provider_message_id: str | None = None
    connection_state: str | None = None
    timestamp: datetime | None = None

    def to_n8n_payload(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "provider": self.provider,
            "client_id": str(self.client_id) if self.client_id else None,
            "instance_id": str(self.instance_id) if self.instance_id else None,
            "provider_instance_name": self.provider_instance_name,
            "from": self.from_number,
            "remote_jid": self.remote_jid,
            "message_type": self.message_type,
            "content": self.content,
            "media_url": self.media_url,
            "provider_message_id": self.provider_message_id,
            "connection_state": self.connection_state,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
