CREATE TABLE IF NOT EXISTS plans (
    plan_name TEXT PRIMARY KEY,
    max_channels INT NOT NULL,
    max_posts_per_month INT NOT NULL
);

-- DEFAULT PLANS
-- We use -1 to represent "unlimited"
INSERT INTO plans (plan_name, max_channels, max_posts_per_month) VALUES
('free', 1, 10) ON CONFLICT(plan_name) DO NOTHING;

INSERT INTO plans (plan_name, max_channels, max_posts_per_month) VALUES
('pro', 5, 100) ON CONFLICT(plan_name) DO NOTHING;

INSERT INTO plans (plan_name, max_channels, max_posts_per_month) VALUES
('premium', -1, -1) ON CONFLICT(plan_name) DO NOTHING;


-- UPDATED users TABLE
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username TEXT,
    role TEXT NOT NULL DEFAULT 'admin',
    registration_date TIMESTAMP WITH TIME ZONE NOT NULL,
    is_banned BOOLEAN NOT NULL DEFAULT FALSE,
    referrer_id BIGINT,
    plan TEXT NOT NULL DEFAULT 'free', -- <-- ADDED COLUMN
    CONSTRAINT fk_user_plan FOREIGN KEY (plan) REFERENCES plans(plan_name), -- <-- ADDED CONSTRAINT
    CONSTRAINT fk_referrer FOREIGN KEY (referrer_id)
        REFERENCES users(user_id)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS scheduled_posts (
    post_id SERIAL PRIMARY KEY,
    channel_id BIGINT NOT NULL,
    text TEXT,
    schedule_time TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    media_path TEXT,
    button_config TEXT,
    sent_message_id BIGINT,
    views BIGINT, -- <-- ADD THIS NEW COLUMN
    CONSTRAINT fk_post_to_channel
        FOREIGN KEY (channel_id)
        REFERENCES channels(channel_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username TEXT,
    role TEXT NOT NULL DEFAULT 'admin',
    registration_date TIMESTAMP WITH TIME ZONE NOT NULL,
    is_banned BOOLEAN NOT NULL DEFAULT FALSE,
    referrer_id BIGINT,
    CONSTRAINT fk_referrer FOREIGN KEY (referrer_id)
        REFERENCES users(user_id)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS channels (
    channel_id BIGINT PRIMARY KEY,
    admin_id BIGINT NOT NULL,
    plan TEXT NOT NULL,
    status TEXT NOT NULL,
    CONSTRAINT fk_channel_admin FOREIGN KEY (admin_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS scheduled_posts (
    post_id SERIAL PRIMARY KEY,
    channel_id BIGINT NOT NULL,
    text TEXT,
    schedule_time TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    media_path TEXT,
    button_config TEXT,
    sent_message_id BIGINT,
    CONSTRAINT fk_post_to_channel
        FOREIGN KEY (channel_id)
        REFERENCES channels(channel_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS blacklist_words (
    id SERIAL PRIMARY KEY,
    channel_id BIGINT NOT NULL,
    word TEXT NOT NULL,
    CONSTRAINT fk_blacklist_channel FOREIGN KEY (channel_id)
        REFERENCES channels(channel_id)
        ON DELETE CASCADE
);
