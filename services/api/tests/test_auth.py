from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient

from api.config import Settings, get_settings
from api.main import app


@pytest.mark.asyncio
async def test_auth_missing_token_when_bypass_disabled(client: AsyncClient) -> None:
    strict_settings = Settings(
        AUTH_BYPASS_ENABLED=False,
        COGNITO_USER_POOL_ID="us-east-1_mockpool",
        COGNITO_CLIENT_ID="mockclient123",
    )
    app.dependency_overrides[get_settings] = lambda: strict_settings
    try:
        response = await client.get("/v1/profile")
        assert response.status_code == 401
        assert "Missing Bearer" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_settings, None)


@pytest.mark.asyncio
async def test_auth_invalid_token_when_bypass_disabled(client: AsyncClient) -> None:
    strict_settings = Settings(
        AUTH_BYPASS_ENABLED=False,
        COGNITO_USER_POOL_ID="us-east-1_mockpool",
        COGNITO_CLIENT_ID="mockclient123",
    )
    app.dependency_overrides[get_settings] = lambda: strict_settings
    try:
        response = await client.get(
            "/v1/profile", headers={"Authorization": "Bearer invalid.token.payload"}
        )
        assert response.status_code == 401
        assert "Invalid or expired" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_settings, None)


@pytest.mark.asyncio
async def test_auth_valid_cognito_token_when_bypass_disabled(client: AsyncClient) -> None:
    strict_settings = Settings(
        AUTH_BYPASS_ENABLED=False,
        COGNITO_USER_POOL_ID="us-east-1_mockpool",
        COGNITO_CLIENT_ID="mockclient123",
    )
    app.dependency_overrides[get_settings] = lambda: strict_settings
    try:
        mock_jwk_client = MagicMock()
        mock_signing_key = MagicMock()
        mock_signing_key.key = "mock-public-key"
        mock_jwk_client.get_signing_key_from_jwt.return_value = mock_signing_key

        with patch("jwt.PyJWKClient", return_value=mock_jwk_client):
            with patch(
                "jwt.decode",
                return_value={
                    "sub": "cognito-user-999",
                    "email": "valid@example.com",
                    "name": "Cognito User",
                },
            ):
                response = await client.get(
                    "/v1/profile", headers={"Authorization": "Bearer valid.token.here"}
                )
                assert response.status_code == 200
                data = response.json()
                assert "id" in data
    finally:
        app.dependency_overrides.pop(get_settings, None)
