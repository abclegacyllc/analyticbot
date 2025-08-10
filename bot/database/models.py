import sqlalchemy as sa
from dataclasses import dataclass

metadata = sa.MetaData()

# 1. 'plans' table (no dependencies)
plans = sa.Table(
    'plans', metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('name', sa.String(50), unique=True, nullable=False),
    sa.Column('max_channels', sa.Integer, default=1),
    sa.Column('max_posts_per_month', sa.Integer, default=30)
)

# 2. 'users' table (depends on 'plans')
users = sa.Table(
    'users', metadata,
    sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=False),
    sa.Column('username', sa.String(255)),
    sa.Column('plan_id', sa.Integer, sa.ForeignKey('plans.id'), default=1),
    sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
)

# 3. 'channels' table (depends on 'users')
channels = sa.Table(
    'channels', metadata,
    sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=False),
    sa.Column('user_id', sa.BigInteger, sa.ForeignKey('users.id'), nullable=False),
    sa.Column('title', sa.String(255)),
    sa.Column('username', sa.String(255), unique=True),
    sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
)

# 4. 'scheduled_posts' table (depends on 'users' and 'channels')
scheduled_posts = sa.Table(
    'scheduled_posts', metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('user_id', sa.BigInteger, sa.ForeignKey('users.id')),
    sa.Column('channel_id', sa.BigInteger, sa.ForeignKey('channels.id')),
    sa.Column('post_text', sa.Text),
    sa.Column('media_id', sa.String(255)),
    sa.Column('media_type', sa.String(50)),
    sa.Column('inline_buttons', sa.JSON),
    sa.Column('status', sa.String(50), default='pending'),
    sa.Column('schedule_time', sa.DateTime(timezone=True)),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column('views', sa.Integer, default=0)
)

# 5. 'sent_posts' table (depends on 'scheduled_posts' and 'channels')
sent_posts = sa.Table(
    'sent_posts', metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('scheduled_post_id', sa.Integer, sa.ForeignKey('scheduled_posts.id'), nullable=False),
    sa.Column('channel_id', sa.BigInteger, sa.ForeignKey('channels.id'), nullable=False),
    sa.Column('message_id', sa.BigInteger, nullable=False),
    sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.func.now())
)

# This dataclass does not affect the database schema
@dataclass
class SubscriptionStatus:
    plan_name: str
    max_channels: int
    current_channels: int
    max_posts_per_month: int
    current_posts_this_month: int