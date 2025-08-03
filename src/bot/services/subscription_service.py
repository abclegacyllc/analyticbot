from src.bot.config import Settings
from src.bot.database.repositories import (
    PlanRepository,
    ChannelRepository,
    SchedulerRepository,
    UserRepository
)

class SubscriptionService:
    def __init__(
        self,
        settings: Settings,
        user_repo: UserRepository,
        plan_repo: PlanRepository,
        channel_repo: ChannelRepository,
        scheduler_repo: SchedulerRepository,
    ):
        self.settings = settings
        self.user_repo = user_repo
        self.plan_repo = plan_repo
        self.channel_repo = channel_repo
        self.scheduler_repo = scheduler_repo

    async def check_channel_limit(self, user_id: int) -> bool:
        """Checks if a user can add a new channel based on their plan."""
        # If enforcement is turned off, always allow
        if not self.settings.ENFORCE_PLAN_LIMITS:
            return True

        user_plan_name = await self.user_repo.get_user_plan(user_id)
        if not user_plan_name:
            return False # Should not happen for existing users

        plan_details = await self.plan_repo.get_plan_by_name(user_plan_name)
        if not plan_details:
            return False # Plan does not exist in DB

        max_channels = plan_details['max_channels']
        # -1 means unlimited
        if max_channels == -1:
            return True

        current_channels = await self.channel_repo.count_user_channels(user_id)
        return current_channels < max_channels

    async def check_post_limit(self, user_id: int) -> bool:
        """Checks if a user can schedule a new post based on their plan."""
        if not self.settings.ENFORCE_PLAN_LIMITS:
            return True
            
        user_plan_name = await self.user_repo.get_user_plan(user_id)
        if not user_plan_name:
            return False

        plan_details = await self.plan_repo.get_plan_by_name(user_plan_name)
        if not plan_details:
            return False

        max_posts = plan_details['max_posts_per_month']
        if max_posts == -1:
            return True

        posts_this_month = await self.scheduler_repo.count_user_posts_this_month(user_id)
        return posts_this_month < max_posts
