from aiogram.types import TelegramObject, User
from aiogram_i18n.managers import BaseManager

from src.bot.config import Config
from src.bot.database.repositories import UserRepository


class LanguageManager(BaseManager):
    """
    Foydalanuvchining tilini aniqlash va o'rnatish uchun mas'ul klass.
    Ma'lumotlar bazasidan foydalanib, har bir foydalanuvchi uchun tanlangan tilni saqlaydi.
    """
    def __init__(self, user_repo: UserRepository, config: Config):
        super().__init__(default=config.bot.default_locale)
        self.user_repo = user_repo
        self.config = config

    async def get_locale(self, event: TelegramObject, data: dict) -> str:
        """Foydalanuvchining tilini aniqlaydi."""
        # `data` lug'atidan `event_from_user` obyektini olamiz,
        # bu obyektni aiogram avtomatik tarzda yaratadi.
        from_user: User | None = data.get("event_from_user")

        if from_user:
            user = await self.user_repo.get_user(from_user.id)
            if not user:
                # Agar foydalanuvchi bazada bo'lmasa, uni yaratamiz
                user = await self.user_repo.create_user(
                    user_id=from_user.id,
                    username=from_user.username,
                    language_code=from_user.language_code
                )
            
            # Agar foydalanuvchining tili bizda mavjud bo'lsa, shu tilni qaytaramiz
            lang_code = user.get("language_code")
            if lang_code and lang_code in self.config.bot.supported_locales:
                return lang_code

        # Aks holda, standart tilni qaytaramiz
        return self.default

    async def set_locale(self, locale: str, data: dict) -> None:
        """Foydalanuvchining tilini ma'lumotlar bazasida yangilaydi."""
        from_user: User | None = data.get("event_from_user")
        if from_user:
            await self.user_repo.update_user_language(from_user.id, locale)