import pytest


@pytest.mark.asyncio
async def test_health_returns_200(async_client):
    response = await async_client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_response_body(async_client):
    response = await async_client.get("/health")
    data = response.json()
    assert data == {"status": "ok", "service": "whatsapp-gateway", "version": "0.1.0"}


@pytest.mark.asyncio
async def test_health_no_auth_required(async_client):
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert "WWW-Authenticate" not in response.headers
    assert "Authorization" not in response.headers
