from fastapi import APIRouter
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["Infrastructure"],
    summary="Health check",
    description="Returns the health status of the backend. Public endpoint, no authentication required.",
    operation_id="health_check",
)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="whatsapp-gateway",
        version="0.1.0",
    )
