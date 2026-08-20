import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_client, get_db, get_provider
from app.models.client import Client
from app.models.instance import InstanceStatus
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
from app.services.instance_service import InstanceService

router = APIRouter(prefix="/v1/instances", tags=["Instances"])


def _service(db: AsyncSession, provider: MessagingProvider) -> InstanceService:
    return InstanceService(db=db, provider=provider)


@router.post("", response_model=InstanceResponse, status_code=201)
async def create_instance(
    data: InstanceCreateRequest,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
    provider: MessagingProvider = Depends(get_provider),
) -> InstanceResponse:
    return await _service(db, provider).create_instance(client, data)


@router.get("", response_model=InstanceListResponse)
async def list_instances(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: InstanceStatus | None = Query(None),
    include_removed: bool = Query(False),
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
    provider: MessagingProvider = Depends(get_provider),
) -> InstanceListResponse:
    return await _service(db, provider).list_instances(
        client, limit=limit, offset=offset, status=status, include_removed=include_removed
    )


@router.patch("/{instance_id}", response_model=InstanceResponse)
async def update_instance(
    instance_id: uuid.UUID,
    data: InstanceUpdateRequest,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
    provider: MessagingProvider = Depends(get_provider),
) -> InstanceResponse:
    return await _service(db, provider).update_instance(instance_id, client, data)


@router.post("/{instance_id}/connect", response_model=InstanceConnectResponse)
async def connect_instance(
    instance_id: uuid.UUID,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
    provider: MessagingProvider = Depends(get_provider),
) -> InstanceConnectResponse:
    return await _service(db, provider).connect_instance(instance_id, client)


@router.get("/{instance_id}/status", response_model=InstanceStatusResponse)
async def get_instance_status(
    instance_id: uuid.UUID,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
    provider: MessagingProvider = Depends(get_provider),
) -> InstanceStatusResponse:
    return await _service(db, provider).get_instance_status(instance_id, client)


@router.post("/{instance_id}/disconnect", response_model=InstanceDisconnectResponse)
async def disconnect_instance(
    instance_id: uuid.UUID,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
    provider: MessagingProvider = Depends(get_provider),
) -> InstanceDisconnectResponse:
    return await _service(db, provider).disconnect_instance(instance_id, client)


@router.delete("/{instance_id}", response_model=InstanceDeleteResponse)
async def delete_instance(
    instance_id: uuid.UUID,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
    provider: MessagingProvider = Depends(get_provider),
) -> InstanceDeleteResponse:
    return await _service(db, provider).delete_instance(instance_id, client)
