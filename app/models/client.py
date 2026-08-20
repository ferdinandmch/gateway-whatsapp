import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class Client(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key_hash: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    instances: Mapped[list["Instance"]] = relationship(  # noqa: F821
        "Instance", back_populates="client", lazy="raise"
    )
    webhook_events: Mapped[list["WebhookEvent"]] = relationship(  # noqa: F821
        "WebhookEvent", back_populates="client", lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<Client id={self.id} name={self.name!r} is_active={self.is_active}>"
