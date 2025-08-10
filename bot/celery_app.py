from celery import Celery
# Importlar yangi strukturaga moslashtirilgan
from bot.config import settings

# Celery ilovasini yaratish
celery_app = Celery(
    "analytic_bot_tasks",
    broker=settings.REDIS_URL.unicode_string(),
    backend=settings.REDIS_URL.unicode_string(),
    # YECHIM: Celery'ga vazifalarni qayerdan topishni 'include' orqali aytamiz.
    # Bu usul 'circular import' muammosining oldini oladi.
    include=["bot.tasks"],
)

# Davriy vazifalarni (Celery Beat) sozlash
celery_app.conf.beat_schedule = {
    'send-scheduled-messages-every-minute': {
        'task': 'bot.tasks.send_scheduled_message',
        'schedule': 60.0,  # Har 60 soniyada ishga tushadi
    },
    'update-post-views-every-15-minutes': {
        'task': 'bot.tasks.update_post_views_task',
        'schedule': 900.0, # Har 900 soniyada (15 daqiqada) ishga tushadi
    },
}

celery_app.conf.timezone = 'UTC'
