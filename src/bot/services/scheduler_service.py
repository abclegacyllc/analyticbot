# FILE: src/bot/services/scheduler_service.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.base import JobLookupError
from src.bot.database.repositories import SchedulerRepository
from datetime import datetime
import logging
from src.bot.tasks import send_scheduled_message

# This service needs access to the bot and db_pool to pass to the job
from src.bot.bot import bot
from src.bot.database.db import create_pool


logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self, scheduler: AsyncIOScheduler, repository: SchedulerRepository):
        self.scheduler = scheduler
        self.repository = repository

    async def schedule_post(self, channel_id: int, text: str, schedule_time: datetime) -> str:
        """Saves a post to the DB and schedules it for sending."""
        post_id = await self.repository.create_scheduled_post(channel_id, text, schedule_time)
        job_id = str(post_id)

        # We must pass the bot and a database pool connection to the job
        # so it can function when it runs in the background.
        db_pool = await create_pool() # Create a fresh pool for the job

        self.scheduler.add_job(
            send_scheduled_message,
            trigger='date',
            run_date=schedule_time,
            id=job_id,
            misfire_grace_time=300,
            kwargs={
                "bot": bot,
                "db_pool": db_pool,
                "post_id": post_id
            }
        )
        logger.info(f"Scheduled job {job_id} for post {post_id} at {schedule_time}")
        return job_id

    async def delete_post(self, post_id: int) -> bool:
        """Removes a scheduled job and deletes the post from the database."""
        job_id = str(post_id)
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job {job_id} from scheduler.")
        except JobLookupError:
            logger.warning(f"Job {job_id} not found in scheduler, but proceeding with DB deletion.")

        was_deleted = await self.repository.delete_scheduled_post(post_id)
        if was_deleted:
            logger.info(f"Deleted post {post_id} from database.")
        else:
            logger.warning(f"Post {post_id} not found in the database for deletion.")
        
        return was_deleted
