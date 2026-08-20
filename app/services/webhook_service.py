from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.error_log import ErrorLog
from app.models.instance import Instance, InstanceStatus
from app.models.message import Message, MessageContentType, MessageDirection
from app.models.webhook_event import WebhookEvent, WebhookProcessingStatus
from app.schemas.webhook import NormalizedEvent, WebhookResponse
from app.webhooks import classifier, normalizer
from app.webhooks.classifier import (
    EVENT_TYPE_CONNECTION_UPDATE,
    EVENT_TYPE_MESSAGE_DELIVERED,
    EVENT_TYPE_MESSAGE_READ,
    EVENT_TYPE_MESSAGE_RECEIVED,
    EVENT_TYPE_SEND_ERROR,
    EVENT_TYPE_UNKNOWN,
    is_forwardable,
)
from app.webhooks.forwarder import forward_to_n8n

logger = logging.getLogger(__name__)

_CONTENT_TYPE_MAP = {
    "text": MessageContentType.text,
    "image": MessageContentType.image,
    "audio": MessageContentType.audio,
    "document": MessageContentType.document,
    "video": MessageContentType.video,
}

_INSTANCE_STATUS_MAP = {
    "connected": InstanceStatus.connected,
    "connecting": InstanceStatus.connecting,
    "disconnected": InstanceStatus.disconnected,
    "error": InstanceStatus.error,
}


