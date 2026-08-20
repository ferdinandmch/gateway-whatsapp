import pytest
from httpx import AsyncClient, ASGITransport


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
}


@pytest.fixture
def mock_env(monkeypatch):
    for key, value in VALID_ENV.items():
        monkeypatch.setenv(key, value)
    return VALID_ENV


@pytest.fixture
def clean_env(monkeypatch):
    for key in VALID_ENV:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
async def async_client(mock_env):
    from app.main import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
