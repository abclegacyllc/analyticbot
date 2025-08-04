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
from aiogram.fsm.context import FSMContext

from src.bot.config import settings
from src.bot.database.repositories import UserRepository, ChannelRepository, SchedulerRepository
from src.bot.services.scheduler_service import SchedulerService
from src.bot.services.subscription_service import SubscriptionService

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.web_app_data)
async def handle_web_app_data(
    message: Message,
    channel_repo: ChannelRepository,
    scheduler_repo: SchedulerRepository,
    scheduler_service: SchedulerService,
    state: FSMContext,
):
    """
    Handles all data requests and actions from the TWA.
    """
    try:
        data = json.loads(message.web_app_data.data)
        request_type = data.get('type')

        response_data = {}
        response_type = "unknown_response"

        # --- HANDLE DATA REQUEST ---
        if request_type == 'get_initial_data':
            # TWA is requesting all data at once
            user_channels = await channel_repo.get_user_channels(message.from_user.id)
            pending_posts = await scheduler_repo.get_pending_posts_by_user(message.from_user.id)
            user_state = await state.get_data()
            
            response_data = {
                "channels": [{"id": str(ch['channel_id']), "name": ch['channel_name']} for ch in user_channels],
                "posts": [
                    {
                        "id": post['post_id'], "text": post['text'] or "", # Ensure text is not None
                        "schedule_time": post['schedule_time'].isoformat(),
                        "channel_name": post['channel_name'],
                        "file_id": post['file_id'], # Pass media info for the list
                        "file_type": post['file_type']
                    } for post in pending_posts
                ],
                "media": { # Pass the temporarily stored media info
                    "file_id": user_state.get('media_file_id'),
                    "file_type": user_state.get('media_file_type')
                }
            }
            response_type = "initial_data_response"
        
        # --- HANDLE ACTIONS ---
        elif request_type == 'new_post':
            try:
                await scheduler_service.schedule_post(
                    channel_id=int(data.get('channel_id')),
                    text=data.get('text'),
                    schedule_time=datetime.fromisoformat(data.get('schedule_time')),
                    file_id=data.get('file_id'),
                    file_type=data.get('file_type')
                )
                # After scheduling, clear the temporary media from state
                await state.update_data(media_file_id=None, media_file_type=None)
            except Exception as e:
                logger.error(f"Failed to create post: {e}")
            return # Actions don't need a data response

        elif request_type == 'delete_post':
            try:
                await scheduler_service.delete_post(int(data.get('post_id')))
            except Exception as e:
                logger.error(f"Failed to delete post: {e}")
            return # Actions don't need a data response

        # --- SEND DATA RESPONSE BACK TO TWA ---
        if response_type != "unknown_response":
            # We add a special wrapper to make it easy to parse on the frontend
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
    # Make sure your TWA_HOST_URL in the .env file is correct
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

    # Show channel usage
    if status.max_channels == -1:
        text.append(i18n.get("myplan-channels-unlimited", current=status.current_channels))
    else:
        text.append(i18n.get("myplan-channels-limit", current=status.current_channels, max=status.max_channels))

    # Show post usage
    if status.max_posts_per_month == -1:
        text.append(i18n.get("myplan-posts-unlimited", current=status.current_posts_this_month))
    else:
        text.append(i18n.get("myplan-posts-limit", current=status.current_posts_this_month, max=status.max_posts_per_month))

    await message.answer("\n".join(text))
