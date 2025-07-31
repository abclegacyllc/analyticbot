import shlex
from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from datetime import datetime, timezone
from aiogram_i18n import I18nContext

# Import necessary repository and service classes for type hinting
from src.bot.services.scheduler_service import SchedulerService
from src.bot.services.analytics_service import AnalyticsService
from src.bot.services.guard_service import GuardService
from src.bot.database.repositories import ChannelRepository

router = Router()


# A helper function to verify channel ownership
async def get_and_verify_channel(
    message: types.Message,
    channel_username: str,
    channel_repo: ChannelRepository,
    i18n: I18nContext
) -> int | None:
    """Checks if a channel exists, is registered, and owned by the user. Returns channel_id or None."""
    try:
        channel = await message.bot.get_chat(chat_id=channel_username)
    except Exception:
        await message.reply(i18n.get("guard-channel-not-found", channel_name=channel_username))
        return None

    db_channel = await channel_repo.get_channel_by_id(channel.id)
    if not db_channel:
        await message.reply(i18n.get("guard-channel-not-registered"))
        return None

    if db_channel['admin_id'] != message.from_user.id:
        await message.reply(i18n.get("guard-channel-not-owner"))
        return None
    
    return channel.id


@router.message(Command("add_channel"))
async def add_channel_handler(
    message: types.Message,
    command: CommandObject,
    channel_repo: ChannelRepository
):
    if not command.args or not command.args.startswith('@'):
        return await message.reply("Usage: /add_channel @your_channel_username")
    
    channel_username = command.args
    try:
        channel = await message.bot.get_chat(chat_id=channel_username)
    except Exception:
        return await message.reply("Could not find that channel. Make sure the username is correct and the bot is an admin there.")
    
    await channel_repo.create_channel(channel_id=channel.id, admin_id=message.from_user.id)
    await message.reply(f"✅ Channel '{channel.title}' (ID: {channel.id}) has been registered.")


# --- GUARD MODULE ---

@router.message(Command("add_word"))
async def add_word_handler(
    message: types.Message,
    command: CommandObject,
    channel_repo: ChannelRepository,
    guard_service: GuardService,
    i18n: I18nContext
):
    args = command.args
    if not args or len(args.split()) != 2:
        return await message.reply(i18n.get("guard-add-usage"))

    channel_username, word = args.split()
    channel_id = await get_and_verify_channel(message, channel_username, channel_repo, i18n)
    
    if channel_id:
        await guard_service.add_word(channel_id, word)
        await message.reply(i18n.get("guard-word-added", word=word, channel_name=channel_username))


@router.message(Command("remove_word"))
async def remove_word_handler(
    message: types.Message,
    command: CommandObject,
    channel_repo: ChannelRepository,
    guard_service: GuardService,
    i18n: I18nContext
):
    args = command.args
    if not args or len(args.split()) != 2:
        return await message.reply(i18n.get("guard-remove-usage"))

    channel_username, word = args.split()
    channel_id = await get_and_verify_channel(message, channel_username, channel_repo, i18n)

    if channel_id:
        await guard_service.remove_word(channel_id, word)
        await message.reply(i18n.get("guard-word-removed", word=word, channel_name=channel_username))


@router.message(Command("list_words"))
async def list_words_handler(
    message: types.Message,
    command: CommandObject,
    channel_repo: ChannelRepository,
    guard_service: GuardService,
    i18n: I18nContext
):
    channel_username = command.args
    if not channel_username:
        return await message.reply(i18n.get("guard-list-usage"))

    channel_id = await get_and_verify_channel(message, channel_username, channel_repo, i18n)
    if channel_id:
        words = await guard_service.list_words(channel_id)
        if not words:
            await message.reply(i18n.get("guard-list-empty"))
            return

        response_text = i18n.get("guard-list-header", channel_name=channel_username) + "\n\n"
        response_text += "\n".join([i18n.get("guard-list-item", word=word) for word in words])
        await message.reply(response_text)


# --- SCHEDULER & ANALYTICS ---

@router.message(Command("schedule"))
async def handle_schedule(
    message: types.Message,
    command: CommandObject,
    channel_repo: ChannelRepository,
    scheduler_service: SchedulerService
):
    if command.args is None:
        return await message.reply('Usage: /schedule @channel_username "YYYY-MM-DD HH:MM" "text"')
    try:
        args = shlex.split(command.args)
        if len(args) != 3: raise ValueError()
        channel_username, dt_str, text = args
        
        try:
            channel = await message.bot.get_chat(chat_id=channel_username)
            db_channel = await channel_repo.get_channel_by_id(channel.id)
            if not db_channel:
                return await message.reply("This channel has not been registered. Use /add_channel first.")
            if db_channel['admin_id'] != message.from_user.id:
                 return await message.reply("You are not the owner of this channel.")
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
async def get_views_handler(
    message: types.Message,
    command: CommandObject,
    analytics_service: AnalyticsService
):
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
