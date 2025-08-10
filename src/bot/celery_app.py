from celery import Celery
from celery.schedules import crontab
from src.bot.config import settings

# Celery ilovasini yaratish
celery_app = Celery(
    "bot_tasks",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    include=["src.bot.tasks"]
)

celery_app.conf.update(
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    # --- O'ZGARTIRILGAN QISM ---
    beat_schedule={
        # Har daqiqada rejalashtirilgan postlarni tekshiradi va yuboradi
        "send-scheduled-posts": {
            "task": "src.bot.tasks.send_scheduled_message",
            "schedule": crontab(minute="*/1"),
        },
        # Har 15 daqiqada post ko'rishlarini yangilaydi
        "update-views": {
            "task": "src.bot.tasks.update_post_views_task",
            "schedule": crontab(minute="*/15"),
        }
    },
)
