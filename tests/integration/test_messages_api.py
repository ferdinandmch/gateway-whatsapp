"""Integration tests for message sending endpoints."""
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.models.instance import InstanceStatus
from app.models.message import Message, MessageContentType, MessageDirection
from app.schemas.provider import ProviderError, ProviderResult

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

RAW_API_KEY = "zapi_msgtestkey"


def make_mock_client():
    client = MagicMock()
    client.id = uuid.uuid4()
    client.is_active = True
    client.deleted_at = None
    return client


def make_mock_instance(client_id, status=InstanceStatus.connected):
    inst = MagicMock()
    inst.id = uuid.uuid4()
    inst.client_id = client_id
    inst.display_name = "Test Instance"
    inst.provider = "evolution"
    inst.provider_instance_id = "inst_abc12345"
    inst.status = status
    inst.phone_number = None
    inst.n8n_webhook_url = None
    inst.webhook_enabled = True
    inst.created_at = datetime.now(timezone.utc)
    inst.updated_at = datetime.now(timezone.utc)
    inst.deleted_at = None
    return inst


def make_mock_message(instance_id, content_type=MessageContentType.text):
    msg = MagicMock(spec=Message)
    msg.id = uuid.uuid4()
    msg.instance_id = instance_id
    msg.direction = MessageDirection.outbound
    msg.content_type = content_type
    msg.body = None
    msg.remote_jid = "5586999999999@s.whatsapp.net"
    msg.status = "sent"
    msg.provider_message_id = "BAE5TEST"
    msg.media_url = None
    msg.filename = None
    msg.raw_payload = {"provider_message_id": "BAE5TEST"}
    msg.created_at = datetime.now(timezone.utc)
    return msg


@pytest.fixture
def mock_env(monkeypatch):
    for key, value in VALID_ENV.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
async def app_with_overrides(mock_env):
    """App fixture with DB and provider mocked; auth override is set per-test."""
    from app.main import create_app
    from app.core import dependencies

    _current_client_holder = [None]

    async def override_get_current_client():
        if _current_client_holder[0] is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": "Missing API key", "details": {}})
        return _current_client_holder[0]

    async def override_get_db():
        yield AsyncMock()

    def override_get_provider():
        return AsyncMock()

    app = create_app()
    app.dependency_overrides[dependencies.get_current_client] = override_get_current_client
    app.dependency_overrides[dependencies.get_db] = override_get_db
    app.dependency_overrides[dependencies.get_provider] = override_get_provider

    return app, _current_client_holder


@pytest.fixture
async def client(app_with_overrides):
    app, _ = app_with_overrides
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@contextmanager
def set_auth(app_with_overrides, mock_client_obj):
    _, holder = app_with_overrides
    holder[0] = mock_client_obj
    try:
        yield
    finally:
        holder[0] = None


def patch_service(mock_service):
    return patch(
        "app.api.v1.routes.messages.MessageService",
        return_value=mock_service,
    )


# ── POST /v1/messages/text ────────────────────────────────────────────────────

