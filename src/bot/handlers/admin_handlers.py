import shlex
from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from datetime import datetime, timezone
from src.bot.services.guard_service import GuardService
from src.bot.services.scheduler_service import SchedulerService
from src.bot.services.analytics_service import AnalyticsService
from src.bot.database.repository import ChannelRepository

router = Router()

# Placeholders for services, to be injected from run_bot.py
guard_service: GuardService = None
scheduler_service: SchedulerService = None
channel_repository: ChannelRepository = None
analytics_service: AnalyticsService = None

# --- CHANNEL MANAGEMENT ---
@router.message(Command("add_channel"))
async def add_channel_handler(message: types.Message, command: CommandObject):
    if not command.args or not command.args.startswith('@'):
        return await message.reply("Usage: /add_channel @your_channel_username")
    
    channel_username = command.args
    try:
        # Check if the bot can access the channel info (and is an admin)
        channel = await message.bot.get_chat(chat_id=channel_username)
    except Exception:
        return await message.reply("Could not find that channel. Make sure the username is correct and the bot is an admin there.")
    
    await channel_repository.create_channel(channel_id=channel.id, admin_id=message.from_user.id)
    await message.reply(f"✅ Channel '{channel.title}' (ID: {channel.id}) has been registered.")

# --- GUARD MODULE (Placeholder) ---
@router.message(Command("add_word", "remove_word", "list_words"))
async def guard_commands_handler(message: types.Message):
    await message.reply("Guard commands are being updated.")

# --- SCHEDULER & ANALYTICS ---
@router.message(Command("schedule"))
async def handle_schedule(message: types.Message, command: CommandObject):
    if command.args is None:
        return await message.reply('Usage: /schedule @channel_username "YYYY-MM-DD HH:MM" "text"')
    try:
        args = shlex.split(command.args)
        if len(args) != 3: raise ValueError()
        channel_username, dt_str, text = args
        
        # Verify the channel exists and is registered
        try:
            channel = await message.bot.get_chat(chat_id=channel_username)
            db_channel = await channel_repository.get_channel_by_id(channel.id)
            if not db_channel:
                return await message.reply("This channel has not been registered. Use /add_channel first.")
        except Exception:
            return await message.reply(f"Could not find channel '{channel_username}'.")

        naive_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        aware_dt = naive_dt.replace(tzinfo=timezone.utc)
        if aware_dt < datetime.now(timezone.utc):
            return await message.reply("The scheduled time cannot be in the past.")

        await scheduler_service.schedule_post(channel_id=channel.id, text=text, schedule_time=aware_dt)
        await message.reply(f"✅ Your message has been scheduled for channel '{channel.title}' at {aware_dt.strftime('%Y-%m-%d %H:%M %Z')}.")

    except ValueError:
        return await message.reply('Usage: /schedule @channel_username "YYYY-MM-DD HH:MM" "text"')

@router.message(Command("views"))
async def get_views_handler(message: types.Message, command: CommandObject):
    if command.args is None:
        return await message.reply("Usage: /views POST_ID")
    try:
        post_id = int(command.args)
    except ValueError:
        return await message.reply("Invalid post_id. It must be a number.")
    
    admin_id = message.from_user.id
    view_count = await analytics_service.get_post_views(post_id, admin_id)
    if view_count is None:
        return await message.reply(f"Could not retrieve views for Post ID {post_id}. Ensure the ID is correct and the post was sent from a channel.")
    
    await message.reply(f"📊 Post ID {post_id} has {view_count} views.")
