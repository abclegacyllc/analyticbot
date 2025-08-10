from celery import Celery
from src.bot.config import settings  # <-- load_config emas, bevosita settings

# Celery app - nomi standart: "app"
app = Celery(
    "analytic_bot_tasks",
    broker=str(settings.REDIS_URL),   # <-- REDIS_URL ni to'g'ri ishlatamiz
    backend=str(settings.REDIS_URL),
    include=["src.bot.tasks"],
)

app.conf.beat_schedule = {
    'send-scheduled-messages-every-minute': {
        'task': 'src.bot.tasks.send_scheduled_message',
        'schedule': 60.0,
    },
    'update-post-views-every-15-minutes': {
        'task': 'src.bot.tasks.update_post_views_task',
        'schedule': 900.0,
    },
}

app.conf.timezone = 'UTC'
