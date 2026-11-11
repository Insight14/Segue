import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class FactKind(str, Enum):
    EXPERIENCE = "experience"
    EDUCATION = "education"
    SKILL = "skill"
    INTEREST = "interest"
    HOBBY = "hobby"
    GOAL = "goal"
    VALUE = "value"
    STORY_SUCCESS = "story_success"
    STORY_FAILURE = "story_failure"
    STORY_COLLABORATION = "story_collaboration"
    OTHER = "other"


class FactSource(str, Enum):
    USER = "user"
    RESUME = "resume"
    AGENT = "agent"


class FactCreate(BaseModel):
    kind: FactKind
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
    source: FactSource = Field(default=FactSource.USER)
    confirmed: bool = Field(default=True)


class FactUpdate(BaseModel):
    kind: FactKind | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    body: str | None = Field(default=None, min_length=1)
    tags: list[str] | None = None
    confirmed: bool | None = None


class FactResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    kind: FactKind
    title: str
    body: str
    tags: list[str]
    source: FactSource
    confirmed: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
