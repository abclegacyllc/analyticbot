from celery import Celery
# Nisbiy import
from .config import settings
from . import tasks

celery_app = Celery(
    "analytic_bot_tasks",
    broker=settings.REDIS_URL.unicode_string(),
    backend=settings.REDIS_URL.unicode_string(),
    include=["bot.tasks"],
)

celery_app.conf.beat_schedule = {
    'send-scheduled-messages-every-minute': {
        'task': 'bot.tasks.send_scheduled_message',
        'schedule': 60.0,
    },
    'update-post-views-every-15-minutes': {
        'task': 'bot.tasks.update_post_views_task',
        'schedule': 900.0,
    },
}
celery_app.conf.timezone = 'UTC'