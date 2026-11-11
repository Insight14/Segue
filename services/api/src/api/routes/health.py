from typing import Any

from fastapi import APIRouter, Response, status

from api.db import check_database_health

router = APIRouter(tags=["ops"])


@router.get("/healthz", status_code=status.HTTP_200_OK)
async def healthz() -> dict[str, str]:
    """Liveness probe: verifies that the web service process is responsive."""
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(response: Response) -> dict[str, Any]:
    """Readiness probe: verifies dependencies (e.g. database connection)."""
    db_ok = await check_database_health()
    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "dependencies": {
                "database": "unhealthy",
            },
        }

    response.status_code = status.HTTP_200_OK
    return {
        "status": "ready",
        "dependencies": {
            "database": "healthy",
        },
    }


@router.get("/metrics", status_code=status.HTTP_200_OK)
async def metrics() -> dict[str, str]:
    """Basic metrics placeholder (Prometheus format or status)."""
    return {"status": "ok"}
