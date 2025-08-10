from aiogram.i18n.middleware import I18nMiddleware
from bot.locales.i18n_hub import I18N_HUB

# I18nMiddleware obyektini yaratish va eksport qilish
# Tilni boshqarish logikasi run_bot.py ichidagi LanguageManager'da amalga oshiriladi
i18n_middleware = I18nMiddleware(i18n=I18N_HUB, default_locale="en")
