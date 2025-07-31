from aiogram import Router, types
from aiogram.filters import Command
from datetime import datetime, timezone
from src.bot.services.guard_service import GuardService
from src.bot.services.scheduler_service import SchedulerService

router = Router()

# Placeholders for services, to be injected from run_bot.py
guard_service: GuardService = None
scheduler_service: SchedulerService = None

# --- GUARD MODULE COMMANDS ---
@router.message(Command("add_word"))
async def add_word_handler(message: types.Message):
    try:
        word = message.text.split(maxsplit=1)[1]
    except IndexError:
        return await message.reply("Usage: /add_word <word_to_block>")
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

# --- SCHEDULER MODULE COMMANDS ---
@router.message(Command("schedule"))
async def handle_schedule(message: types.Message):
    # Command format: /schedule "YYYY-MM-DD HH:MM" "Your post text"
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        return await message.reply('Usage: /schedule "YYYY-MM-DD HH:MM" "Your post text"\n\nNote: Time must be provided in UTC.')

    try:
        naive_dt_str = parts[1].strip('"')
        naive_dt = datetime.strptime(naive_dt_str, "%Y-%m-%d %H:%M")
        aware_dt = naive_dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return await message.reply("Invalid datetime format. Please use 'YYYY-MM-DD HH:MM' in quotes.")

    text = parts[2].strip('"')
    
    if aware_dt < datetime.now(timezone.utc):
        return await message.reply("The scheduled time cannot be in the past.")

    channel_id = message.chat.id
    await scheduler_service.schedule_post(
        channel_id=channel_id,
        text=text,
        schedule_time=aware_dt
    )
    await message.reply(f"✅ Your message has been scheduled for {aware_dt.strftime('%Y-%m-%d %H:%M %Z')}.")
