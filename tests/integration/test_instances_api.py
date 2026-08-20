"""Integration tests for instance management endpoints."""
import hashlib
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.models.instance import InstanceStatus
from app.schemas.provider import ProviderError, ProviderResult

VALID_ENV = {
    "APP_ENV": "development",
    "APP_PORT": "8000",
    "LOG_LEVEL": "INFO",
    "HTTP_TIMEOUT": "30",
    "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db",
    "REDIS_URL": "redis://localhost:6379/0",
    "EVOLUTION_API_URL": "http://localhost:8080",
    "EVOLUTION_API_KEY": "test-key",
    "WEBHOOK_SECRET": "test-webhook-secret",
    "API_KEY_SALT": "test-salt",
    "ADMIN_TOKEN": "test-admin-token",
    "N8N_DEFAULT_WEBHOOK_URL": "http://localhost:5678/webhook/test",
    "WEBHOOK_BASE_URL": "http://localhost:8000",
}

RAW_API_KEY = "zapi_integrationtestkey"


def _hash_key(key: str) -> str:
    return hashlib.sha256(f"test-salt{key}".encode()).hexdigest()


def make_mock_client():
    client = MagicMock()
    client.id = uuid.uuid4()
    client.is_active = True
    client.api_key_hash = _hash_key(RAW_API_KEY)
    client.deleted_at = None
    return client


def make_mock_instance(client_id, status=InstanceStatus.created):
    inst = MagicMock()
    inst.id = uuid.uuid4()
    inst.client_id = client_id
    inst.display_name = "Test Instance"
    inst.provider = "evolution"
    inst.provider_instance_id = "inst_abc12345"
    inst.status = status
    inst.phone_number = None
    inst.n8n_webhook_url = None
    inst.webhook_enabled = True
    from datetime import datetime, timezone
    inst.created_at = datetime.now(timezone.utc)
    inst.updated_at = datetime.now(timezone.utc)
    inst.deleted_at = None
    return inst


@pytest.fixture
def mock_env(monkeypatch):
    for k, v in VALID_ENV.items():
        monkeypatch.setenv(k, v)


@pytest.fixture
def mock_client_obj(mock_env):
    return make_mock_client()


@pytest.fixture
def mock_instance(mock_client_obj):
    return make_mock_instance(mock_client_obj.id)


@pytest.fixture
async def test_app(mock_env, mock_client_obj):
    from app.main import create_app
    from app.core import dependencies

    async def override_get_current_client():
        return mock_client_obj

    async def override_get_db():
        yield AsyncMock()

    def override_get_provider():
        return AsyncMock()

    app = create_app()
    app.dependency_overrides[dependencies.get_current_client] = override_get_current_client
    app.dependency_overrides[dependencies.get_db] = override_get_db
    app.dependency_overrides[dependencies.get_provider] = override_get_provider
    return app


@pytest.fixture
async def client(test_app):
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as c:
        yield c


HEADERS = {"X-API-Key": RAW_API_KEY}


