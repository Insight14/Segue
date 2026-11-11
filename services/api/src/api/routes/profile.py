from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from api.db import get_db_session
from api.models.profile import Profile
from api.models.user import User
from api.schemas.profile import ProfileResponse, ProfileUpdate

router = APIRouter(prefix="/v1/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse, status_code=status.HTTP_200_OK)
async def get_profile(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> Profile:
    """Retrieve the authenticated user's profile, creating one if it doesn't exist."""
    stmt = select(Profile).where(Profile.user_id == user.id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        profile = Profile(user_id=user.id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

    return profile


@router.put("", response_model=ProfileResponse, status_code=status.HTTP_200_OK)
async def update_profile(
    payload: ProfileUpdate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> Profile:
    """Update or upsert the authenticated user's profile."""
    stmt = select(Profile).where(Profile.user_id == user.id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        profile = Profile(user_id=user.id)
        db.add(profile)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)
    return profile
