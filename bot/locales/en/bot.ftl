start = 👋 Hello, { $user_firstname }! I will help you schedule posts and gather analytics for your channels.
main-menu = 🏠 Main menu
back = ⬅️ Back
twa-button-text = ⚙️ Dashboard
language-set = Language has been changed
choose-language = Choose language
my-plan-button = My Plan
my-plan-info =
    Your current plan: <b>{ $plan_name }</b>
    Channel limit: <b>{ $channel_limit }</b>
    Monthly post limit: <b>{ $post_limit }</b>

    Used this month:
    - Channels: <b>{ $used_channels }/{ $channel_limit }</b>
    - Posts: <b>{ $used_posts }/{ $post_limit }</b>

admin-main-menu = Admin Panel
stats-button = 📊 Statistics
user-count = 👥 User count: { $count }
active-user-count = ⚡️ Active users (24h): { $count }
blocked-user-count = 🚫 Blocked users: { $count }

add-channel-success = ✅ Channel added successfully!
add-channel-instruction =
    To add a channel, send its username or ID.
    Example: @durov_channel or -1001234567890
    The bot must be an administrator in the channel!
delete-channel-success = ✅ Channel deleted successfully!
channel-not-found = ❌ Channel not found or the bot is not an admin in the channel.
channel-already-exists = ⚠️ This channel is already registered.
channel-limit-exceeded = 🚫 You have exceeded your channel limit for your plan.
post-limit-exceeded = 🚫 You have exceeded your monthly post limit.

# --- This version remains ---
twa-data-received-post = ✅ Post data received.
Ready to schedule:
    - Channel ID: { $channel_id }
    - Schedule time: { $schedule_time }
    - Text: <pre>{ $text }</pre>

post-scheduled-success = ✅ Post scheduled successfully!
post-scheduled-error = ❌ An error occurred while scheduling the post.
post-deleted-success = ✅ Scheduled post deleted successfully.
post-not-found = ❌ Scheduled post not found.
scheduled-post-info =
    Post ID: { $post_id }
    Channel: { $channel_title }
    Time: { $schedule_time }
    Text: { $text }
