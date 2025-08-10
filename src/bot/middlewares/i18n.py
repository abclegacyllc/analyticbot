from typing import Any, Awaitable, Callable, Dict

from aiogram.types import TelegramObject
from aiogram_i18n.managers import BaseManager
from aiogram_i18n.cores.fluent_runtime_core import FluentRuntimeCore
from aiogram_i18n import I18nMiddleware

# Ma'lumotlar bazasidan foydalanuvchi repozitoriysini import qilish
from src.bot.database.repositories.user_repository import UserRepository

class LanguageManager(BaseManager):
    """
    Foydalanuvchi tilini ma'lumotlar bazasidan oladi va o'rnatadi.
    """
    async def get_locale(self, event: TelegramObject, user_repo: UserRepository) -> str:
        """
        Foydalanuvchi tilini DB'dan oladi. Agar topilmasa, standart tilni qaytaradi.
        """
        if event.from_user:
            user = await user_repo.get_or_create_user(event.from_user.id, event.from_user.full_name)
            # Agar foydalanuvchi tili DB'da mavjud bo'lsa, uni qaytaramiz
            if user and user.language_code:
                return user.language_code
        # Har qanday boshqa holatda standart 'uz' tilini qaytaramiz
        return "uz"

    async def set_locale(self, locale: str, event: TelegramObject, user_repo: UserRepository) -> None:
        """
        Foydalanuvchining yangi tanlagan tilini DB'ga saqlaydi.
        """
        if event.from_user:
            await user_repo.update_user_language(event.from_user.id, locale)

# aiogram_i18n uchun Core'ni sozlash
# Bu yerda tarjima fayllari joylashgan yo'l ko'rsatiladi
core = FluentRuntimeCore(
    path="src/bot/locales/{locale}",
)

# I18nMiddleware ni yakuniy va to'g'ri sozlash
# Bu middleware har bir xabarni ushlab olib, unga tarjima funksiyalarini qo'shadi
i18n_middleware = I18nMiddleware(
    core=core,
    manager=LanguageManager(),
    # YAKUNIY TUZATISH: Standart tilni 'uz' qilib belgilaymiz
    default_locale="uz"
)
