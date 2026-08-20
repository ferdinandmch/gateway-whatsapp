"""Testes unitários do normalizador de payload de webhook."""
import uuid

import pytest

from app.webhooks.normalizer import normalize
from app.webhooks.classifier import (
    EVENT_TYPE_CONNECTION_UPDATE,
    EVENT_TYPE_MESSAGE_DELIVERED,
    EVENT_TYPE_MESSAGE_READ,
    EVENT_TYPE_MESSAGE_RECEIVED,
    EVENT_TYPE_UNKNOWN,
)


_INSTANCE_ID = uuid.uuid4()
_CLIENT_ID = uuid.uuid4()


def _make_text_payload(from_me: bool = False, content: str = "Olá") -> dict:
    return {
        "event": "messages.upsert",
        "instance": "inst_01",
        "data": {
            "key": {"fromMe": from_me, "id": "msg_abc123", "remoteJid": "5511999999999@s.whatsapp.net"},
            "message": {"conversation": content},
            "messageTimestamp": 1700000000,
        },
    }


# ---------------------------------------------------------------------------
# US1: Normalização de mensagem de texto
# ---------------------------------------------------------------------------


def test_normalize_text_message_received():
    payload = _make_text_payload()
    result = normalize(payload, EVENT_TYPE_MESSAGE_RECEIVED, _INSTANCE_ID, _CLIENT_ID)

    assert result.event_type == EVENT_TYPE_MESSAGE_RECEIVED
    assert result.provider == "evolution"
    assert result.provider_instance_name == "inst_01"
    assert result.instance_id == _INSTANCE_ID
    assert result.client_id == _CLIENT_ID
    assert result.remote_jid == "5511999999999@s.whatsapp.net"
    assert result.from_number == "5511999999999"
    assert result.message_type == "text"
    assert result.content == "Olá"
    assert result.provider_message_id == "msg_abc123"
    assert result.timestamp is not None


def test_normalize_text_message_no_from_number_when_from_me():
    payload = _make_text_payload(from_me=True)
    result = normalize(payload, EVENT_TYPE_MESSAGE_RECEIVED, _INSTANCE_ID, _CLIENT_ID)
    assert result.from_number is None


# ---------------------------------------------------------------------------
# US1: Normalização de mensagens de mídia
# ---------------------------------------------------------------------------


def test_normalize_image_message():
    payload = {
        "event": "messages.upsert",
        "instance": "inst_01",
        "data": {
            "key": {"fromMe": False, "id": "msg_img1", "remoteJid": "5511999999999@s.whatsapp.net"},
            "message": {
                "imageMessage": {
                    "url": "http://example.com/image.jpg",
                    "caption": "Veja isso",
                }
            },
        },
    }
    result = normalize(payload, EVENT_TYPE_MESSAGE_RECEIVED, _INSTANCE_ID, _CLIENT_ID)
    assert result.message_type == "image"
    assert result.media_url == "http://example.com/image.jpg"
    assert result.content == "Veja isso"


def test_normalize_audio_message():
    payload = {
        "event": "messages.upsert",
        "instance": "inst_01",
        "data": {
            "key": {"fromMe": False, "id": "msg_aud1", "remoteJid": "5511999999999@s.whatsapp.net"},
            "message": {
                "audioMessage": {"url": "http://example.com/audio.ogg"}
            },
        },
    }
    result = normalize(payload, EVENT_TYPE_MESSAGE_RECEIVED, _INSTANCE_ID, _CLIENT_ID)
    assert result.message_type == "audio"
    assert result.media_url == "http://example.com/audio.ogg"


def test_normalize_document_message():
    payload = {
        "event": "messages.upsert",
        "instance": "inst_01",
        "data": {
            "key": {"fromMe": False, "id": "msg_doc1", "remoteJid": "5511999999999@s.whatsapp.net"},
            "message": {
                "documentMessage": {"url": "http://example.com/doc.pdf", "caption": "Documento"}
            },
        },
    }
    result = normalize(payload, EVENT_TYPE_MESSAGE_RECEIVED, _INSTANCE_ID, _CLIENT_ID)
    assert result.message_type == "document"
    assert result.media_url == "http://example.com/doc.pdf"
    assert result.content == "Documento"


# ---------------------------------------------------------------------------
# US2: Normalização de eventos de conexão
# ---------------------------------------------------------------------------


def test_normalize_connection_update_open():
    payload = {"event": "connection.update", "instance": "inst_01", "data": {"state": "open"}}
    result = normalize(payload, EVENT_TYPE_CONNECTION_UPDATE, _INSTANCE_ID, _CLIENT_ID)
    assert result.connection_state == "connected"
    assert result.timestamp is not None


def test_normalize_connection_update_close():
    payload = {"event": "connection.update", "instance": "inst_01", "data": {"state": "close"}}
    result = normalize(payload, EVENT_TYPE_CONNECTION_UPDATE, _INSTANCE_ID, _CLIENT_ID)
    assert result.connection_state == "disconnected"


def test_normalize_connection_update_qrcode():
    payload = {"event": "connection.update", "instance": "inst_01", "data": {"state": "qrcode"}}
    result = normalize(payload, EVENT_TYPE_CONNECTION_UPDATE, _INSTANCE_ID, _CLIENT_ID)
    assert result.connection_state == "connecting"


# ---------------------------------------------------------------------------
# US3: Normalização de eventos de status
# ---------------------------------------------------------------------------


def test_normalize_message_delivered():
    payload = {
        "event": "messages.update",
        "instance": "inst_01",
        "data": [{"key": {"id": "msg_out1"}, "update": {"status": "DELIVERY_ACK"}}],
    }
    result = normalize(payload, EVENT_TYPE_MESSAGE_DELIVERED, _INSTANCE_ID, _CLIENT_ID)
    assert result.provider_message_id == "msg_out1"
    assert result.timestamp is not None


def test_normalize_message_read():
    payload = {
        "event": "messages.update",
        "instance": "inst_01",
        "data": [{"key": {"id": "msg_out2"}, "update": {"status": "READ"}}],
    }
    result = normalize(payload, EVENT_TYPE_MESSAGE_READ, _INSTANCE_ID, _CLIENT_ID)
    assert result.provider_message_id == "msg_out2"


# ---------------------------------------------------------------------------
# US4: Eventos desconhecidos
# ---------------------------------------------------------------------------


def test_normalize_unknown_event():
    payload = {"event": "random", "instance": "inst_01", "data": {}}
    result = normalize(payload, EVENT_TYPE_UNKNOWN, None, None)
    assert result.event_type == EVENT_TYPE_UNKNOWN
    assert result.instance_id is None
    assert result.client_id is None
    assert result.timestamp is not None


# ---------------------------------------------------------------------------
# to_n8n_payload
# ---------------------------------------------------------------------------


def test_to_n8n_payload_contains_required_keys():
    payload = _make_text_payload()
    result = normalize(payload, EVENT_TYPE_MESSAGE_RECEIVED, _INSTANCE_ID, _CLIENT_ID)
    n8n = result.to_n8n_payload()
    assert "event_type" in n8n
    assert "provider" in n8n
    assert n8n["event_type"] == EVENT_TYPE_MESSAGE_RECEIVED
