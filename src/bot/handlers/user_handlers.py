import json
import logging
from datetime import datetime
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
from src.bot.database.repositories import (
    ChannelRepository,
    SchedulerRepository,
    UserRepository,
)
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
    try:
        data = json.loads(message.web_app_data.data)
        request_type = data.get("type")

        # --- HANDLE DATA REQUEST ---
        if request_type == "get_initial_data":
            user_channels = await channel_repo.get_user_channels(message.from_user.id)
            pending_posts = await scheduler_repo.get_pending_posts_by_user(
                message.from_user.id
            )
            user_state = await state.get_data()

            response_data = {
                "channels": [
                    {"id": str(ch["channel_id"]), "name": ch["channel_name"]}
                    for ch in user_channels
                ],
                "posts": [
                    {
                        "id": post["post_id"],
                        "text": post["text"] or "",
                        "schedule_time": post["schedule_time"].isoformat(),
                        "channel_name": post["channel_name"],
                        "file_id": post["file_id"],
                        "file_type": post["file_type"],
                    }
                    for post in pending_posts
                ],
                "media": {
                    "file_id": user_state.get("media_file_id"),
                    "file_type": user_state.get("media_file_type"),
                },
            }

            # --- JAVOB YUBORISH MANTIG'INI TO'LIQ O'ZGARTIRDIK ---
            logger.info("Sending 'initial_data_response' to TWA.")
            # Biz endi oddiy va ishonchli JSON formatida javob yuboramiz
            await message.answer(json.dumps({
                "type": "initial_data_response",
                "data": response_data
            }))
            return # Javob yuborilgach, funksiyadan chiqamiz

        # --- HANDLE ACTIONS ---
        elif request_type == "new_post":
            # ... (bu qism o'zgarmaydi)
            await scheduler_service.schedule_post(
                channel_id=int(data.get("channel_id")),
                text=data.get("text"),
                schedule_time=datetime.fromisoformat(data.get("schedule_time")),
                file_id=data.get("file_id"),
                file_type=data.get("file_type"),
            )
            await state.update_data(media_file_id=None, media_file_type=None)

        elif request_type == "delete_post":
            # ... (bu qism o'zgarmaydi)
            await scheduler_service.delete_post(int(data.get("post_id")))

    except Exception as e:
        logger.error(f"Critical error in handle_web_app_data: {e}", exc_info=True)


# ... (qolgan barcha funksiyalar o'zgarishsiz qoladi) ...
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
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.get("menu-button-dashboard"), web_app=web_app_info
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
    status = await subscription_service.get_user_subscription_status(
        message.from_user.id
    )
    if not status:
        return await message.answer(i18n.get("myplan-error"))

    text = [f"<b>{i18n.get('myplan-header')}</b>\n"]
    text.append(i18n.get("myplan-plan-name", plan_name=status.plan_name.upper()))

    if status.max_channels == -1:
        text.append(
            i18n.get("myplan-channels-unlimited", current=status.current_channels)
        )
    else:
        text.append(
            i18n.get(
                "myplan-channels-limit",
                current=status.current_channels,
                max=status.max_channels,
            )
        )

    if status.max_posts_per_month == -1:
        text.append(
            i18n.get(
                "myplan-posts-unlimited", current=status.current_posts_this_month
            )
        )
    else:
        text.append(
            i18n.get(
                "myplan-posts-limit",
                current=status.current_posts_this_month,
                max=status.max_posts_per_month,
            )
        )

    await message.answer("\n".join(text))

@router.message(F.content_type.in_({types.ContentType.PHOTO, types.ContentType.VIDEO}))
async def handle_media(message: Message, state: FSMContext, i18n: I18nContext):
    logger.info(f"--- handle_media triggered! Content type: {message.content_type} ---")
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
    else:
        logger.warning(
            "Media handler was triggered but could not extract file_id or file_type."
        )

@router.message()
async def unhandled_message_handler(message: Message):
    logger.info(
        f"CATCH-ALL HANDLER: Caught a message that was not handled by other functions. "
        f"Content type: {message.content_type}. Text: '{message.text}'"
    )
