"""Unit tests for FastAPI dependencies."""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest


def make_client(is_active: bool = True, api_key_hash: str | None = None):
    client = MagicMock()
    client.id = uuid.uuid4()
    client.is_active = is_active
    client.api_key_hash = api_key_hash
    client.deleted_at = None
    return client


class TestGetCurrentClient:
    async def test_missing_api_key_raises_401(self, mock_env):
        from fastapi import HTTPException
        from app.core.dependencies import get_current_client

        db = AsyncMock()
        with pytest.raises(HTTPException) as exc_info:
            await get_current_client(x_api_key=None, db=db)
        assert exc_info.value.status_code == 401

    async def test_invalid_api_key_raises_401(self, mock_env):
        from fastapi import HTTPException
        from app.core.dependencies import get_current_client

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute.return_value = result

        with pytest.raises(HTTPException) as exc_info:
            await get_current_client(x_api_key="invalid_key", db=db)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["code"] == "UNAUTHORIZED"

    async def test_inactive_client_raises_401(self, mock_env):
        from fastapi import HTTPException
        from app.core.dependencies import get_current_client
        from app.core.security import hash_api_key

        raw_key = "zapi_testkey"
        key_hash = hash_api_key(raw_key, "test-salt")
        client = make_client(is_active=False, api_key_hash=key_hash)

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = client
        db.execute.return_value = result

        with pytest.raises(HTTPException) as exc_info:
            await get_current_client(x_api_key=raw_key, db=db)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["code"] == "UNAUTHORIZED"

    async def test_valid_active_client_returns(self, mock_env):
        from app.core.dependencies import get_current_client
        from app.core.security import hash_api_key

        raw_key = "zapi_testkey"
        key_hash = hash_api_key(raw_key, "test-salt")
        client = make_client(is_active=True, api_key_hash=key_hash)

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = client
        db.execute.return_value = result

        returned = await get_current_client(x_api_key=raw_key, db=db)
        assert returned is client
