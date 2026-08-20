"""Testes de integração: isolamento entre API Keys e tokens internos."""
import uuid
from unittest.mock import AsyncMock, MagicMock

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


@pytest.fixture
def mock_env(monkeypatch):
    for k, v in VALID_ENV.items():
        monkeypatch.setenv(k, v)


@pytest.fixture
async def app_no_db_override(mock_env):
    """App sem override de get_current_client — valida tokens reais."""
    from app.main import create_app
    from app.core import dependencies

    async def override_get_db():
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None  # nenhum cliente encontrado
        db.execute.return_value = result
        yield db

    def override_get_provider():
        return MagicMock()

    _app = create_app()
    _app.dependency_overrides[dependencies.get_db] = override_get_db
    _app.dependency_overrides[dependencies.get_provider] = override_get_provider
    return _app


class TestTokenIsolation:
    async def test_evolution_api_key_como_x_api_key_retorna_401(self, app_no_db_override):
        """Token interno da Evolution API não deve funcionar como API Key de cliente."""
        async with AsyncClient(
            transport=ASGITransport(app=app_no_db_override), base_url="http://test"
        ) as client:
            response = await client.get(
                "/v1/instances",
                headers={"X-API-Key": "test-evolution-key"},
            )
        assert response.status_code == 401

    async def test_admin_token_como_x_api_key_retorna_401(self, app_no_db_override):
        """ADMIN_TOKEN não deve funcionar como API Key de cliente."""
        async with AsyncClient(
            transport=ASGITransport(app=app_no_db_override), base_url="http://test"
        ) as client:
            response = await client.get(
                "/v1/instances",
                headers={"X-API-Key": "test-admin-token"},
            )
        assert response.status_code == 401

    async def test_resposta_nao_expoe_evolution_key(self, mock_env):
        """Nenhuma resposta da API deve conter o token interno da Evolution API."""
        from app.main import create_app
        from app.core import dependencies

        active_client = MagicMock()
        active_client.id = uuid.uuid4()
        active_client.is_active = True
        active_client.deleted_at = None
        active_client.api_key_hash = "some-hash"

        instances = []

        async def override_get_db():
            db = AsyncMock()
            result = MagicMock()
            result.scalar_one_or_none.return_value = active_client
            result.scalars.return_value.all.return_value = instances
            db.execute.return_value = result
            yield db

        def override_get_provider():
            return MagicMock()

        _app = create_app()
        _app.dependency_overrides[dependencies.get_db] = override_get_db
        _app.dependency_overrides[dependencies.get_provider] = override_get_provider

        from app.core.security import generate_api_key, hash_api_key
        raw_key = generate_api_key()

        async with AsyncClient(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/v1/instances",
                headers={"X-API-Key": raw_key},
            )

        response_text = response.text
        assert "test-evolution-key" not in response_text
        assert "test-admin-token" not in response_text
        assert "test-webhook-secret" not in response_text
