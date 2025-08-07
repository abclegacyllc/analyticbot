import logging
import asyncio
import json
import asyncpg
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.bot.config import settings
from src.bot.database.db import create_pool
from src.bot.celery_app import celery_app # <-- Celery ilovasini import qilamiz
from src.bot.database.repositories import SchedulerRepository, AnalyticsRepository
from src.bot.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

# --- Celery vazifasiga aylantirilgan funksiya ---
@celery_app.task(bind=True)
def send_scheduled_message(self, post_id: int):
    """
    Bu funksiya endi Celery workeri tomonidan chaqiriladi.
    """
    async def _send():
        db_pool = None
        bot = Bot(token=settings.BOT_TOKEN.get_secret_value())
        try:
            db_pool = await create_pool()
            repo = SchedulerRepository(db_pool)
            post = await repo.get_scheduled_post(post_id)

            if not post or post['status'] != 'pending':
                logger.warning(f"Post {post_id} not found or not pending. Skipping.")
                return

            # ... (qolgan qismi deyarli o'zgarishsiz) ...
            buttons = json.loads(post['inline_buttons']) if post['inline_buttons'] else []
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=btn['text'], url=btn['url']) for btn in row]
                for row in buttons
            ]) if buttons else None
            
            sent_message = None
            if post['file_id'] and post['file_type'] == 'photo':
                sent_message = await bot.send_photo(
                    chat_id=post['channel_id'], photo=post['file_id'],
                    caption=post['text'], reply_markup=keyboard
                )
            elif post['file_id'] and post['file_type'] == 'video':
                sent_message = await bot.send_video(
                    chat_id=post['channel_id'], video=post['file_id'],
                    caption=post['text'], reply_markup=keyboard
                )
            else:
                sent_message = await bot.send_message(
                    chat_id=post['channel_id'], text=post['text'], reply_markup=keyboard
                )

            await repo.update_post_status(post_id, 'sent')
            await repo.set_sent_message_id(post_id, sent_message.message_id)
            logger.info(f"Successfully sent scheduled post {post_id}")

        except TelegramAPIError as e:
            logger.error(f"Telegram API error while sending post {post_id}: {e}")
            if db_pool:
                await SchedulerRepository(db_pool).update_post_status(post_id, 'failed')
        except Exception as e:
            logger.error(f"Unexpected error while sending post {post_id}: {e}", exc_info=True)
            if db_pool:
                await SchedulerRepository(db_pool).update_post_status(post_id, 'failed')
        finally:
            if db_pool:
                await db_pool.close()
            await bot.session.close()

    # Celery sinxron ishlagani uchun, asinxron kodni shunday ishga tushiramiz
    asyncio.run(_send())

# --- Ikkinchi Celery vazifasi ---
@celery_app.task
def update_all_post_views():
    """
    Barcha postlarning ko'rishlar sonini yangilaydi.
    Bu vazifa Celery Beat tomonidan har soatda avtomatik ishga tushiriladi.
    """
    async def _update():
        db_pool = None
        bot = Bot(token=settings.BOT_TOKEN.get_secret_value())
        try:
            db_pool = await create_pool()
            analytics_repo = AnalyticsRepository(db_pool)
            scheduler_repo = SchedulerRepository(db_pool)
            analytics_service = AnalyticsService(bot, analytics_repo, scheduler_repo)
            
            await analytics_service.update_all_post_views()
        except Exception as e:
            logger.error(f"Error in periodic task update_all_post_views: {e}", exc_info=True)
        finally:
            if db_pool:
                await db_pool.close()
            await bot.session.close()

    asyncio.run(_update())
