from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from src.bot.services.guard_service import GuardService
from src.bot.services.scheduler_service import SchedulerService
from src.bot.services.analytics_service import AnalyticsService
from src.bot.services.subscription_service import SubscriptionService # <-- Added
from src.bot.database.repositories import (
    UserRepository,
    ChannelRepository,
    SchedulerRepository,
    AnalyticsRepository,
    PlanRepository # <-- Added
)

class DependencyMiddleware(BaseMiddleware):
    def __init__(
        self,
        user_repo: UserRepository,
        channel_repo: ChannelRepository,
        scheduler_repo: SchedulerRepository,
        analytics_repo: AnalyticsRepository,
        plan_repo: PlanRepository, # <-- Added
        guard_service: GuardService,
        scheduler_service: SchedulerService,
        analytics_service: AnalyticsService,
        subscription_service: SubscriptionService, # <-- Added
    ):
        self.user_repo = user_repo
        self.channel_repo = channel_repo
        self.scheduler_repo = scheduler_repo
        self.analytics_repo = analytics_repo
        self.plan_repo = plan_repo # <-- Added
        self.guard_service = guard_service
        self.scheduler_service = scheduler_service
        self.analytics_service = analytics_service
        self.subscription_service = subscription_service # <-- Added

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["user_repo"] = self.user_repo
        data["channel_repo"] = self.channel_repo
        data["scheduler_repo"] = self.scheduler_repo
        data["analytics_repo"] = self.analytics_repo
        data["plan_repo"] = self.plan_repo # <-- Added
        data["guard_service"] = self.guard_service
        data["scheduler_service"] = self.scheduler_service
        data["analytics_service"] = self.analytics_service
        data["subscription_service"] = self.subscription_service # <-- Added
        
        return await handler(event, data)
