from typing import Dict, Any

from aiogram.types import TelegramObject, User
from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores import FluentRuntimeCore
from aiogram_i18n.managers import BaseManager

from src.bot.config import settings
from src.bot.database.repositories import UserRepository

class LanguageManager(BaseManager):
    """
    Foydalanuvchi tilini boshqaradi.
    Bu class endi o'ziga `user_repo`ni argument sifatida kutadi va
    uni `aiogram-i18n` tizimi orqali avtomatik oladi.
    """
    async def get_locale(
        self, event: TelegramObject, data: Dict[str, Any]
    ) -> str:
        """
        Foydalanuvchini aniqlab, uning tilini qaytaradi.
        """
        user_repo: UserRepository | None = data.get("user_repo")
        if user_repo is None:
            return settings.DEFAULT_LOCALE
        
        event_from_user: User | None = data.get("event_from_user")
        
        if event_from_user:
            user = await user_repo.get_or_create_user(
                event_from_user.id,
                event_from_user.username,
                event_from_user.language_code,
            )
            if user and user.language_code in settings.SUPPORTED_LOCALES:
                return user.language_code
                
        return settings.DEFAULT_LOCALE

    async def set_locale(self, locale: str, data: Dict[str, Any]) -> None:
        """
        Foydalanuvchining yangi tilini ma'lumotlar bazasiga saqlaydi.
        """
        user_repo: UserRepository | None = data.get("user_repo")
        if user_repo is None:
            return

        event_from_user: User | None = data.get("event_from_user")

        if event_from_user:
            await user_repo.update_user_language(event_from_user.id, locale)

# Tayyor, sozlab bo'lingan i18n_middleware
i18n_middleware = I18nMiddleware(
    core=FluentRuntimeCore(path="src/bot/locales/{locale}"),
    manager=LanguageManager(),
    default_locale=settings.DEFAULT_LOCALE,
)
