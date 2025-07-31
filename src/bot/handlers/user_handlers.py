from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram_i18n import I18nContext

# Import necessary repository and service classes for type hinting
from src.bot.database.repositories import UserRepository
from src.bot.services.guard_service import GuardService

router = Router()

# NO MORE GLOBAL PLACEHOLDERS

@router.message(CommandStart())
async def cmd_start(
    message: Message,
    i18n: I18nContext,
    user_repo: UserRepository # Dependency injected by middleware
):
    await user_repo.create_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
    )
    await message.answer(
        i18n.get("start_message", user_name=message.from_user.full_name)
    )


@router.message(F.text)
async def check_blacklist_handler(
    message: Message,
    guard_service: GuardService # Dependency injected by middleware
):
    # This handler checks for blacklisted words in messages
    is_blocked = await guard_service.is_blocked(message.chat.id, message.text)
    
    if is_blocked:
        try:
            await message.delete()
        except Exception:
            # Bot might not have deletion rights in the chat
            pass
