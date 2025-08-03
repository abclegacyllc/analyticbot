-- This script creates the database schema from scratch.
-- It is designed to be idempotent, meaning it can be run multiple times without causing errors.

-- Table for subscription plans
CREATE TABLE IF NOT EXISTS plans (
    plan_name TEXT PRIMARY KEY,
    max_channels INT NOT NULL,
    max_posts_per_month INT NOT NULL
);

-- Insert default plans if they don't exist
-- We use -1 to represent "unlimited"
INSERT INTO plans (plan_name, max_channels, max_posts_per_month) VALUES
('free', 1, 10),
('pro', 5, 100),
('premium', -1, -1)
ON CONFLICT(plan_name) DO NOTHING;


-- Table for bot users
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username TEXT,
    role TEXT NOT NULL DEFAULT 'admin',
    registration_date TIMESTAMP WITH TIME ZONE NOT NULL,
    is_banned BOOLEAN NOT NULL DEFAULT FALSE,
    referrer_id BIGINT,
    plan TEXT NOT NULL DEFAULT 'free', -- User's current plan
    CONSTRAINT fk_user_plan FOREIGN KEY (plan) REFERENCES plans(plan_name) ON UPDATE CASCADE,
    CONSTRAINT fk_referrer FOREIGN KEY (referrer_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- Table for channels registered by users
CREATE TABLE IF NOT EXISTS channels (
    channel_id BIGINT PRIMARY KEY,
    admin_id BIGINT NOT NULL,
    -- The 'plan' and 'status' columns were in the old model but are not used in the current repo logic.
    -- They are removed for simplification. Plan is managed at the user level.
    CONSTRAINT fk_channel_admin FOREIGN KEY (admin_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Table for scheduled posts
CREATE TABLE IF NOT EXISTS scheduled_posts (
    post_id SERIAL PRIMARY KEY,
    channel_id BIGINT NOT NULL,
    text TEXT,
    schedule_time TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- e.g., 'pending', 'sent', 'failed'
    media_path TEXT,
    button_config TEXT,
    sent_message_id BIGINT,
    views BIGINT, -- For analytics
    CONSTRAINT fk_post_to_channel FOREIGN KEY (channel_id) REFERENCES channels(channel_id) ON DELETE CASCADE
);

-- Table for channel-specific blacklisted words
CREATE TABLE IF NOT EXISTS blacklist_words (
    id SERIAL PRIMARY KEY,
    channel_id BIGINT NOT NULL,
    word TEXT NOT NULL,
    CONSTRAINT uq_channel_word UNIQUE (channel_id, word), -- prevent duplicate words per channel
    CONSTRAINT fk_blacklist_channel FOREIGN KEY (channel_id) REFERENCES channels(channel_id) ON DELETE CASCADE
);
