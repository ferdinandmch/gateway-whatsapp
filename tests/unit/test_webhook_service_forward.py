"""Testes unitários de encaminhamento n8n no WebhookService (spec 007)."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.instance import Instance, InstanceStatus
from app.models.webhook_event import WebhookProcessingStatus
from app.services.webhook_service import WebhookService
from app.webhooks.forwarder import ForwardResult


def _make_instance(
    n8n_webhook_url: str | None = "http://n8n.test/webhook/abc",
    webhook_enabled: bool = True,
) -> MagicMock:
    inst = MagicMock(spec=Instance)
    inst.id = uuid.uuid4()
    inst.client_id = uuid.uuid4()
    inst.provider_instance_id = "inst_01"
    inst.status = InstanceStatus.connected
    inst.n8n_webhook_url = n8n_webhook_url
    inst.webhook_enabled = webhook_enabled
    inst.deleted_at = None
    inst.updated_at = datetime.now(timezone.utc)
    return inst


def _make_db(instance: MagicMock | None = None) -> AsyncMock:
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=instance)
    db.execute = AsyncMock(return_value=result)
    return db


_MSG_PAYLOAD = {
    "event": "messages.upsert",
    "instance": "inst_01",
    "data": {
        "key": {"fromMe": False, "id": "msg_001", "remoteJid": "5511999999999@s.whatsapp.net"},
        "message": {"conversation": "Olá"},
        "messageTimestamp": 1700000000,
    },
}

_CONN_PAYLOAD = {
    "event": "connection.update",
    "instance": "inst_01",
    "data": {"state": "open"},
}

_SEND_ERROR_PAYLOAD = {
    "event": "messages.update",
    "instance": "inst_01",
    "data": [{"key": {"id": "msg_out1"}, "update": {"status": "ERROR"}}],
}

_DELIVERED_PAYLOAD = {
    "event": "messages.update",
    "instance": "inst_01",
    "data": [{"key": {"id": "msg_out2"}, "update": {"status": "DELIVERY_ACK"}}],
}

_UNKNOWN_PAYLOAD = {
    "event": "some.unknown.event",
    "instance": "inst_01",
    "data": {},
}

_FWD_SUCCESS = ForwardResult(success=True, status_code=200, response={"ok": True})
_FWD_FAILURE = ForwardResult(success=False, status_code=500, response={"error": "server error"})


# ---------------------------------------------------------------------------
# T014 — message.received encaminhado com sucesso
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_message_received_forwarded_when_webhook_active():
    instance = _make_instance()
    db = _make_db(instance=instance)

    with patch("app.services.webhook_service.forward_to_n8n", new_callable=AsyncMock) as mock_fwd:
        mock_fwd.return_value = _FWD_SUCCESS
        service = WebhookService(db)
        response, _ = await service.process(_MSG_PAYLOAD)

    mock_fwd.assert_called_once()
    assert response.forwarded_to_n8n is True


# ---------------------------------------------------------------------------
# T015 — webhook_enabled=False → NÃO encaminha
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_message_received_not_forwarded_when_webhook_disabled():
    instance = _make_instance(webhook_enabled=False)
    db = _make_db(instance=instance)

    with patch("app.services.webhook_service.forward_to_n8n", new_callable=AsyncMock) as mock_fwd:
        service = WebhookService(db)
        response, _ = await service.process(_MSG_PAYLOAD)

    mock_fwd.assert_not_called()
    assert response.forwarded_to_n8n is False


# ---------------------------------------------------------------------------
# T016 — n8n_webhook_url=None → NÃO encaminha
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_message_received_not_forwarded_when_url_is_none():
    instance = _make_instance(n8n_webhook_url=None)
    db = _make_db(instance=instance)

    with patch("app.services.webhook_service.forward_to_n8n", new_callable=AsyncMock) as mock_fwd:
        service = WebhookService(db)
        response, _ = await service.process(_MSG_PAYLOAD)

    mock_fwd.assert_not_called()
    assert response.forwarded_to_n8n is False


# ---------------------------------------------------------------------------
# T017 — Falha no n8n não afeta processing_status nem quebra o webhook
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_n8n_failure_does_not_affect_processing_status():
    instance = _make_instance()
    db = _make_db(instance=instance)

    with patch("app.services.webhook_service.forward_to_n8n", new_callable=AsyncMock) as mock_fwd:
        mock_fwd.return_value = _FWD_FAILURE
        service = WebhookService(db)
        response, status_code = await service.process(_MSG_PAYLOAD)

    assert response.processing_status == WebhookProcessingStatus.processed.value
    assert status_code == 200
    assert response.forwarded_to_n8n is False
    assert db.add.called  # ErrorLog criado


# ---------------------------------------------------------------------------
# T019 — connection.update encaminhado com payload contendo connection_state
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_connection_update_forwarded_with_connection_state():
    instance = _make_instance()
    db = _make_db(instance=instance)

    with patch("app.services.webhook_service.forward_to_n8n", new_callable=AsyncMock) as mock_fwd:
        mock_fwd.return_value = _FWD_SUCCESS
        service = WebhookService(db)
        response, _ = await service.process(_CONN_PAYLOAD)

    mock_fwd.assert_called_once()
    call_payload = mock_fwd.call_args[0][1]
    assert call_payload.get("connection_state") is not None
    assert response.forwarded_to_n8n is True


# ---------------------------------------------------------------------------
# T020 — send.error encaminhado com provider_message_id
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_error_forwarded_with_provider_message_id():
    instance = _make_instance()
    db = _make_db(instance=instance)

    with patch("app.services.webhook_service.forward_to_n8n", new_callable=AsyncMock) as mock_fwd:
        mock_fwd.return_value = _FWD_SUCCESS
        service = WebhookService(db)
        response, _ = await service.process(_SEND_ERROR_PAYLOAD)

    mock_fwd.assert_called_once()
    call_payload = mock_fwd.call_args[0][1]
    assert call_payload.get("provider_message_id") == "msg_out1"
    assert response.forwarded_to_n8n is True


# ---------------------------------------------------------------------------
# T021 — message.delivered NÃO é encaminhado
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_message_delivered_not_forwarded():
    instance = _make_instance()
    # Simular que a mensagem existe no banco para atualização de status
    result_instance = MagicMock()
    message_mock = MagicMock()
    message_mock.status = "sent"
    message_mock.updated_at = datetime.now(timezone.utc)
    result_instance.scalar_one_or_none = MagicMock(side_effect=[instance, message_mock])
    db = _make_db(instance=instance)
    db.execute = AsyncMock(return_value=result_instance)

    with patch("app.services.webhook_service.forward_to_n8n", new_callable=AsyncMock) as mock_fwd:
        service = WebhookService(db)
        response, _ = await service.process(_DELIVERED_PAYLOAD)

    mock_fwd.assert_not_called()
    assert response.forwarded_to_n8n is False


# ---------------------------------------------------------------------------
# T022 — unknown NÃO é encaminhado
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_unknown_event_not_forwarded():
    instance = _make_instance()
    db = _make_db(instance=instance)

    with patch("app.services.webhook_service.forward_to_n8n", new_callable=AsyncMock) as mock_fwd:
        service = WebhookService(db)
        response, _ = await service.process(_UNKNOWN_PAYLOAD)

    mock_fwd.assert_not_called()
    assert response.forwarded_to_n8n is False
