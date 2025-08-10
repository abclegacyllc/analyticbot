import asyncio
from celery.utils.log import get_task_logger

# YECHIM: Endi 'celery_app'ni xavfsiz import qila olamiz,
# chunki 'celery_app.py' endi bu faylni import qilmayapti.
from bot.celery_app import celery_app
from bot.container import container
from bot.services import SchedulerService, AnalyticsService

logger = get_task_logger(__name__)


@celery_app.task
def send_scheduled_message():
    """Vaqti kelgan rejalashtirilgan xabarlarni yuboradi."""
    logger.info("Running task: send_scheduled_message")
    # Har bir vazifa o'zi uchun kerakli servisni konteynerdan oladi
    scheduler_service = container.resolve(SchedulerService)
    asyncio.run(scheduler_service.send_due_messages())
    logger.info("Finished task: send_scheduled_message")


@celery_app.task
def update_post_views_task():
    """Yuborilgan postlarning ko'rishlar sonini yangilaydi."""
    logger.info("Running task: update_post_views_task")
    analytics_service = container.resolve(AnalyticsService)
    asyncio.run(analytics_service.update_all_post_views())
    logger.info("Finished task: update_post_views_task")
