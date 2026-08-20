"""Testes unitários do forward_to_n8n (spec 007)."""
import pytest
import respx
import httpx

from app.webhooks.forwarder import ForwardResult, forward_to_n8n


_PAYLOAD = {"event_type": "message.received", "content": "Olá"}
_URL = "http://n8n.test/webhook/abc"


# ---------------------------------------------------------------------------
# T008 — Sucesso (HTTP 200)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@respx.mock
async def test_forward_success(mock_env):
    respx.post(_URL).mock(return_value=httpx.Response(200, json={"ok": True}))
    result = await forward_to_n8n(_URL, _PAYLOAD)
    assert result.success is True
    assert result.status_code == 200


# ---------------------------------------------------------------------------
# T009 — Timeout
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@respx.mock
async def test_forward_timeout(mock_env):
    respx.post(_URL).mock(side_effect=httpx.TimeoutException("timeout"))
    result = await forward_to_n8n(_URL, _PAYLOAD)
    assert result.success is False
    assert result.status_code is None
    assert result.response == {"error": "timeout"}


# ---------------------------------------------------------------------------
# T010 — Erro HTTP 500
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@respx.mock
async def test_forward_http_500(mock_env):
    respx.post(_URL).mock(return_value=httpx.Response(500, json={"error": "internal"}))
    result = await forward_to_n8n(_URL, _PAYLOAD)
    assert result.success is False
    assert result.status_code == 500


# ---------------------------------------------------------------------------
# T011 — URL inválida (sem scheme)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_forward_invalid_url_no_scheme(mock_env):
    result = await forward_to_n8n("n8n.test/webhook/abc", _PAYLOAD)
    assert result.success is False
    assert result.status_code is None
    assert result.response == {"error": "invalid_url"}


@pytest.mark.asyncio
async def test_forward_invalid_url_ftp_scheme(mock_env):
    result = await forward_to_n8n("ftp://n8n.test/webhook/abc", _PAYLOAD)
    assert result.success is False
    assert result.response == {"error": "invalid_url"}


@pytest.mark.asyncio
async def test_forward_invalid_url_empty(mock_env):
    result = await forward_to_n8n("", _PAYLOAD)
    assert result.success is False
    assert result.response == {"error": "invalid_url"}


# ---------------------------------------------------------------------------
# T012 — Connection error
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@respx.mock
async def test_forward_connection_error(mock_env):
    respx.post(_URL).mock(side_effect=httpx.ConnectError("refused"))
    result = await forward_to_n8n(_URL, _PAYLOAD)
    assert result.success is False
    assert result.status_code is None


# ---------------------------------------------------------------------------
# T013 — Resposta 2xx não-200 (ex: 201) também é sucesso
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@respx.mock
async def test_forward_2xx_non_200_is_success(mock_env):
    respx.post(_URL).mock(return_value=httpx.Response(201, json={"created": True}))
    result = await forward_to_n8n(_URL, _PAYLOAD)
    assert result.success is True
    assert result.status_code == 201


# ---------------------------------------------------------------------------
# T013b — Payload grande (~50 KB)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@respx.mock
async def test_forward_large_payload(mock_env):
    large_payload = {"event_type": "message.received", "content": "x" * 50_000}
    respx.post(_URL).mock(return_value=httpx.Response(200, json={"ok": True}))
    result = await forward_to_n8n(_URL, large_payload)
    assert result.success is True
    assert result.status_code == 200
