"""Unit tests for InstanceService."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.instance import CONNECTABLE_STATUSES, Instance, InstanceStatus
from app.schemas.instance import InstanceCreateRequest, InstanceUpdateRequest
from app.schemas.provider import ProviderError, ProviderResult


def make_client(is_active: bool = True):
    client = MagicMock()
    client.id = uuid.uuid4()
    client.is_active = is_active
    return client


def make_instance(
    client_id=None,
    status=InstanceStatus.created,
    provider_instance_id="inst_abc12345",
    display_name="Test",
    deleted_at=None,
):
    inst = MagicMock(spec=Instance)
    inst.id = uuid.uuid4()
    inst.client_id = client_id or uuid.uuid4()
    inst.status = status
    inst.provider_instance_id = provider_instance_id
    inst.display_name = display_name
    inst.phone_number = None
    inst.provider = "evolution"
    inst.n8n_webhook_url = None
    inst.webhook_enabled = True
    inst.deleted_at = deleted_at
    inst.created_at = datetime.now(timezone.utc)
    inst.updated_at = datetime.now(timezone.utc)
    return inst


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
    from app.services.instance_service import InstanceService
    return InstanceService(db=mock_db, provider=mock_provider)


# --- create_instance ---

class TestCreateInstance:
    async def test_create_success(self, service, mock_db, mock_provider):
        client = make_client()
        data = InstanceCreateRequest(display_name="Meu WhatsApp")

        # count returns 0
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0

        # refresh sets provider_instance_id, id and timestamps (simulates DB flush)
        async def fake_refresh(inst):
            inst.provider_instance_id = "inst_abc12345"
            inst.id = uuid.uuid4()
            inst.created_at = datetime.now(timezone.utc)
            inst.updated_at = datetime.now(timezone.utc)
        mock_db.refresh.side_effect = fake_refresh
        mock_db.execute.return_value = count_result

        mock_provider.create_instance.return_value = ProviderResult(success=True, data={"instance_name": "inst_abc12345"})

        result = await service.create_instance(client, data)
        assert result.display_name == "Meu WhatsApp"
        mock_provider.create_instance.assert_called_once()
        mock_db.commit.assert_called_once()

    async def test_create_limit_reached(self, service, mock_db, mock_provider):
        from fastapi import HTTPException
        client = make_client()
        data = InstanceCreateRequest(display_name="Excess")

        count_result = MagicMock()
        count_result.scalar_one.return_value = 10
        mock_db.execute.return_value = count_result

        with pytest.raises(HTTPException) as exc_info:
            await service.create_instance(client, data)
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["code"] == "INSTANCE_LIMIT_REACHED"

    async def test_create_provider_error_sets_error_status(self, service, mock_db, mock_provider):
        from fastapi import HTTPException
        client = make_client()
        data = InstanceCreateRequest(display_name="Test")

        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        mock_db.execute.return_value = count_result

        mock_provider.create_instance.return_value = ProviderResult(
            success=False,
            error=ProviderError(code="PROVIDER_ERROR", message="fail"),
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.create_instance(client, data)
        assert exc_info.value.status_code == 502
        assert exc_info.value.detail["code"] == "PROVIDER_ERROR"
        mock_db.commit.assert_called_once()


# --- connect_instance ---

class TestConnectInstance:
    async def test_connect_success(self, service, mock_db, mock_provider):
        client = make_client()
        instance = make_instance(client_id=client.id, status=InstanceStatus.created)

        scalar_result = MagicMock()
        scalar_result.scalar_one_or_none.return_value = instance
        mock_db.execute.return_value = scalar_result

        mock_provider.connect_instance.return_value = ProviderResult(
            success=True,
            data={"qrcode": "base64qr", "pairingCode": None},
        )

        result = await service.connect_instance(instance.id, client)
        assert result.status == InstanceStatus.connecting
        assert result.qr_code == "base64qr"

    async def test_connect_wrong_status_raises(self, service, mock_db, mock_provider):
        from fastapi import HTTPException
        client = make_client()
        instance = make_instance(client_id=client.id, status=InstanceStatus.connected)

        scalar_result = MagicMock()
        scalar_result.scalar_one_or_none.return_value = instance
        mock_db.execute.return_value = scalar_result

        with pytest.raises(HTTPException) as exc_info:
            await service.connect_instance(instance.id, client)
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["code"] == "INSTANCE_NOT_CONNECTABLE"

    async def test_connect_all_connectable_statuses(self, service, mock_db, mock_provider):
        client = make_client()
        mock_provider.connect_instance.return_value = ProviderResult(
            success=True, data={"qrcode": "qr"}
        )
        for status in CONNECTABLE_STATUSES:
            instance = make_instance(client_id=client.id, status=status)
            scalar_result = MagicMock()
            scalar_result.scalar_one_or_none.return_value = instance
            mock_db.execute.return_value = scalar_result
            result = await service.connect_instance(instance.id, client)
            assert result.status == InstanceStatus.connecting


# --- disconnect_instance ---

class TestDisconnectInstance:
    async def test_disconnect_already_disconnected_idempotent(self, service, mock_db, mock_provider):
        client = make_client()
        instance = make_instance(client_id=client.id, status=InstanceStatus.disconnected)

        scalar_result = MagicMock()
        scalar_result.scalar_one_or_none.return_value = instance
        mock_db.execute.return_value = scalar_result

        result = await service.disconnect_instance(instance.id, client)
        assert result.status == InstanceStatus.disconnected
        mock_provider.disconnect_instance.assert_not_called()

    async def test_disconnect_connected(self, service, mock_db, mock_provider):
        client = make_client()
        instance = make_instance(client_id=client.id, status=InstanceStatus.connected)

        scalar_result = MagicMock()
        scalar_result.scalar_one_or_none.return_value = instance
        mock_db.execute.return_value = scalar_result
        mock_provider.disconnect_instance.return_value = ProviderResult(success=True)

        async def fake_refresh(inst):
            inst.status = InstanceStatus.disconnected
            inst.updated_at = datetime.now(timezone.utc)
        mock_db.refresh.side_effect = fake_refresh

        result = await service.disconnect_instance(instance.id, client)
        assert result.status == InstanceStatus.disconnected


# --- delete_instance ---

class TestDeleteInstance:
    async def test_delete_success(self, service, mock_db, mock_provider):
        client = make_client()
        instance = make_instance(client_id=client.id, status=InstanceStatus.connected)

        scalar_result = MagicMock()
        scalar_result.scalar_one_or_none.return_value = instance
        mock_db.execute.return_value = scalar_result
        mock_provider.delete_instance.return_value = ProviderResult(success=True)

        result = await service.delete_instance(instance.id, client)
        assert result.status == InstanceStatus.removed


# --- list_instances ---

class TestListInstances:
    async def test_list_returns_items(self, service, mock_db, mock_provider):
        client = make_client()
        instances = [make_instance(client_id=client.id) for _ in range(3)]

        call_count = 0

        async def fake_execute(query):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.scalar_one.return_value = 3
            else:
                result.scalars.return_value.all.return_value = instances
            return result

        mock_db.execute.side_effect = fake_execute

        result = await service.list_instances(client)
        assert result.total == 3
        assert len(result.items) == 3

    async def test_list_empty(self, service, mock_db, mock_provider):
        client = make_client()
        call_count = 0

        async def fake_execute(query):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.scalar_one.return_value = 0
            else:
                result.scalars.return_value.all.return_value = []
            return result

        mock_db.execute.side_effect = fake_execute

        result = await service.list_instances(client)
        assert result.total == 0
        assert result.items == []


# --- update_instance ---

class TestUpdateInstance:
    async def test_update_display_name(self, service, mock_db, mock_provider):
        client = make_client()
        instance = make_instance(client_id=client.id)

        scalar_result = MagicMock()
        scalar_result.scalar_one_or_none.return_value = instance
        mock_db.execute.return_value = scalar_result

        async def fake_refresh(inst):
            pass
        mock_db.refresh.side_effect = fake_refresh

        data = InstanceUpdateRequest(display_name="Novo Nome")
        result = await service.update_instance(instance.id, client, data)
        assert instance.display_name == "Novo Nome"


# --- update_status_from_webhook ---

class TestUpdateStatusFromWebhook:
    async def test_update_status_found(self, service, mock_db, mock_provider):
        instance = make_instance(status=InstanceStatus.connecting)
        scalar_result = MagicMock()
        scalar_result.scalar_one_or_none.return_value = instance
        mock_db.execute.return_value = scalar_result

        result = await service.update_status_from_webhook("inst_abc12345", InstanceStatus.connected, "5586999999999")
        assert result is True
        assert instance.status == InstanceStatus.connected
        assert instance.phone_number == "5586999999999"

    async def test_update_status_not_found(self, service, mock_db, mock_provider):
        scalar_result = MagicMock()
        scalar_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = scalar_result

        result = await service.update_status_from_webhook("inst_unknown", InstanceStatus.connected)
        assert result is False


# --- _count_active_instances limit ---

class TestInstanceLimit:
    async def test_limit_is_10(self):
        from app.services.instance_service import MAX_INSTANCES_PER_CLIENT
        assert MAX_INSTANCES_PER_CLIENT == 10
