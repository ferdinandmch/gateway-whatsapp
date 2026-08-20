import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ClientCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class ClientCreateResponse(BaseModel):
    id: uuid.UUID
    name: str
    api_key: str
    is_active: bool
    created_at: datetime
