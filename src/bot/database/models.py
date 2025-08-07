from sqlalchemy import (
    MetaData, Table, Column, Integer, BigInteger, String, DateTime,
    ForeignKey, Text, JSON, Boolean
)
from sqlalchemy.sql import func

# Alembic va SQLAlchemy uchun yagona metadata obyekti
metadata_obj = MetaData()

users_table = Table(
    "users",
    metadata_obj,
    Column("user_id", BigInteger, primary_key=True, autoincrement=False),
    Column("username", String(255), nullable=True),
    Column("plan_id", Integer, ForeignKey("plans.plan_id"), default=1),
    Column("created_at", DateTime, server_default=func.now()),
)

plans_table = Table(
    "plans",
    metadata_obj,
    Column("plan_id", Integer, primary_key=True),
    Column("plan_name", String(50), nullable=False, unique=True),
    Column("max_channels", Integer, default=3),
    Column("max_posts_per_month", Integer, default=30),
)

channels_table = Table(
    "channels",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("channel_id", BigInteger, nullable=False, unique=True),
    Column("channel_name", String(255), nullable=False),
    Column("admin_id", BigInteger, ForeignKey("users.user_id"), nullable=False),
    Column("created_at", DateTime, server_default=func.now()),
)

scheduled_posts_table = Table(
    "scheduled_posts",
    metadata_obj,
    Column("post_id", Integer, primary_key=True),
    Column("channel_id", BigInteger, ForeignKey("channels.channel_id"), nullable=False),
    Column("text", Text, nullable=True),
    Column("file_id", String(255), nullable=True),
    Column("file_type", String(50), nullable=True),
    Column("inline_buttons", JSON, nullable=True),
    Column("schedule_time", DateTime, nullable=False),
    Column("status", String(20), default="pending"),
    Column("sent_message_id", BigInteger, nullable=True),
    Column("created_at", DateTime, server_default=func.now()),
)

post_views_table = Table(
    "post_views",
    metadata_obj,
    Column("view_id", Integer, primary_key=True),
    Column("post_id", Integer, ForeignKey("scheduled_posts.post_id"), nullable=False),
    Column("views_count", Integer, nullable=False),
    Column("timestamp", DateTime, server_default=func.now()),
)

guard_words_table = Table(
    "guard_words",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("channel_id", BigInteger, nullable=False),
    Column("word", String(255), nullable=False),
)
