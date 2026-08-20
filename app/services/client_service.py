from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import generate_api_key, hash_api_key
from app.models.client import Client


class ClientService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_client(self, name: str) -> tuple[Client, str]:
        settings = get_settings()
        raw_key = generate_api_key()
        key_hash = hash_api_key(raw_key, settings.API_KEY_SALT)

        client = Client(name=name, api_key_hash=key_hash, is_active=True)
        self._db.add(client)
        await self._db.commit()
        await self._db.refresh(client)

        return client, raw_key
