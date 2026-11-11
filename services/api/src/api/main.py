import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_settings
from api.routes.agent import router as agent_router
from api.routes.contacts import router as contacts_router
from api.routes.conversations import router as conversations_router
from api.routes.documents import router as documents_router
from api.routes.events import router as events_router
from api.routes.facts import router as facts_router
from api.routes.health import router as health_router
from api.routes.profile import router as profile_router
from api.routes.suggestions import router as suggestions_router
from api.routes.talking_points import router as talking_points_router

logger = logging.getLogger("convo-glasses-api")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info("Starting Convo Glasses API in %s mode", settings.ENVIRONMENT)
    yield
    logger.info("Shutting down Convo Glasses API")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Convo Glasses API",
        version="0.1.0",
        description="Companion backend API for Convo Glasses smart-glasses coach.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health and ops probes at root
    app.include_router(health_router)

    # Versioned API routes under /v1
    app.include_router(profile_router)
    app.include_router(facts_router)
    app.include_router(documents_router)
    app.include_router(agent_router)
    app.include_router(talking_points_router)
    app.include_router(events_router)
    app.include_router(contacts_router)
    app.include_router(conversations_router)
    app.include_router(suggestions_router)

    return app


app = create_app()
