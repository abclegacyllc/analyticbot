-- FILE: database/init_db.sql
-- This script initializes the entire database schema for the bot.

-- Table to store information about bot users.
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    
    -- Plan-related columns
    plan_id INT NOT NULL DEFAULT 1, -- Default to the 'free' plan
    plan_expiry_date TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensures that plan_id refers to a valid plan in the 'plans' table.
    CONSTRAINT fk_plan
        FOREIGN KEY(plan_id) 
        REFERENCES plans(plan_id)
        ON DELETE SET DEFAULT
);

-- Table to store information about subscription plans.
CREATE TABLE IF NOT EXISTS plans (
    plan_id SERIAL PRIMARY KEY,
    plan_name VARCHAR(100) NOT NULL, -- e.g., 'free', 'premium', 'business'
    
    -- Plan limits (-1 means unlimited)
    max_channels INT NOT NULL DEFAULT 1,
    max_posts_per_month INT NOT NULL DEFAULT 30,
    
    -- Price in cents (e.g., 1000 for $10.00)
    price_monthly INT,
    price_yearly INT
);

-- Table to store channels registered by users.
CREATE TABLE IF NOT EXISTS channels (
    channel_id BIGINT PRIMARY KEY,
    admin_id BIGINT NOT NULL,
    channel_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensures that admin_id refers to a valid user.
    CONSTRAINT fk_admin
        FOREIGN KEY(admin_id) 
        REFERENCES users(user_id)
        ON DELETE CASCADE
);

-- Table to store posts scheduled by users.
-- This is the updated version with media support.
CREATE TABLE IF NOT EXISTS scheduled_posts (
    post_id SERIAL PRIMARY KEY,
    channel_id BIGINT NOT NULL,
    
    -- Text content of the post (can be a caption for media)
    text TEXT, 
    
    -- NEW: Columns for storing media information
    file_id VARCHAR(255) NULL, -- Telegram file_id can be long
    file_type VARCHAR(20) NULL,  -- e.g., 'photo', 'video', 'document'
    
    -- Scheduling and status information
    schedule_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, sent, failed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP WITH TIME ZONE,
    
    -- Analytics information
    views INT DEFAULT 0,
    sent_message_id BIGINT,

    -- Ensures that a post is always linked to a valid channel.
    -- If a channel is deleted, all its scheduled posts are also deleted.
    CONSTRAINT fk_channel
        FOREIGN KEY(channel_id) 
        REFERENCES channels(channel_id)
        ON DELETE CASCADE
);

-- Pre-populate the 'plans' table with a default free plan.
-- This ensures that every new user can be assigned to plan_id = 1.
INSERT INTO plans (plan_id, plan_name, max_channels, max_posts_per_month)
VALUES (1, 'free', 1, 30)
ON CONFLICT (plan_id) DO NOTHING;
