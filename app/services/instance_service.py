import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.instance import CONNECTABLE_STATUSES, Instance, InstanceStatus
from app.providers.base import MessagingProvider
from app.schemas.instance import (
    InstanceConnectResponse,
    InstanceCreateRequest,
    InstanceDeleteResponse,
    InstanceDisconnectResponse,
    InstanceListResponse,
    InstanceResponse,
    InstanceStatusResponse,
    InstanceUpdateRequest,
)

logger = logging.getLogger(__name__)

MAX_INSTANCES_PER_CLIENT = 10


class InstanceService:
    def __init__(self, db: AsyncSession, provider: MessagingProvider) -> None:
        self._db = db
        self._provider = provider

    async def _get_instance_or_404(self, instance_id: uuid.UUID, client_id: uuid.UUID) -> Instance:
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
            from fastapi import HTTPException
            raise HTTPException(
                status_code=404,
                detail={"code": "INSTANCE_NOT_FOUND", "message": "Instância não encontrada.", "details": {}},
            )
        return instance

    async def _count_active_instances(self, client_id: uuid.UUID) -> int:
        result = await self._db.execute(
            select(func.count()).where(
                Instance.client_id == client_id,
                Instance.deleted_at.is_(None),
                Instance.status != InstanceStatus.removed,
            )
        )
        return result.scalar_one()

    def _generate_provider_instance_id(self) -> str:
        return f"inst_{uuid.uuid4().hex[:8]}"

    async def create_instance(self, client: Client, data: InstanceCreateRequest) -> InstanceResponse:
        from fastapi import HTTPException

        count = await self._count_active_instances(client.id)
        if count >= MAX_INSTANCES_PER_CLIENT:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "INSTANCE_LIMIT_REACHED",
                    "message": f"Limite de {MAX_INSTANCES_PER_CLIENT} instâncias atingido.",
                    "details": {},
                },
            )

        provider_id = self._generate_provider_instance_id()
        instance = Instance(
            client_id=client.id,
            display_name=data.display_name,
            provider="evolution",
            status=InstanceStatus.created,
            provider_instance_id=provider_id,
            n8n_webhook_url=data.n8n_webhook_url,
            webhook_enabled=data.webhook_enabled,
        )
        self._db.add(instance)
        await self._db.flush()

        provider_result = await self._provider.create_instance(provider_id)
        if not provider_result.success:
            instance.status = InstanceStatus.error
            logger.error(
                "provider.create_instance failed",
                extra={
                    "instance_id": str(instance.id),
                    "provider_instance_id": provider_id,
                    "error": provider_result.error.model_dump() if provider_result.error else None,
                },
            )
            await self._db.commit()
            raise HTTPException(
                status_code=502,
                detail={
                    "code": "PROVIDER_ERROR",
                    "message": "Falha ao criar instância no provider.",
                    "details": {},
                },
            )

        await self._db.commit()
        await self._db.refresh(instance)
        logger.info("instance.created", extra={"instance_id": str(instance.id), "client_id": str(client.id)})
        return InstanceResponse.from_orm_instance(instance)

    async def connect_instance(self, instance_id: uuid.UUID, client: Client) -> InstanceConnectResponse:
        from fastapi import HTTPException

        instance = await self._get_instance_or_404(instance_id, client.id)

        if instance.status not in CONNECTABLE_STATUSES:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "INSTANCE_NOT_CONNECTABLE",
                    "message": f"Instância não pode ser conectada no status '{instance.status.value}'.",
                    "details": {},
                },
            )

        provider_result = await self._provider.connect_instance(instance.provider_instance_id)
        if not provider_result.success:
            logger.error(
                "provider.connect_instance failed",
                extra={"instance_id": str(instance.id), "error": provider_result.error.model_dump() if provider_result.error else None},
            )
            raise HTTPException(
                status_code=502,
                detail={"code": "PROVIDER_ERROR", "message": "Falha ao conectar instância no provider.", "details": {}},
            )

        instance.status = InstanceStatus.connecting
        await self._db.commit()

        data = provider_result.data or {}
        logger.info("instance.connecting", extra={"instance_id": str(instance.id)})
        return InstanceConnectResponse(
            instance_id=instance.id,
            status=instance.status,
            qr_code=data.get("qrcode"),
            pairing_code=data.get("pairingCode"),
            provider_response={},
        )

    async def get_instance_status(self, instance_id: uuid.UUID, client: Client) -> InstanceStatusResponse:
        instance = await self._get_instance_or_404(instance_id, client.id)

        provider_status: str | None = None
        provider_result = await self._provider.get_instance_status(instance.provider_instance_id)
        if provider_result.success and provider_result.data:
            state = provider_result.data.get("state")
            provider_status = state.value if hasattr(state, "value") else str(state)

        return InstanceStatusResponse(
            instance_id=instance.id,
            status=instance.status,
            provider=instance.provider,
            provider_status=provider_status,
            phone_number=instance.phone_number,
            connected_at=instance.updated_at if instance.status == InstanceStatus.connected else None,
            disconnected_at=instance.updated_at if instance.status == InstanceStatus.disconnected else None,
        )

    async def disconnect_instance(self, instance_id: uuid.UUID, client: Client) -> InstanceDisconnectResponse:
        instance = await self._get_instance_or_404(instance_id, client.id)

        if instance.status == InstanceStatus.disconnected:
            return InstanceDisconnectResponse(
                instance_id=instance.id,
                status=instance.status,
                disconnected_at=instance.updated_at,
            )

        provider_result = await self._provider.disconnect_instance(instance.provider_instance_id)
        if not provider_result.success:
            from fastapi import HTTPException
            logger.error(
                "provider.disconnect_instance failed",
                extra={"instance_id": str(instance.id), "error": provider_result.error.model_dump() if provider_result.error else None},
            )
            raise HTTPException(
                status_code=502,
                detail={"code": "PROVIDER_ERROR", "message": "Falha ao desconectar instância no provider.", "details": {}},
            )

        instance.status = InstanceStatus.disconnected
        await self._db.commit()
        await self._db.refresh(instance)
        logger.info("instance.disconnected", extra={"instance_id": str(instance.id)})
        return InstanceDisconnectResponse(
            instance_id=instance.id,
            status=instance.status,
            disconnected_at=instance.updated_at,
        )

    async def delete_instance(self, instance_id: uuid.UUID, client: Client) -> InstanceDeleteResponse:
        from fastapi import HTTPException

        instance = await self._get_instance_or_404(instance_id, client.id)

        if instance.provider_instance_id:
            provider_result = await self._provider.delete_instance(instance.provider_instance_id)
            if not provider_result.success:
                logger.error(
                    "provider.delete_instance failed",
                    extra={"instance_id": str(instance.id), "error": provider_result.error.model_dump() if provider_result.error else None},
                )
                raise HTTPException(
                    status_code=502,
                    detail={"code": "PROVIDER_ERROR", "message": "Falha ao remover instância no provider.", "details": {}},
                )

        now = datetime.now(timezone.utc)
        instance.status = InstanceStatus.removed
        instance.deleted_at = now
        await self._db.commit()
        logger.info("instance.removed", extra={"instance_id": str(instance.id)})
        return InstanceDeleteResponse(instance_id=instance.id, status=instance.status)

    async def list_instances(
        self,
        client: Client,
        limit: int = 20,
        offset: int = 0,
        status: InstanceStatus | None = None,
        include_removed: bool = False,
    ) -> InstanceListResponse:
        base_query = select(Instance).where(Instance.client_id == client.id)
        count_query = select(func.count()).where(Instance.client_id == client.id)

        if not include_removed:
            base_query = base_query.where(
                Instance.deleted_at.is_(None),
                Instance.status != InstanceStatus.removed,
            )
            count_query = count_query.where(
                Instance.deleted_at.is_(None),
                Instance.status != InstanceStatus.removed,
            )

        if status is not None:
            base_query = base_query.where(Instance.status == status)
            count_query = count_query.where(Instance.status == status)

        count_result = await self._db.execute(count_query)
        total = count_result.scalar_one()

        instances_result = await self._db.execute(
            base_query.order_by(Instance.created_at.desc()).limit(limit).offset(offset)
        )
        instances = instances_result.scalars().all()

        return InstanceListResponse(
            items=[InstanceResponse.from_orm_instance(i) for i in instances],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def update_instance(
        self, instance_id: uuid.UUID, client: Client, data: InstanceUpdateRequest
    ) -> InstanceResponse:
        instance = await self._get_instance_or_404(instance_id, client.id)

        if data.display_name is not None:
            instance.display_name = data.display_name
        if data.n8n_webhook_url is not None or "n8n_webhook_url" in data.model_fields_set:
            instance.n8n_webhook_url = data.n8n_webhook_url
        if data.webhook_enabled is not None:
            instance.webhook_enabled = data.webhook_enabled

        await self._db.commit()
        await self._db.refresh(instance)
        logger.info("instance.updated", extra={"instance_id": str(instance.id)})
        return InstanceResponse.from_orm_instance(instance)

    async def update_status_from_webhook(
        self,
        provider_instance_id: str,
        new_status: InstanceStatus,
        phone_number: str | None = None,
    ) -> bool:
        result = await self._db.execute(
            select(Instance).where(
                Instance.provider_instance_id == provider_instance_id,
                Instance.deleted_at.is_(None),
            )
        )
        instance = result.scalar_one_or_none()
        if instance is None:
            return False

        instance.status = new_status
        if phone_number is not None:
            instance.phone_number = phone_number
        await self._db.commit()
        logger.info(
            "instance.status_updated_from_webhook",
            extra={"provider_instance_id": provider_instance_id, "new_status": new_status.value},
        )
        return True
