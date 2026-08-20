from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_client, get_db, get_provider
from app.models.client import Client
from app.providers.base import MessagingProvider
from app.schemas.message import (
    MessageResponse,
    SendAudioRequest,
    SendDocumentRequest,
    SendImageRequest,
    SendTextRequest,
    SendVideoRequest,
)
from app.schemas.provider import MessageType
from app.services.message_service import MessageService

router = APIRouter(prefix="/v1/messages", tags=["messages"])


def _get_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    provider: Annotated[MessagingProvider, Depends(get_provider)],
) -> MessageService:
    return MessageService(db=db, provider=provider)


@router.post("/text", response_model=MessageResponse)
async def send_text(
    body: SendTextRequest,
    client: Annotated[Client, Depends(get_current_client)],
    service: Annotated[MessageService, Depends(_get_service)],
) -> MessageResponse:
    return await service.send_text(
        client_id=client.id,
        instance_id=body.instance_id,
        to=body.to,
        message_text=body.message,
    )


@router.post("/image", response_model=MessageResponse)
async def send_image(
    body: SendImageRequest,
    client: Annotated[Client, Depends(get_current_client)],
    service: Annotated[MessageService, Depends(_get_service)],
) -> MessageResponse:
    return await service.send_media(
        client_id=client.id,
        instance_id=body.instance_id,
        to=body.to,
        media_type=MessageType.image,
        media_url=body.media_url,
        caption=body.caption,
    )


@router.post("/audio", response_model=MessageResponse)
async def send_audio(
    body: SendAudioRequest,
    client: Annotated[Client, Depends(get_current_client)],
    service: Annotated[MessageService, Depends(_get_service)],
) -> MessageResponse:
    return await service.send_media(
        client_id=client.id,
        instance_id=body.instance_id,
        to=body.to,
        media_type=MessageType.audio,
        media_url=body.media_url,
    )


@router.post("/document", response_model=MessageResponse)
async def send_document(
    body: SendDocumentRequest,
    client: Annotated[Client, Depends(get_current_client)],
    service: Annotated[MessageService, Depends(_get_service)],
) -> MessageResponse:
    return await service.send_media(
        client_id=client.id,
        instance_id=body.instance_id,
        to=body.to,
        media_type=MessageType.document,
        media_url=body.media_url,
        caption=body.caption,
        filename=body.filename,
    )


@router.post("/video", response_model=MessageResponse)
async def send_video(
    body: SendVideoRequest,
    client: Annotated[Client, Depends(get_current_client)],
    service: Annotated[MessageService, Depends(_get_service)],
) -> MessageResponse:
    return await service.send_media(
        client_id=client.id,
        instance_id=body.instance_id,
        to=body.to,
        media_type=MessageType.video,
        media_url=body.media_url,
        caption=body.caption,
    )
