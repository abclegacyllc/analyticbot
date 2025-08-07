from celery import Celery
from celery.schedules import crontab
from src.bot.config import settings

# Celery ilovasini yaratamiz
celery_app = Celery(
    "tasks",
    broker=settings.REDIS_URL.unicode_string(),  # Xabar brokeri sifatida Redis'ni ishlatamiz
    backend=settings.REDIS_URL.unicode_string(), # Natijalarni saqlash uchun ham Redis
    include=["src.bot.tasks"]  # Vazifalar (tasks) qaysi faylda joylashganini ko'rsatamiz
)

# Celery sozlamalari
celery_app.conf.update(
    task_track_started=True,
)

# --- Davomiy (periodic) vazifalarni sozlash (Celery Beat) ---
# Bu APScheduler'dagi interval vazifasining o'rnini bosadi
celery_app.conf.beat_schedule = {
    'update-post-views-every-hour': {
        'task': 'src.bot.tasks.update_all_post_views',  # Ishga tushiriladigan vazifa
        'schedule': 3600.0,  # Har 3600 soniyada (1 soatda)
    },
}
celery_app.conf.timezone = 'UTC'
