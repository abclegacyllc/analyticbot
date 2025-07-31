from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram_i18n import I18nContext
from src.bot.database.repository import UserRepository
from src.bot.services.guard_service import GuardService

router = Router()

# Repositories and Services placeholders
user_repository: UserRepository = None
guard_service: GuardService = None

@router.message(CommandStart())
async def cmd_start(message: Message, i18n: I18nContext):
    await user_repository.create_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
    )
    await message.answer(
        i18n.get("start_message", user_name=message.from_user.full_name)
    )

# IMPORTANT: This handler must be registered after all other text-based handlers
@router.message(F.text)
async def check_blacklist_handler(message: Message):
    # Here we should check if the bot is an admin in the channel and has deletion rights
    # For now, we use message.chat.id for testing purposes
    is_blocked = await guard_service.is_blocked(message.chat.id, message.text)
    
    if is_blocked:
        try:
            await message.delete()
            # We could also notify the user (based on settings)
            # await message.answer("Your message was deleted because it contained a forbidden word.")
        except Exception:
            # Bot is not an admin in the channel or lacks deletion permissions
            pass