class TestCreateInstance:
    async def test_create_success(self, client, mock_client_obj, monkeypatch):
        from app.services import instance_service as svc_module

        async def fake_create(self_svc, client, data):
            from app.schemas.instance import InstanceResponse
            from datetime import datetime, timezone
            return InstanceResponse(
                id=uuid.uuid4(),
                display_name=data.display_name,
                provider="evolution",
                provider_instance_name="inst_abc12345",
                status=InstanceStatus.created,
                phone_number=None,
                webhook_enabled=data.webhook_enabled,
                n8n_webhook_url=data.n8n_webhook_url,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

        monkeypatch.setattr(svc_module.InstanceService, "create_instance", fake_create)

        resp = await client.post("/v1/instances", json={"display_name": "Atendimento"}, headers=HEADERS)
        assert resp.status_code == 201
        data = resp.json()
        assert data["display_name"] == "Atendimento"
        assert data["status"] == "created"

    async def test_create_missing_display_name(self, client):
        resp = await client.post("/v1/instances", json={}, headers=HEADERS)
        assert resp.status_code == 422

    async def test_create_limit_reached(self, client, monkeypatch):
        from fastapi import HTTPException
        from app.services import instance_service as svc_module

        async def fake_create(self_svc, client, data):
            raise HTTPException(
                status_code=409,
                detail={"code": "INSTANCE_LIMIT_REACHED", "message": "Limite atingido.", "details": {}},
            )

        monkeypatch.setattr(svc_module.InstanceService, "create_instance", fake_create)
        resp = await client.post("/v1/instances", json={"display_name": "Test"}, headers=HEADERS)
        assert resp.status_code == 409
        assert resp.json()["detail"]["code"] == "INSTANCE_LIMIT_REACHED"


class TestListInstances:
    async def test_list_empty(self, client, monkeypatch):
        from app.services import instance_service as svc_module

        async def fake_list(self_svc, client, **kwargs):
            from app.schemas.instance import InstanceListResponse
            return InstanceListResponse(items=[], total=0, limit=20, offset=0)

        monkeypatch.setattr(svc_module.InstanceService, "list_instances", fake_list)

        resp = await client.get("/v1/instances", headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    async def test_list_pagination_params(self, client, monkeypatch):
        from app.services import instance_service as svc_module

        captured = {}

        async def fake_list(self_svc, cl, limit=20, offset=0, status=None, include_removed=False):
            captured.update({"limit": limit, "offset": offset, "include_removed": include_removed})
            from app.schemas.instance import InstanceListResponse
            return InstanceListResponse(items=[], total=0, limit=limit, offset=offset)

        monkeypatch.setattr(svc_module.InstanceService, "list_instances", fake_list)

        resp = await client.get("/v1/instances?limit=5&offset=10&include_removed=true", headers=HEADERS)
        assert resp.status_code == 200
        assert captured["limit"] == 5
        assert captured["offset"] == 10
        assert captured["include_removed"] is True


class TestConnectInstance:
    async def test_connect_success(self, client, monkeypatch):
        from app.services import instance_service as svc_module

        async def fake_connect(self_svc, instance_id, cl):
            from app.schemas.instance import InstanceConnectResponse
            return InstanceConnectResponse(
                instance_id=instance_id,
                status=InstanceStatus.connecting,
                qr_code="base64qr",
                pairing_code=None,
            )

        monkeypatch.setattr(svc_module.InstanceService, "connect_instance", fake_connect)
        inst_id = uuid.uuid4()
        resp = await client.post(f"/v1/instances/{inst_id}/connect", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["status"] == "connecting"
        assert resp.json()["qr_code"] == "base64qr"

    async def test_connect_not_found(self, client, monkeypatch):
        from fastapi import HTTPException
        from app.services import instance_service as svc_module

        async def fake_connect(self_svc, instance_id, cl):
            raise HTTPException(
                status_code=404,
                detail={"code": "INSTANCE_NOT_FOUND", "message": "Instância não encontrada.", "details": {}},
            )

        monkeypatch.setattr(svc_module.InstanceService, "connect_instance", fake_connect)
        resp = await client.post(f"/v1/instances/{uuid.uuid4()}/connect", headers=HEADERS)
        assert resp.status_code == 404
        assert resp.json()["detail"]["code"] == "INSTANCE_NOT_FOUND"


class TestGetInstanceStatus:
    async def test_get_status_connected(self, client, monkeypatch):
        from app.services import instance_service as svc_module
        from datetime import datetime, timezone

        async def fake_status(self_svc, instance_id, cl):
            from app.schemas.instance import InstanceStatusResponse
            return InstanceStatusResponse(
                instance_id=instance_id,
                status=InstanceStatus.connected,
                provider="evolution",
                provider_status="open",
                phone_number="5586999999999",
                connected_at=datetime.now(timezone.utc),
                disconnected_at=None,
            )

        monkeypatch.setattr(svc_module.InstanceService, "get_instance_status", fake_status)
        resp = await client.get(f"/v1/instances/{uuid.uuid4()}/status", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["status"] == "connected"
        assert resp.json()["phone_number"] == "5586999999999"


class TestDisconnectInstance:
    async def test_disconnect_success(self, client, monkeypatch):
        from app.services import instance_service as svc_module
        from datetime import datetime, timezone

        async def fake_disconnect(self_svc, instance_id, cl):
            from app.schemas.instance import InstanceDisconnectResponse
            return InstanceDisconnectResponse(
                instance_id=instance_id,
                status=InstanceStatus.disconnected,
                disconnected_at=datetime.now(timezone.utc),
            )

        monkeypatch.setattr(svc_module.InstanceService, "disconnect_instance", fake_disconnect)
        resp = await client.post(f"/v1/instances/{uuid.uuid4()}/disconnect", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["status"] == "disconnected"


class TestDeleteInstance:
    async def test_delete_success(self, client, monkeypatch):
        from app.services import instance_service as svc_module

        async def fake_delete(self_svc, instance_id, cl):
            from app.schemas.instance import InstanceDeleteResponse
            return InstanceDeleteResponse(instance_id=instance_id, status=InstanceStatus.removed)

        monkeypatch.setattr(svc_module.InstanceService, "delete_instance", fake_delete)
        resp = await client.delete(f"/v1/instances/{uuid.uuid4()}", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["status"] == "removed"


class TestUpdateInstance:
    async def test_patch_display_name(self, client, monkeypatch):
        from app.services import instance_service as svc_module
        from datetime import datetime, timezone

        async def fake_update(self_svc, instance_id, cl, data):
            from app.schemas.instance import InstanceResponse
            return InstanceResponse(
                id=instance_id,
                display_name=data.display_name or "Old Name",
                provider="evolution",
                provider_instance_name="inst_abc12345",
                status=InstanceStatus.connected,
                phone_number=None,
                webhook_enabled=True,
                n8n_webhook_url=None,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

        monkeypatch.setattr(svc_module.InstanceService, "update_instance", fake_update)
        resp = await client.patch(
            f"/v1/instances/{uuid.uuid4()}",
            json={"display_name": "Novo Nome"},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["display_name"] == "Novo Nome"


class TestAuthErrors:
    async def test_missing_api_key_returns_401(self, test_app):
        from app.core import dependencies

        async def real_auth(x_api_key=None, db=None):
            from fastapi import HTTPException
            if not x_api_key:
                raise HTTPException(
                    status_code=401,
                    detail={"code": "UNAUTHORIZED", "message": "API Key ausente.", "details": {}},
                )

        test_app.dependency_overrides[dependencies.get_current_client] = real_auth
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as c:
            resp = await c.get("/v1/instances")
        assert resp.status_code == 401
