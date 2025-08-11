# Database Schema

## channels

The `channels` table stores Telegram channels linked to users.

| Column     | Type      | Constraints / Notes                        |
|------------|-----------|---------------------------------------------|
| id         | BIGINT    | Primary key (Telegram channel ID)          |
| user_id    | BIGINT    | References `users.id`; owner of the channel |
| title      | VARCHAR(255) | Human‑readable channel title                |
| username   | VARCHAR(255) | Optional public @username; unique          |
| created_at | TIMESTAMPTZ | Timestamp of creation (defaults to `now()`) |

These names are canonical and should be used consistently across
models, repositories, and queries.