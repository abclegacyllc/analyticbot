import json
import logging
from datetime import datetime, timezone
from aiogram import Router, F, types, Bot
from aiogram.types import (
    Message,
    WebAppInfo,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import CommandStart, Command
from aiogram_i18n import I18nContext

from src.bot.config import settings
from src.bot.database.repositories import UserRepository, ChannelRepository, SchedulerRepository
from src.bot.services.scheduler_service import SchedulerService
from src.bot.services.subscription_service import SubscriptionService # Added back for myplan

router = Router()
logger = logging.getLogger(__name__)

@router.message(F.web_app_data)
async def handle_web_app_data(
    message: Message,
    channel_repo: ChannelRepository,
    scheduler_repo: SchedulerRepository,
    scheduler_service: SchedulerService,
):
    """
    Handles data from TWA by sending a direct message back to the user,
    which is the most reliable communication method.
    """
    try:
        data = json.loads(message.web_app_data.data)
        request_type = data.get('type')

        # --- Step 1: Handle actions that change data (like creating or deleting) ---
        if request_type == 'new_post':
            try:
                channel_id = int(data.get('channel_id'))
                post_text = data.get('text', 'No text provided')
                naive_dt = datetime.fromisoformat(data.get('schedule_time'))
                aware_dt = naive_dt.replace(tzinfo=timezone.utc)
                await scheduler_service.schedule_post(channel_id, post_text, aware_dt)
            except Exception as e:
                logger.error(f"Failed to create post: {e}")
            return # Stop processing for this type

        elif request_type == 'delete_post':
            try:
                post_id = int(data.get('post_id'))
                await scheduler_service.delete_post(post_id)
            except Exception as e:
                logger.error(f"Failed to delete post: {e}")
            return # Stop processing for this type

        # --- Step 2: Handle requests that need data back ---
        response_data = {}
        response_type = "unknown_response"

        if request_type == 'get_channels':
            user_channels = await channel_repo.get_user_channels(message.from_user.id)
            response_data = [{"id": str(ch['channel_id']), "name": ch['channel_name']} for ch in user_channels]
            response_type = "channels_response"

        elif request_type == 'get_scheduled_posts':
            pending_posts = await scheduler_repo.get_pending_posts_by_user(message.from_user.id)
            response_data = [
                {
                    "id": post['post_id'],
                    "text": post['text'],
                    "schedule_time": post['schedule_time'].isoformat(),
                    "channel_name": post['channel_name']
                } for post in pending_posts
            ]
            response_type = "scheduled_posts_response"
        
        # --- Step 3: Send the data back in a specially formatted message ---
        if response_type != "unknown_response":
            formatted_message = (
                f"<pre>__TWA_RESPONSE__||{response_type}||"
                f"{json.dumps(response_data)}</pre>"
            )
            await message.answer(formatted_message, parse_mode="HTML")
            
    except Exception as e:
        logger.error(f"An error occurred in handle_web_app_data: {e}", exc_info=True)


@router.message(CommandStart())
async def cmd_start(message: Message, i18n: I18nContext, user_repo: UserRepository):
    await user_repo.create_user(
        user_id=message.from_user.id, 
        username=message.from_user.username
    )
    await message.answer(i18n.get("start_message", user_name=message.from_user.full_name))


@router.message(Command("dashboard"))
async def cmd_dashboard(message: Message, i18n: I18nContext):
    web_app_info = WebAppInfo(url=str(settings.TWA_HOST_URL))
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=i18n.get("menu-button-dashboard"), web_app=web_app_info)]
    ])
    await message.answer("Click the button below to open your dashboard:", reply_markup=keyboard)


@router.message(Command("myplan"))
async def my_plan_handler(
    message: Message,
    i18n: I18nContext,
    subscription_service: SubscriptionService,
):
    status = await subscription_service.get_user_subscription_status(message.from_user.id)
    if not status:
        return await message.answer(i18n.get("myplan-error"))
        
    text = [f"<b>{i18n.get('myplan-header')}</b>\n"]
    text.append(i18n.get("myplan-plan-name", plan_name=status.plan_name.upper()))
    
    if status.max_channels == -1:
        text.append(i18n.get("myplan-channels-unlimited", current=status.current_channels))
    else:
        text.append(i18n.get("myplan-channels-limit", current=status.current_channels, max=status.max_channels))
        
    if status.max_posts_per_month == -1:
        text.append(i18n.get("myplan-posts-unlimited", current=status.current_posts_this_month))
    else:
        text.append(i18n.get("myplan-posts-limit", current=status.current_posts_this_month, max=status.max_posts_per_month))

    await message.answer("\n".join(text))
