from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.client import Client
    from app.models.instance import Instance


class WebhookProcessingStatus(str, enum.Enum):
    received = "received"
    processing = "processing"
    processed = "processed"
    failed = "failed"
    ignored = "ignored"


class WebhookEvent(Base, TimestampMixin):
    __tablename__ = "webhook_events"
    __table_args__ = (
        Index("ix_webhook_event_instance_id", "instance_id"),
        Index("ix_webhook_event_event_type", "event_type"),
        Index("ix_webhook_event_created_at", "created_at"),
        Index("ix_webhook_event_client_id", "client_id"),
        Index("ix_webhook_event_provider_instance_name", "provider_instance_name"),
        Index("ix_webhook_event_forwarded_to_n8n", "forwarded_to_n8n"),
        Index("ix_webhook_event_received_at", "received_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clients.id"), nullable=True, default=None
    )
    instance_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("instances.id"), nullable=True, default=None
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="evolution")
    provider_instance_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    normalized_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    processing_status: Mapped[WebhookProcessingStatus] = mapped_column(
        Enum(WebhookProcessingStatus, native_enum=False, length=20),
        nullable=False,
        default=WebhookProcessingStatus.received,
    )
    forwarded_to_n8n: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    n8n_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    n8n_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    forwarded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    client: Mapped[Client | None] = relationship(
        "Client", back_populates="webhook_events", lazy="raise"
    )
    instance: Mapped[Instance | None] = relationship(
        "Instance", back_populates="webhook_events", lazy="raise"
    )

    def __repr__(self) -> str:
        return (
            f"<WebhookEvent id={self.id} event_type={self.event_type!r} "
            f"status={self.processing_status.value}>"
        )
