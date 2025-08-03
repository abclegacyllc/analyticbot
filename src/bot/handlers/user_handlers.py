import json
from datetime import datetime, timezone # <-- ADDED timezone
from aiogram import Router, F, types, Bot
# --- ADDED IMPORTS for answerWebAppQuery ---
from aiogram.types import Message, WebAppInfo, MenuButtonWebApp, InlineQueryResultArticle, InputTextMessageContent
from aiogram.filters import CommandStart, Command
from aiogram_i18n import I18nContext

from src.bot.database.repositories import UserRepository, ChannelRepository # <-- ADDED ChannelRepository
from src.bot.services.guard_service import GuardService
from src.bot.services.scheduler_service import SchedulerService # <-- ADDED SchedulerService
from src.bot.services.subscription_service import SubscriptionService


router = Router()

# --- UPDATED HANDLER FOR DATA FROM WEB APP ---
@router.message(F.web_app_data)
async def handle_web_app_data(
    message: Message, 
    i18n: I18nContext, 
    bot: Bot, # <-- ADDED bot instance
    channel_repo: ChannelRepository, # <-- ADDED channel_repo
    scheduler_service: SchedulerService, # <-- ADDED scheduler_service
):
    """
    This handler receives data sent from the Telegram Web App.
    """
    data = json.loads(message.web_app_data.data)
    query_id = message.web_app_data.query_id # Get the query_id for the response

    # --- HANDLE CHANNEL LIST REQUEST ---
    if data.get('type') == 'get_channels':
        user_channels = await channel_repo.get_user_channels(message.from_user.id)
        
        # Format channels for sending to the web app
        channels_payload = [
            {"id": str(ch['channel_id']), "name": ch['channel_name']} for ch in user_channels
        ]
        
        # Send the channel list back to the TWA as a JSON string
        result = InlineQueryResultArticle(
            id=query_id, # Must be unique, so we use the query_id
            title="Channels Response",
            input_message_content=InputTextMessageContent(message_text="."), # Required but not shown
            description=json.dumps(channels_payload) # <-- OUR DATA PAYLOAD
        )
        
        await bot.answer_web_app_query(query_id, results=[result])
        return # Stop processing after sending the channel list

    # --- HANDLE NEW POST SUBMISSION ---
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
            
            await message.answer(
                i18n.get(
                    "schedule-success", 
                    channel_name=f"ID {channel_id}",
                    schedule_time=aware_dt.strftime('%Y-%m-%d %H:%M %Z')
                )
            )

        except (ValueError, TypeError, KeyError) as e:
            await message.answer(f"Error processing post data: {e}")
            
    else:
        await message.answer(i18n.get('twa-data-unknown'))


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    i18n: I18nContext,
    user_repo: UserRepository, # Dependency injected by middleware
    bot: Bot # Getting the bot instance itself
):
    # Create or update user
    await user_repo.create_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
    )

    # Set the menu button
    dashboard_url = "https://jubilant-enigma-x5q55p7vpwrr3vp56-5173.app.github.dev/"
    await bot.set_chat_menu_button(
        chat_id=message.chat.id,
        menu_button=MenuButtonWebApp(
            text=i18n.get("menu-button-dashboard"),
            web_app=WebAppInfo(url=dashboard_url)
        )
    )
    
    # Send the welcome message
    await message.answer(
        i18n.get("start_message", user_name=message.from_user.full_name)
    )


@router.message(Command("myplan"))
async def my_plan_handler(
    message: Message,
    i18n: I18nContext,
    subscription_service: SubscriptionService, # Dependency injected
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
    

@router.message(F.text)
async def check_blacklist_handler(
    message: Message,
    guard_service: GuardService # Dependency injected by middleware
):
    if message.chat.type in ["group", "supergroup", "channel"]:
        is_blocked = await guard_service.is_blocked(message.chat.id, message.text)
        
        if is_blocked:
            try:
                await message.delete()
            except Exception:
                pass
