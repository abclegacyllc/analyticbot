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
