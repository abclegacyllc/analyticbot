from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram_i18n import I18nContext

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, i18n: I18nContext):
    await message.answer(
        i18n.get("start_message", user_name=message.from_user.full_name)
    )
