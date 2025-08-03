import asyncpg
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class User:
    user_id: int
    username: Optional[str]
    role: str  # 'admin' or 'superadmin'
    registration_date: datetime
    is_banned: bool
    referrer_id: Optional[int]

@dataclass
class Channel:
    channel_id: int
    admin_id: int
    plan: str  # 'free', 'pro', 'premium'
    status: str  # 'active', 'inactive'

@dataclass
class ScheduledPost:
    post_id: int
    channel_id: int
    text: str
    schedule_time: datetime
    status: str  # 'pending', 'sent', 'failed'
    media_path: Optional[str]
    button_config: Optional[str]

@dataclass
class BlacklistWord:
    id: int
    channel_id: int
    word: str

@dataclass
class SubscriptionStatus:
    """A data class to hold the user's current subscription status and usage."""
    plan_name: str
    max_channels: int
    current_channels: int
    max_posts_per_month: int
    current_posts_this_month: int
    
