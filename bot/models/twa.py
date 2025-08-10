from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

class Button(BaseModel):
    text: str
    url: str

class AddChannelRequest(BaseModel):
    type: str
    channel_name: str

    @field_validator('channel_name')
    def username_must_be_valid(cls, v):
        if not v or not v.startswith('@'):
            raise ValueError('Channel username must start with @')
        return v

class NewPostRequest(BaseModel):
    type: str
    channel_id: int
    schedule_time: datetime
    text: Optional[str] = None
    file_id: Optional[str] = None
    file_type: Optional[str] = None
    inline_buttons: Optional[List[Button]] = []

class DeletePostRequest(BaseModel):
    type: str
    post_id: int
