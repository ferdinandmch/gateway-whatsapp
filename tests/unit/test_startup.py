import pytest
from pydantic import ValidationError


def test_settings_fail_with_missing_database_url(clean_env, monkeypatch):
    from tests.unit.conftest import VALID_ENV
    for key, value in VALID_ENV.items():
        if key != "DATABASE_URL":
            monkeypatch.setenv(key, value)

    import app.core.config as config_module
    config_module._settings = None

    from app.core.config import AppSettings
    with pytest.raises(ValidationError) as exc_info:
        AppSettings()

    fields = [str(e["loc"][0]) for e in exc_info.value.errors()]
    assert "DATABASE_URL" in fields


def test_settings_load_successfully_with_all_vars(mock_env):
    import app.core.config as config_module
    config_module._settings = None

    from app.core.config import get_settings
    settings = get_settings()
    assert settings.APP_ENV == "development"
    assert settings.DATABASE_URL.startswith("postgresql+asyncpg://")


def test_startup_error_message_lists_missing_field(clean_env, monkeypatch):
    from tests.unit.conftest import VALID_ENV
    for key, value in VALID_ENV.items():
        if key != "DATABASE_URL":
            monkeypatch.setenv(key, value)

    import app.core.config as config_module
    config_module._settings = None

    from app.core.config import AppSettings
    import sys
    import io

    with pytest.raises(ValidationError) as exc_info:
        AppSettings()

    # Error should identify the missing field
    error_text = str(exc_info.value)
    assert "DATABASE_URL" in error_text
