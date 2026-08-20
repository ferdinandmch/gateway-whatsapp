"""Testes de integração para o endpoint POST /v1/webhooks/evolution."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.models.webhook_event import WebhookProcessingStatus

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

_WEBHOOK_SECRET = "test-webhook-secret"
_HEADERS = {"X-Webhook-Secret": _WEBHOOK_SECRET}


@pytest.fixture
def mock_env(monkeypatch):
    for k, v in VALID_ENV.items():
        monkeypatch.setenv(k, v)


@pytest.fixture
async def test_app(mock_env):
    from app.main import create_app
    from app.core import dependencies

    async def override_get_db():
        yield AsyncMock()

    app = create_app()
    app.dependency_overrides[dependencies.get_db] = override_get_db
    return app


@pytest.fixture
async def client(test_app):
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as c:
        yield c


def _make_service_response(event_type: str, status: str, forwarded: bool = False, code: int = 200):
    from app.schemas.webhook import WebhookResponse
    response = WebhookResponse(
        received=True,
        event_id=uuid.uuid4(),
        event_type=event_type,
        processing_status=status,
        forwarded_to_n8n=forwarded,
    )
    return response, code


# ---------------------------------------------------------------------------
# T038: Autenticação — segredo inválido
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_missing_webhook_secret_returns_401(client):
    resp = await client.post(
        "/v1/webhooks/evolution",
        json={"event": "messages.upsert", "instance": "inst_01", "data": {}},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"]["code"] == "WEBHOOK_UNAUTHORIZED"


@pytest.mark.asyncio
async def test_invalid_webhook_secret_returns_401(client):
    resp = await client.post(
        "/v1/webhooks/evolution",
        headers={"X-Webhook-Secret": "wrong-secret"},
        json={"event": "messages.upsert", "instance": "inst_01", "data": {}},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# T021: US1 — mensagem recebida → 200
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_message_received_returns_200(client):
    from app.services import webhook_service as svc_module

    svc_response = _make_service_response("message.received", "processed", code=200)

    async def fake_process(self_svc, payload):
        return svc_response

    with patch.object(svc_module.WebhookService, "process", fake_process):
        payload = {
            "event": "messages.upsert",
            "instance": "inst_01",
            "data": {
                "key": {"fromMe": False, "id": "msg_001", "remoteJid": "5511999@s.whatsapp.net"},
                "message": {"conversation": "Olá mundo"},
                "messageTimestamp": 1700000000,
            },
        }
        resp = await client.post("/v1/webhooks/evolution", headers=_HEADERS, json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["received"] is True
    assert body["event_type"] == "message.received"


# ---------------------------------------------------------------------------
# T027: US2 — connection.update → 200
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_connection_update_returns_200(client):
    from app.services import webhook_service as svc_module

    svc_response = _make_service_response("connection.update", "processed", code=200)

    async def fake_process(self_svc, payload):
        return svc_response

    with patch.object(svc_module.WebhookService, "process", fake_process):
        payload = {
            "event": "connection.update",
            "instance": "inst_01",
            "data": {"state": "open"},
        }
        resp = await client.post("/v1/webhooks/evolution", headers=_HEADERS, json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["event_type"] == "connection.update"


# ---------------------------------------------------------------------------
# T032: US3 — message.delivered → 200
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_message_delivered_returns_200(client):
    from app.services import webhook_service as svc_module

    svc_response = _make_service_response("message.delivered", "processed", code=200)

    async def fake_process(self_svc, payload):
        return svc_response

    with patch.object(svc_module.WebhookService, "process", fake_process):
        payload = {
            "event": "messages.update",
            "instance": "inst_01",
            "data": [{"key": {"id": "msg_out1"}, "update": {"status": "DELIVERY_ACK"}}],
        }
        resp = await client.post("/v1/webhooks/evolution", headers=_HEADERS, json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["event_type"] == "message.delivered"


# ---------------------------------------------------------------------------
# T037: US4 — evento desconhecido → 202
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unknown_event_returns_202(client):
    from app.services import webhook_service as svc_module

    svc_response = _make_service_response("unknown", "ignored", code=202)

    async def fake_process(self_svc, payload):
        return svc_response

    with patch.object(svc_module.WebhookService, "process", fake_process):
        payload = {
            "event": "some.random.event",
            "instance": "inst_01",
            "data": {"foo": "bar"},
        }
        resp = await client.post("/v1/webhooks/evolution", headers=_HEADERS, json=payload)

    assert resp.status_code == 202
    body = resp.json()
    assert body["received"] is True
    assert body["event_type"] == "unknown"
    assert body["processing_status"] == "ignored"
