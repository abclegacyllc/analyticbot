from aiogram.types import TelegramObject, User
from aiogram_i18n.managers import BaseManager

# Use relative imports and the correct Settings class
from ..config import Settings
from ..database.repositories import UserRepository


class LanguageManager(BaseManager):
    def __init__(self, user_repo: UserRepository, config: Settings):
        super().__init__(default=config.DEFAULT_LOCALE)
        self.user_repo = user_repo
        self.config = config

    async def get_locale(self, event: TelegramObject, data: dict) -> str:
        from_user: User | None = data.get("event_from_user")

        if from_user:
            user = await self.user_repo.get_user(from_user.id)
            if not user:
                user = await self.user_repo.create_user(
                    user_id=from_user.id,
                    username=from_user.username,
                    language_code=from_user.language_code
                )

            lang_code = user.get("language_code")
            if lang_code and lang_code in self.config.SUPPORTED_LOCALES:
                return lang_code

        return self.default

    async def set_locale(self, locale: str, data: dict) -> None:
        from_user: User | None = data.get("event_from_user")
        if from_user:
            await self.user_repo.update_user_language(from_user.id, locale)