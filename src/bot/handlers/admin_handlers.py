import shlex # Use the shlex library for robust parsing
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

# ... (other guard handlers remain the same) ...
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
    try:
        # shlex.split correctly handles arguments in quotes
        args = shlex.split(message.text)
        if len(args) != 3:
            raise ValueError("Incorrect number of arguments")
        
        # args[0] is the command, args[1] is the datetime, args[2] is the text
        dt_str = args[1]
        text = args[2]
        
        naive_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        aware_dt = naive_dt.replace(tzinfo=timezone.utc)

    except (ValueError, IndexError):
        return await message.reply(
            'Usage: /schedule "YYYY-MM-DD HH:MM" "Your post text"\n\n'
            'Note: Time must be in UTC. Both arguments must be in double quotes.'
        )
    
    if aware_dt < datetime.now(timezone.utc):
        return await message.reply("The scheduled time cannot be in the past.")

    channel_id = message.chat.id
    await scheduler_service.schedule_post(
        channel_id=channel_id,
        text=text,
        schedule_time=aware_dt
    )
    await message.reply(f"✅ Your message has been scheduled for {aware_dt.strftime('%Y-%m-%d %H:%M %Z')}.")