class WebhookService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def process(self, raw_payload: dict[str, Any]) -> WebhookResponse:
        now = datetime.now(timezone.utc)
        provider_instance_name = raw_payload.get("instance")

        event = WebhookEvent(
            id=uuid.uuid4(),
            provider="evolution",
            provider_instance_name=provider_instance_name,
            event_type=EVENT_TYPE_UNKNOWN,
            raw_payload=raw_payload,
            processing_status=WebhookProcessingStatus.received,
            forwarded_to_n8n=False,
            received_at=now,
        )
        self._db.add(event)
        await self._db.flush()

        instance = await self._lookup_instance(provider_instance_name)

        if instance is not None:
            event.instance_id = instance.id
            event.client_id = instance.client_id

        event_type = classifier.classify(raw_payload)
        event.event_type = event_type

        normalized = normalizer.normalize(
            payload=raw_payload,
            event_type=event_type,
            instance_id=instance.id if instance else None,
            client_id=instance.client_id if instance else None,
        )
        event.normalized_payload = normalized.model_dump(mode="json")

        try:
            await self._handle_event(event_type, normalized, raw_payload, instance, event)
            event.processing_status = (
                WebhookProcessingStatus.processed
                if event_type != EVENT_TYPE_UNKNOWN
                else WebhookProcessingStatus.ignored
            )
        except Exception as exc:
            logger.error("webhook.process.error", extra={"event_id": str(event.id), "error": str(exc)})
            event.processing_status = WebhookProcessingStatus.failed
            await self._record_error(
                context="webhook.processing",
                error_code="WEBHOOK_PROCESSING_ERROR",
                message=str(exc),
                instance_id=instance.id if instance else None,
                client_id=instance.client_id if instance else None,
            )

        if instance and instance.webhook_enabled and instance.n8n_webhook_url and is_forwardable(event_type):
            await self._forward(event, normalized, instance.n8n_webhook_url)

        event.processed_at = datetime.now(timezone.utc)
        await self._db.commit()

        http_status = 200 if event.processing_status == WebhookProcessingStatus.processed else 202

        return WebhookResponse(
            received=True,
            event_id=event.id,
            event_type=event.event_type,
            processing_status=event.processing_status.value,
            forwarded_to_n8n=event.forwarded_to_n8n,
        ), http_status

    async def _lookup_instance(self, provider_instance_name: str | None) -> Instance | None:
        if not provider_instance_name:
            return None
        result = await self._db.execute(
            select(Instance).where(
                Instance.provider_instance_id == provider_instance_name,
                Instance.deleted_at.is_(None),
            )
        )
        instance = result.scalar_one_or_none()
        if instance is None:
            logger.warning(
                "webhook.instance_not_found",
                extra={"provider_instance_name": provider_instance_name},
            )
            await self._record_error(
                context="webhook.instance_lookup",
                error_code="INSTANCE_NOT_FOUND_FOR_WEBHOOK",
                message=f"Instância não encontrada: {provider_instance_name}",
            )
        return instance

    async def _handle_event(
        self,
        event_type: str,
        normalized: NormalizedEvent,
        raw_payload: dict[str, Any],
        instance: Instance | None,
        event: WebhookEvent,
    ) -> None:
        if event_type == EVENT_TYPE_MESSAGE_RECEIVED and instance:
            await self._register_inbound_message(normalized, instance, raw_payload)

        elif event_type in (EVENT_TYPE_MESSAGE_DELIVERED, EVENT_TYPE_MESSAGE_READ) and normalized.provider_message_id:
            new_status = "delivered" if event_type == EVENT_TYPE_MESSAGE_DELIVERED else "read"
            await self._update_message_status(normalized.provider_message_id, new_status)

        elif event_type == EVENT_TYPE_SEND_ERROR and normalized.provider_message_id:
            await self._update_message_status(normalized.provider_message_id, "failed")

        elif event_type == EVENT_TYPE_CONNECTION_UPDATE and instance and normalized.connection_state:
            await self._update_instance_status(instance, normalized.connection_state)

    async def _register_inbound_message(
        self,
        normalized: NormalizedEvent,
        instance: Instance,
        raw_payload: dict[str, Any],
    ) -> None:
        content_type = _CONTENT_TYPE_MAP.get(normalized.message_type or "", MessageContentType.text)
        remote_jid = normalized.remote_jid or normalized.from_number or ""
        now = datetime.now(timezone.utc)
        message = Message(
            id=uuid.uuid4(),
            instance_id=instance.id,
            direction=MessageDirection.inbound,
            content_type=content_type,
            body=normalized.content,
            remote_jid=remote_jid,
            status="received",
            media_url=normalized.media_url,
            provider_message_id=normalized.provider_message_id,
            raw_payload=raw_payload,
            created_at=now,
            updated_at=now,
        )
        self._db.add(message)
        await self._db.flush()
        logger.info(
            "webhook.message_received",
            extra={
                "instance_id": str(instance.id),
                "message_id": str(message.id),
                "content_type": content_type.value,
            },
        )

    async def _update_message_status(self, provider_message_id: str, new_status: str) -> None:
        result = await self._db.execute(
            select(Message).where(Message.provider_message_id == provider_message_id)
        )
        message = result.scalar_one_or_none()
        if message:
            message.status = new_status
            message.updated_at = datetime.now(timezone.utc)
            await self._db.flush()
            logger.info(
                "webhook.message_status_updated",
                extra={"message_id": str(message.id), "new_status": new_status},
            )

    async def _update_instance_status(self, instance: Instance, connection_state: str) -> None:
        new_status = _INSTANCE_STATUS_MAP.get(connection_state)
        if new_status is None:
            return
        now = datetime.now(timezone.utc)
        instance.status = new_status
        instance.updated_at = now
        await self._db.flush()
        logger.info(
            "webhook.instance_status_updated",
            extra={"instance_id": str(instance.id), "new_status": new_status.value},
        )

    async def _forward(self, event: WebhookEvent, normalized: NormalizedEvent, n8n_url: str) -> None:
        result = await forward_to_n8n(n8n_url, normalized.to_n8n_payload())
        event.forwarded_to_n8n = result.success
        event.n8n_status_code = result.status_code
        event.n8n_response = result.response
        event.forwarded_at = datetime.now(timezone.utc)
        if not result.success:
            await self._record_error(
                context="webhook.n8n_forwarding",
                error_code="N8N_FORWARDING_ERROR",
                message=f"Falha ao encaminhar evento ao n8n: status={result.status_code}",
                instance_id=event.instance_id,
                client_id=event.client_id,
            )

    async def _record_error(
        self,
        context: str,
        error_code: str,
        message: str,
        instance_id: uuid.UUID | None = None,
        client_id: uuid.UUID | None = None,
    ) -> None:
        error_log = ErrorLog(
            context=context,
            error_message=message,
            details={"error_code": error_code, "instance_id": str(instance_id) if instance_id else None},
        )
        self._db.add(error_log)
