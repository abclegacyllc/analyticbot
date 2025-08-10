from celery import Celery
from src.bot.config import load_config

# Ilova sozlamalarini yuklash
settings = load_config()

# Celery ilovasini yaratish
# Endi broker va backend uchun yagona .dsn() metodidan foydalanamiz
celery_app = Celery(
    "analytic_bot_tasks",
    broker=settings.redis.dsn(),
    backend=settings.redis.dsn(),
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
