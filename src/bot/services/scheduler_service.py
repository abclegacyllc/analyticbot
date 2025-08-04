from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.base import JobLookupError
from src.bot.database.repositories import SchedulerRepository
from datetime import datetime
import logging
from typing import Optional

from src.bot.tasks import send_scheduled_message

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self, scheduler: AsyncIOScheduler, repository: SchedulerRepository):
        self.scheduler = scheduler
        self.repository = repository

    async def schedule_post(
        self,
        channel_id: int,
        schedule_time: datetime,
        text: Optional[str] = None,
        file_id: Optional[str] = None,
        file_type: Optional[str] = None
    ) -> str:
        """Saves a post to the DB and schedules a self-sufficient task."""
        if not text and not file_id:
            raise ValueError("Post must have either text or a file.")

        post_id = await self.repository.create_scheduled_post(
            channel_id, schedule_time, text, file_id, file_type
        )
        job_id = str(post_id)

        # The task is now self-sufficient, we only need to pass the post_id
        self.scheduler.add_job(
            send_scheduled_message,
            trigger='date',
            run_date=schedule_time,
            id=job_id,
            misfire_grace_time=300,
            args=[post_id]  # Only pass simple, pickle-safe arguments
        )
        logger.info(f"Scheduled job {job_id} for post {post_id} at {schedule_time}")
        return job_id

    async def delete_post(self, post_id: int) -> bool:
        """Removes a scheduled job and deletes the post from the database."""
        job_id = str(post_id)
        try:
            self.scheduler.remove_job(job_id)
        except JobLookupError:
            logger.warning(f"Job {job_id} not found in scheduler.")
        
        return await self.repository.delete_scheduled_post(post_id)
