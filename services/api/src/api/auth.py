import logging
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import Settings, get_settings
from api.db import get_db_session
from api.models.user import User

logger = logging.getLogger("convo-glasses-auth")
security = HTTPBearer(auto_error=False)


async def get_current_user(
    auth: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    x_user_sub: Annotated[str | None, Header()] = None,
    x_user_email: Annotated[str | None, Header()] = None,
) -> User:
    """Authenticate the current user via JWT or local bypass."""

    sub: str
    email: str
    display_name: str | None = None

    # 1. Local / Dev Bypass Mode
    if settings.AUTH_BYPASS_ENABLED:
        sub = x_user_sub or (auth.credentials if auth and auth.credentials else "dev-user-sub-001")
        email = x_user_email or f"{sub}@example.com"
        display_name = sub
    else:
        # 2. Production Cognito JWT Verification
        if not auth or not auth.credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Bearer authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth.credentials
        try:
            jwks_url = (
                f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/"
                f"{settings.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
            )
            jwks_client = jwt.PyJWKClient(jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=settings.COGNITO_CLIENT_ID if settings.COGNITO_CLIENT_ID else None,
                options={"verify_aud": bool(settings.COGNITO_CLIENT_ID)},
            )
        except Exception as err:
            logger.warning("Token verification failed: %s", err)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from err

        sub_val = payload.get("sub")
        if not sub_val:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload missing subject ('sub')",
            )
        sub = str(sub_val)

        email_claim = payload.get("email")
        email = str(email_claim) if email_claim else f"{sub}@example.com"
        name_claim = payload.get("name") or payload.get("cognito:username")
        display_name = str(name_claim) if name_claim else None

    # Find or create user
    stmt = select(User).where(User.cognito_sub == sub)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            cognito_sub=sub,
            email=email,
            display_name=display_name,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user
