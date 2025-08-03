from aiogram import Router, F, types, Bot
from aiogram.types import Message, WebAppInfo, MenuButtonWebApp
from aiogram.filters import CommandStart, Command
from aiogram_i18n import I18nContext

# Import necessary repository and service classes for type hinting
from src.bot.database.repositories import UserRepository
from src.bot.services.guard_service import GuardService
from src.bot.services.subscription_service import SubscriptionService


router = Router()

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

    # --- SET THE MENU BUTTON TO OPEN THE WEB APP ---
    # NOTE: We will replace this URL with our actual dashboard URL later
    dashboard_url = "https://core.telegram.org/bots/webapps"
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

    # Build the response message text
    text = [f"<b>{i18n.get('myplan-header')}</b>\n"]
    text.append(i18n.get("myplan-plan-name", plan_name=status.plan_name.upper()))
    
    # Format channel usage string
    if status.max_channels == -1:
        text.append(i18n.get("myplan-channels-unlimited", current=status.current_channels))
    else:
        text.append(i18n.get("myplan-channels-limit", current=status.current_channels, max=status.max_channels))
        
    # Format post usage string
    if status.max_posts_per_month == -1:
        text.append(i18n.get("myplan-posts-unlimited", current=status.current_posts_this_month))
    else:
        text.append(i18n.get("myplan-posts-limit", current=status.current_posts_this_month, max=status.max_posts_per_month))

    # Join all parts and send the message
    await message.answer("\n".join(text))
    

@router.message(F.text)
async def check_blacklist_handler(
    message: Message,
    guard_service: GuardService # Dependency injected by middleware
):
    # This handler checks for blacklisted words in messages
    # Make sure this handler only triggers in channels/groups, not in private chat
    if message.chat.type in ["group", "supergroup", "channel"]:
        is_blocked = await guard_service.is_blocked(message.chat.id, message.text)
        
        if is_blocked:
            try:
                await message.delete()
            except Exception:
                # Bot might not have deletion rights in the chat
                pass
