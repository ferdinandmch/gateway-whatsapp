"""Testes unitários para ClientService."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestClientServiceCreateClient:
    async def test_cria_cliente_retorna_raw_key(self, mock_env):
        from app.services.client_service import ClientService

        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        created = MagicMock()
        created.id = uuid.uuid4()
        created.name = "Teste"
        created.is_active = True

        async def mock_refresh(obj):
            obj.id = created.id
            obj.name = created.name
            obj.is_active = True

        db.refresh.side_effect = mock_refresh

        service = ClientService(db=db)
        client, raw_key = await service.create_client("Teste")

        assert raw_key.startswith("zapi_")
        assert len(raw_key) == 37
        db.add.assert_called_once()
        db.commit.assert_called_once()

    async def test_api_key_armazenada_como_hash(self, mock_env):
        from app.services.client_service import ClientService
        from app.core.security import hash_api_key

        db = AsyncMock()
        db.add = MagicMock()

        captured_client = {}

        def capture_add(obj):
            captured_client["obj"] = obj

        db.add.side_effect = capture_add

        service = ClientService(db=db)
        _, raw_key = await service.create_client("Teste")

        obj = captured_client["obj"]
        assert obj.api_key_hash is not None
        assert obj.api_key_hash != raw_key
        expected_hash = hash_api_key(raw_key, "test-salt")
        assert obj.api_key_hash == expected_hash
