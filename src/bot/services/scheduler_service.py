# src/bot/services/scheduler_service.py

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.bot.database.repository import SchedulerRepository
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self, scheduler: AsyncIOScheduler, bot: Bot, repository: SchedulerRepository):
        self.scheduler = scheduler
        self.bot = bot
        self.repository = repository

    async def schedule_post(self, channel_id: int, text: str, schedule_time: datetime) -> str:
        """
        Saves a post to the DB and schedules it for sending.
        Returns the job_id.
        """
        post_id = await self.repository.create_scheduled_post(channel_id, text, schedule_time)
        job_id = str(post_id)

        self.scheduler.add_job(
            self._send_scheduled_message,
            trigger='date',
            run_date=schedule_time,
            args=[post_id],
            id=job_id,
            misfire_grace_time=300  # Allow job to run up to 5 minutes late
        )
        logger.info(f"Scheduled job {job_id} for post {post_id} at {schedule_time}")
        return job_id

    async def _send_scheduled_message(self, post_id: int):
        """The actual function that is called by the scheduler."""
        logger.info(f"Executing job for post_id: {post_id}")
        post = await self.repository.get_scheduled_post(post_id)

        if not post or post['status'] != 'pending':
            logger.warning(f"Post {post_id} not found or not in 'pending' state. Skipping.")
            return

        try:
            await self.bot.send_message(chat_id=post["channel_id"], text=post["text"])
            await self.repository.update_post_status(post_id, "sent")
            logger.info(f"Successfully sent post {post_id} to channel {post['channel_id']}")
        except Exception as e:
            await self.repository.update_post_status(post_id, "failed")
            logger.error(f"Failed to send post {post_id} to channel {post['channel_id']}: {e}")
