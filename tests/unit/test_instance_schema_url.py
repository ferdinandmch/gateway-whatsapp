"""Testes de validação de n8n_webhook_url e N8N_FORWARD_TIMEOUT (spec 007)."""
import pytest
from pydantic import ValidationError

from app.schemas.instance import InstanceCreateRequest, InstanceUpdateRequest


# ---------------------------------------------------------------------------
# Validação de n8n_webhook_url — InstanceCreateRequest
# ---------------------------------------------------------------------------

def test_create_accepts_valid_https_url():
    req = InstanceCreateRequest(display_name="Test", n8n_webhook_url="https://n8n.example.com/webhook/abc")
    assert req.n8n_webhook_url == "https://n8n.example.com/webhook/abc"


def test_create_accepts_valid_http_url():
    req = InstanceCreateRequest(display_name="Test", n8n_webhook_url="http://localhost:5678/webhook/test")
    assert req.n8n_webhook_url == "http://localhost:5678/webhook/test"


def test_create_accepts_none_url():
    req = InstanceCreateRequest(display_name="Test", n8n_webhook_url=None)
    assert req.n8n_webhook_url is None


def test_create_rejects_url_without_scheme():
    with pytest.raises(ValidationError):
        InstanceCreateRequest(display_name="Test", n8n_webhook_url="n8n.example.com/webhook/abc")


def test_create_rejects_ftp_scheme():
    with pytest.raises(ValidationError):
        InstanceCreateRequest(display_name="Test", n8n_webhook_url="ftp://n8n.example.com/webhook")


# ---------------------------------------------------------------------------
# Validação de n8n_webhook_url — InstanceUpdateRequest
# ---------------------------------------------------------------------------

def test_update_accepts_valid_url():
    req = InstanceUpdateRequest(n8n_webhook_url="https://n8n.example.com/webhook/updated")
    assert req.n8n_webhook_url == "https://n8n.example.com/webhook/updated"


def test_update_accepts_none_url():
    req = InstanceUpdateRequest(n8n_webhook_url=None)
    assert req.n8n_webhook_url is None


def test_update_rejects_url_without_scheme():
    with pytest.raises(ValidationError):
        InstanceUpdateRequest(n8n_webhook_url="n8n.example.com/webhook")


# ---------------------------------------------------------------------------
# Validação de N8N_FORWARD_TIMEOUT — AppSettings
# ---------------------------------------------------------------------------

def test_n8n_forward_timeout_default(mock_env):
    from app.core.config import AppSettings
    settings = AppSettings()
    assert settings.N8N_FORWARD_TIMEOUT == 5


def test_n8n_forward_timeout_custom(mock_env, monkeypatch):
    monkeypatch.setenv("N8N_FORWARD_TIMEOUT", "10")
    from app.core.config import AppSettings
    settings = AppSettings()
    assert settings.N8N_FORWARD_TIMEOUT == 10


def test_n8n_forward_timeout_rejects_zero(mock_env, monkeypatch):
    monkeypatch.setenv("N8N_FORWARD_TIMEOUT", "0")
    from app.core.config import AppSettings
    with pytest.raises(ValidationError):
        AppSettings()


def test_n8n_forward_timeout_rejects_negative(mock_env, monkeypatch):
    monkeypatch.setenv("N8N_FORWARD_TIMEOUT", "-1")
    from app.core.config import AppSettings
    with pytest.raises(ValidationError):
        AppSettings()
