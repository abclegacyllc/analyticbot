from celery import Celery
# Nisbiy import orqali sozlamalarni olamiz
from .config import settings
# Vazifalarni aniq import qilamiz
from . import tasks

celery_app = Celery(
    "analytic_bot_tasks",
    broker=settings.REDIS_URL.unicode_string(),
    backend=settings.REDIS_URL.unicode_string(),
    # 'include' hali ham yaxshi amaliyot, lekin yuqoridagi import ishonchliroq
    include=["src.bot.tasks"],
)

# Davriy vazifalarni sozlash
celery_app.conf.beat_schedule = {
    'send-scheduled-messages-every-minute': {
        'task': 'src.bot.tasks.send_scheduled_message',
        'schedule': 60.0,
    },
    'update-post-views-every-15-minutes': {
        'task': 'src.bot.tasks.update_post_views_task',
        'schedule': 900.0,
    },
}

celery_app.conf.timezone = 'UTC'