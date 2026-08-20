"""Testes de integração: endpoint POST /v1/clients."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

VALID_ENV = {
    "APP_ENV": "development",
    "APP_PORT": "8000",
    "LOG_LEVEL": "INFO",
    "HTTP_TIMEOUT": "30",
    "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db",
    "REDIS_URL": "redis://localhost:6379/0",
    "EVOLUTION_API_URL": "http://localhost:8080",
    "EVOLUTION_API_KEY": "test-evolution-key",
    "WEBHOOK_SECRET": "test-webhook-secret",
    "API_KEY_SALT": "test-salt",
    "ADMIN_TOKEN": "test-admin-token",
    "N8N_DEFAULT_WEBHOOK_URL": "http://localhost:5678/webhook/test",
    "WEBHOOK_BASE_URL": "http://localhost:8000",
}

ADMIN_TOKEN = "test-admin-token"


@pytest.fixture
def mock_env(monkeypatch):
    for k, v in VALID_ENV.items():
        monkeypatch.setenv(k, v)


@pytest.fixture
async def app(mock_env):
    from app.main import create_app
    from app.core import dependencies

    async def override_get_db():
        yield AsyncMock()

    def override_get_provider():
        return MagicMock()

    _app = create_app()
    _app.dependency_overrides[dependencies.get_db] = override_get_db
    _app.dependency_overrides[dependencies.get_provider] = override_get_provider
    return _app


class TestCreateClientAuth:
    async def test_sem_admin_token_retorna_401(self, app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/v1/clients", json={"name": "Teste"})
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "UNAUTHORIZED"

    async def test_admin_token_invalido_retorna_401(self, app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/v1/clients",
                json={"name": "Teste"},
                headers={"X-Admin-Token": "token-errado"},
            )
        assert response.status_code == 401

    async def test_body_invalido_retorna_422(self, app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/v1/clients",
                json={},
                headers={"X-Admin-Token": ADMIN_TOKEN},
            )
        assert response.status_code == 422

    async def test_nome_vazio_retorna_422(self, app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/v1/clients",
                json={"name": ""},
                headers={"X-Admin-Token": ADMIN_TOKEN},
            )
        assert response.status_code == 422


class TestCreateClientSuccess:
    async def test_cria_cliente_retorna_api_key(self, mock_env):
        from datetime import datetime, timezone
        from app.main import create_app
        from app.core import dependencies
        from app.core.security import generate_api_key, hash_api_key

        raw_key = generate_api_key()
        created_client = MagicMock()
        created_client.id = uuid.uuid4()
        created_client.name = "Novo Cliente"
        created_client.is_active = True
        created_client.created_at = datetime.now(timezone.utc)

        async def override_get_db():
            yield AsyncMock()

        def override_get_provider():
            return MagicMock()

        _app = create_app()
        _app.dependency_overrides[dependencies.get_db] = override_get_db
        _app.dependency_overrides[dependencies.get_provider] = override_get_provider

        with patch("app.services.client_service.ClientService.create_client") as mock_create:
            mock_create.return_value = (created_client, raw_key)

            async with AsyncClient(
                transport=ASGITransport(app=_app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/v1/clients",
                    json={"name": "Novo Cliente"},
                    headers={"X-Admin-Token": ADMIN_TOKEN},
                )

        assert response.status_code == 201
        data = response.json()
        assert "api_key" in data
        assert data["api_key"].startswith("zapi_")
        assert data["name"] == "Novo Cliente"

    async def test_api_key_retornada_funciona_em_rotas(self, mock_env):
        """API Key retornada na criação deve autenticar em rotas protegidas."""
        from app.main import create_app
        from app.core import dependencies
        from app.core.security import generate_api_key, hash_api_key

        raw_key = generate_api_key()
        key_hash = hash_api_key(raw_key, "test-salt")

        active_client = MagicMock()
        active_client.id = uuid.uuid4()
        active_client.is_active = True
        active_client.api_key_hash = key_hash
        active_client.deleted_at = None

        async def override_get_db():
            db = AsyncMock()
            result = MagicMock()
            result.scalar_one_or_none.return_value = active_client
            db.execute.return_value = result
            yield db

        def override_get_provider():
            return MagicMock()

        _app = create_app()
        _app.dependency_overrides[dependencies.get_db] = override_get_db
        _app.dependency_overrides[dependencies.get_provider] = override_get_provider

        async with AsyncClient(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as client:
            response = await client.get("/v1/instances", headers={"X-API-Key": raw_key})

        # Não deve ser 401 — auth passou
        assert response.status_code != 401
