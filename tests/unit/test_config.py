import pytest
from pydantic import ValidationError


def test_settings_defaults(mock_env):
    from app.core.config import AppSettings
    settings = AppSettings()
    assert settings.APP_ENV == "development"
    assert settings.APP_PORT == 8000
    assert settings.LOG_LEVEL == "INFO"
    assert settings.HTTP_TIMEOUT == 30


def test_settings_invalid_app_env(mock_env, monkeypatch):
    monkeypatch.setenv("APP_ENV", "invalid")
    from app.core.config import AppSettings
    with pytest.raises(ValidationError):
        AppSettings()


def test_settings_invalid_log_level(mock_env, monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "VERBOSE")
    from app.core.config import AppSettings
    with pytest.raises(ValidationError):
        AppSettings()


def test_settings_missing_required_var(clean_env):
    from app.core.config import AppSettings
    with pytest.raises(ValidationError):
        AppSettings()


def test_settings_database_url_required(mock_env, monkeypatch):
    monkeypatch.delenv("DATABASE_URL")
    from app.core.config import AppSettings
    with pytest.raises(ValidationError):
        AppSettings()
