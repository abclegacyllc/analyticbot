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
    This handler processes all data sent from the Telegram Web App.
    """
    data = json.loads(message.web_app_data.data)
    query_id = message.web_app_data.query_id

    # --- Route requests based on the 'type' field ---

    # Request: Get the user's registered channels
    if data.get('type') == 'get_channels':
        user_channels = await channel_repo.get_user_channels(message.from_user.id)
        channels_payload = [{"id": str(ch['channel_id']), "name": ch['channel_name']} for ch in user_channels]
        result = InlineQueryResultArticle(
            id=query_id,
            title="Channels Response", # Used by the frontend to identify the data
            input_message_content=InputTextMessageContent(message_text="."),
            description=json.dumps(channels_payload)
        )
        await bot.answer_web_app_query(query_id, results=[result])
        return

    # Request: Schedule a new post
    elif data.get('type') == 'new_post':
        try:
            channel_id = int(data.get('channel_id'))
            post_text = data.get('text', 'No text provided')
            naive_dt = datetime.fromisoformat(data.get('schedule_time'))
            aware_dt = naive_dt.replace(tzinfo=timezone.utc)
            await scheduler_service.schedule_post(
                channel_id=channel_id,
                text=post_text,
                schedule_time=aware_dt
            )
            # This confirmation message is sent to the private chat with the bot
            await message.answer(
                i18n.get(
                    "schedule-success",
                    channel_name=f"ID {channel_id}",
                    schedule_time=aware_dt.strftime('%Y-%m-%d %H:%M %Z')
                )
            )
        except (ValueError, TypeError, KeyError) as e:
            await message.answer(f"Error processing post data: {e}")
        return

    # Request: Get all currently pending scheduled posts
    elif data.get('type') == 'get_scheduled_posts':
        pending_posts = await scheduler_repo.get_pending_posts_by_user(message.from_user.id)
        posts_payload = [
            {
                "id": post['post_id'],
                "text": post['text'],
                "schedule_time": post['schedule_time'].isoformat(),
                "channel_name": post['channel_name']
            } for post in pending_posts
        ]
        result = InlineQueryResultArticle(
            id=query_id,
            title="Scheduled Posts Response", # Used by the frontend
            input_message_content=InputTextMessageContent(message_text="."),
            description=json.dumps(posts_payload)
        )
        await bot.answer_web_app_query(query_id, results=[result])
        return

    # Request: Delete a specific scheduled post
    elif data.get('type') == 'delete_post':
        try:
            post_id = int(data.get('post_id'))
            success = await scheduler_service.delete_post(post_id)
            if success:
                # Acknowledge successful deletion to the TWA. An empty result is fine.
                await bot.answer_web_app_query(query_id, results=[])
            else:
                 # Inform the TWA if deletion failed in the backend
                 await bot.answer_web_app_query(
                    query_id,
                    results=[InlineQueryResultArticle(
                        id=f"error_{post_id}",
                        title="Deletion Failed",
                        input_message_content=InputTextMessageContent(message_text="."),
                        description=json.dumps({"error": "Post not found or could not be deleted."})
                    )]
                )
        except (ValueError, TypeError, KeyError) as e:
            # Handle cases where the request from the TWA is malformed
            await bot.answer_web_app_query(
                query_id,
                results=[InlineQueryResultArticle(
                    id="error_delete",
                    title="Error",
                    input_message_content=InputTextMessageContent(message_text="."),
                    description=json.dumps({"error": f"Invalid request: {e}"})
                )]
            )
        return

    # Fallback for any unknown request types
    else:
        await message.answer(i18n.get('twa-data-unknown'))


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
