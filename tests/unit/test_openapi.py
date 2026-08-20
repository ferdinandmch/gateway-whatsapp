import pytest


@pytest.mark.asyncio
async def test_docs_returns_200(async_client):
    response = await async_client.get("/docs")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_openapi_json_contains_health_path(async_client):
    response = await async_client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "/health" in schema["paths"]


@pytest.mark.asyncio
async def test_openapi_schema_title_and_version(async_client):
    response = await async_client.get("/openapi.json")
    schema = response.json()
    assert schema["info"]["title"] == "WhatsApp Gateway"
    assert schema["info"]["version"] == "0.1.0"
