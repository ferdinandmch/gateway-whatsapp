from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, verify_webhook_secret
from app.services.webhook_service import WebhookService

router = APIRouter(prefix="/v1/webhooks", tags=["webhooks"])


@router.post(
    "/evolution",
    dependencies=[Depends(verify_webhook_secret)],
    summary="Receber webhook da Evolution API",
)
async def receive_evolution_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Response:
    raw_payload: dict[str, Any] = await request.json()
    service = WebhookService(db)
    response_body, http_status = await service.process(raw_payload)
    from fastapi.responses import JSONResponse
    return JSONResponse(content=response_body.model_dump(mode="json"), status_code=http_status)


@router.post(
    "/evolution/{instance_name}",
    dependencies=[Depends(verify_webhook_secret)],
    summary="Receber webhook da Evolution API (por instância)",
)
async def receive_evolution_webhook_instance(
    instance_name: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Response:
    raw_payload: dict[str, Any] = await request.json()
    service = WebhookService(db)
    response_body, http_status = await service.process(raw_payload)
    from fastapi.responses import JSONResponse
    return JSONResponse(content=response_body.model_dump(mode="json"), status_code=http_status)
