from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, verify_admin_token
from app.schemas.client import ClientCreateRequest, ClientCreateResponse
from app.services.client_service import ClientService

router = APIRouter(prefix="/v1/clients", tags=["Clients"])


@router.post(
    "",
    response_model=ClientCreateResponse,
    status_code=201,
    dependencies=[Depends(verify_admin_token)],
    summary="Criar novo cliente",
)
async def create_client(
    body: ClientCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> ClientCreateResponse:
    service = ClientService(db=db)
    client, raw_key = await service.create_client(body.name)
    return ClientCreateResponse(
        id=client.id,
        name=client.name,
        api_key=raw_key,
        is_active=client.is_active,
        created_at=client.created_at,
    )
