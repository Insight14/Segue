import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProfileBase(BaseModel):
    headline: str | None = Field(default=None, max_length=255)
    status: str | None = Field(
        default=None, max_length=255, description="e.g. CS junior, Senior SRE"
    )
    goals: str | None = Field(default=None, description="Career and networking goals")
    tone_preference: str | None = Field(
        default=None, max_length=100, description="e.g. casual, professional, enthusiastic"
    )
    summary_md: str | None = Field(default=None, description="Markdown summary generated or edited")


class ProfileUpdate(ProfileBase):
    pass


class ProfileResponse(ProfileBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
