import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import ValidationError

logger = logging.getLogger("whatsapp_gateway")


def create_app() -> FastAPI:
    from dotenv import load_dotenv
    load_dotenv()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        from app.core.config import get_settings, AppSettings
        from app.core.logging import configure_logging

        try:
            settings = get_settings()
        except ValidationError as exc:
            missing = [str(e["loc"][0]) for e in exc.errors() if e["type"] == "missing"]
            msg = f"[whatsapp-gateway] Startup failed: missing required environment variables: {missing}"
            print(msg, file=sys.stderr)
            raise RuntimeError(msg) from exc

        configure_logging(settings)
        logger.info("WhatsApp Gateway starting up (env=%s)", settings.APP_ENV)
        yield
        logger.info("WhatsApp Gateway shutting down")

    app = FastAPI(
        title="WhatsApp Gateway",
        version="0.1.0",
        description="Proprietary WhatsApp messaging gateway API",
        lifespan=lifespan,
        openapi_tags=[
            {"name": "Infrastructure", "description": "Health and operational endpoints"},
            {"name": "messages", "description": "Message sending endpoints"},
        ],
    )

    from app.api.routes.health import router as health_router
    from app.api.v1.routes.clients import router as clients_router
    from app.api.v1.routes.instances import router as instances_router
    from app.api.v1.routes.messages import router as messages_router
    from app.api.v1.routes.webhooks import router as webhooks_router

    app.include_router(health_router)
    app.include_router(clients_router)
    app.include_router(instances_router)
    app.include_router(messages_router)
    app.include_router(webhooks_router)

    return app


app = create_app()
