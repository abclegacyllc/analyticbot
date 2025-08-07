from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

# Loyihadagi kerakli modullarni import qilamiz
from src.bot.database.repositories import (
    UserRepository,
    ChannelRepository,
    PlanRepository,
)
from src.bot.services.guard_service import GuardService
from src.bot.services.subscription_service import SubscriptionService

class DependencyMiddleware(BaseMiddleware):
    # --- YECHIM: Endi faqat botga kerakli argumentlarni qabul qilamiz ---
    def __init__(
        self,
        user_repo: UserRepository,
        channel_repo: ChannelRepository,
        plan_repo: PlanRepository,
        guard_service: GuardService,
        subscription_service: SubscriptionService,
    ):
        self.user_repo = user_repo
        self.channel_repo = channel_repo
        self.plan_repo = plan_repo
        self.guard_service = guard_service
        self.subscription_service = subscription_service

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Har bir handler'ga kerakli obyektlarni "data" lug'ati orqali uzatamiz
        data["user_repo"] = self.user_repo
        data["channel_repo"] = self.channel_repo
        data["plan_repo"] = self.plan_repo
        data["guard_service"] = self.guard_service
        data["subscription_service"] = self.subscription_service
        
        return await handler(event, data)
