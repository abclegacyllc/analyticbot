from celery import Celery
from celery.schedules import crontab

from src.bot.config import settings

celery_app = Celery(
    "tasks",
    broker=settings.REDIS_URL,
    include=["src.bot.tasks"]
)

celery_app.conf.beat_schedule = {
    # Har daqiqada rejalashtirilgan postlarni yuborishni tekshiradi
    'send-scheduled-posts': {
        'task': 'src.bot.tasks.send_pending_posts_task',
        'schedule': crontab(minute='*'),  # Har daqiqada
    },
    # --- YANGI JADVAL ---
    # Har 30 daqiqada postlarning ko'rishlar sonini yangilaydi
    'update-post-views-every-30-minutes': {
        'task': 'src.bot.tasks.update_post_views_task',
        'schedule': crontab(minute='*/30'),  # Har 30 daqiqada
    },
}

celery_app.conf.timezone = 'UTC'
