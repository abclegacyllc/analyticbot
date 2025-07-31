from aiogram import Router, types
from aiogram.filters import Command

# Kelajakda bu yerga adminlarni tekshiradigan filtr qo'shamiz
# from src.bot.filters.admin import IsAdmin

from src.bot.services.guard_service import GuardService

router = Router()
# router.message.filter(IsAdmin()) # Va bu filtrni yoqamiz

# GuardService uchun placeholder
guard_service: GuardService = None

@router.message(Command("add_word"))
async def add_word_handler(message: types.Message):
    try:
        word = message.text.split(maxsplit=1)[1]
    except IndexError:
        return await message.reply("Usage: /add_word <word_to_block>")

    # Biz bu yerda chat_id'ni emas, balki admin boshqaradigan kanal ID'sini olishimiz kerak
    # Hozircha test uchun message.chat.id dan foydalanamiz
    channel_id_to_manage = message.chat.id 
    
    await guard_service.add_word(channel_id_to_manage, word)
    await message.reply(f"✅ Word '{word}' has been added to the blacklist.")

@router.message(Command("remove_word"))
async def remove_word_handler(message: types.Message):
    try:
        word = message.text.split(maxsplit=1)[1]
    except IndexError:
        return await message.reply("Usage: /remove_word <word_to_remove>")

    channel_id_to_manage = message.chat.id
    await guard_service.remove_word(channel_id_to_manage, word)
    await message.reply(f"✅ Word '{word}' has been removed from the blacklist.")

@router.message(Command("list_words"))
async def list_words_handler(message: types.Message):
    channel_id_to_manage = message.chat.id
    words = await guard_service.list_words(channel_id_to_manage)
    
    if not words:
        return await message.reply("ℹ️ The blacklist is empty.")
    
    word_list = "\n".join(f"• {w}" for w in words)
    await message.reply(f"🚫 Blacklisted words:\n{word_list}")
