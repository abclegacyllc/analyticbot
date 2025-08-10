import punq
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# We are moving the database connection function here to remove all external imports
# that could fail.
def create_async_pool(db_url: str) -> async_sessionmaker:
    """Creates a new asynchronous session pool for the database."""
    engine = create_async_engine(db_url, echo=False)
    return async_sessionmaker(engine, expire_on_commit=False)

# Import other project files after the function is defined
from .config import settings, Settings
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
    config = settings
    pool = create_async_pool(config.DATABASE_URL.unicode_string())

    container = punq.Container()

    # --- THIS IS THE FINAL AND CORRECT FIX ---
    # We define the factory function first...
    def get_bot_instance(config: Settings) -> Bot:
        return Bot(
            token=config.BOT_TOKEN.get_secret_value(),
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
    # ...and then we register it using a direct method call.
    # We are NO LONGER using the incorrect '@' decorator syntax.
    container.register(Bot, factory=get_bot_instance, scope=punq.Scope.singleton)
    # ----------------------------------------

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
