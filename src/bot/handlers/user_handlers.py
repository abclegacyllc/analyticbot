import logging
import json
from datetime import datetime, timezone
from aiogram import Router, F, types, Bot
from aiogram.types import (
    Message,
    WebAppInfo,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import CommandStart, Command
from aiogram_i18n import I18nContext

# Local application imports
from src.bot.config import settings
from src.bot.database.repositories import UserRepository, ChannelRepository, SchedulerRepository
from src.bot.services.guard_service import GuardService
from src.bot.services.scheduler_service import SchedulerService
from src.bot.services.subscription_service import SubscriptionService


router = Router()

logger = logging.getLogger(__name__)

@router.message(F.web_app_data)
async def handle_web_app_data(
    message: types.Message,
    i18n: I18nContext,
    bot: Bot,
    channel_repo: ChannelRepository,
    scheduler_repo: SchedulerRepository,
    scheduler_service: SchedulerService,
):
    """
    This handler processes data from the TWA using the answer_web_app_query method.
    """
    data = json.loads(message.web_app_data.data)
    query_id = message.web_app_data.query_id

    if not query_id:
        logger.error("query_id is missing! Cannot respond to TWA.")
        return

    try:
        response_payload = {}
        title = "Unknown Response"
        request_type = data.get('type')

        if request_type == 'get_channels':
            title = "Channels Response"
            user_channels = await channel_repo.get_user_channels(message.from_user.id)
            response_payload = [{"id": str(ch['channel_id']), "name": ch['channel_name']} for ch in user_channels]

        elif request_type == 'get_scheduled_posts':
            title = "Scheduled Posts Response"
            pending_posts = await scheduler_repo.get_pending_posts_by_user(message.from_user.id)
            response_payload = [
                {
                    "id": post['post_id'], "text": post['text'],
                    "schedule_time": post['schedule_time'].isoformat(),
                    "channel_name": post['channel_name']
                } for post in pending_posts
            ]

        elif request_type == 'new_post':
            title = "Action Acknowledged"
            channel_id = int(data.get('channel_id'))
            post_text = data.get('text', 'No text provided')
            naive_dt = datetime.fromisoformat(data.get('schedule_time'))
            aware_dt = naive_dt.replace(tzinfo=timezone.utc)
            await scheduler_service.schedule_post(channel_id, post_text, aware_dt)
            # No response payload needed, just an acknowledgement.

        # --- FIX IS HERE ---
        # The logic for delete_post is now correctly indented inside the elif block.
        elif request_type == 'delete_post':
            title = "Action Acknowledged"
            post_id = int(data.get('post_id'))
            await scheduler_service.delete_post(post_id)
            # No response payload needed.

        # Send the response back to the TWA
        result = types.InlineQueryResultArticle(
            id=query_id,
            title=title,
            input_message_content=types.InputTextMessageContent(
                message_text=f"Processed TWA request: {title}"
            ),
            description=json.dumps(response_payload)
        )
        await bot.answer_web_app_query(query_id, results=[result])

    except Exception as e:
        logger.error(f"Error processing TWA data: {e}", exc_info=True)
        # Try to notify the user via TWA about the error
        await bot.answer_web_app_query(query_id, results=[
            types.InlineQueryResultArticle(
                id=query_id,
                title="Error",
                input_message_content=types.InputTextMessageContent(message_text="An error occurred."),
                description=json.dumps({"error": str(e)})
            )
        ])

@router.message(CommandStart())
async def cmd_start(
    message: Message,
    i18n: I18nContext,
    user_repo: UserRepository,
    bot: Bot
):
    """
    Handles the /start command. Onboards the user.
    """
    # Create or update user in the database
    await user_repo.create_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
    )
    
    # We no longer set the menu button here.
    
    # Send the welcome message
    await message.answer(
        i18n.get("start_message", user_name=message.from_user.full_name)
    )


@router.message(Command("dashboard"))
async def cmd_dashboard(message: Message, i18n: I18nContext):
    """
    This handler sends a message with an inline button that opens the TWA.
    This is the correct way to launch a TWA that needs to communicate back.
    """
    web_app_info = WebAppInfo(url=str(settings.TWA_HOST_URL))
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.get("menu-button-dashboard"), # We can reuse the same text key
                    web_app=web_app_info
                )
            ]
        ]
    )
    
    await message.answer("Click the button below to open your dashboard:", reply_markup=keyboard)


@router.message(Command("myplan"))
async def my_plan_handler(
    message: Message,
    i18n: I18nContext,
    subscription_service: SubscriptionService,
):
    """
    Displays the user's current subscription plan and usage.
    """
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


@router.message(F.text)
async def check_blacklist_handler(
    message: Message,
    guard_service: GuardService
):
    """
    Checks for blacklisted words in group/channel messages.
    """
    if message.chat.type in ["group", "supergroup", "channel"]:
        is_blocked = await guard_service.is_blocked(message.chat.id, message.text)
        
        if is_blocked:
            try:
                await message.delete()
            except Exception:
                # Bot might not have delete permissions, fail silently.
                pass
