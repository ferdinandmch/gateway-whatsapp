import logging
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.phone import normalize_phone, validate_phone_format
from app.models.error_log import ErrorLog
from app.models.instance import Instance, InstanceStatus
from app.models.message import Message, MessageContentType, MessageDirection
from app.providers.base import MessagingProvider
from app.schemas.message import MessageResponse
from app.schemas.provider import MessageType

logger = logging.getLogger(__name__)


class MessageService:
    def __init__(self, db: AsyncSession, provider: MessagingProvider) -> None:
        self._db = db
        self._provider = provider

    async def _get_instance_for_sending(
        self, instance_id: uuid.UUID, client_id: uuid.UUID
    ) -> Instance:
        result = await self._db.execute(
            select(Instance).where(
                Instance.id == instance_id,
                Instance.client_id == client_id,
                Instance.deleted_at.is_(None),
                Instance.status != InstanceStatus.removed,
            )
        )
        instance = result.scalar_one_or_none()
        if instance is None:
            raise HTTPException(
                status_code=404,
                detail={"code": "INSTANCE_NOT_FOUND", "message": "Instância não encontrada.", "details": {}},
            )
        if instance.status != InstanceStatus.connected:
            raise HTTPException(
                status_code=409,
                detail={"code": "INSTANCE_DISCONNECTED", "message": "A instância não está conectada.", "details": {}},
            )
        return instance

    async def _record_message(
        self,
        instance_id: uuid.UUID,
        content_type: MessageContentType,
        remote_jid: str,
        body: str | None = None,
        media_url: str | None = None,
        filename: str | None = None,
    ) -> Message:
        now = datetime.now(timezone.utc)
        message = Message(
            id=uuid.uuid4(),
            instance_id=instance_id,
            direction=MessageDirection.outbound,
            content_type=content_type,
            body=body,
            remote_jid=remote_jid,
            status="pending",
            media_url=media_url,
            filename=filename,
            created_at=now,
            updated_at=now,
        )
        self._db.add(message)
        await self._db.flush()
        return message

    async def _handle_send_result(
        self,
        message: Message,
        result,
        instance_id: uuid.UUID,
    ) -> None:
        if result.success:
            message.status = "sent"
            message.provider_message_id = (result.data or {}).get("provider_message_id")
            message.raw_payload = result.data
        else:
            message.status = "failed"
            error_details = result.error.model_dump() if result.error else {}
            error_log = ErrorLog(
                context="message.send_failed",
                error_message=result.error.message if result.error else "Unknown provider error",
                details={
                    "instance_id": str(instance_id),
                    "message_id": str(message.id),
                    "provider_error": error_details,
                },
            )
            self._db.add(error_log)
        await self._db.commit()
        await self._db.refresh(message)

    def _to_response(self, message: Message, to: str) -> MessageResponse:
        return MessageResponse(
            message_id=message.id,
            instance_id=message.instance_id,
            direction=message.direction.value,
            message_type=message.content_type.value,
            to=to,
            status=message.status,
            media_url=message.media_url,
            filename=message.filename,
            provider_message_id=message.provider_message_id,
            created_at=message.created_at,
        )

    async def send_text(
        self,
        client_id: uuid.UUID,
        instance_id: uuid.UUID,
        to: str,
        message_text: str,
    ) -> MessageResponse:
        try:
            validate_phone_format(to)
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail={"code": "VALIDATION_ERROR", "message": str(exc), "details": {}},
            ) from exc

        instance = await self._get_instance_for_sending(instance_id, client_id)
        remote_jid = normalize_phone(to)

        message = await self._record_message(
            instance_id=instance.id,
            content_type=MessageContentType.text,
            remote_jid=remote_jid,
            body=message_text,
        )

        result = await self._provider.send_text(
            instance_name=instance.provider_instance_id,
            to=remote_jid,
            content=message_text,
        )

        await self._handle_send_result(message, result, instance.id)

        if message.status == "failed":
            logger.error(
                "message.send_text.failed",
                extra={"instance_id": str(instance.id), "message_id": str(message.id)},
            )
            raise HTTPException(
                status_code=502,
                detail={"code": "PROVIDER_ERROR", "message": "Falha ao enviar mensagem.", "details": {}},
            )

        logger.info(
            "message.send_text.sent",
            extra={
                "instance_id": str(instance.id),
                "message_id": str(message.id),
                "client_id": str(client_id),
                "content_type": "text",
            },
        )
        return self._to_response(message, to)

    async def send_media(
        self,
        client_id: uuid.UUID,
        instance_id: uuid.UUID,
        to: str,
        media_type: MessageType,
        media_url: str,
        caption: str | None = None,
        filename: str | None = None,
    ) -> MessageResponse:
        try:
            validate_phone_format(to)
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail={"code": "VALIDATION_ERROR", "message": str(exc), "details": {}},
            ) from exc

        instance = await self._get_instance_for_sending(instance_id, client_id)
        remote_jid = normalize_phone(to)

        content_type = MessageContentType(media_type.value)
        message = await self._record_message(
            instance_id=instance.id,
            content_type=content_type,
            remote_jid=remote_jid,
            body=caption,
            media_url=media_url,
            filename=filename,
        )

        result = await self._provider.send_media(
            instance_name=instance.provider_instance_id,
            to=remote_jid,
            media_type=media_type,
            media_url=media_url,
            caption=caption,
            filename=filename,
        )

        await self._handle_send_result(message, result, instance.id)

        if message.status == "failed":
            logger.error(
                "message.send_media.failed",
                extra={
                    "instance_id": str(instance.id),
                    "message_id": str(message.id),
                    "media_type": media_type.value,
                },
            )
            raise HTTPException(
                status_code=502,
                detail={"code": "PROVIDER_ERROR", "message": "Falha ao enviar mídia.", "details": {}},
            )

        logger.info(
            "message.send_media.sent",
            extra={
                "instance_id": str(instance.id),
                "message_id": str(message.id),
                "client_id": str(client_id),
                "content_type": media_type.value,
            },
        )
        return self._to_response(message, to)
