from enum import Enum
from typing import Any
from pydantic import BaseModel


class InstanceState(str, Enum):
    connected = "connected"
    disconnected = "disconnected"
    connecting = "connecting"
    not_found = "not_found"


class MessageType(str, Enum):
    text = "text"
    image = "image"
    audio = "audio"
    document = "document"
    video = "video"


class ProviderError(BaseModel):
    code: str
    message: str


class ProviderResult(BaseModel):
    success: bool
    data: dict[str, Any] | None = None
    error: ProviderError | None = None
