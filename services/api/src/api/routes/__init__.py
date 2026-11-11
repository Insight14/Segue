from api.routes.agent import router as agent_router
from api.routes.coach import router as coach_router
from api.routes.contacts import router as contacts_router
from api.routes.conversations import router as conversations_router
from api.routes.documents import router as documents_router
from api.routes.events import router as events_router
from api.routes.facts import router as facts_router
from api.routes.health import router as health_router
from api.routes.profile import router as profile_router
from api.routes.suggestions import router as suggestions_router
from api.routes.talking_points import router as talking_points_router

__all__ = [
    "agent_router",
    "coach_router",
    "contacts_router",
    "conversations_router",
    "documents_router",
    "events_router",
    "facts_router",
    "health_router",
    "profile_router",
    "suggestions_router",
    "talking_points_router",
]
