from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores import FluentRuntimeCore
# Import the single settings object
from src.bot.config import settings

i18n_middleware = I18nMiddleware(
    core=FluentRuntimeCore(path="src/bot/locales/{locale}"),
    default_locale=settings.DEFAULT_LOCALE
)
