from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores import FluentRuntimeCore
from src.bot.config import SUPPORTED_LOCALES, DEFAULT_LOCALE

i18n_middleware = I18nMiddleware(
    core=FluentRuntimeCore(path="src/bot/locales/{locale}"),
    default_locale=DEFAULT_LOCALE,
    locales=SUPPORTED_LOCALES,
)
