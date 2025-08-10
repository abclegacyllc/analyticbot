from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from asyncpg import Pool
from redis.asyncio import Redis

# Repozitoriylarni import qilamiz
from src.bot.database.repositories import (
    UserRepository,
    PlanRepository,
    ChannelRepository,
    SchedulerRepository,
    AnalyticsRepository
)

# --- YECHIM: Har bir servisni o'zining faylidan to'g'ridan-to'g'ri import qilamiz ---
from src.bot.services.guard_service import GuardService
from src.bot.services.subscription_service import SubscriptionService
from src.bot.services.scheduler_service import SchedulerService
from src.bot.services.analytics_service import AnalyticsService

class DependencyMiddleware(BaseMiddleware):
    def __init__(
        self,
        db_pool: Pool,
        redis_pool: Redis,
        user_repo: UserRepository,
        plan_repo: PlanRepository,
        channel_repo: ChannelRepository,
        scheduler_repo: SchedulerRepository,
        analytics_repo: AnalyticsRepository,
        guard_service: GuardService,
        subscription_service: SubscriptionService,
        scheduler_service: SchedulerService,
        analytics_service: AnalyticsService
    ):
        super().__init__()
        self.db_pool = db_pool
        self.redis_pool = redis_pool
        self.user_repo = user_repo
        self.plan_repo = plan_repo
        self.channel_repo = channel_repo
        self.scheduler_repo = scheduler_repo
        self.analytics_repo = analytics_repo
        self.guard_service = guard_service
        self.subscription_service = subscription_service
        self.scheduler_service = scheduler_service
        self.analytics_service = analytics_service

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        data["db_pool"] = self.db_pool
        data["redis_pool"] = self.redis_pool
        data["user_repo"] = self.user_repo
        data["plan_repo"] = self.plan_repo
        data["channel_repo"] = self.channel_repo
        data["scheduler_repo"] = self.scheduler_repo
        data["analytics_repo"] = self.analytics_repo
        data["guard_service"] = self.guard_service
        data["subscription_service"] = self.subscription_service
        data["scheduler_service"] = self.scheduler_service
        data["analytics_service"] = self.analytics_service
        
        return await handler(event, data)
