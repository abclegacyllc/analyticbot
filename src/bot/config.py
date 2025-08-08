from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, RedisDsn, PostgresDsn, AnyHttpUrl
from typing import Optional

class Settings(BaseSettings):
    """
    Bot settings are defined here.
    Pydantic automatically reads them from environment variables or a .env file.
    It also validates the data types.
    """
    # Bot token is stored as a SecretStr to prevent accidental logging
    BOT_TOKEN: SecretStr

    # Database and Redis URLs are validated to ensure they have the correct format
    DATABASE_URL: PostgresDsn
    REDIS_URL: RedisDsn

    # URL for the Telegram Web App (Frontend)
    TWA_HOST_URL: AnyHttpUrl
    
    # Sentry DSN for error tracking
    SENTRY_DSN: Optional[str] = None

    # This acts as a master switch to enable/disable plan limit checks
    ENFORCE_PLAN_LIMITS: bool = True
    
    # ID of the private channel used to store media and get file_ids
    STORAGE_CHANNEL_ID: int

    # I18n settings
    SUPPORTED_LOCALES: list[str] = ["en", "uz"]
    DEFAULT_LOCALE: str = "uz"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# Create a single instance of the settings class
# All other modules in the project will import this 'settings' object
settings = Settings()