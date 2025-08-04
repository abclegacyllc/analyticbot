import json
from datetime import datetime, timezone
from aiogram import Router, F, types, Bot
from aiogram.types import Message, WebAppInfo, MenuButtonWebApp, InlineQueryResultArticle, InputTextMessageContent
from aiogram.filters import CommandStart, Command
from aiogram_i18n import I18nContext

# --- NEW IMPORT ---
# Import the central settings object
from src.bot.config import settings
from src.bot.database.repositories import UserRepository, ChannelRepository, SchedulerRepository
from src.bot.services.guard_service import GuardService
from src.bot.services.scheduler_service import SchedulerService
from src.bot.services.subscription_service import SubscriptionService


router = Router()

# ... handle_web_app_data function stays the same ...
@router.message(F.web_app_data)
async def handle_web_app_data(
    message: Message,
    i18n: I18nContext,
    bot: Bot,
    channel_repo: ChannelRepository,
    scheduler_repo: SchedulerRepository, # <-- NEW: scheduler_repo is now needed here
    scheduler_service: SchedulerService,
):
    """
    This handler receives data sent from the Telegram Web App.
    """
    data = json.loads(message.web_app_data.data)
    query_id = message.web_app_data.query_id

    # --- HANDLE 'get_channels' REQUEST ---
    if data.get('type') == 'get_channels':
        user_channels = await channel_repo.get_user_channels(message.from_user.id)
        channels_payload = [{"id": str(ch['channel_id']), "name": ch['channel_name']} for ch in user_channels]
        result = InlineQueryResultArticle(
            id=query_id,
            title="Channels Response",
            input_message_content=InputTextMessageContent(message_text="."),
            description=json.dumps(channels_payload)
        )
        await bot.answer_web_app_query(query_id, results=[result])
        return

    # --- HANDLE 'new_post' SUBMISSION ---
    elif data.get('type') == 'new_post':
        try:
            # ... (this part is unchanged)
            channel_id = int(data.get('channel_id'))
            post_text = data.get('text', 'No text provided')
            naive_dt = datetime.fromisoformat(data.get('schedule_time'))
            aware_dt = naive_dt.replace(tzinfo=timezone.utc)

            await scheduler_service.schedule_post(
                channel_id=channel_id,
                text=post_text,
                schedule_time=aware_dt
            )
            await message.answer(
                i18n.get(
                    "schedule-success",
                    channel_name=f"ID {channel_id}",
                    schedule_time=aware_dt.strftime('%Y-%m-%d %H:%M %Z')
                )
            )
        except (ValueError, TypeError, KeyError) as e:
            await message.answer(f"Error processing post data: {e}")
        return # <-- Important: Add return here

    # --- NEW: HANDLE 'get_scheduled_posts' REQUEST ---
    elif data.get('type') == 'get_scheduled_posts':
        # We need the scheduler_repo, which we already get from middleware
        pending_posts = await scheduler_repo.get_pending_posts_by_user(message.from_user.id)
        
        # Format posts for sending to the web app
        posts_payload = [
            {
                "id": post['post_id'],
                "text": post['text'],
                # Format datetime to a string that JS can easily parse
                "schedule_time": post['schedule_time'].isoformat(),
                "channel_name": post['channel_name']
            } for post in pending_posts
        ]
        
        result = InlineQueryResultArticle(
            id=query_id,
            title="Scheduled Posts Response",
            input_message_content=InputTextMessageContent(message_text="."),
            description=json.dumps(posts_payload)
        )
        await bot.answer_web_app_query(query_id, results=[result])
        return

    # --- NEW: HANDLE 'delete_post' REQUEST ---
    elif data.get('type') == 'delete_post':
        try:
            post_id = int(data.get('post_id'))
            success = await scheduler_service.delete_post(post_id)
            if success:
                # We can just respond with a simple alert in the TWA
                await bot.answer_web_app_query(query_id, results=[]) # Sending an empty result is fine
                # Optionally, you can send a message to the chat
                # await message.answer(f"Post {post_id} deleted.")
            else:
                # Inform the TWA if deletion failed
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
            # Handle potential errors if post_id is missing or invalid
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

    # --- Fallback for unknown data types ---
    else:
        await message.answer(i18n.get('twa-data-unknown'))


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    i18n: I18nContext,
    user_repo: UserRepository,
    bot: Bot
):
    # Create or update user
    await user_repo.create_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
    )

    # --- MODIFIED PART ---
    # The menu button URL is now loaded from our configuration settings
    await bot.set_chat_menu_button(
        chat_id=message.chat.id,
        menu_button=MenuButtonWebApp(
            text=i18n.get("menu-button-dashboard"),
            # Convert the Pydantic AnyHttpUrl to a string for the API call
            web_app=WebAppInfo(url=str(settings.TWA_HOST_URL))
        )
    )
    
    # Send the welcome message
    await message.answer(
        i18n.get("start_message", user_name=message.from_user.full_name)
    )


# ... my_plan_handler and check_blacklist_handler stay the same ...
@router.message(Command("myplan"))
async def my_plan_handler(
    message: Message,
    i18n: I18nContext,
    subscription_service: SubscriptionService,
):
# ... this function's code is unchanged ...
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
# ... this function's code is unchanged ...
    if message.chat.type in ["group", "supergroup", "channel"]:
        is_blocked = await guard_service.is_blocked(message.chat.id, message.text)
        
        if is_blocked:
            try:
                await message.delete()
            except Exception:
                pass
