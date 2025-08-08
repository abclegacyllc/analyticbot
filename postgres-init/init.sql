-- Step 1: Create all tables WITHOUT foreign key constraints
CREATE TABLE IF NOT EXISTS plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    max_channels INTEGER DEFAULT 1,
    max_posts_per_month INTEGER DEFAULT 30
);

CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    plan_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS channels (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    title VARCHAR(255),
    username VARCHAR(255) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS scheduled_posts (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    channel_id BIGINT,
    post_text TEXT,
    media_id VARCHAR(255),
    media_type VARCHAR(50),
    inline_buttons JSON,
    status VARCHAR(50) DEFAULT 'pending',
    schedule_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    views INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sent_posts (
    id SERIAL PRIMARY KEY,
    scheduled_post_id INTEGER NOT NULL,
    channel_id BIGINT NOT NULL,
    message_id BIGINT NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Step 2: Add all the foreign key constraints AFTER the tables exist
ALTER TABLE users ADD CONSTRAINT fk_users_plan_id FOREIGN KEY (plan_id) REFERENCES plans(id);
ALTER TABLE channels ADD CONSTRAINT fk_channels_user_id FOREIGN KEY (user_id) REFERENCES users(id);
ALTER TABLE scheduled_posts ADD CONSTRAINT fk_scheduled_posts_user_id FOREIGN KEY (user_id) REFERENCES users(id);
ALTER TABLE scheduled_posts ADD CONSTRAINT fk_scheduled_posts_channel_id FOREIGN KEY (channel_id) REFERENCES channels(id);
ALTER TABLE sent_posts ADD CONSTRAINT fk_sent_posts_scheduled_post_id FOREIGN KEY (scheduled_post_id) REFERENCES scheduled_posts(id);
ALTER TABLE sent_posts ADD CONSTRAINT fk_sent_posts_channel_id FOREIGN KEY (channel_id) REFERENCES channels(id);
