import json
import logging
from datetime import datetime
from aiogram import Router, F, types, Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)
from aiogram_i18n import I18nContext
# Pydantic modellarni import qilamiz (keyingi qadamda yaratiladi)
from pydantic import ValidationError
from src.bot.models.twa import AddChannelRequest, NewPostRequest, DeletePostRequest

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


def web_app_data_filter(message: types.Message) -> bool:
    return message.web_app_data is not None


@router.message(web_app_data_filter)
async def handle_web_app_data(
    message: Message,
    bot: Bot,
    channel_repo: ChannelRepository,
    scheduler_repo: SchedulerRepository,
    scheduler_service: SchedulerService,
    state: FSMContext,
):
    try:
        data = json.loads(message.web_app_data.data)
        request_type = data.get("type")
        logger.info(f"Received TWA request: {request_type}")

        # --- KANAL QO'SHISH SO'ROVI ---
        if request_type == "add_channel":
            response = {"success": False, "message": "An unexpected error occurred."}
            try:
                request = AddChannelRequest(**data)
                
                # Kanal ma'lumotlarini olamiz
                chat = await bot.get_chat(chat_id=request.channel_name)
                # Bot kanalda admin ekanligini tekshiramiz
                bot_member = await bot.get_chat_member(chat_id=chat.id, user_id=bot.id)
                
                if bot_member.status != ChatMemberStatus.ADMINISTRATOR:
                    response["message"] = f"Bot is not an admin in {request.channel_name}. Please add the bot as an admin and try again."
                else:
                    # Kanalni ma'lumotlar bazasiga qo'shamiz
                    await channel_repo.create_channel(
                        channel_id=chat.id,
                        channel_name=chat.title,
                        admin_id=message.from_user.id
                    )
                    response["success"] = True
                    response["message"] = f"Channel '{chat.title}' added successfully!"

            except ValidationError as e:
                logger.warning(f"TWA add_channel validation error: {e}")
                response["message"] = "Invalid format. Channel username must start with @"
            except TelegramBadRequest:
                logger.warning(f"TWA add_channel: Channel not found or no access to '{data.get('channel_name')}'")
                response["message"] = f"Channel '{data.get('channel_name')}' not found or the bot does not have access to it."
            except Exception as e:
                logger.error(f"Error adding channel via TWA: {e}", exc_info=True)
            
            # Veb-ilovaga javob yuboramiz
            await message.answer(json.dumps({"type": "add_channel_response", "data": response}))
            return

        # --- ASOSIY MA'LUMOTLAR SO'ROVI ---
        elif request_type == "get_initial_data":
            try:
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
                            "id": post["post_id"], "text": post["text"] or "",
                            "schedule_time": post["schedule_time"].isoformat(),
                            "channel_name": post["channel_name"],
                            "file_id": post["file_id"], "file_type": post["file_type"],
                            "inline_buttons": json.loads(post["inline_buttons"]) if post["inline_buttons"] else []
                        } for post in pending_posts
                    ],
                    "media": {
                        "file_id": user_state.get("media_file_id"),
                        "file_type": user_state.get("media_file_type"),
                    },
                }
                await message.answer(json.dumps({
                    "type": "initial_data_response", "data": response_data
                }))
            except Exception as e:
                logger.error(f"Error in get_initial_data: {e}", exc_info=True)
                # Foydalanuvchiga xatolik haqida xabar berishimiz ham mumkin
            return

        # --- POST YARATISH SO'ROVI ---
        elif request_type == "new_post":
            try:
                request = NewPostRequest(**data)
                await scheduler_service.schedule_post(
                    channel_id=request.channel_id,
                    text=request.text,
                    schedule_time=request.schedule_time,
                    file_id=request.file_id,
                    file_type=request.file_type,
                    inline_buttons=request.inline_buttons
                )
                await state.update_data(media_file_id=None, media_file_type=None)
                # Foydalanuvchiga muvaffaqiyat haqida xabar berish ixtiyoriy
            except ValidationError as e:
                logger.error(f"TWA new_post validation error: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Error in new_post: {e}", exc_info=True)
            return

        # --- POSTNI O'CHIRISH SO'ROVI ---
        elif request_type == "delete_post":
            try:
                request = DeletePostRequest(**data)
                await scheduler_service.delete_post(request.post_id)
            except ValidationError as e:
                logger.error(f"TWA delete_post validation error: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Error in delete_post: {e}", exc_info=True)
            return
        
        else:
            logger.warning(f"Received unknown TWA request type: {request_type}")

    except json.JSONDecodeError:
        logger.error("Failed to decode JSON from TWA.", exc_info=True)
    except Exception as e:
        logger.error(f"Critical error in handle_web_app_data: {e}", exc_info=True)


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
