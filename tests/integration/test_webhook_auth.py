"""Testes de integração: autenticação do webhook da Evolution API."""
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

WEBHOOK_SECRET = "test-webhook-secret"
WEBHOOK_PAYLOAD = {
    "event": "messages.upsert",
    "instance": "test-instance",
    "data": {},
}


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


class TestWebhookAuth:
    async def test_sem_segredo_retorna_401(self, app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/v1/webhooks/evolution", json=WEBHOOK_PAYLOAD)
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "WEBHOOK_UNAUTHORIZED"

    async def test_segredo_invalido_retorna_401(self, app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/v1/webhooks/evolution",
                json=WEBHOOK_PAYLOAD,
                headers={"X-Webhook-Secret": "segredo-errado"},
            )
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "WEBHOOK_UNAUTHORIZED"

    async def test_segredo_valido_aceita_evento(self, app):
        response_body = MagicMock()
        response_body.model_dump.return_value = {"status": "received"}

        with patch("app.services.webhook_service.WebhookService.process") as mock_process:
            mock_process.return_value = (response_body, 200)
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/v1/webhooks/evolution",
                    json=WEBHOOK_PAYLOAD,
                    headers={"X-Webhook-Secret": WEBHOOK_SECRET},
                )
        # Não deve retornar 401 — segredo válido
        assert response.status_code != 401