class TestSendTextEndpoint:
    @pytest.mark.asyncio
    async def test_send_text_success(self, client, app_with_overrides):
        mock_client = make_mock_client()
        instance = make_mock_instance(mock_client.id)
        message = make_mock_message(instance.id, MessageContentType.text)

        mock_service = AsyncMock()
        from app.schemas.message import MessageResponse
        mock_service.send_text.return_value = MessageResponse(
            message_id=message.id,
            instance_id=instance.id,
            direction="outbound",
            message_type="text",
            to="86999999999",
            status="sent",
            provider_message_id="BAE5TEST",
            created_at=message.created_at,
        )

        with set_auth(app_with_overrides, mock_client), patch_service(mock_service):
            resp = await client.post(
                "/v1/messages/text",
                json={"instance_id": str(instance.id), "to": "86999999999", "message": "Olá"},
                headers={"X-API-Key": RAW_API_KEY},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "sent"
        assert data["message_type"] == "text"
        assert data["direction"] == "outbound"

    @pytest.mark.asyncio
    async def test_send_text_missing_api_key(self, client):
        resp = await client.post(
            "/v1/messages/text",
            json={"instance_id": str(uuid.uuid4()), "to": "86999999999", "message": "Olá"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_send_text_missing_message_field(self, client, app_with_overrides):
        mock_client = make_mock_client()
        with set_auth(app_with_overrides, mock_client):
            resp = await client.post(
                "/v1/messages/text",
                json={"instance_id": str(uuid.uuid4()), "to": "86999999999"},
                headers={"X-API-Key": RAW_API_KEY},
            )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_send_text_instance_disconnected(self, client, app_with_overrides):
        mock_client = make_mock_client()

        mock_service = AsyncMock()
        mock_service.send_text.side_effect = __import__("fastapi").HTTPException(
            status_code=409,
            detail={"code": "INSTANCE_DISCONNECTED", "message": "A instância não está conectada.", "details": {}},
        )

        with set_auth(app_with_overrides, mock_client), patch_service(mock_service):
            resp = await client.post(
                "/v1/messages/text",
                json={"instance_id": str(uuid.uuid4()), "to": "86999999999", "message": "Olá"},
                headers={"X-API-Key": RAW_API_KEY},
            )
        assert resp.status_code == 409
        assert resp.json()["detail"]["code"] == "INSTANCE_DISCONNECTED"


# ── POST /v1/messages/image ───────────────────────────────────────────────────

class TestSendImageEndpoint:
    @pytest.mark.asyncio
    async def test_send_image_success(self, client, app_with_overrides):
        mock_client = make_mock_client()
        instance = make_mock_instance(mock_client.id)
        message = make_mock_message(instance.id, MessageContentType.image)

        mock_service = AsyncMock()
        from app.schemas.message import MessageResponse
        mock_service.send_media.return_value = MessageResponse(
            message_id=message.id,
            instance_id=instance.id,
            direction="outbound",
            message_type="image",
            to="86999999999",
            status="sent",
            media_url="https://example.com/img.jpg",
            provider_message_id="BAE5IMG",
            created_at=message.created_at,
        )

        with set_auth(app_with_overrides, mock_client), patch_service(mock_service):
            resp = await client.post(
                "/v1/messages/image",
                json={
                    "instance_id": str(instance.id),
                    "to": "86999999999",
                    "media_url": "https://example.com/img.jpg",
                    "caption": "Test image",
                },
                headers={"X-API-Key": RAW_API_KEY},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["message_type"] == "image"
        assert data["media_url"] == "https://example.com/img.jpg"

    @pytest.mark.asyncio
    async def test_send_image_missing_media_url(self, client, app_with_overrides):
        mock_client = make_mock_client()
        with set_auth(app_with_overrides, mock_client):
            resp = await client.post(
                "/v1/messages/image",
                json={"instance_id": str(uuid.uuid4()), "to": "86999999999"},
                headers={"X-API-Key": RAW_API_KEY},
            )
        assert resp.status_code == 422


# ── POST /v1/messages/audio, /document, /video ───────────────────────────────

class TestSendOtherMediaEndpoints:
    @pytest.mark.asyncio
    async def test_send_audio_success(self, client, app_with_overrides):
        mock_client = make_mock_client()
        instance = make_mock_instance(mock_client.id)
        message = make_mock_message(instance.id, MessageContentType.audio)

        mock_service = AsyncMock()
        from app.schemas.message import MessageResponse
        mock_service.send_media.return_value = MessageResponse(
            message_id=message.id,
            instance_id=instance.id,
            direction="outbound",
            message_type="audio",
            to="86999999999",
            status="sent",
            media_url="https://example.com/audio.mp3",
            created_at=message.created_at,
        )

        with set_auth(app_with_overrides, mock_client), patch_service(mock_service):
            resp = await client.post(
                "/v1/messages/audio",
                json={
                    "instance_id": str(instance.id),
                    "to": "86999999999",
                    "media_url": "https://example.com/audio.mp3",
                },
                headers={"X-API-Key": RAW_API_KEY},
            )

        assert resp.status_code == 200
        assert resp.json()["message_type"] == "audio"

    @pytest.mark.asyncio
    async def test_send_document_success(self, client, app_with_overrides):
        mock_client = make_mock_client()
        instance = make_mock_instance(mock_client.id)
        message = make_mock_message(instance.id, MessageContentType.document)

        mock_service = AsyncMock()
        from app.schemas.message import MessageResponse
        mock_service.send_media.return_value = MessageResponse(
            message_id=message.id,
            instance_id=instance.id,
            direction="outbound",
            message_type="document",
            to="86999999999",
            status="sent",
            media_url="https://example.com/doc.pdf",
            filename="doc.pdf",
            created_at=message.created_at,
        )

        with set_auth(app_with_overrides, mock_client), patch_service(mock_service):
            resp = await client.post(
                "/v1/messages/document",
                json={
                    "instance_id": str(instance.id),
                    "to": "86999999999",
                    "media_url": "https://example.com/doc.pdf",
                    "filename": "doc.pdf",
                },
                headers={"X-API-Key": RAW_API_KEY},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["message_type"] == "document"
        assert data["filename"] == "doc.pdf"

    @pytest.mark.asyncio
    async def test_send_video_success(self, client, app_with_overrides):
        mock_client = make_mock_client()
        instance = make_mock_instance(mock_client.id)
        message = make_mock_message(instance.id, MessageContentType.video)

        mock_service = AsyncMock()
        from app.schemas.message import MessageResponse
        mock_service.send_media.return_value = MessageResponse(
            message_id=message.id,
            instance_id=instance.id,
            direction="outbound",
            message_type="video",
            to="86999999999",
            status="sent",
            media_url="https://example.com/video.mp4",
            created_at=message.created_at,
        )

        with set_auth(app_with_overrides, mock_client), patch_service(mock_service):
            resp = await client.post(
                "/v1/messages/video",
                json={
                    "instance_id": str(instance.id),
                    "to": "86999999999",
                    "media_url": "https://example.com/video.mp4",
                    "caption": "My video",
                },
                headers={"X-API-Key": RAW_API_KEY},
            )

        assert resp.status_code == 200
        assert resp.json()["message_type"] == "video"
