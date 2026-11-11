import datetime
import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# Events
class EventBase(BaseModel):
    name: str = Field(..., max_length=255)
    date: datetime.datetime | None = None
    type: str | None = Field(None, max_length=100)
    notes: str | None = None


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    date: datetime.datetime | None = None
    type: str | None = Field(None, max_length=100)
    notes: str | None = None


class EventResponse(EventBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# Contacts
class ContactBase(BaseModel):
    event_id: uuid.UUID | None = None
    name: str = Field(..., max_length=255)
    company: str | None = Field(None, max_length=255)
    role: str | None = Field(None, max_length=255)
    notes: str | None = None
    consent_noted: bool = False


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    event_id: uuid.UUID | None = None
    name: str | None = Field(None, max_length=255)
    company: str | None = Field(None, max_length=255)
    role: str | None = Field(None, max_length=255)
    notes: str | None = None
    consent_noted: bool | None = None


class ContactResponse(ContactBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# Messages
class MessageCreate(BaseModel):
    speaker: Literal["user", "partner"]
    text: str = Field(..., min_length=1)
    seq: int | None = None


class ConversationMessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    seq: int
    speaker: str
    text: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# Backwards compatibility alias
MessageResponse = ConversationMessageResponse


# Suggestions
class SuggestionResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    after_message_seq: int
    type: str
    text: str
    shown: bool
    selected: bool
    rating: int | None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class SuggestionUpdate(BaseModel):
    shown: bool | None = None
    selected: bool | None = None
    rating: int | None = Field(None, ge=1, le=5)


# Conversations
class ConversationCreate(BaseModel):
    contact_id: uuid.UUID | None = None
    event_id: uuid.UUID | None = None
    source: Literal["phone", "laptop", "glasses"] = "phone"


class ConversationUpdate(BaseModel):
    ended_at: datetime.datetime | None = None
    summary: str | None = None


class ConversationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    contact_id: uuid.UUID | None
    event_id: uuid.UUID | None
    started_at: datetime.datetime
    ended_at: datetime.datetime | None
    summary: str | None
    source: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationDetailResponse(ConversationResponse):
    contact: ContactResponse | None = None
    event: EventResponse | None = None
    messages: list[MessageResponse] = []
    suggestions: list[SuggestionResponse] = []


class ConversationExportResponse(BaseModel):
    conversation: ConversationResponse
    contact: ContactResponse | None
    event: EventResponse | None
    messages: list[MessageResponse]
    suggestions: list[SuggestionResponse]
    exported_at: datetime.datetime
