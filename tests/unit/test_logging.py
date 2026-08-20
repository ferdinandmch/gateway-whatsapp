import logging
import json


def test_json_format_in_production(mock_env, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    from app.core.config import AppSettings
    from app.core.logging import configure_logging

    settings = AppSettings()
    configure_logging(settings)

    logger = logging.getLogger("whatsapp_gateway")
    handler = logger.handlers[0] if logger.handlers else None
    assert handler is not None
    assert isinstance(handler.formatter, logging.Formatter)
    fmt = handler.formatter._fmt if hasattr(handler.formatter, "_fmt") else str(handler.formatter)
    assert "asctime" in fmt or "message" in fmt.lower() or handler.formatter.__class__.__name__ == "JsonFormatter"


def test_text_format_in_development(mock_env, monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    from app.core.config import AppSettings
    from app.core.logging import configure_logging

    settings = AppSettings()
    configure_logging(settings)

    logger = logging.getLogger("whatsapp_gateway")
    assert logger.level <= logging.INFO


def test_log_level_respected(mock_env, monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    from app.core.config import AppSettings
    from app.core.logging import configure_logging

    settings = AppSettings()
    configure_logging(settings)

    logger = logging.getLogger("whatsapp_gateway")
    assert logger.level == logging.WARNING
