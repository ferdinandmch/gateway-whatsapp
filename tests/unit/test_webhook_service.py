"""Testes unitários do WebhookService."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.instance import Instance, InstanceStatus
from app.models.message import Message, MessageContentType, MessageDirection
from app.models.webhook_event import WebhookEvent, WebhookProcessingStatus
from app.services.webhook_service import WebhookService


def _make_instance(
    provider_instance_id: str = "inst_01",
    status: InstanceStatus = InstanceStatus.connected,
    n8n_webhook_url: str | None = None,
    webhook_enabled: bool = True,
) -> MagicMock:
    inst = MagicMock(spec=Instance)
    inst.id = uuid.uuid4()
    inst.client_id = uuid.uuid4()
    inst.provider_instance_id = provider_instance_id
    inst.status = status
    inst.n8n_webhook_url = n8n_webhook_url
    inst.webhook_enabled = webhook_enabled
    inst.deleted_at = None
    inst.updated_at = datetime.now(timezone.utc)
    return inst


def _make_mock_db(instance: MagicMock | None = None) -> AsyncMock:
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=instance)
    db.execute = AsyncMock(return_value=mock_result)
    return db


_TEXT_PAYLOAD = {
    "event": "messages.upsert",
    "instance": "inst_01",
    "data": {
        "key": {"fromMe": False, "id": "msg_xyz", "remoteJid": "5511999999999@s.whatsapp.net"},
        "message": {"conversation": "Olá!"},
        "messageTimestamp": 1700000000,
    },
}

_CONN_PAYLOAD = {
    "event": "connection.update",
    "instance": "inst_01",
    "data": {"state": "open"},
}

_UNKNOWN_PAYLOAD = {
    "event": "some.random.event",
    "instance": "inst_01",
    "data": {},
}


# ---------------------------------------------------------------------------
# US1: Receber mensagem de entrada
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_message_received_creates_message():
    instance = _make_instance()
    db = _make_mock_db(instance=instance)

    service = WebhookService(db)
    response, status_code = await service.process(_TEXT_PAYLOAD)

    assert response.received is True
    assert response.event_type == "message.received"
    assert response.processing_status == WebhookProcessingStatus.processed.value
    assert status_code == 200
    assert db.add.called
    assert db.commit.called


@pytest.mark.asyncio
async def test_process_message_received_instance_not_found():
    db = _make_mock_db(instance=None)

    service = WebhookService(db)
    response, status_code = await service.process(_TEXT_PAYLOAD)

    assert response.received is True
    assert response.event_type == "message.received"
    # Evento conhecido → processed (200), mesmo sem instância (mensagem não criada)
    assert status_code == 200


@pytest.mark.asyncio
async def test_process_message_received_forwards_to_n8n():
    instance = _make_instance(n8n_webhook_url="http://n8n/webhook/test")
    db = _make_mock_db(instance=instance)

    from app.webhooks.forwarder import ForwardResult
    forward_result = ForwardResult(success=True, status_code=200, response={"ok": True})

    with patch("app.services.webhook_service.forward_to_n8n", new_callable=AsyncMock) as mock_fwd:
        mock_fwd.return_value = forward_result
        service = WebhookService(db)
        response, _ = await service.process(_TEXT_PAYLOAD)

    mock_fwd.assert_called_once()
    assert response.forwarded_to_n8n is True


# ---------------------------------------------------------------------------
# US2: Atualização de conexão
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_connection_update_changes_instance_status():
    instance = _make_instance(status=InstanceStatus.disconnected)
    db = _make_mock_db(instance=instance)

    service = WebhookService(db)
    response, status_code = await service.process(_CONN_PAYLOAD)

    assert response.event_type == "connection.update"
    assert response.processing_status == WebhookProcessingStatus.processed.value
    assert status_code == 200
    assert instance.status == InstanceStatus.connected


@pytest.mark.asyncio
async def test_process_connection_update_forwards_to_n8n():
    instance = _make_instance(n8n_webhook_url="http://n8n/webhook/conn")
    db = _make_mock_db(instance=instance)

    from app.webhooks.forwarder import ForwardResult
    fwd_result = ForwardResult(success=True, status_code=200, response={})

    with patch("app.services.webhook_service.forward_to_n8n", new_callable=AsyncMock) as mock_fwd:
        mock_fwd.return_value = fwd_result
        service = WebhookService(db)
        await service.process(_CONN_PAYLOAD)

    mock_fwd.assert_called_once()


# ---------------------------------------------------------------------------
# US3: Status de entrega/leitura
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_message_delivered_updates_status():
    instance = _make_instance()
    db = _make_mock_db(instance=instance)

    message_mock = MagicMock(spec=Message)
    message_mock.id = uuid.uuid4()
    message_mock.status = "sent"
    message_mock.updated_at = datetime.now(timezone.utc)

    result_instance = MagicMock()
    result_instance.scalar_one_or_none = MagicMock(side_effect=[instance, message_mock])
    db.execute = AsyncMock(return_value=result_instance)

    delivered_payload = {
        "event": "messages.update",
        "instance": "inst_01",
        "data": [{"key": {"id": "msg_out1"}, "update": {"status": "DELIVERY_ACK"}}],
    }

    service = WebhookService(db)
    response, status_code = await service.process(delivered_payload)

    assert response.event_type == "message.delivered"
    assert status_code == 200
    assert message_mock.status == "delivered"


# ---------------------------------------------------------------------------
# US4: Eventos desconhecidos
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_unknown_event_returns_202():
    db = _make_mock_db(instance=None)

    service = WebhookService(db)
    response, status_code = await service.process(_UNKNOWN_PAYLOAD)

    assert response.received is True
    assert response.event_type == "unknown"
    assert response.processing_status == WebhookProcessingStatus.ignored.value
    assert status_code == 202


@pytest.mark.asyncio
async def test_process_unknown_event_still_saves_raw_payload():
    db = _make_mock_db(instance=None)

    service = WebhookService(db)
    await service.process(_UNKNOWN_PAYLOAD)

    assert db.add.called
    assert db.commit.called
