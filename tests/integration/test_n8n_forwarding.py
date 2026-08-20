"""Testes de integração: fluxo completo de webhook + encaminhamento ao n8n (spec 007).

Estratégia: DB mockado + respx interceptando chamadas HTTP ao n8n,
verificando payload normalizado enviado.
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
import respx
import httpx
from httpx import ASGITransport, AsyncClient

from app.models.instance import Instance, InstanceStatus
from app.models.webhook_event import WebhookEvent, WebhookProcessingStatus


VALID_ENV = {
    "APP_ENV": "development",
    "APP_PORT": "8000",
    "LOG_LEVEL": "INFO",
    "HTTP_TIMEOUT": "30",
    "N8N_FORWARD_TIMEOUT": "5",
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
_N8N_URL = "http://n8n.test/webhook/instance-abc"


@pytest.fixture
def mock_env(monkeypatch):
    for k, v in VALID_ENV.items():
        monkeypatch.setenv(k, v)


def _make_instance(n8n_webhook_url: str = _N8N_URL) -> MagicMock:
    inst = MagicMock(spec=Instance)
    inst.id = uuid.uuid4()
    inst.client_id = uuid.uuid4()
    inst.provider_instance_id = "inst_01"
    inst.status = InstanceStatus.connected
    inst.n8n_webhook_url = n8n_webhook_url
    inst.webhook_enabled = True
    inst.deleted_at = None
    inst.updated_at = datetime.now(timezone.utc)
    return inst


def _make_db(instance: MagicMock) -> AsyncMock:
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=instance)
    db.execute = AsyncMock(return_value=result)
    return db


@pytest.fixture
def app_with_db(mock_env):
    from app.main import create_app
    from app.core import dependencies

    instance = _make_instance()
    db = _make_db(instance)

    async def override_get_db():
        yield db

    app = create_app()
    app.dependency_overrides[dependencies.get_db] = override_get_db
    return app


# ---------------------------------------------------------------------------
# T018 — message.received: resposta 200 + forwarded_to_n8n + payload correto
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@respx.mock
async def test_message_received_forwarded_to_n8n(app_with_db):
    n8n_route = respx.post(_N8N_URL).mock(return_value=httpx.Response(200, json={"ok": True}))

    async with AsyncClient(transport=ASGITransport(app=app_with_db), base_url="http://test") as client:
        payload = {
            "event": "messages.upsert",
            "instance": "inst_01",
            "data": {
                "key": {"fromMe": False, "id": "msg_001", "remoteJid": "5511999999999@s.whatsapp.net"},
                "message": {"conversation": "Olá"},
                "messageTimestamp": 1700000000,
            },
        }
        resp = await client.post("/v1/webhooks/evolution", headers=_HEADERS, json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["received"] is True
    assert body["forwarded_to_n8n"] is True

    assert n8n_route.called
    sent = n8n_route.calls.last.request
    import json
    sent_payload = json.loads(sent.content)
    assert sent_payload["event_type"] == "message.received"
    assert sent_payload["provider"] == "evolution"
    assert "from" in sent_payload or "remote_jid" in sent_payload


# ---------------------------------------------------------------------------
# T023 — connection.update: payload ao n8n contém connection_state
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@respx.mock
async def test_connection_update_forwarded_with_state(app_with_db):
    n8n_route = respx.post(_N8N_URL).mock(return_value=httpx.Response(200, json={"ok": True}))

    async with AsyncClient(transport=ASGITransport(app=app_with_db), base_url="http://test") as client:
        payload = {
            "event": "connection.update",
            "instance": "inst_01",
            "data": {"state": "open"},
        }
        resp = await client.post("/v1/webhooks/evolution", headers=_HEADERS, json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["forwarded_to_n8n"] is True

    assert n8n_route.called
    import json
    sent_payload = json.loads(n8n_route.calls.last.request.content)
    assert sent_payload["event_type"] == "connection.update"
    assert sent_payload.get("connection_state") is not None


# ---------------------------------------------------------------------------
# T024 — send.error: payload ao n8n contém provider_message_id
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@respx.mock
async def test_send_error_forwarded_with_message_id(app_with_db):
    n8n_route = respx.post(_N8N_URL).mock(return_value=httpx.Response(200, json={"ok": True}))

    async with AsyncClient(transport=ASGITransport(app=app_with_db), base_url="http://test") as client:
        payload = {
            "event": "messages.update",
            "instance": "inst_01",
            "data": [{"key": {"id": "msg_out1"}, "update": {"status": "ERROR"}}],
        }
        resp = await client.post("/v1/webhooks/evolution", headers=_HEADERS, json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["forwarded_to_n8n"] is True

    assert n8n_route.called
    import json
    sent_payload = json.loads(n8n_route.calls.last.request.content)
    assert sent_payload["event_type"] == "send.error"
    assert sent_payload.get("provider_message_id") == "msg_out1"
