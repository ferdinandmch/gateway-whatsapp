import uuid
from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_validator

from app.models.instance import InstanceStatus


class InstanceCreateRequest(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=255)
    n8n_webhook_url: str | None = None
    webhook_enabled: bool = True

    @field_validator("display_name")
    @classmethod
    def strip_display_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("display_name must not be empty")
        return v

    @field_validator("n8n_webhook_url")
    @classmethod
    def validate_webhook_url(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("n8n_webhook_url must start with http:// or https://")
        return v


class InstanceUpdateRequest(BaseModel):
    display_name: str | None = Field(None, min_length=1, max_length=255)
    n8n_webhook_url: str | None = None
    webhook_enabled: bool | None = None

    @field_validator("display_name")
    @classmethod
    def strip_display_name(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("display_name must not be empty")
        return v

    @field_validator("n8n_webhook_url")
    @classmethod
    def validate_webhook_url(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("n8n_webhook_url must start with http:// or https://")
        return v


class InstanceResponse(BaseModel):
    id: uuid.UUID
    display_name: str
    provider: str
    provider_instance_name: str | None
    status: InstanceStatus
    phone_number: str | None
    webhook_enabled: bool
    n8n_webhook_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_instance(cls, instance) -> "InstanceResponse":
        return cls(
            id=instance.id,
            display_name=instance.display_name,
            provider=instance.provider,
            provider_instance_name=instance.provider_instance_id,
            status=instance.status,
            phone_number=instance.phone_number,
            webhook_enabled=instance.webhook_enabled,
            n8n_webhook_url=instance.n8n_webhook_url,
            created_at=instance.created_at,
            updated_at=instance.updated_at,
        )


class InstanceListResponse(BaseModel):
    items: list[InstanceResponse]
    total: int
    limit: int
    offset: int


class InstanceConnectResponse(BaseModel):
    instance_id: uuid.UUID
    status: InstanceStatus
    qr_code: str | None
    pairing_code: str | None
    provider_response: dict = {}


class InstanceStatusResponse(BaseModel):
    instance_id: uuid.UUID
    status: InstanceStatus
    provider: str
    provider_status: str | None
    phone_number: str | None
    connected_at: datetime | None
    disconnected_at: datetime | None


class InstanceDisconnectResponse(BaseModel):
    instance_id: uuid.UUID
    status: InstanceStatus
    disconnected_at: datetime | None


class InstanceDeleteResponse(BaseModel):
    instance_id: uuid.UUID
    status: InstanceStatus
