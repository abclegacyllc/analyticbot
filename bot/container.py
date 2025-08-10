import punq
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Barcha importlar yangi strukturaga moslashtirilgan
from bot.config import settings, Settings
from bot.database.repositories import (
    UserRepository,
    PlanRepository,
    ChannelRepository,
    SchedulerRepository,
    AnalyticsRepository,
)
from bot.services import (
    SubscriptionService,
    GuardService,
    SchedulerService,
    AnalyticsService,
)

def create_async_pool(db_url: str) -> async_sessionmaker:
    """Ma'lumotlar bazasi uchun asinxron ulanishlar pulini (pool) yaratadi."""
    engine = create_async_engine(db_url, echo=False)
    return async_sessionmaker(engine, expire_on_commit=False)


def get_container() -> punq.Container:
    """
    DI konteynerini yaratadi va barcha kerakli
    obyektlarni (qaramliklarni) ro'yxatdan o'tkazadi.
    """
    config = settings
    pool = create_async_pool(config.DATABASE_URL.unicode_string())

    container = punq.Container()

    # --- YECHIM: Bot'ni ro'yxatdan o'tkazishning to'g'ri usuli ---
    # Avval funksiyani aniqlaymiz...
    def get_bot_instance(settings: Settings) -> Bot:
        return Bot(
            token=settings.BOT_TOKEN.get_secret_value(),
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
    # ...keyin uni 'factory' sifatida to'g'ridan-to'g'ri metod orqali registratsiya qilamiz.
    container.register(Bot, factory=get_bot_instance, scope=punq.Scope.singleton)
    # --------------------------------------------------------------

    # Asosiy resurslarni registratsiya qilamiz
    container.register(Settings, instance=config)
    container.register(async_sessionmaker, instance=pool)

    # Repozitoriy'larni registratsiya qilamiz
    container.register(UserRepository)
    container.register(PlanRepository)
    container.register(ChannelRepository)
    container.register(SchedulerRepository)
    container.register(AnalyticsRepository)

    # Servis'larni registratsiya qilamiz
    container.register(SubscriptionService)
    container.register(GuardService)
    container.register(SchedulerService)
    container.register(AnalyticsService)

    return container

# Global konteyner obyektini yaratib qo'yamiz
container = get_container()
