from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, RedisDsn, PostgresDsn

class Settings(BaseSettings):
    """
    Bot settings are defined here.
    Pydantic automatically reads them from environment variables or a .env file.
    It also validates the data types.
    """
    # model_config tells pydantic to load variables from a .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Bot token is stored as a SecretStr to prevent accidental logging
    BOT_TOKEN: SecretStr

    # Database and Redis URLs are validated to ensure they have the correct format
    DATABASE_URL: PostgresDsn
    REDIS_URL: RedisDsn

    # I18n settings
    SUPPORTED_LOCALES: list[str] = ["en", "uz"]
    DEFAULT_LOCALE: str = "uz"


# Create a single instance of the settings class
# All other modules in the project will import this 'settings' object
settings = Settings()
