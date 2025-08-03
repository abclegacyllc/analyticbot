start_message = Hello, { $user_name }!

# === Guard Module Commands ===
guard-channel-not-found = ❗️ Channel "{ $channel_name }" not found. Please check the username.
guard-channel-not-registered = ❗️ This channel is not registered with the bot. Use /add_channel first.
guard-channel-not-owner = ❗️ You are not the owner of this channel.

# /add_word
guard-add-usage = 📝 Usage: /add_word @channel_username <word>
guard-word-added = ✅ The word "{ $word }" has been added to the blacklist for channel "{ $channel_name }".

# /remove_word
guard-remove-usage = 📝 Usage: /remove_word @channel_username <word>
guard-word-removed = ✅ The word "{ $word }" has been removed from the blacklist for channel "{ $channel_name }".

# /list_words
guard-list-usage = 📝 Usage: /list_words @channel_username
guard-list-header = 📋 Blacklisted words for channel "{ $channel_name }":
guard-list-empty = 📭 The blacklist for this channel is empty.
guard-list-item = • { $word }

# === Monetization Limits ===
limit-reached-channels = 🚫 You have reached your channel limit for the '{ $plan_name }' plan. Please upgrade to add more channels.
limit-reached-posts = 🚫 You have reached your monthly post limit for the '{ $plan_name }' plan. Please upgrade to schedule more posts.

# === Analytics Module ===
# /stats command
stats-usage = 📝 Usage: /stats [@channel_username]
stats-generating = ⏳ Generating statistics, please wait...
stats-caption-all = 📊 Here is the overall performance chart for all your channels for the last 30 days.
stats-caption-specific = 📊 Here is the performance chart for { $channel_name } for the last 30 days.
stats-no-data = 🤷‍♂️ Could not find any view data to generate a chart.
