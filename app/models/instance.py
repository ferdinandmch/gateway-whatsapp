import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class InstanceStatus(str, enum.Enum):
    created = "created"
    connecting = "connecting"
    connected = "connected"
    disconnected = "disconnected"
    error = "error"
    removed = "removed"


CONNECTABLE_STATUSES = {
    InstanceStatus.created,
    InstanceStatus.disconnected,
    InstanceStatus.error,
}


class Instance(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "instances"
    __table_args__ = (
        Index("ix_instance_client_id", "client_id"),
        Index("ix_instance_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clients.id"), nullable=False
    )
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="evolution")
    status: Mapped[InstanceStatus] = mapped_column(
        Enum(InstanceStatus, native_enum=False, length=20),
        nullable=False,
        default=InstanceStatus.created,
    )
    provider_instance_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True, default=None
    )
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None)
    n8n_webhook_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    webhook_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    client: Mapped["Client"] = relationship(  # noqa: F821
        "Client", back_populates="instances", lazy="raise"
    )
    messages: Mapped[list["Message"]] = relationship(  # noqa: F821
        "Message", back_populates="instance", lazy="raise"
    )
    webhook_events: Mapped[list["WebhookEvent"]] = relationship(  # noqa: F821
        "WebhookEvent", back_populates="instance", lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<Instance id={self.id} display_name={self.display_name!r} status={self.status.value}>"
