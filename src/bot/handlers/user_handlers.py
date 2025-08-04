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
    message: Message,
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

        if data.get('type') == 'get_channels':
            title = "Channels Response"
            user_channels = await channel_repo.get_user_channels(message.from_user.id)
            response_payload = [{"id": str(ch['channel_id']), "name": ch['channel_name']} for ch in user_channels]

        elif data.get('type') == 'get_scheduled_posts':
            title = "Scheduled Posts Response"
            pending_posts = await scheduler_repo.get_pending_posts_by_user(message.from_user.id)
            response_payload = [
                {
                    "id": post['post_id'], "text": post['text'],
                    "schedule_time": post['schedule_time'].isoformat(),
                    "channel_name": post['channel_name']
                } for post in pending_posts
            ]

        # For other types like 'new_post' or 'delete_post', we just send an empty successful response
        elif data.get('type') in ['new_post', 'delete_post']:
            title = "Action Acknowledged"
            # Handle the actual action
            if data.get('type') == 'new_post':
                # ... (new_post logic)
            elif data.get('type') == 'delete_post':
                # ... (delete_post logic)

        result = InlineQueryResultArticle(
            id=query_id,
            title=title,
            # Let's try sending a more descriptive text.
            input_message_content=InputTextMessageContent(
                message_text=f"Processed TWA request: {title}"
            ),
            description=json.dumps(response_payload)
        )
        await bot.answer_web_app_query(query_id, results=[result])

    except Exception as e:
        logger.error(f"Error processing TWA data: {e}", exc_info=True)
        # You can also try to notify the user via answer_web_app_query
        await bot.answer_web_app_query(query_id, results=[
            InlineQueryResultArticle(
                id=query_id,
                title="Error",
                input_message_content=InputTextMessageContent(message_text="An error occurred."),
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
