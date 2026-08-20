"""Unit tests for MessageService."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, call

import pytest
from fastapi import HTTPException

from app.models.instance import Instance, InstanceStatus
from app.models.message import Message, MessageContentType, MessageDirection
from app.schemas.provider import MessageType, ProviderError, ProviderResult
from app.services.message_service import MessageService


def make_instance(status=InstanceStatus.connected, client_id=None):
    inst = MagicMock(spec=Instance)
    inst.id = uuid.uuid4()
    inst.client_id = client_id or uuid.uuid4()
    inst.status = status
    inst.provider_instance_id = "inst_abc12345"
    inst.deleted_at = None
    inst.created_at = datetime.now(timezone.utc)
    inst.updated_at = datetime.now(timezone.utc)
    return inst


def make_message(content_type=MessageContentType.text):
    msg = MagicMock(spec=Message)
    msg.id = uuid.uuid4()
    msg.instance_id = uuid.uuid4()
    msg.direction = MessageDirection.outbound
    msg.content_type = content_type
    msg.body = None
    msg.remote_jid = "5586999999999@s.whatsapp.net"
    msg.status = "pending"
    msg.provider_message_id = None
    msg.media_url = None
    msg.filename = None
    msg.raw_payload = None
    msg.created_at = datetime.now(timezone.utc)
    return msg


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def mock_provider():
    return AsyncMock()


@pytest.fixture
def service(mock_db, mock_provider):
    return MessageService(db=mock_db, provider=mock_provider)


def _mock_instance_query(mock_db, instance):
    result = MagicMock()
    result.scalar_one_or_none.return_value = instance
    mock_db.execute.return_value = result


def _mock_message_after_flush(mock_db, message):
    mock_db.refresh.side_effect = lambda obj: setattr(obj, "created_at", message.created_at)


# ── send_text ────────────────────────────────────────────────────────────────

class TestSendText:
    @pytest.mark.asyncio
    async def test_success(self, service, mock_db, mock_provider):
        client_id = uuid.uuid4()
        instance = make_instance(client_id=client_id)
        _mock_instance_query(mock_db, instance)

        mock_provider.send_text.return_value = ProviderResult(
            success=True, data={"provider_message_id": "BAE5ABC"}
        )

        # Simulate DB flush assigning an id to the message
        async def fake_flush():
            pass
        mock_db.flush.side_effect = fake_flush

        response = await service.send_text(
            client_id=client_id,
            instance_id=instance.id,
            to="86999999999",
            message_text="Olá",
        )

        mock_provider.send_text.assert_called_once()
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_instance_not_found(self, service, mock_db):
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result

        with pytest.raises(HTTPException) as exc_info:
            await service.send_text(
                client_id=uuid.uuid4(),
                instance_id=uuid.uuid4(),
                to="86999999999",
                message_text="Olá",
            )
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["code"] == "INSTANCE_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_instance_disconnected(self, service, mock_db):
        instance = make_instance(status=InstanceStatus.disconnected)
        _mock_instance_query(mock_db, instance)

        with pytest.raises(HTTPException) as exc_info:
            await service.send_text(
                client_id=instance.client_id,
                instance_id=instance.id,
                to="86999999999",
                message_text="Olá",
            )
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["code"] == "INSTANCE_DISCONNECTED"

    @pytest.mark.asyncio
    async def test_provider_failure(self, service, mock_db, mock_provider):
        instance = make_instance()
        _mock_instance_query(mock_db, instance)

        mock_provider.send_text.return_value = ProviderResult(
            success=False,
            error=ProviderError(code="PROVIDER_TIMEOUT", message="Timeout"),
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.send_text(
                client_id=instance.client_id,
                instance_id=instance.id,
                to="86999999999",
                message_text="Olá",
            )
        assert exc_info.value.status_code == 502
        assert exc_info.value.detail["code"] == "PROVIDER_ERROR"

    @pytest.mark.asyncio
    async def test_invalid_phone_too_short(self, service, mock_db):
        with pytest.raises(HTTPException) as exc_info:
            await service.send_text(
                client_id=uuid.uuid4(),
                instance_id=uuid.uuid4(),
                to="123",
                message_text="Olá",
            )
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_invalid_phone_with_letters(self, service, mock_db):
        with pytest.raises(HTTPException) as exc_info:
            await service.send_text(
                client_id=uuid.uuid4(),
                instance_id=uuid.uuid4(),
                to="abc-def-ghij",
                message_text="Olá",
            )
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "VALIDATION_ERROR"


# ── send_media (image) ────────────────────────────────────────────────────────

class TestSendMediaImage:
    @pytest.mark.asyncio
    async def test_success_with_caption(self, service, mock_db, mock_provider):
        instance = make_instance()
        _mock_instance_query(mock_db, instance)

        mock_provider.send_media.return_value = ProviderResult(
            success=True, data={"provider_message_id": "BAE5IMG"}
        )

        response = await service.send_media(
            client_id=instance.client_id,
            instance_id=instance.id,
            to="86999999999",
            media_type=MessageType.image,
            media_url="https://example.com/img.jpg",
            caption="My image",
        )

        mock_provider.send_media.assert_called_once()
        call_kwargs = mock_provider.send_media.call_args
        assert call_kwargs.kwargs.get("caption") == "My image" or "My image" in str(call_kwargs)

    @pytest.mark.asyncio
    async def test_success_without_caption(self, service, mock_db, mock_provider):
        instance = make_instance()
        _mock_instance_query(mock_db, instance)

        mock_provider.send_media.return_value = ProviderResult(
            success=True, data={"provider_message_id": "BAE5IMG2"}
        )

        await service.send_media(
            client_id=instance.client_id,
            instance_id=instance.id,
            to="86999999999",
            media_type=MessageType.image,
            media_url="https://example.com/img.jpg",
        )

        mock_provider.send_media.assert_called_once()

    @pytest.mark.asyncio
    async def test_provider_failure_for_media(self, service, mock_db, mock_provider):
        instance = make_instance()
        _mock_instance_query(mock_db, instance)

        mock_provider.send_media.return_value = ProviderResult(
            success=False,
            error=ProviderError(code="PROVIDER_ERROR", message="Media error"),
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.send_media(
                client_id=instance.client_id,
                instance_id=instance.id,
                to="86999999999",
                media_type=MessageType.image,
                media_url="https://example.com/img.jpg",
            )
        assert exc_info.value.status_code == 502


# ── send_media (audio, document, video) ──────────────────────────────────────

class TestSendMediaOtherTypes:
    @pytest.mark.asyncio
    async def test_audio_without_caption(self, service, mock_db, mock_provider):
        instance = make_instance()
        _mock_instance_query(mock_db, instance)

        mock_provider.send_media.return_value = ProviderResult(
            success=True, data={"provider_message_id": "BAE5AUD"}
        )

        await service.send_media(
            client_id=instance.client_id,
            instance_id=instance.id,
            to="86999999999",
            media_type=MessageType.audio,
            media_url="https://example.com/audio.mp3",
        )

        call_kwargs = mock_provider.send_media.call_args
        assert call_kwargs.kwargs.get("media_type") == MessageType.audio or MessageType.audio in str(call_kwargs)

    @pytest.mark.asyncio
    async def test_document_with_filename(self, service, mock_db, mock_provider):
        instance = make_instance()
        _mock_instance_query(mock_db, instance)

        mock_provider.send_media.return_value = ProviderResult(
            success=True, data={"provider_message_id": "BAE5DOC"}
        )

        await service.send_media(
            client_id=instance.client_id,
            instance_id=instance.id,
            to="86999999999",
            media_type=MessageType.document,
            media_url="https://example.com/doc.pdf",
            filename="doc.pdf",
        )

        call_kwargs = mock_provider.send_media.call_args
        assert call_kwargs.kwargs.get("filename") == "doc.pdf" or "doc.pdf" in str(call_kwargs)

    @pytest.mark.asyncio
    async def test_video_with_caption(self, service, mock_db, mock_provider):
        instance = make_instance()
        _mock_instance_query(mock_db, instance)

        mock_provider.send_media.return_value = ProviderResult(
            success=True, data={"provider_message_id": "BAE5VID"}
        )

        await service.send_media(
            client_id=instance.client_id,
            instance_id=instance.id,
            to="86999999999",
            media_type=MessageType.video,
            media_url="https://example.com/video.mp4",
            caption="My video",
        )

        mock_provider.send_media.assert_called_once()


# ── _record_message fields (US4) ─────────────────────────────────────────────

class TestRecordMessage:
    @pytest.mark.asyncio
    async def test_stores_all_required_fields(self, service, mock_db):
        instance_id = uuid.uuid4()
        added_objects = []
        mock_db.add.side_effect = lambda obj: added_objects.append(obj)

        await service._record_message(
            instance_id=instance_id,
            content_type=MessageContentType.text,
            remote_jid="5586999999999@s.whatsapp.net",
            body="Hello",
            media_url=None,
            filename=None,
        )

        assert len(added_objects) == 1
        msg = added_objects[0]
        assert msg.instance_id == instance_id
        assert msg.direction == MessageDirection.outbound
        assert msg.content_type == MessageContentType.text
        assert msg.body == "Hello"
        assert msg.remote_jid == "5586999999999@s.whatsapp.net"
        assert msg.status == "pending"
        assert msg.media_url is None
        assert msg.filename is None

    @pytest.mark.asyncio
    async def test_stores_media_fields(self, service, mock_db):
        added_objects = []
        mock_db.add.side_effect = lambda obj: added_objects.append(obj)

        await service._record_message(
            instance_id=uuid.uuid4(),
            content_type=MessageContentType.document,
            remote_jid="5586999999999@s.whatsapp.net",
            body="Caption",
            media_url="https://example.com/doc.pdf",
            filename="doc.pdf",
        )

        msg = added_objects[0]
        assert msg.media_url == "https://example.com/doc.pdf"
        assert msg.filename == "doc.pdf"
        assert msg.body == "Caption"


# ── _handle_send_result (US4) ─────────────────────────────────────────────────

class TestHandleSendResult:
    @pytest.mark.asyncio
    async def test_success_stores_raw_payload(self, service, mock_db):
        msg = MagicMock(spec=Message)
        msg.id = uuid.uuid4()

        result = ProviderResult(
            success=True,
            data={"provider_message_id": "BAE5XYZ", "extra": "data"},
        )

        await service._handle_send_result(msg, result, uuid.uuid4())

        assert msg.status == "sent"
        assert msg.provider_message_id == "BAE5XYZ"
        assert msg.raw_payload == {"provider_message_id": "BAE5XYZ", "extra": "data"}

    @pytest.mark.asyncio
    async def test_failure_creates_error_log(self, service, mock_db):
        instance_id = uuid.uuid4()
        msg = MagicMock(spec=Message)
        msg.id = uuid.uuid4()

        added_objects = []
        mock_db.add.side_effect = lambda obj: added_objects.append(obj)

        result = ProviderResult(
            success=False,
            error=ProviderError(code="PROVIDER_TIMEOUT", message="Timeout"),
        )

        await service._handle_send_result(msg, result, instance_id)

        assert msg.status == "failed"
        error_logs = [o for o in added_objects if hasattr(o, "context")]
        assert len(error_logs) == 1
        error_log = error_logs[0]
        assert error_log.context == "message.send_failed"
        assert str(instance_id) in str(error_log.details)
        assert str(msg.id) in str(error_log.details)
