from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

# Import all your services and repositories
from src.bot.services.guard_service import GuardService
from src.bot.services.scheduler_service import SchedulerService
from src.bot.services.analytics_service import AnalyticsService
from src.bot.database.repositories import (
    UserRepository,
    ChannelRepository,
    SchedulerRepository,
    AnalyticsRepository
)


class DependencyMiddleware(BaseMiddleware):
    def __init__(
        self,
        user_repo: UserRepository,
        channel_repo: ChannelRepository,
        scheduler_repo: SchedulerRepository,
        analytics_repo: AnalyticsRepository,
        guard_service: GuardService,
        scheduler_service: SchedulerService,
        analytics_service: AnalyticsService,
    ):
        # Store all dependencies
        self.user_repo = user_repo
        self.channel_repo = channel_repo
        self.scheduler_repo = scheduler_repo
        self.analytics_repo = analytics_repo
        self.guard_service = guard_service
        self.scheduler_service = scheduler_service
        self.analytics_service = analytics_service

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Add dependencies to the data dictionary, which is then passed to the handler
        data["user_repo"] = self.user_repo
        data["channel_repo"] = self.channel_repo
        data["scheduler_repo"] = self.scheduler_repo
        data["analytics_repo"] = self.analytics_repo
        data["guard_service"] = self.guard_service
        data["scheduler_service"] = self.scheduler_service
        data["analytics_service"] = self.analytics_service
        
        return await handler(event, data)
