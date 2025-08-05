-- Plans Table: Defines subscription tiers
CREATE TABLE IF NOT EXISTS plans (
    plan_id SERIAL PRIMARY KEY,
    plan_name VARCHAR(50) UNIQUE NOT NULL,
    max_channels INT NOT NULL,
    max_posts_per_month INT NOT NULL
);

-- Users Table: Stores user information
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    plan_id INT REFERENCES plans(plan_id) DEFAULT 1,
    role VARCHAR(50) DEFAULT 'user' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Channels Table: Stores channels added by users
CREATE TABLE IF NOT EXISTS channels (
    channel_id BIGINT PRIMARY KEY,
    channel_name VARCHAR(255) NOT NULL,
    admin_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE
);

-- Scheduler Table: Stores posts to be sent
CREATE TABLE IF NOT EXISTS scheduled_posts (
    post_id SERIAL PRIMARY KEY,
    channel_id BIGINT REFERENCES channels(channel_id) ON DELETE CASCADE,
    text TEXT,
    file_id VARCHAR(255),
    file_type VARCHAR(50),
    schedule_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    sent_message_id BIGINT,
    views INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Seed the initial data for the plans
INSERT INTO plans (plan_id, plan_name, max_channels, max_posts_per_month)
VALUES (1, 'free', 3, 30)
ON CONFLICT (plan_id) DO NOTHING;

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_scheduled_posts_status_time ON scheduled_posts(status, schedule_time);
CREATE INDEX IF NOT EXISTS idx_channels_admin_id ON channels(admin_id);
