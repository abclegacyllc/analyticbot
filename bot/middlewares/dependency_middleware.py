import punq
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker

# Repozitoriy va Servislarni type hinting uchun import qilamiz
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


class DependencyMiddleware(BaseMiddleware):
    """
    Bu middleware har bir 'update' (xabar, callback) uchun DI konteyneridan foydalanib,
    kerakli qaramliklarni (servis va repozitoriylarni) yaratadi va ularni
    handler'larga `data` lug'ati orqali uzatadi.
    """
    def __init__(self, container: punq.Container):
        self.container = container

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Har bir so'rov uchun konteynerdan kerakli qaramliklarni "tortib olamiz"
        # va ularni `data` lug'atiga qo'shamiz.
        data["session_pool"] = self.container.resolve(async_sessionmaker)
        data["user_repo"] = self.container.resolve(UserRepository)
        data["plan_repo"] = self.container.resolve(PlanRepository)
        data["channel_repo"] = self.container.resolve(ChannelRepository)
        data["scheduler_repo"] = self.container.resolve(SchedulerRepository)
        data["analytics_repo"] = self.container.resolve(AnalyticsRepository)
        data["subscription_service"] = self.container.resolve(SubscriptionService)
        data["guard_service"] = self.container.resolve(GuardService)
        data["scheduler_service"] = self.container.resolve(SchedulerService)
        data["analytics_service"] = self.container.resolve(AnalyticsService)

        return await handler(event, data)