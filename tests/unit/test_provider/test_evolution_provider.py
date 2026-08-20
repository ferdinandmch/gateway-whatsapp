import pytest
import respx
import httpx

from app.providers.evolution.provider import EvolutionProvider
from app.schemas.provider import InstanceState, MessageType

BASE_URL = "http://evolution-test"
INSTANCE = "inst_abc12345"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _json_response(data: dict, status: int = 200) -> httpx.Response:
    return httpx.Response(status, json=data)


def _error_response(status: int) -> httpx.Response:
    return httpx.Response(status, json={"error": "error"})


# ---------------------------------------------------------------------------
# US1 — send_text
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_text_success(provider, mock_evolution):
    mock_evolution.post(f"/message/sendText/{INSTANCE}").mock(
        return_value=_json_response({"key": {"id": "msg-id-123"}})
    )
    result = await provider.send_text(INSTANCE, "86999999999", "Hello")

    assert result.success is True
    assert result.data["provider_message_id"] == "msg-id-123"

    # Verify normalized phone in outgoing payload
    last_request = mock_evolution.calls.last.request
    import json as _json
    payload = _json.loads(last_request.content)
    assert payload["number"] == "5586999999999@s.whatsapp.net"
    assert payload["text"] == "Hello"


@pytest.mark.asyncio
async def test_send_text_timeout(provider):
    with respx.mock() as mock:
        mock.post(f"{BASE_URL}/message/sendText/{INSTANCE}").mock(
            side_effect=httpx.TimeoutException("timeout")
        )
        result = await provider.send_text(INSTANCE, "86999999999", "Hello")

    assert result.success is False
    assert result.error.code == "PROVIDER_TIMEOUT"


@pytest.mark.asyncio
async def test_send_text_connection_error(provider):
    with respx.mock() as mock:
        mock.post(f"{BASE_URL}/message/sendText/{INSTANCE}").mock(
            side_effect=httpx.ConnectError("refused")
        )
        result = await provider.send_text(INSTANCE, "86999999999", "Hello")

    assert result.success is False
    assert result.error.code == "PROVIDER_UNAVAILABLE"


@pytest.mark.asyncio
async def test_send_text_500(provider, mock_evolution):
    mock_evolution.post(f"/message/sendText/{INSTANCE}").mock(return_value=_error_response(500))
    result = await provider.send_text(INSTANCE, "86999999999", "Hello")

    assert result.success is False
    assert result.error.code == "PROVIDER_ERROR"


@pytest.mark.asyncio
async def test_send_text_404_instance_not_found(provider, mock_evolution):
    mock_evolution.post(f"/message/sendText/{INSTANCE}").mock(return_value=_error_response(404))
    result = await provider.send_text(INSTANCE, "86999999999", "Hello")

    assert result.success is False
    assert result.error.code == "INSTANCE_NOT_FOUND"


@pytest.mark.asyncio
async def test_send_text_unexpected_response(provider, mock_evolution):
    mock_evolution.post(f"/message/sendText/{INSTANCE}").mock(
        return_value=httpx.Response(200, content=b"not-json{{{{")
    )
    result = await provider.send_text(INSTANCE, "86999999999", "Hello")

    assert result.success is False
    assert result.error.code == "UNEXPECTED_RESPONSE"


# ---------------------------------------------------------------------------
# US2 — send_media
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_media_image_with_caption(provider, mock_evolution):
    import json as _json
    mock_evolution.post(f"/message/sendMedia/{INSTANCE}").mock(
        return_value=_json_response({"key": {"id": "img-id-1"}})
    )
    result = await provider.send_media(
        INSTANCE, "86999999999", MessageType.image, "https://example.com/img.jpg", caption="Look!"
    )
    assert result.success is True
    assert result.data["provider_message_id"] == "img-id-1"

    payload = _json.loads(mock_evolution.calls.last.request.content)
    assert payload["number"] == "5586999999999@s.whatsapp.net"
    assert payload["mediatype"] == "image"
    assert payload["caption"] == "Look!"


@pytest.mark.asyncio
async def test_send_media_audio(provider, mock_evolution):
    import json as _json
    mock_evolution.post(f"/message/sendMedia/{INSTANCE}").mock(
        return_value=_json_response({"key": {"id": "aud-id-1"}})
    )
    result = await provider.send_media(
        INSTANCE, "86999999999", MessageType.audio, "https://example.com/audio.mp3"
    )
    assert result.success is True
    payload = _json.loads(mock_evolution.calls.last.request.content)
    assert payload["mediatype"] == "audio"
    assert "caption" not in payload


@pytest.mark.asyncio
async def test_send_media_document_with_filename(provider, mock_evolution):
    import json as _json
    mock_evolution.post(f"/message/sendMedia/{INSTANCE}").mock(
        return_value=_json_response({"key": {"id": "doc-id-1"}})
    )
    result = await provider.send_media(
        INSTANCE, "86999999999", MessageType.document,
        "https://example.com/doc.pdf", filename="report.pdf"
    )
    assert result.success is True
    payload = _json.loads(mock_evolution.calls.last.request.content)
    assert payload["mediatype"] == "document"
    assert payload["fileName"] == "report.pdf"


@pytest.mark.asyncio
async def test_send_media_video_with_caption(provider, mock_evolution):
    import json as _json
    mock_evolution.post(f"/message/sendMedia/{INSTANCE}").mock(
        return_value=_json_response({"key": {"id": "vid-id-1"}})
    )
    result = await provider.send_media(
        INSTANCE, "86999999999", MessageType.video,
        "https://example.com/video.mp4", caption="Watch this"
    )
    assert result.success is True
    payload = _json.loads(mock_evolution.calls.last.request.content)
    assert payload["mediatype"] == "video"
    assert payload["caption"] == "Watch this"


