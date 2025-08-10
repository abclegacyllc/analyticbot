from celery import Celery
# To'g'ridan-to'g'ri tayyor 'settings' obyektini import qilamiz
from src.bot.config import settings

# Celery ilovasini yaratish
# Endi broker va backend uchun yagona .dsn() metodidan foydalanamiz
celery_app = Celery(
    "analytic_bot_tasks",
    broker=settings.REDIS_URL.unicode_string(),
    backend=settings.REDIS_URL.unicode_string(),
    include=["src.bot.tasks"],
)

# Davriy vazifalarni (Celery Beat) sozlash
celery_app.conf.beat_schedule = {
    'send-scheduled-messages-every-minute': {
        'task': 'src.bot.tasks.send_scheduled_message',
        'schedule': 60.0,  # Har 60 soniyada ishga tushadi
    },
    'update-post-views-every-15-minutes': {
        'task': 'src.bot.tasks.update_post_views_task',
        'schedule': 900.0, # Har 900 soniyada (15 daqiqada) ishga tushadi
    },
}

celery_app.conf.timezone = 'UTC'
