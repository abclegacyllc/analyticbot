import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.bot.database.repositories import SchedulerRepository
from src.bot.tasks import send_scheduled_message

class SchedulerService:
    def __init__(self, scheduler: AsyncIOScheduler, repo: SchedulerRepository):
        self.scheduler = scheduler
        self.repo = repo

    async def schedule_post(
        self,
        channel_id: int,
        text: Optional[str],
        schedule_time: datetime,
        file_id: Optional[str] = None,
        file_type: Optional[str] = None,
        # --- YANGI PARAMETR ---
        inline_buttons: Optional[List[Dict[str, str]]] = None
    ):
        """
        Schedules a post to be sent at a specific time.
        """
        # Tugmalarni saqlashdan oldin JSON satriga aylantiramiz
        buttons_json = json.dumps(inline_buttons) if inline_buttons else None

        post_id = await self.repo.create_scheduled_post(
            channel_id=channel_id,
            text=text,
            schedule_time=schedule_time,
            file_id=file_id,
            file_type=file_type,
            # --- YANGI MAYDON ---
            inline_buttons=buttons_json
        )
        
        # Add the job to APScheduler
        self.scheduler.add_job(
            send_scheduled_message,
            "date",
            run_date=schedule_time,
            args=[post_id],
            id=f"post_{post_id}",
            replace_existing=True
        )

    async def delete_post(self, post_id: int):
        """
        Deletes a scheduled post and removes it from the scheduler.
        """
        await self.repo.delete_scheduled_post(post_id)
        
        # Remove the job from APScheduler
        job_id = f"post_{post_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
