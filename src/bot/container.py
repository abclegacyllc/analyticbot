import punq
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy.ext.asyncio import async_sessionmaker

# --- THIS IS THE FINAL AND CORRECT FIX ---
# Import the ready-made 'settings' object and the 'Settings' class directly.
# The '.' makes the import relative and more reliable inside a package.
from .config import settings, Settings
# ----------------------------------------

from .database.db import create_async_pool
from .database.repositories import (
    UserRepository,
    PlanRepository,
    ChannelRepository,
    SchedulerRepository,
    AnalyticsRepository,
)
from .services import (
    SubscriptionService,
    GuardService,
    SchedulerService,
    AnalyticsService,
)

def get_container() -> punq.Container:
    """
    Creates the DI container and registers all necessary dependencies.
    """
    # Use the imported settings object directly
    config = settings
    pool = create_async_pool(config.DATABASE_URL.unicode_string())

    container = punq.Container()

    @container.register(Bot, scope=punq.Scope.singleton)
    def get_bot_instance(config: Settings) -> Bot:
        return Bot(
            token=config.BOT_TOKEN.get_secret_value(),
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )

    # Register the main resources
    container.register(Settings, instance=config)
    container.register(async_sessionmaker, instance=pool)

    # Register Repositories
    container.register(UserRepository)
    container.register(PlanRepository)
    container.register(ChannelRepository)
    container.register(SchedulerRepository)
    container.register(AnalyticsRepository)

    # Register Services
    container.register(SubscriptionService)
    container.register(GuardService)
    container.register(SchedulerService)
    container.register(AnalyticsService)

    return container

# Create the global container instance
container = get_container()
