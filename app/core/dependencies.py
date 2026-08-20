import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db_session
from app.core.security import hash_api_key
from app.models.client import Client
from app.providers.base import MessagingProvider
from app.providers.evolution.provider import EvolutionProvider


async def get_db() -> AsyncSession:
    settings = get_settings()
    async for session in get_db_session(settings.DATABASE_URL):
        yield session


def get_provider() -> MessagingProvider:
    settings = get_settings()
    return EvolutionProvider(
        base_url=settings.EVOLUTION_API_URL,
        api_key=settings.EVOLUTION_API_KEY,
        webhook_base_url=settings.WEBHOOK_BASE_URL,
        webhook_secret=settings.WEBHOOK_SECRET,
        timeout=settings.HTTP_TIMEOUT,
    )


async def get_current_client(
    x_api_key: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> Client:
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "API Key ausente.", "details": {}},
        )

    settings = get_settings()
    key_hash = hash_api_key(x_api_key, settings.API_KEY_SALT)
    result = await db.execute(
        select(Client).where(Client.api_key_hash == key_hash, Client.deleted_at.is_(None))
    )
    client = result.scalar_one_or_none()

    if client is None or not client.is_active:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "API Key inválida.", "details": {}},
        )

    return client


async def verify_webhook_secret(
    x_webhook_secret: Annotated[str | None, Header()] = None,
) -> None:
    settings = get_settings()
    if not x_webhook_secret or not secrets.compare_digest(
        x_webhook_secret, settings.WEBHOOK_SECRET
    ):
        raise HTTPException(
            status_code=401,
            detail={"code": "WEBHOOK_UNAUTHORIZED", "message": "Webhook não autorizado.", "details": {}},
        )


async def verify_admin_token(
    x_admin_token: Annotated[str | None, Header()] = None,
) -> None:
    settings = get_settings()
    if not x_admin_token or not secrets.compare_digest(x_admin_token, settings.ADMIN_TOKEN):
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "Token administrativo ausente ou inválido.", "details": {}},
        )
