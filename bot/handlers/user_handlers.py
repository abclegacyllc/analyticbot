from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo
from aiogram_i18n import I18nContext

from bot.database.repositories import UserRepository
from bot.services.subscription_service import SubscriptionService
from bot.config import settings

router = Router()

@router.message(CommandStart())
async def cmd_start(
    message: types.Message,
    user_repo: UserRepository,
    i18n: I18nContext,
):
    """
    Handles the /start command.
    Greets the user, registers them, and sets up the menu button.
    """
    # Register user if not exists
    await user_repo.create_user(message.from_user.id, message.from_user.username)

    # Set up the menu button to open the Web App
    await message.bot.set_chat_menu_button(
        chat_id=message.chat.id,
        menu_button=types.MenuButtonWebApp(
            text=i18n.get("menu-button-dashboard"),
            web_app=WebAppInfo(url=str(settings.TWA_HOST_URL))
        )
    )

    await message.answer(i18n.get("start_message", user_name=message.from_user.full_name))


@router.message(F.web_app_data)
async def handle_web_app_data(message: types.Message, i18n: I18nContext):
    """
    Handles data received from the Telegram Web App.
    NOTE: In our architecture, most data is sent directly to the FastAPI backend.
    This handler is a fallback or for specific bot-TWA interactions.
    """
    # The main logic is now handled by the FastAPI backend.
    # We can just acknowledge receipt here if needed.
    await message.answer(i18n.get("twa-data-received-post"))
    

@router.message(F.text == "/myplan")
async def cmd_myplan(message: types.Message, subscription_service: SubscriptionService, i18n: I18nContext):
    """
    Handles the /myplan command.
    Shows the user their current subscription plan and usage.
    """
    status = await subscription_service.get_user_subscription_status(message.from_user.id)
    if not status:
        return await message.answer(i18n.get("myplan-error"))

    # Build the response message
    plan_name = status.plan_name.capitalize()
    
    # Channel limits
    if status.max_channels == -1:
        channels_text = i18n.get("myplan-channels-unlimited", current=status.current_channels)
    else:
        channels_text = i18n.get("myplan-channels-limit", current=status.current_channels, max=status.max_channels)

    # Post limits
    if status.max_posts_per_month == -1:
        posts_text = i18n.get("myplan-posts-unlimited", current=status.current_posts_this_month)
    else:
        posts_text = i18n.get("myplan-posts-limit", current=status.current_posts_this_month, max=status.max_posts_per_month)

    # Combine all parts
    response_text = "\n".join([
        i18n.get("myplan-header"),
        i18n.get("myplan-plan-name", plan_name=plan_name),
        channels_text,
        posts_text,
        "\n" + i18n.get("myplan-upgrade-prompt")
    ])
    
    await message.answer(response_text)
