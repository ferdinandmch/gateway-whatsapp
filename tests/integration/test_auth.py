"""Testes de integração: autenticação por API Key nas rotas protegidas."""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import generate_api_key, hash_api_key

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

RAW_API_KEY = generate_api_key()


def make_active_client(raw_key: str) -> MagicMock:
    client = MagicMock()
    client.id = uuid.uuid4()
    client.is_active = True
    client.api_key_hash = hash_api_key(raw_key, "test-salt")
    client.deleted_at = None
    return client


def make_inactive_client(raw_key: str) -> MagicMock:
    client = MagicMock()
    client.id = uuid.uuid4()
    client.is_active = False
    client.api_key_hash = hash_api_key(raw_key, "test-salt")
    client.deleted_at = None
    return client


@pytest.fixture
def mock_env(monkeypatch):
    for k, v in VALID_ENV.items():
        monkeypatch.setenv(k, v)


@pytest.fixture
async def app_with_real_auth(mock_env):
    """App sem override de get_current_client — testa a dependência real."""
    from app.main import create_app
    from app.core import dependencies

    async def override_get_db():
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute.return_value = result
        yield db

    def override_get_provider():
        return MagicMock()

    app = create_app()
    app.dependency_overrides[dependencies.get_db] = override_get_db
    app.dependency_overrides[dependencies.get_provider] = override_get_provider
    return app


@pytest.fixture
async def app_with_valid_client(mock_env):
    """App com DB mockado que retorna cliente ativo."""
    from app.main import create_app
    from app.core import dependencies

    active_client = make_active_client(RAW_API_KEY)

    async def override_get_db():
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = active_client
        db.execute.return_value = result
        yield db

    def override_get_provider():
        return MagicMock()

    app = create_app()
    app.dependency_overrides[dependencies.get_db] = override_get_db
    app.dependency_overrides[dependencies.get_provider] = override_get_provider
    return app


@pytest.fixture
async def app_with_inactive_client(mock_env):
    """App com DB mockado que retorna cliente inativo."""
    from app.main import create_app
    from app.core import dependencies

    inactive_client = make_inactive_client(RAW_API_KEY)

    async def override_get_db():
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = inactive_client
        db.execute.return_value = result
        yield db

    def override_get_provider():
        return MagicMock()

    app = create_app()
    app.dependency_overrides[dependencies.get_db] = override_get_db
    app.dependency_overrides[dependencies.get_provider] = override_get_provider
    return app


class TestAuthMissingHeader:
    async def test_instances_sem_api_key_retorna_401(self, app_with_real_auth):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_real_auth), base_url="http://test"
        ) as client:
            response = await client.get("/v1/instances")
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "UNAUTHORIZED"

    async def test_messages_sem_api_key_retorna_401(self, app_with_real_auth):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_real_auth), base_url="http://test"
        ) as client:
            response = await client.post("/v1/messages/text", json={})
        assert response.status_code == 401

    async def test_header_vazio_retorna_401(self, app_with_real_auth):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_real_auth), base_url="http://test"
        ) as client:
            response = await client.get("/v1/instances", headers={"X-API-Key": ""})
        assert response.status_code == 401


class TestAuthInvalidKey:
    async def test_api_key_invalida_retorna_401(self, app_with_real_auth):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_real_auth), base_url="http://test"
        ) as client:
            result = MagicMock()
            result.scalar_one_or_none.return_value = None

            response = await client.get(
                "/v1/instances", headers={"X-API-Key": "zapi_chave_invalida_0000000"}
            )
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "UNAUTHORIZED"


class TestAuthValidKey:
    async def test_api_key_valida_nao_retorna_401(self, app_with_valid_client):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_valid_client), base_url="http://test"
        ) as client:
            response = await client.get(
                "/v1/instances", headers={"X-API-Key": RAW_API_KEY}
            )
        # Auth passou — não deve retornar 401
        assert response.status_code != 401


class TestAuthInactiveClient:
    async def test_cliente_inativo_retorna_401(self, app_with_inactive_client):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_inactive_client), base_url="http://test"
        ) as client:
            response = await client.get(
                "/v1/instances", headers={"X-API-Key": RAW_API_KEY}
            )
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "UNAUTHORIZED"

    async def test_cliente_inativo_nao_revela_existencia(self, app_with_inactive_client):
        """Resposta de inativo deve ser idêntica a chave inexistente."""
        async with AsyncClient(
            transport=ASGITransport(app=app_with_inactive_client), base_url="http://test"
        ) as client:
            inactive_response = await client.get(
                "/v1/instances", headers={"X-API-Key": RAW_API_KEY}
            )

        assert inactive_response.json()["detail"]["message"] == "API Key inválida."
