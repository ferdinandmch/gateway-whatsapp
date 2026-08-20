"""Integration tests for models against a real PostgreSQL database.

Requires TEST_DATABASE_URL env var (postgresql+asyncpg://...).
Run with: TEST_DATABASE_URL=... uv run pytest tests/integration/ -v
"""
import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select, text

from app.models.client import Client
from app.models.error_log import ErrorLog
from app.models.instance import Instance, InstanceStatus
from app.models.message import Message, MessageContentType, MessageDirection
from app.models.webhook_event import WebhookEvent, WebhookProcessingStatus


# T025: Client → Instance → Message chain with FK constraints
@pytest.mark.asyncio
async def test_client_instance_message_chain(db_session):
    client = Client(name="Integration Test Client")
    db_session.add(client)
    await db_session.flush()

    instance = Instance(client_id=client.id, name="test-instance")
    db_session.add(instance)
    await db_session.flush()

    message = Message(
        instance_id=instance.id,
        direction=MessageDirection.outbound,
        content_type=MessageContentType.text,
        body="Hello integration",
        remote_jid="5511999999999@s.whatsapp.net",
    )
    db_session.add(message)
    await db_session.flush()

    result = await db_session.execute(
        select(Message).where(Message.instance_id == instance.id)
    )
    msgs = result.scalars().all()
    assert len(msgs) == 1
    assert msgs[0].body == "Hello integration"
    assert msgs[0].direction == MessageDirection.outbound


# T026: Soft-delete behavior — deleted_at set but record still queryable
@pytest.mark.asyncio
async def test_soft_delete_preserves_record(db_session):
    client = Client(name="Soft Delete Client")
    db_session.add(client)
    await db_session.flush()

    client.deleted_at = datetime.now(timezone.utc)
    await db_session.flush()

    # Record still exists in DB
    result = await db_session.execute(
        select(Client).where(Client.id == client.id)
    )
    found = result.scalar_one_or_none()
    assert found is not None
    assert found.deleted_at is not None

    # Active-only query excludes it
    result_active = await db_session.execute(
        select(Client).where(Client.deleted_at.is_(None))
    )
    active_ids = [c.id for c in result_active.scalars().all()]
    assert client.id not in active_ids


# T027: Client isolation — instances scoped to client_id
@pytest.mark.asyncio
async def test_client_isolation(db_session):
    client_a = Client(name="Client A")
    client_b = Client(name="Client B")
    db_session.add_all([client_a, client_b])
    await db_session.flush()

    inst_a = Instance(client_id=client_a.id, name="instance-a")
    inst_b = Instance(client_id=client_b.id, name="instance-b")
    db_session.add_all([inst_a, inst_b])
    await db_session.flush()

    result = await db_session.execute(
        select(Instance).where(Instance.client_id == client_a.id)
    )
    instances_a = result.scalars().all()
    ids = [i.id for i in instances_a]
    assert inst_a.id in ids
    assert inst_b.id not in ids


# ErrorLog persistido no banco (FR-005, US4)
@pytest.mark.asyncio
async def test_error_log_persisted(db_session):
    log = ErrorLog(
        id=uuid.uuid4(),
        context="send_message",
        error_message="Connection refused",
        details={"code": 503, "provider": "evolution"},
    )
    db_session.add(log)
    await db_session.flush()

    result = await db_session.execute(
        select(ErrorLog).where(ErrorLog.id == log.id)
    )
    found = result.scalar_one()
    assert found.context == "send_message"
    assert found.details["code"] == 503


# Instance soft-delete (FR-002, clarification)
@pytest.mark.asyncio
async def test_instance_soft_delete(db_session):
    client = Client(id=uuid.uuid4(), name="Soft Delete Instance Client", is_active=True)
    db_session.add(client)
    await db_session.flush()

    instance = Instance(
        id=uuid.uuid4(),
        client_id=client.id,
        name="to-be-deleted",
        status=InstanceStatus.disconnected,
    )
    db_session.add(instance)
    await db_session.flush()

    instance.deleted_at = datetime.now(timezone.utc)
    await db_session.flush()

    # Record still exists
    result = await db_session.execute(
        select(Instance).where(Instance.id == instance.id)
    )
    found = result.scalar_one_or_none()
    assert found is not None
    assert found.deleted_at is not None

    # Active-only query excludes it
    result_active = await db_session.execute(
        select(Instance).where(
            Instance.client_id == client.id,
            Instance.deleted_at.is_(None),
        )
    )
    active_ids = [i.id for i in result_active.scalars().all()]
    assert instance.id not in active_ids


# WebhookEvent filtrado por instance_id e event_type (US4 acceptance scenario 2)
@pytest.mark.asyncio
async def test_webhook_event_filter_by_instance_and_type(db_session):
    client = Client(id=uuid.uuid4(), name="Webhook Filter Client", is_active=True)
    db_session.add(client)
    await db_session.flush()

    instance = Instance(
        id=uuid.uuid4(),
        client_id=client.id,
        name="webhook-instance",
        status=InstanceStatus.connected,
    )
    db_session.add(instance)
    await db_session.flush()

    e1 = WebhookEvent(
        id=uuid.uuid4(),
        instance_id=instance.id,
        event_type="message.received",
        raw_payload={"msg": "hello"},
        processing_status=WebhookProcessingStatus.received,
    )
    e2 = WebhookEvent(
        id=uuid.uuid4(),
        instance_id=instance.id,
        event_type="connection.update",
        raw_payload={"status": "open"},
        processing_status=WebhookProcessingStatus.received,
    )
    e3 = WebhookEvent(
        id=uuid.uuid4(),
        instance_id=None,
        event_type="message.received",
        raw_payload={"msg": "other"},
        processing_status=WebhookProcessingStatus.received,
    )
    db_session.add_all([e1, e2, e3])
    await db_session.flush()

    # Filter by instance_id
    result = await db_session.execute(
        select(WebhookEvent).where(WebhookEvent.instance_id == instance.id)
    )
    instance_events = result.scalars().all()
    ids = [e.id for e in instance_events]
    assert e1.id in ids
    assert e2.id in ids
    assert e3.id not in ids  # e3 has no instance_id

    # Filter by event_type
    result_type = await db_session.execute(
        select(WebhookEvent).where(
            WebhookEvent.instance_id == instance.id,
            WebhookEvent.event_type == "message.received",
        )
    )
    typed_events = result_type.scalars().all()
    assert len(typed_events) == 1
    assert typed_events[0].id == e1.id


# Bonus: Webhook event with large JSONB payload (SC-004)
@pytest.mark.asyncio
async def test_webhook_event_large_payload(db_session):
    large_value = "x" * (1024 * 1024)  # 1MB
    event = WebhookEvent(
        event_type="message.received",
        raw_payload={"data": large_value},
    )
    db_session.add(event)
    await db_session.flush()

    result = await db_session.execute(
        select(WebhookEvent).where(WebhookEvent.id == event.id)
    )
    found = result.scalar_one()
    assert len(found.raw_payload["data"]) == 1024 * 1024
