from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.bot.database.repositories import SchedulerRepository
from datetime import datetime
import logging
from src.bot.tasks import send_scheduled_message

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self, scheduler: AsyncIOScheduler, repository: SchedulerRepository):
        self.scheduler = scheduler
        self.repository = repository

    async def schedule_post(self, channel_id: int, text: str, schedule_time: datetime) -> str:
        """Saves a post to the DB and schedules it for sending."""
        post_id = await self.repository.create_scheduled_post(channel_id, text, schedule_time)
        job_id = str(post_id)

        self.scheduler.add_job(
            send_scheduled_message,
            trigger='date',
            run_date=schedule_time,
            args=[post_id], # We only pass the simple, pickle-safe post_id
            id=job_id,
            misfire_grace_time=300
        )
        logger.info(f"Scheduled job {job_id} for post {post_id} at {schedule_time}")
        return job_id
