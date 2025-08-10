import { create } from 'zustand';

// Telegram Web App obyektini xavfsiz tarzda olish
const tg = window.Telegram?.WebApp;

// Foydalanuvchi ID'sini olish. Agar Telegram'dan tashqarida bo'lsa, test uchun ID ishlatamiz.
const getUserId = () => {
    // production'da initDataUnsafe dan foydalanish xavfsiz.
    return tg?.initDataUnsafe?.user?.id || 12345; // 12345 - faqat test uchun fallback
};


export const useAppStore = create((set, get) => ({
    channels: [],
    scheduledPosts: [],
    isLoading: false,
    addChannelStatus: { success: false, message: '' },
    pendingMedia: { file_id: null, media_type: null, previewUrl: null },

    // Boshlang'ich ma'lumotlarni yuklash
    fetchData: async () => {
        set({ isLoading: true });
        const userId = getUserId();
        try {
            const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/initial-data/${userId}`);
            const data = await response.json();

            if (data.ok) {
                // Ma'lumotlarni store'ga joylashtirish
                set({
                    channels: data.data.channels || [],
                    // Postlarni kanal nomi bilan boyitish
                    scheduledPosts: data.data.posts?.map(post => ({
                        ...post,
                        channel_name: data.data.channels?.find(ch => ch.id === post.channel_id)?.title || 'Unknown Channel'
                    })) || [],
                });
            }
        } catch (error) {
            console.error('Error fetching data:', error);
        } finally {
            set({ isLoading: false });
        }
    },

    // Yangi kanal qo'shish
    addChannel: async (username) => {
        set({ isLoading: true, addChannelStatus: { success: false, message: '' } });
        const userId = getUserId();
        try {
            const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/channels/${userId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username }),
            });
            const data = await response.json();
            set({ addChannelStatus: { success: data.ok, message: data.detail || data.message } });
            if (data.ok) {
                get().fetchData(); // Muvaffaqiyatli bo'lsa, ma'lumotlarni yangilaymiz
            }
        } catch (error) {
            set({ addChannelStatus: { success: false, message: 'An unexpected error occurred.' } });
        } finally {
            set({ isLoading: false });
        }
    },

    // Media fayl yuklash
    uploadMedia: async (file) => {
        set({ isLoading: true });
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/media/upload`, {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();

            if (data.ok) {
                set({
                    pendingMedia: {
                        file_id: data.file_id,
                        media_type: data.media_type,
                        previewUrl: URL.createObjectURL(file)
                    }
                });
            } else {
                console.error("File upload failed:", data.detail);
            }
        } catch (error) {
            console.error("Error uploading file:", error);
        } finally {
            set({ isLoading: false });
        }
    },
    
    // Yuklangan mediani tozalash
    clearPendingMedia: () => {
        const { previewUrl } = get().pendingMedia;
        if (previewUrl) {
            URL.revokeObjectURL(previewUrl);
        }
        set({ pendingMedia: { file_id: null, media_type: null, previewUrl: null } });
    },

    // Postni rejalashtirish
    schedulePost: async (postData) => {
        set({ isLoading: true });
        const { pendingMedia, clearPendingMedia } = get();
        const userId = getUserId();

        const body = {
            user_id: userId,
            channel_id: postData.channel_id,
            post_text: postData.text,
            schedule_time: postData.schedule_time,
            inline_buttons: postData.inline_buttons,
            media_id: pendingMedia.file_id,
            media_type: pendingMedia.media_type,
        };

        try {
            const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/posts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            const data = await response.json();
            if (data.ok) {
                clearPendingMedia();
                get().fetchData();
            }
        } catch (error) {
            console.error('Network error:', error);
        } finally {
            set({ isLoading: false });
        }
    },

    // Rejalashtirilgan postni o'chirish
    deletePost: async (postId) => {
        set({ isLoading: true });
        const userId = getUserId();
        try {
            // API endpoint to'g'ri user_id bilan chaqirilmoqda
            const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/posts/${postId}/${userId}`, {
                method: 'DELETE',
            });
            const data = await response.json();
            if (data.ok) {
                get().fetchData();
            }
        } catch (error) {
            console.error('Network error:', error);
        } finally {
            set({ isLoading: false });
        }
    },
}));

// Ilova ilk bor ishga tushganda ma'lumotlarni avtomatik yuklash
useAppStore.getState().fetchData();
