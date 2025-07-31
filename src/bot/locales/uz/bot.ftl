start_message = Salom, { $user_name }!

# === Guard Module Commands ===
guard-channel-not-found = ❗️ "{ $channel_name }" nomli kanal topilmadi. Iltimos, nomini tekshiring.
guard-channel-not-registered = ❗️ Bu kanal botda ro'yxatdan o'tmagan. Avval /add_channel buyrug'idan foydalaning.
guard-channel-not-owner = ❗️ Siz ushbu kanalning egasi emassiz.

# /add_word
guard-add-usage = 📝 Foydalanish: /add_word @kanal_nomi <so'z>
guard-word-added = ✅ "{ $word }" so'zi "{ $channel_name }" kanali uchun taqiqlangan so'zlar ro'yxatiga qo'shildi.

# /remove_word
guard-remove-usage = 📝 Foydalanish: /remove_word @kanal_nomi <so'z>
guard-word-removed = ✅ "{ $word }" so'zi "{ $channel_name }" kanali uchun taqiqlangan so'zlar ro'yxatidan olib tashlandi.

# /list_words
guard-list-usage = 📝 Foydalanish: /list_words @kanal_nomi
guard-list-header = 📋 "{ $channel_name }" kanali uchun taqiqlangan so'zlar ro'yxati:
guard-list-empty = 📭 Bu kanal uchun taqiqlangan so'zlar ro'yxati bo'sh.
guard-list-item = • { $word }

# === Analytics Module ===
# /stats command
stats-usage = 📝 Foydalanish: /stats [@kanal_nomi]
stats-generating = ⏳ Statistika tayyorlanmoqda, iltimos kuting...
stats-caption-all = 📊 Barcha kanallaringiz uchun so'nggi 30 kunlik umumiy statistika diagrammasi.
stats-caption-specific = 📊 { $channel_name } kanali uchun so'nggi 30 kunlik statistika diagrammasi.
stats-no-data = 🤷‍♂️ Diagramma yaratish uchun yetarli ma'lumot topilmadi.
