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
