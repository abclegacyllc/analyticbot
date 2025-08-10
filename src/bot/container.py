import punq
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.bot.config import load_config, Config
from src.bot.database.db import create_async_pool
from src.bot.database.repositories import (
    UserRepository,
    PlanRepository,
    ChannelRepository,
    SchedulerRepository,
    AnalyticsRepository,
)
from src.bot.services import (
    SubscriptionService,
    GuardService,
    SchedulerService,
    AnalyticsService,
)

def get_container() -> punq.Container:
    """
    DI konteynerini yaratadi va barcha kerakli
    obyektlarni (qaramliklarni) ro'yxatdan o'tkazadi.
    """
    config = load_config()
    pool = create_async_pool(config.db.construct_connection_url())

    container = punq.Container()

    # --- 1-TUZATISH START ---
    # Bot obyektini "singleton" sifatida ro'yxatdan o'tkazamiz.
    # Bu shuni anglatadiki, butun ilova davomida yagona Bot obyekti ishlatiladi.
    @container.register(Bot, scope=punq.Scope.singleton)
    def get_bot_instance(config: Config) -> Bot:
        return Bot(
            token=config.bot.token.get_secret_value(),
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
    # --- 1-TUZATISH TUGADI ---

    # Asosiy resurslarni registratsiya qilamiz
    container.register(Config, instance=config)
    container.register(async_sessionmaker, instance=pool)

    # Repozitoriy'larni registratsiya qilamiz
    container.register(UserRepository)
    container.register(PlanRepository)
    container.register(ChannelRepository)
    container.register(SchedulerRepository)
    container.register(AnalyticsRepository)

    # Servis'larni registratsiya qilamiz
    # Endi ularning Bot obyektiga bog'liqligi avtomatik ta'minlanadi.
    container.register(SubscriptionService)
    container.register(GuardService)
    container.register(SchedulerService)
    container.register(AnalyticsService)

    return container

# Global konteyner obyektini yaratib qo'yamiz
container = get_container()