import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SendTextRequest(BaseModel):
    instance_id: uuid.UUID
    to: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class SendImageRequest(BaseModel):
    instance_id: uuid.UUID
    to: str = Field(..., min_length=1)
    media_url: str = Field(..., min_length=1)
    caption: str | None = None


class SendAudioRequest(BaseModel):
    instance_id: uuid.UUID
    to: str = Field(..., min_length=1)
    media_url: str = Field(..., min_length=1)


class SendDocumentRequest(BaseModel):
    instance_id: uuid.UUID
    to: str = Field(..., min_length=1)
    media_url: str = Field(..., min_length=1)
    filename: str | None = None
    caption: str | None = None


class SendVideoRequest(BaseModel):
    instance_id: uuid.UUID
    to: str = Field(..., min_length=1)
    media_url: str = Field(..., min_length=1)
    caption: str | None = None


class MessageResponse(BaseModel):
    message_id: uuid.UUID
    instance_id: uuid.UUID
    direction: str
    message_type: str
    to: str
    status: str
    media_url: str | None = None
    caption: str | None = None
    filename: str | None = None
    provider_message_id: str | None = None
    created_at: datetime
