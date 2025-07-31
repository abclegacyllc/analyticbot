import shlex
from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from datetime import datetime, timezone
from src.bot.services.guard_service import GuardService
from src.bot.services.scheduler_service import SchedulerService
from src.bot.database.repository import ChannelRepository

router = Router()

# Placeholders for services, to be injected from run_bot.py
guard_service: GuardService = None
scheduler_service: SchedulerService = None
channel_repository: ChannelRepository = None

# --- TEMPORARY COMMAND TO REGISTER A CHANNEL ---
@router.message(Command("add_channel"))
async def add_channel_handler(message: types.Message):
    """Temporary command to register a chat/channel in the DB."""
    channel_id = message.chat.id
    admin_id = message.from_user.id
    await channel_repository.create_channel(channel_id=channel_id, admin_id=admin_id)
    await message.reply(f"✅ Channel {channel_id} has been registered. You can now schedule posts.")


# --- GUARD MODULE COMMANDS ---
@router.message(Command("add_word"))
async def add_word_handler(message: types.Message, command: CommandObject):
    if not command.args:
        return await message.reply("Usage: /add_word <word_to_block>")
    word = command.args
    channel_id_to_manage = message.chat.id
    await guard_service.add_word(channel_id_to_manage, word)
    await message.reply(f"✅ Word '{word}' has been added to the blacklist.")

@router.message(Command("remove_word"))
async def remove_word_handler(message: types.Message, command: CommandObject):
    if not command.args:
        return await message.reply("Usage: /remove_word <word_to_remove>")
    word = command.args
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
async def handle_schedule(message: types.Message, command: CommandObject):
    if command.args is None:
        return await message.reply(
            'Usage: /schedule "YYYY-MM-DD HH:MM" "Your post text"\n\n'
            'Note: Both arguments must be in double quotes.'
        )

    try:
        args = shlex.split(command.args)
        if len(args) != 2:
            raise ValueError("Incorrect number of arguments")
        
        dt_str, text = args
        
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
