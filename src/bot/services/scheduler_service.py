from apscheduler.schedulers.asyncio import AsyncIOScheduler
# --- ADD JOBDOESNOTEXISTERROR ---
from apscheduler.jobstores.base import JobLookupError
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
            args=[post_id],
            id=job_id,
            misfire_grace_time=300
        )
        logger.info(f"Scheduled job {job_id} for post {post_id} at {schedule_time}")
        return job_id

    # --- NEW METHOD ---
    async def delete_post(self, post_id: int) -> bool:
        """Removes a scheduled job and deletes the post from the database."""
        job_id = str(post_id)

        # First, try to remove the job from the scheduler
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job {job_id} from scheduler.")
        except JobLookupError:
            # This is not critical, maybe the job already ran or failed.
            logger.warning(f"Job {job_id} not found in scheduler, but proceeding with DB deletion.")

        # Next, delete the post from the database
        was_deleted = await self.repository.delete_scheduled_post(post_id)
        if was_deleted:
            logger.info(f"Deleted post {post_id} from database.")
        else:
            logger.warning(f"Post {post_id} was not found in the database for deletion.")
        
        return was_deleted
