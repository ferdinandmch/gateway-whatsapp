"""Unit tests for SQLAlchemy ORM models.

NOTE: SQLAlchemy column defaults (uuid4, bool defaults, enum defaults) apply
at flush/insert time, not at Python __init__ time. Unit tests pass explicit
values; defaults are validated in integration tests.
"""
import uuid
from datetime import datetime, timezone

from app.models.client import Client
from app.models.instance import Instance, InstanceStatus
from app.models.message import Message, MessageContentType, MessageDirection
from app.models.webhook_event import WebhookEvent, WebhookProcessingStatus
from app.models.error_log import ErrorLog


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class TestClientModel:
    def test_client_construction(self):
        client = Client(id=uuid.uuid4(), name="Acme Corp", is_active=True)
        assert client.name == "Acme Corp"
        assert client.is_active is True
        assert client.deleted_at is None

    def test_client_uuid_is_uuid_type(self):
        cid = uuid.uuid4()
        client = Client(id=cid, name="A", is_active=True)
        assert isinstance(client.id, uuid.UUID)
        assert client.id == cid

    def test_two_clients_have_different_uuids(self):
        c1 = Client(id=uuid.uuid4(), name="A", is_active=True)
        c2 = Client(id=uuid.uuid4(), name="B", is_active=True)
        assert c1.id != c2.id

    def test_client_soft_delete_field(self):
        client = Client(id=uuid.uuid4(), name="X", is_active=True)
        client.deleted_at = datetime.now(timezone.utc)
        assert client.deleted_at is not None

    def test_client_repr(self):
        client = Client(id=uuid.uuid4(), name="Test", is_active=True)
        assert "Test" in repr(client)

    def test_client_inactive(self):
        client = Client(id=uuid.uuid4(), name="Disabled", is_active=False)
        assert client.is_active is False


# ---------------------------------------------------------------------------
# Instance
# ---------------------------------------------------------------------------

class TestInstanceModel:
    def test_instance_status_values(self):
        valid = {"created", "connecting", "connected", "disconnected", "error", "removed"}
        assert {s.value for s in InstanceStatus} == valid

    def test_instance_construction_with_status(self):
        instance = Instance(
            id=uuid.uuid4(),
            client_id=uuid.uuid4(),
            display_name="my-instance",
            status=InstanceStatus.disconnected,
        )
        assert instance.status == InstanceStatus.disconnected
        assert instance.display_name == "my-instance"

    def test_instance_status_transitions(self):
        instance = Instance(
            id=uuid.uuid4(),
            client_id=uuid.uuid4(),
            display_name="x",
            status=InstanceStatus.disconnected,
        )
        instance.status = InstanceStatus.connecting
        assert instance.status == InstanceStatus.connecting
        instance.status = InstanceStatus.connected
        assert instance.status == InstanceStatus.connected
        instance.status = InstanceStatus.error
        assert instance.status == InstanceStatus.error

    def test_instance_provider_instance_id_nullable(self):
        instance = Instance(
            id=uuid.uuid4(),
            client_id=uuid.uuid4(),
            display_name="x",
            status=InstanceStatus.disconnected,
        )
        assert instance.provider_instance_id is None

    def test_instance_soft_delete_field(self):
        instance = Instance(
            id=uuid.uuid4(),
            client_id=uuid.uuid4(),
            display_name="x",
            status=InstanceStatus.disconnected,
        )
        instance.deleted_at = datetime.now(timezone.utc)
        assert instance.deleted_at is not None

    def test_instance_repr(self):
        instance = Instance(
            id=uuid.uuid4(),
            client_id=uuid.uuid4(),
            display_name="my-instance",
            status=InstanceStatus.connected,
        )
        assert "my-instance" in repr(instance)
        assert "connected" in repr(instance)


# ---------------------------------------------------------------------------
# Message
# ---------------------------------------------------------------------------

class TestMessageModel:
    def test_message_direction_values(self):
        assert MessageDirection.inbound.value == "inbound"
        assert MessageDirection.outbound.value == "outbound"

    def test_message_content_types(self):
        valid = {"text", "image", "audio", "document", "video"}
        assert {t.value for t in MessageContentType} == valid

    def test_message_construction(self):
        msg = Message(
            id=uuid.uuid4(),
            instance_id=uuid.uuid4(),
            direction=MessageDirection.outbound,
            content_type=MessageContentType.text,
            remote_jid="5511999999999@s.whatsapp.net",
            status="pending",
        )
        assert msg.status == "pending"
        assert msg.provider_message_id is None
        assert msg.body is None

    def test_message_inbound(self):
        msg = Message(
            id=uuid.uuid4(),
            instance_id=uuid.uuid4(),
            direction=MessageDirection.inbound,
            content_type=MessageContentType.audio,
            remote_jid="jid1",
            status="received",
        )
        assert msg.direction == MessageDirection.inbound
        assert msg.content_type == MessageContentType.audio

    def test_message_repr(self):
        msg = Message(
            id=uuid.uuid4(),
            instance_id=uuid.uuid4(),
            direction=MessageDirection.outbound,
            content_type=MessageContentType.text,
            remote_jid="jid",
            status="pending",
        )
        assert "outbound" in repr(msg)


# ---------------------------------------------------------------------------
# WebhookEvent
# ---------------------------------------------------------------------------

class TestWebhookEventModel:
    def test_webhook_event_construction(self):
        event = WebhookEvent(
            id=uuid.uuid4(),
            event_type="message.received",
            raw_payload={"key": "value"},
            processing_status=WebhookProcessingStatus.received,
        )
        assert event.processing_status == WebhookProcessingStatus.received
        assert event.instance_id is None
        assert event.processed_at is None

    def test_webhook_event_instance_id_nullable(self):
        event = WebhookEvent(
            id=uuid.uuid4(),
            event_type="connection.update",
            raw_payload={},
            processing_status=WebhookProcessingStatus.received,
        )
        assert event.instance_id is None

    def test_webhook_event_large_payload(self):
        # SC-004: payloads up to 1MB must be stored and retrieved
        large_value = "x" * (1024 * 1024)  # 1MB string
        event = WebhookEvent(
            id=uuid.uuid4(),
            event_type="message.received",
            raw_payload={"data": large_value},
            processing_status=WebhookProcessingStatus.received,
        )
        assert len(event.raw_payload["data"]) == 1024 * 1024

    def test_webhook_event_repr(self):
        event = WebhookEvent(
            id=uuid.uuid4(),
            event_type="test.event",
            raw_payload={},
            processing_status=WebhookProcessingStatus.received,
        )
        assert "test.event" in repr(event)

    def test_webhook_processing_status_values(self):
        valid = {"received", "processing", "processed", "failed", "ignored"}
        assert {s.value for s in WebhookProcessingStatus} == valid


# ---------------------------------------------------------------------------
# ErrorLog
# ---------------------------------------------------------------------------

class TestErrorLogModel:
    def test_error_log_construction(self):
        log = ErrorLog(
            id=uuid.uuid4(),
            context="send_message",
            error_message="Connection refused",
        )
        assert log.details is None
        assert isinstance(log.id, uuid.UUID)

    def test_error_log_with_details(self):
        log = ErrorLog(
            id=uuid.uuid4(),
            context="webhook_processing",
            error_message="Invalid payload",
            details={"code": 400, "raw": "bad data"},
        )
        assert log.details["code"] == 400

    def test_error_log_repr(self):
        log = ErrorLog(
            id=uuid.uuid4(),
            context="ctx",
            error_message="err",
        )
        assert "ctx" in repr(log)
