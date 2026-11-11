from api.routes.facts import router as facts_router
from api.routes.health import router as health_router
from api.routes.profile import router as profile_router

__all__ = ["facts_router", "health_router", "profile_router"]
