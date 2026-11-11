import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ThreadMode(str, Enum):
    DISCOVER = "discover"
    PREP = "prep"


class ThreadCreateRequest(BaseModel):
    mode: ThreadMode = ThreadMode.DISCOVER
    title: str = Field(default="New Thread", max_length=255)


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1)


class MessageResponse(BaseModel):
    id: uuid.UUID
    thread_id: uuid.UUID
    role: str
    content: str
    proposed_fact: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ThreadResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    mode: ThreadMode
    title: str
    messages: list[MessageResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TalkingPointStory(BaseModel):
    title: str
    situation: str
    action: str
    result: str
    fact_id: str | None = None


class TalkingPointsContent(BaseModel):
    pitch_30s: str = Field(description="30-second first person pitch")
    stories: list[TalkingPointStory] = Field(default_factory=list, max_length=3)
    questions_to_ask: list[str] = Field(default_factory=list)
    icebreakers: list[str] = Field(default_factory=list)
    if_asked_about_weakness: str | None = None
    gaps: list[str] = Field(default_factory=list)


class GenerateTalkingPointsRequest(BaseModel):
    event_id: uuid.UUID | None = None
    contact_id: uuid.UUID | None = None
    notes: str | None = None


class TalkingPointsResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    event_id: uuid.UUID | None = None
    contact_id: uuid.UUID | None = None
    content: TalkingPointsContent
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
