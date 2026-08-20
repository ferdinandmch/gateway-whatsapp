from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.instance import Instance


class MessageDirection(str, enum.Enum):
    inbound = "inbound"
    outbound = "outbound"


class MessageContentType(str, enum.Enum):
    text = "text"
    image = "image"
    audio = "audio"
    document = "document"
    video = "video"


class Message(Base, TimestampMixin):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_message_instance_id", "instance_id"),
        Index("ix_message_created_at", "created_at"),
        Index("ix_message_provider_message_id", "provider_message_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    instance_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("instances.id"), nullable=False
    )
    direction: Mapped[MessageDirection] = mapped_column(
        Enum(MessageDirection, native_enum=False, length=10), nullable=False
    )
    content_type: Mapped[MessageContentType] = mapped_column(
        Enum(MessageContentType, native_enum=False, length=20), nullable=False
    )
    body: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    remote_jid: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    provider_message_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )
    media_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    instance: Mapped[Instance] = relationship(
        "Instance", back_populates="messages", lazy="raise"
    )

    def __repr__(self) -> str:
        return (
            f"<Message id={self.id} direction={self.direction.value} "
            f"type={self.content_type.value} status={self.status!r}>"
        )
