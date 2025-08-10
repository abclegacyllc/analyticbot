import os
from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    "analytic_bot",
    broker=os.environ.get("CELERY_BROKER_URL"),
    backend=os.environ.get("CELERY_RESULT_BACKEND"),
    include=["src.bot.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Tashkent",
    enable_utc=True,
    beat_schedule={
        "send-scheduled-posts": {
            # XATO TO'G'RILANDI: Vazifa nomi to'g'ri ko'rsatildi
            "task": "src.bot.tasks.send_scheduled_message",
            # Har daqiqada tekshirish
            "schedule": crontab(minute="*/1"),
        },
    },
)
