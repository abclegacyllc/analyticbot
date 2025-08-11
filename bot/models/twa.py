from __future__ import annotations

"""Pydantic models used by the FastAPI layer.

The original project referenced a number of classes that were removed
from the repository.  To keep the API functional we provide lightweight
Pydantic models that mirror the simple dictionary structures returned by
the repositories.  These models are intentionally minimal and are not
backed by any ORM.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class Button(BaseModel):
    text: str
    url: str


class AddChannelRequest(BaseModel):
    """Request body for adding a new channel."""

    channel_username: str

    @field_validator("channel_username")
    @classmethod
    def username_must_be_valid(cls, v: str) -> str:  # noqa: D401 - short note
        """Ensure the username starts with '@'."""
        if not v or not v.startswith("@"):
            raise ValueError("Channel username must start with @")
        return v


class SchedulePostRequest(BaseModel):
    """Request body for scheduling a post."""

    channel_id: int
    scheduled_at: datetime
    text: Optional[str] = None
    media_id: Optional[str] = None
    media_type: Optional[str] = None
    buttons: Optional[List[Button]] = None


class Channel(BaseModel):
    """Representation of a Telegram channel in API responses."""

    id: int
    channel_name: str


class ScheduledPost(BaseModel):
    """Representation of a scheduled post returned from the API."""

    id: int
    channel_id: int
    scheduled_at: datetime
    text: Optional[str] = None
    media_id: Optional[str] = None
    media_type: Optional[str] = None
    buttons: Optional[List[Button]] = None


class User(BaseModel):
    id: int
    username: Optional[str] = None


class Plan(BaseModel):
    name: str
    max_channels: int
    max_posts_per_month: int


class InitialDataResponse(BaseModel):
    user: User
    plan: Optional[Plan] = None
    channels: List[Channel] = Field(default_factory=list)
    scheduled_posts: List[ScheduledPost] = Field(default_factory=list)


class ValidationErrorResponse(BaseModel):
    detail: str


class MessageResponse(BaseModel):
    message: str
