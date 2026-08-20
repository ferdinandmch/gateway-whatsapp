import pytest
import respx
import httpx

from app.providers.evolution.provider import EvolutionProvider

BASE_URL = "http://evolution-test"
API_KEY = "test-api-key"
WEBHOOK_BASE_URL = "http://backend-test:8000"
TIMEOUT = 5


@pytest.fixture
def provider() -> EvolutionProvider:
    return EvolutionProvider(
        base_url=BASE_URL,
        api_key=API_KEY,
        webhook_base_url=WEBHOOK_BASE_URL,
        timeout=TIMEOUT,
    )


@pytest.fixture
def mock_evolution():
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as mock:
        yield mock
