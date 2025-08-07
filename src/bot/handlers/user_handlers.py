import logging
from aiogram import Router, F, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)
from aiogram_i18n import I18nContext

from src.bot.config import settings
from src.bot.database.repositories import UserRepository
from src.bot.services.subscription_service import SubscriptionService

router = Router()
logger = logging.getLogger(__name__)

# handle_web_app_data funksiyasi olib tashlandi.

@router.message(CommandStart())
async def cmd_start(message: Message, i18n: I18nContext, user_repo: UserRepository):
    await user_repo.create_user(
        user_id=message.from_user.id, username=message.from_user.username
    )
    await message.answer(i18n.get("start_message", user_name=message.from_user.full_name))


@router.message(Command("dashboard"))
async def cmd_dashboard(message: Message, i18n: I18nContext):
    web_app_info = WebAppInfo(url=str(settings.TWA_HOST_URL))
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=i18n.get("menu-button-dashboard"), web_app=web_app_info)]]
    )
    await message.answer("Click the button below to open your dashboard:", reply_markup=keyboard)


@router.message(Command("myplan"))
async def my_plan_handler(
    message: Message,
    i18n: I18nContext,
    subscription_service: SubscriptionService,
):
    status = await subscription_service.get_user_subscription_status(
        message.from_user.id
    )
    if not status:
        return await message.answer(i18n.get("myplan-error"))
        
    # ... qolgan qismi o'zgarishsiz ...
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


@router.message(F.content_type.in_({types.ContentType.PHOTO, types.ContentType.VIDEO}))
async def handle_media(message: Message, state: FSMContext, i18n: I18nContext):
    # Bu logikani keyinroq API'ga o'tkazamiz.
    # Hozircha foydalanuvchi rasm yuborsa, uni TWA'da ko'rsatish logikasi ishlamaydi.
    # Buni keyingi qadamda to'g'rilaymiz.
    file_id = None
    file_type = None

    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
    elif message.video:
        file_id = message.video.file_id
        file_type = "video"

    if file_id and file_type:
        await state.update_data(media_file_id=file_id, media_file_type=file_type)
        await message.answer(i18n.get("media-received-success"))

@router.message()
async def unhandled_message_handler(message: Message):
    logger.info(
        f"CATCH-ALL HANDLER: Caught a message that wasn't handled. "
        f"Content type: {message.content_type}. Text: '{message.text}'"
    )
