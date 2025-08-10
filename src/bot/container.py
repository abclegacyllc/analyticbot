import punq
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

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

# Bu funksiya konteynerni yaratadi va barcha kerakli
# obyektlarni (qaramliklarni) ro'yxatdan o'tkazadi.
def get_container() -> punq.Container:
    config = load_config()
    pool = create_async_pool(config.db.construct_connection_url())

    container = punq.Container()

    # Asosiy resurslarni registratsiya qilamiz
    container.register(Config, instance=config)
    container.register(async_sessionmaker, instance=pool)

    # Repozitoriy'larni registratsiya qilamiz
    # Ular `async_sessionmaker`'ga bog'liqligi avtomatik aniqlanadi.
    container.register(UserRepository)
    container.register(PlanRepository)
    container.register(ChannelRepository)
    container.register(SchedulerRepository)
    container.register(AnalyticsRepository)

    # Servis'larni registratsiya qilamiz
    # Ularning repozitoriy'larga bog'liqligi ham avtomatik aniqlanadi.
    container.register(SubscriptionService)
    container.register(GuardService)
    container.register(SchedulerService)
    container.register(AnalyticsService)

    return container

# Global konteyner obyektini yaratib qo'yamiz
# Butun ilova shu bitta obyektni ishlatadi
container = get_container()