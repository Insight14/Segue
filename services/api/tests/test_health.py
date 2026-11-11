from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from api.db import check_database_health, get_db_session
from api.main import create_app, lifespan


@pytest.mark.asyncio
async def test_healthz(client: AsyncClient) -> None:
    response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_readyz_healthy(client: AsyncClient) -> None:
    with patch("api.routes.health.check_database_health", new_callable=AsyncMock) as mock_db:
        mock_db.return_value = True
        response = await client.get("/readyz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["dependencies"]["database"] == "healthy"


@pytest.mark.asyncio
async def test_readyz_unhealthy(client: AsyncClient) -> None:
    with patch("api.routes.health.check_database_health", new_callable=AsyncMock) as mock_db:
        mock_db.return_value = False
        response = await client.get("/readyz")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["dependencies"]["database"] == "unhealthy"


@pytest.mark.asyncio
async def test_metrics(client: AsyncClient) -> None:
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_lifespan() -> None:
    app = create_app()
    async with lifespan(app):
        pass


@pytest.mark.asyncio
async def test_check_database_health_failure() -> None:
    with patch("api.db.engine") as mock_engine:
        mock_engine.connect.side_effect = Exception("DB Down")
        result = await check_database_health()
        assert result is False


@pytest.mark.asyncio
async def test_get_db_session() -> None:
    session_gen = get_db_session()
    assert isinstance(session_gen, AsyncGenerator)
