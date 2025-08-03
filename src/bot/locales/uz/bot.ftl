start_message = Salom, { $user_name }!

# === Channel Management ===
add-channel-usage = 📝 Foydalanish: /add_channel @kanal_nomi
add-channel-not-found = ❗️ "{ $channel_name }" nomli kanal topilmadi. Kanal nomini to'g'ri yozganingizga va bot ushbu kanalda admin ekanligiga ishonch hosil qiling.
add-channel-success = ✅ '{ $channel_title }' kanali (ID: { $channel_id }) muvaffaqiyatli ro'yxatdan o'tkazildi.

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

# === Scheduler Module ===
schedule-usage = 📝 Foydalanish: /schedule @kanal_nomi "YYYY-MM-DD HH:MM" "Sizning matningiz"
schedule-past-time-error = ❗️ Rejalashtirilgan vaqt o'tmishda bo'lishi mumkin emas.
schedule-success = ✅ Xabaringiz '{ $channel_name }' kanali uchun { $schedule_time } vaqtiga rejalashtirildi.

# === Monetization Limits ===
limit-reached-channels = 🚫 Siz '{ $plan_name }' tarif rejasidagi kanallar chegarasiga yetdingiz. Ko'proq kanal qo'shish uchun tarifingizni yangilang.
limit-reached-posts = 🚫 Siz '{ $plan_name }' tarif rejasidagi oylik postlar chegarasiga yetdingiz. Ko'proq post rejalashtirish uchun tarifingizni yangilang.

# === Analytics Module ===
# /stats command
stats-usage = 📝 Foydalanish: /stats [@kanal_nomi]
stats-generating = ⏳ Statistika tayyorlanmoqda, iltimos kuting...
stats-caption-all = 📊 Barcha kanallaringiz uchun so'nggi 30 kunlik umumiy statistika diagrammasi.
stats-caption-specific = 📊 { $channel_name } kanali uchun so'nggi 30 kunlik statistika diagrammasi.
stats-no-data = 🤷‍♂️ Diagramma yaratish uchun yetarli ma'lumot topilmadi.

# /views command
views-usage = 📝 Foydalanish: /views <POST_ID>
views-invalid-id = ❗️ Post ID xato. U raqam bo'lishi kerak.
views-not-found = 🤷‍♂️ Post ID { $post_id } uchun ko'rishlar sonini olib bo'lmadi. ID to'g'riligiga va ruxsatingiz borligiga ishonch hosil qiling.
views-success = 📊 Post ID { $post_id } da { $view_count } ta ko'rishlar soni mavjud.

# === /myplan command ===
myplan-header = 📄 Sizning Obuna Rejangiz
myplan-plan-name = Tarif: <b>{ $plan_name }</b>
myplan-channels-limit = Kanallar: { $current } / { $max }
myplan-channels-unlimited = Kanallar: { $current } / Cheksiz
myplan-posts-limit = Shu oydagi postlar: { $current } / { $max }
myplan-posts-unlimited = Shu oydagi postlar: { $current } / Cheksiz
myplan-upgrade-prompt = Qo'shimcha imkoniyatlarga ega bo'lish uchun tarifingizni yangilashingiz mumkin.
myplan-error = ❗️ Sizning rejangiz haqidagi ma'lumotlarni olib bo'lmadi. Iltimos, keyinroq qayta urinib ko'ring.

menu-button-dashboard = 🖥 Boshqaruv

# TWA data handling
twa-data-received-post = ✅ Veb-ilovadan post ma'lumotlari qabul qilindi. Matn:
twa-data-unknown = 🤷‍♂️ Veb-ilovadan noma'lum formatdagi ma'lumot keldi.

twa-data-received-post = ✅ Post ma'lumotlari qabul qilindi. Rejalashtirishga tayyor:
    - Kanal IDsi: { $channel_id }
    - Reja vaqti: { $schedule_time }
    - Matn: <pre>{ $text }</pre>
