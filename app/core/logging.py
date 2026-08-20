import logging
import logging.config
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.config import AppSettings


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        import json
        log_record = {
            "asctime": self.formatTime(record),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


def configure_logging(settings: "AppSettings") -> None:
    formatter_class = (
        "app.core.logging.JsonFormatter"
        if settings.APP_ENV == "production"
        else "logging.Formatter"
    )
    fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": formatter_class,
                "fmt": fmt,
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stdout",
            }
        },
        "loggers": {
            "whatsapp_gateway": {
                "handlers": ["console"],
                "level": settings.LOG_LEVEL,
                "propagate": False,
            }
        },
        "root": {
            "handlers": ["console"],
            "level": settings.LOG_LEVEL,
        },
    }
    logging.config.dictConfig(config)
