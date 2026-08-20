from pydantic import BaseModel


class CreateInstanceRequest(BaseModel):
    instanceName: str
    webhook: str
    webhookByEvents: bool = False


class SendTextRequest(BaseModel):
    number: str
    text: str


class SendMediaRequest(BaseModel):
    number: str
    mediatype: str
    media: str
    caption: str | None = None
    fileName: str | None = None


class ConnectionStateResponse(BaseModel):
    instance: dict
    state: str
