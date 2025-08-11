import shlex
from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from datetime import datetime, timezone
from aiogram_i18n import I18nContext

# Import necessary repository and service classes for type hinting
from bot.services.scheduler_service import SchedulerService
from bot.services.analytics_service import AnalyticsService
from bot.services.guard_service import GuardService
from bot.database.repositories import ChannelRepository

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

    if db_channel["user_id"] != message.from_user.id:
        await message.reply(i18n.get("guard-channel-not-owner"))
        return None
    
    return channel.id


@router.message(Command("add_channel"))
async def add_channel_handler(
    message: types.Message,
    command: CommandObject,
    channel_repo: ChannelRepository,
    i18n: I18nContext
):
    if not command.args or not command.args.startswith('@'):
        return await message.reply(i18n.get("add-channel-usage"))
    
    channel_username = command.args
    try:
        channel = await message.bot.get_chat(chat_id=channel_username)
    except Exception:
        return await message.reply(i18n.get("add-channel-not-found", channel_name=channel_username))
    
    # Store basic channel information in the database
    await channel_repo.create_channel(
        channel_id=channel.id,
        user_id=message.from_user.id,
        title=channel.title,
        username=channel.username,
    )
    await message.reply(
        i18n.get("add-channel-success", channel_title=channel.title, channel_id=channel.id)
    )


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

@router.message(Command("stats"))
async def get_stats_handler(
    message: types.Message,
    command: CommandObject,
    i18n: I18nContext,
    channel_repo: ChannelRepository,
    analytics_service: AnalyticsService,
):
    """Handles the /stats command, generating a chart for all or a specific channel."""
    await message.reply(i18n.get("stats-generating"))
    
    channel_id: int | None = None
    channel_name: str | None = command.args

    if channel_name:
        if not channel_name.startswith('@'):
            return await message.reply(i18n.get("stats-usage"))
        
        channel_id = await get_and_verify_channel(message, channel_name, channel_repo, i18n)
        if not channel_id:
            return
    
    chart_image = await analytics_service.create_views_chart(
        user_id=message.from_user.id,
        channel_id=channel_id
    )

    if chart_image:
        photo = types.BufferedInputFile(chart_image.read(), filename="stats.png")
        caption = (
            i18n.get("stats-caption-specific", channel_name=channel_name)
            if channel_name
            else i18n.get("stats-caption-all")
        )
        await message.answer_photo(photo=photo, caption=caption)
    else:
        await message.answer(i18n.get("stats-no-data"))


@router.message(Command("schedule"))
async def handle_schedule(
    message: types.Message,
    command: CommandObject,
    channel_repo: ChannelRepository,
    scheduler_service: SchedulerService,
    i18n: I18nContext # Added i18n
):
    if command.args is None:
        # FIXED: Using i18n key
        return await message.reply(i18n.get("schedule-usage"))
    try:
        args = shlex.split(command.args)
        if len(args) != 3: raise ValueError()
        
        channel_username, dt_str, text = args
        
        channel_id = await get_and_verify_channel(message, channel_username, channel_repo, i18n)
        if not channel_id:
            return # Error messages are handled inside the helper function

        naive_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        aware_dt = naive_dt.replace(tzinfo=timezone.utc)
        
        if aware_dt < datetime.now(timezone.utc):
            # FIXED: Using i18n key
            return await message.reply(i18n.get("schedule-past-time-error"))

        await scheduler_service.schedule_post(channel_id=channel_id, text=text, schedule_time=aware_dt)
        # FIXED: Using i18n key
        await message.reply(i18n.get("schedule-success", channel_name=channel_username, schedule_time=aware_dt.strftime('%Y-%m-%d %H:%M %Z')))

    except ValueError:
        # FIXED: Using i18n key
        return await message.reply(i18n.get("schedule-usage"))


@router.message(Command("views"))
async def get_views_handler(
    message: types.Message,
    command: CommandObject,
    analytics_service: AnalyticsService,
    i18n: I18nContext # Added i18n
):
    if command.args is None:
        # FIXED: Using i18n key
        return await message.reply(i18n.get("views-usage"))
    try:
        post_id = int(command.args)
    except ValueError:
        # FIXED: Using i18n key
        return await message.reply(i18n.get("views-invalid-id"))
    
    admin_id = message.from_user.id
    view_count = await analytics_service.get_post_views(post_id, admin_id)
    if view_count is None:
        # FIXED: Using i18n key
        return await message.reply(i18n.get("views-not-found", post_id=post_id))
    
    # FIXED: Using i18n key
    await message.reply(i18n.get("views-success", post_id=post_id, view_count=view_count))