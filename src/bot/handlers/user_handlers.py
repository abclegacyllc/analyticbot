from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram_i18n import I18nContext
from src.bot.database.repository import UserRepository

router = Router()

# Temporary placeholder for pool — will be injected in run_bot.py
user_repository: UserRepository = None

@router.message(CommandStart())
async def cmd_start(message: Message, i18n: I18nContext):
    # Create user on first contact
    await user_repository.create_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
    )

    await message.answer(
        i18n.get("start_message", user_name=message.from_user.full_name)
    )