@pytest.mark.asyncio
async def test_send_media_timeout(provider):
    with respx.mock() as mock:
        mock.post(f"{BASE_URL}/message/sendMedia/{INSTANCE}").mock(
            side_effect=httpx.TimeoutException("timeout")
        )
        result = await provider.send_media(
            INSTANCE, "86999999999", MessageType.image, "https://example.com/img.jpg"
        )
    assert result.success is False
    assert result.error.code == "PROVIDER_TIMEOUT"


@pytest.mark.asyncio
async def test_send_media_400_invalid_request(provider, mock_evolution):
    mock_evolution.post(f"/message/sendMedia/{INSTANCE}").mock(return_value=_error_response(400))
    result = await provider.send_media(
        INSTANCE, "86999999999", MessageType.image, "https://bad-url"
    )
    assert result.success is False
    assert result.error.code == "INVALID_REQUEST"


# ---------------------------------------------------------------------------
# US3 — get_instance_status
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("raw_state,expected", [
    ("open", InstanceState.connected),
    ("close", InstanceState.disconnected),
    ("connecting", InstanceState.connecting),
    ("qrcode", InstanceState.connecting),
])
async def test_get_instance_status_maps_state(provider, mock_evolution, raw_state, expected):
    mock_evolution.get(f"/instance/connectionState/{INSTANCE}").mock(
        return_value=_json_response({"instance": {"state": raw_state}})
    )
    result = await provider.get_instance_status(INSTANCE)
    assert result.success is True
    assert result.data["state"] == expected


@pytest.mark.asyncio
async def test_get_instance_status_not_found(provider, mock_evolution):
    mock_evolution.get(f"/instance/connectionState/{INSTANCE}").mock(
        return_value=_error_response(404)
    )
    result = await provider.get_instance_status(INSTANCE)
    assert result.success is True
    assert result.data["state"] == InstanceState.not_found


@pytest.mark.asyncio
async def test_get_instance_status_500(provider, mock_evolution):
    mock_evolution.get(f"/instance/connectionState/{INSTANCE}").mock(
        return_value=_error_response(500)
    )
    result = await provider.get_instance_status(INSTANCE)
    assert result.success is False
    assert result.error.code == "PROVIDER_ERROR"


# ---------------------------------------------------------------------------
# US4 — create_instance
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_instance_success(provider, mock_evolution):
    mock_evolution.post("/instance/create").mock(
        return_value=_json_response({"instance": {"instanceName": INSTANCE}})
    )
    result = await provider.create_instance(INSTANCE)
    assert result.success is True
    assert result.data["instance_name"] == INSTANCE


@pytest.mark.asyncio
async def test_create_instance_webhook_url(provider, mock_evolution):
    import json as _json
    mock_evolution.post("/instance/create").mock(
        return_value=_json_response({"instance": {"instanceName": INSTANCE}})
    )
    await provider.create_instance(INSTANCE)
    payload = _json.loads(mock_evolution.calls.last.request.content)
    assert payload["webhook"] == f"http://backend-test:8000/v1/webhooks/evolution/{INSTANCE}"


@pytest.mark.asyncio
async def test_create_instance_already_exists(provider, mock_evolution):
    mock_evolution.post("/instance/create").mock(return_value=_error_response(409))
    result = await provider.create_instance(INSTANCE)
    assert result.success is False
    assert result.error.code == "INSTANCE_ALREADY_EXISTS"


# ---------------------------------------------------------------------------
# US5 — connect_instance / disconnect_instance
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_connect_instance_success(provider, mock_evolution):
    mock_evolution.get(f"/instance/connect/{INSTANCE}").mock(
        return_value=_json_response({"qrcode": "data:image/png;base64,abc", "pairingCode": None})
    )
    result = await provider.connect_instance(INSTANCE)
    assert result.success is True
    assert result.data["qrcode"] == "data:image/png;base64,abc"


@pytest.mark.asyncio
async def test_connect_instance_not_found(provider, mock_evolution):
    mock_evolution.get(f"/instance/connect/{INSTANCE}").mock(return_value=_error_response(404))
    result = await provider.connect_instance(INSTANCE)
    assert result.success is False
    assert result.error.code == "INSTANCE_NOT_FOUND"


@pytest.mark.asyncio
async def test_disconnect_instance_success(provider, mock_evolution):
    mock_evolution.delete(f"/instance/logout/{INSTANCE}").mock(
        return_value=_json_response({"instance": {"instanceName": INSTANCE}})
    )
    result = await provider.disconnect_instance(INSTANCE)
    assert result.success is True
    assert result.data["instance_name"] == INSTANCE


@pytest.mark.asyncio
async def test_disconnect_instance_not_found(provider, mock_evolution):
    mock_evolution.delete(f"/instance/logout/{INSTANCE}").mock(return_value=_error_response(404))
    result = await provider.disconnect_instance(INSTANCE)
    assert result.success is False
    assert result.error.code == "INSTANCE_NOT_FOUND"


# ---------------------------------------------------------------------------
# US6 — delete_instance
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_instance_success(provider, mock_evolution):
    mock_evolution.delete(f"/instance/delete/{INSTANCE}").mock(
        return_value=_json_response({"instance": {"instanceName": INSTANCE}})
    )
    result = await provider.delete_instance(INSTANCE)
    assert result.success is True
    assert result.data["instance_name"] == INSTANCE


@pytest.mark.asyncio
async def test_delete_instance_not_found(provider, mock_evolution):
    mock_evolution.delete(f"/instance/delete/{INSTANCE}").mock(return_value=_error_response(404))
    result = await provider.delete_instance(INSTANCE)
    assert result.success is False
    assert result.error.code == "INSTANCE_NOT_FOUND"
