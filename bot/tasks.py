import asyncio
import logging

from aiogram import Bot

from bot.celery_app import celery_app
from bot.config import settings
from bot.database import db
from bot.database.repositories import SchedulerRepository, AnalyticsRepository
from bot.services.scheduler_service import SchedulerService
from bot.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)


@celery_app.task(name='send_scheduled_message')
def send_scheduled_message(post_data: dict):
    """
    Rejalashtirilgan postni yuborish uchun Celery vazifasi.
    Bu vazifa SchedulerService orqali rejalashtiriladi.
    """
    logger.info(f"Executing task to send post {post_data.get('id')}")

    async def run_task():
        db_pool = await db.create_pool()
        bot = Bot(token=settings.BOT_TOKEN.get_secret_value(), parse_mode='HTML')
        
        scheduler_repo = SchedulerRepository(db_pool)
        analytics_repo = AnalyticsRepository(db_pool)
        scheduler_service = SchedulerService(bot, scheduler_repo, analytics_repo)
        
        try:
            await scheduler_service.send_post_to_channel(post_data)
        finally:
            await db_pool.close()
            await bot.session.close()

    asyncio.run(run_task())


# --- YANGI VAZIFA ---
@celery_app.task(name='update_post_views_task')
def update_post_views_task():
    """
    Barcha kuzatuvdagi postlarning ko'rishlar sonini yangilash uchun Celery vazifasi.
    Bu vazifa celery_app.py da jadval asosida (periodically) ishga tushiriladi.
    """
    logger.info("Starting scheduled task to update post views.")

    async def run_task():
        db_pool = await db.create_pool()
        bot = Bot(token=settings.BOT_TOKEN.get_secret_value(), parse_mode='HTML')

        analytics_repo = AnalyticsRepository(db_pool)
        analytics_service = AnalyticsService(bot, analytics_repo)

        try:
            await analytics_service.update_all_post_views()
        finally:
            await db_pool.close()
            await bot.session.close()

    asyncio.run(run_task())
