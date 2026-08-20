"""Testes unitários do classificador de eventos de webhook."""
import pytest

from app.webhooks.classifier import (
    EVENT_TYPE_CONNECTION_UPDATE,
    EVENT_TYPE_MESSAGE_DELIVERED,
    EVENT_TYPE_MESSAGE_READ,
    EVENT_TYPE_MESSAGE_RECEIVED,
    EVENT_TYPE_MESSAGE_SENT,
    EVENT_TYPE_SEND_ERROR,
    EVENT_TYPE_UNKNOWN,
    classify,
    is_forwardable,
)


# ---------------------------------------------------------------------------
# US1: Mensagem recebida (messages.upsert, fromMe=false)
# ---------------------------------------------------------------------------


def test_classify_message_received_text():
    payload = {
        "event": "messages.upsert",
        "instance": "inst_01",
        "data": {"key": {"fromMe": False, "id": "msg_abc"}, "message": {"conversation": "Olá"}},
    }
    assert classify(payload) == EVENT_TYPE_MESSAGE_RECEIVED


def test_classify_message_sent_from_me():
    payload = {
        "event": "messages.upsert",
        "instance": "inst_01",
        "data": {"key": {"fromMe": True, "id": "msg_abc"}, "message": {"conversation": "Oi"}},
    }
    assert classify(payload) == EVENT_TYPE_MESSAGE_SENT


def test_classify_message_received_image():
    payload = {
        "event": "messages.upsert",
        "instance": "inst_01",
        "data": {
            "key": {"fromMe": False, "id": "msg_img"},
            "message": {"imageMessage": {"url": "http://example.com/img.jpg", "caption": "foto"}},
        },
    }
    assert classify(payload) == EVENT_TYPE_MESSAGE_RECEIVED


# ---------------------------------------------------------------------------
# US2: Atualização de conexão
# ---------------------------------------------------------------------------


def test_classify_connection_update_lowercase():
    payload = {"event": "connection.update", "instance": "inst_01", "data": {"state": "open"}}
    assert classify(payload) == EVENT_TYPE_CONNECTION_UPDATE


def test_classify_connection_update_uppercase():
    payload = {"event": "CONNECTION_UPDATE", "instance": "inst_01", "data": {"state": "close"}}
    assert classify(payload) == EVENT_TYPE_CONNECTION_UPDATE


# ---------------------------------------------------------------------------
# US3: Status de entrega/leitura
# ---------------------------------------------------------------------------


def test_classify_message_delivered():
    payload = {
        "event": "messages.update",
        "instance": "inst_01",
        "data": [{"key": {"id": "msg_abc"}, "update": {"status": "DELIVERY_ACK"}}],
    }
    assert classify(payload) == EVENT_TYPE_MESSAGE_DELIVERED


def test_classify_message_read():
    payload = {
        "event": "messages.update",
        "instance": "inst_01",
        "data": [{"key": {"id": "msg_abc"}, "update": {"status": "READ"}}],
    }
    assert classify(payload) == EVENT_TYPE_MESSAGE_READ


def test_classify_send_error_from_messages_update():
    payload = {
        "event": "messages.update",
        "instance": "inst_01",
        "data": [{"key": {"id": "msg_abc"}, "update": {"status": "ERROR"}}],
    }
    assert classify(payload) == EVENT_TYPE_SEND_ERROR


# ---------------------------------------------------------------------------
# US4: Eventos desconhecidos
# ---------------------------------------------------------------------------


def test_classify_unknown_event():
    payload = {"event": "some.random.event", "instance": "inst_01", "data": {}}
    assert classify(payload) == EVENT_TYPE_UNKNOWN


def test_classify_missing_event_key():
    assert classify({}) == EVENT_TYPE_UNKNOWN


# ---------------------------------------------------------------------------
# is_forwardable
# ---------------------------------------------------------------------------


def test_is_forwardable_message_received():
    assert is_forwardable(EVENT_TYPE_MESSAGE_RECEIVED) is True


def test_is_forwardable_connection_update():
    assert is_forwardable(EVENT_TYPE_CONNECTION_UPDATE) is True


def test_is_forwardable_send_error():
    assert is_forwardable(EVENT_TYPE_SEND_ERROR) is True


def test_not_forwardable_message_sent():
    assert is_forwardable(EVENT_TYPE_MESSAGE_SENT) is False


def test_not_forwardable_message_delivered():
    assert is_forwardable(EVENT_TYPE_MESSAGE_DELIVERED) is False


def test_not_forwardable_unknown():
    assert is_forwardable(EVENT_TYPE_UNKNOWN) is False
