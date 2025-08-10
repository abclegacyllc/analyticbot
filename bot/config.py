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

    # --- PostgreSQL Sozlamalari ---
    # Bu o'zgaruvchilar docker-compose.yml tomonidan ishlatiladi,
    # lekin Pydantic ularni bilishi uchun shu yerda ham ta'riflab qo'yamiz.
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int
    
    # Python ilovasi uchun asosiy ulanish manzili
    DATABASE_URL: PostgresDsn
    
    # Redis ulanish manzili
    REDIS_URL: RedisDsn

    # Telegram Web App (Frontend) uchun manzil
    TWA_HOST_URL: AnyHttpUrl
    
    # Xatoliklarni kuzatish uchun Sentry DSN
    SENTRY_DSN: Optional[str] = None

    # Tarif rejalarini tekshirishni yoqish/o'chirish
    ENFORCE_PLAN_LIMITS: bool = True
    
    # Media-fayllarni saqlash uchun "ombor" kanal IDsi
    STORAGE_CHANNEL_ID: int

    # I18n (Lokalizatsiya) sozlamalari
    SUPPORTED_LOCALES: list[str] = ["en", "uz"]
    DEFAULT_LOCALE: str = "uz"
    
    # Pydantic'ga .env faylini o'qishni buyuramiz
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra='ignore'  # <-- ADD THIS
    )

# Sozlamalarning yagona nusxasini yaratamiz
# Loyihadagi boshqa barcha modullar shu 'settings' obyektini import qiladi
settings = Settings()
