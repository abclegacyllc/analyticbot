import { create } from 'zustand';

export const useAppStore = create((set, get) => ({
    channels: [],
    scheduledPosts: [],
    isLoading: false,
    addChannelStatus: { success: false, message: '' },
    // Media ma'lumotlarini saqlash uchun yangi state
    pendingMedia: { file_id: null, media_type: null, previewUrl: null },

    fetchData: async () => {
        set({ isLoading: true });
        try {
            // Bu yerda user_id ni qanday olishni keyinroq hal qilamiz. Hozircha statik.
            const user_id = 12345; // TODO: Replace with dynamic user ID from Telegram
            const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/initial-data/${user_id}`);
            const data = await response.json();

            if (data.ok) {
                set({
                    channels: data.data.channels || [],
                    scheduledPosts: data.data.posts || [],
                });
            }
        } catch (error) {
            console.error('Error fetching data:', error);
        } finally {
            set({ isLoading: false });
        }
    },

    addChannel: async (username) => {
        set({ isLoading: true, addChannelStatus: { success: false, message: '' } });
        try {
            const user_id = 12345; // TODO: Replace with dynamic user ID
            const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/channels/${user_id}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username }),
            });
            const data = await response.json();
            set({ addChannelStatus: { success: data.ok, message: data.message } });
            if (data.ok) {
                get().fetchData();
            }
        } catch (error) {
            set({ addChannelStatus: { success: false, message: 'An unexpected error occurred.' } });
        } finally {
            set({ isLoading: false });
        }
    },

    // YANGI FUNKSIYA: Media yuklash uchun
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
                        previewUrl: URL.createObjectURL(file) // Rasm prevyusi uchun vaqtinchalik URL
                    }
                });
            } else {
                console.error("File upload failed:", data.error);
            }
        } catch (error) {
            console.error("Error uploading file:", error);
        } finally {
            set({ isLoading: false });
        }
    },
    
    // YANGI FUNKSIYA: Yuklangan mediani tozalash
    clearPendingMedia: () => {
        const { previewUrl } = get().pendingMedia;
        if (previewUrl) {
            URL.revokeObjectURL(previewUrl); // Xotirani tozalash
        }
        set({ pendingMedia: { file_id: null, media_type: null, previewUrl: null } });
    },

    schedulePost: async (postData) => {
        set({ isLoading: true });
        const { pendingMedia, clearPendingMedia } = get();
        const user_id = 12345; // TODO: Replace with dynamic user ID

        const body = {
            user_id: user_id,
            channel_id: postData.channel_id,
            post_text: postData.text,
            schedule_time: postData.schedule_time,
            inline_buttons: postData.inline_buttons,
            // media ma'lumotlarini qo'shamiz
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
                clearPendingMedia(); // Muvaffaqiyatli bo'lganda mediani tozalaymiz
                get().fetchData();
            }
        } catch (error) {
            console.error('Network error:', error);
        } finally {
            set({ isLoading: false });
        }
    },

    deleteScheduledPost: async (postId) => {
        set({ isLoading: true });
        const user_id = 12345; // TODO: Replace with dynamic user ID
        try {
            const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/posts/${postId}/${user_id}`, {
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