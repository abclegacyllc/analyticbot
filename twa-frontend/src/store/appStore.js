import { create } from 'zustand';

const webApp = window.Telegram.WebApp;
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
const USER_ID = webApp.initDataUnsafe?.user?.id;

export const useAppStore = create((set, get) => ({
    // State
    channels: [],
    scheduledPosts: [],
    pendingMedia: null, // Bu qismni keyinroq o'zgartiramiz
    isLoading: true,
    addChannelStatus: { success: null, message: '' },

    // Actions
    fetchData: async () => {
        set({ isLoading: true, addChannelStatus: { success: null, message: '' } });
        try {
            if (!USER_ID) throw new Error("User not authenticated");

            const response = await fetch(`${API_BASE_URL}/api/v1/initial-data/${USER_ID}`);
            if (!response.ok) throw new Error("Failed to fetch data");
            
            const data = await response.json();
            set({
                channels: data.channels || [],
                scheduledPosts: data.posts || [],
                // pendingMedia'ni ham API orqali boshqarish kerak bo'ladi
                // Hozircha buni tozalab turamiz
                pendingMedia: null, 
                isLoading: false,
            });
        } catch (error) {
            console.error("Fetch data error:", error);
            set({ isLoading: false });
        }
    },

    schedulePost: async (postData) => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/posts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(postData),
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.detail || "Failed to schedule post");
            
            webApp.showAlert('Post scheduled successfully!');
            get().fetchData(); // Ma'lumotlarni yangilash
        } catch (error) {
            webApp.showAlert(`Error: ${error.message}`);
        }
    },

    deletePost: async (postId) => {
         webApp.showConfirm(`Are you sure you want to delete this post?`, async (isConfirmed) => {
            if (isConfirmed) {
                try {
                    const response = await fetch(`${API_BASE_URL}/api/v1/posts/${postId}`, {
                        method: 'DELETE',
                    });
                     const result = await response.json();
                    if (!response.ok) throw new Error(result.detail || "Failed to delete post");
                    
                    get().fetchData(); // Ma'lumotlarni yangilash
                } catch (error) {
                     webApp.showAlert(`Error: ${error.message}`);
                }
            }
        });
    },

    addChannel: async (channelName) => {
        set({ isLoading: true, addChannelStatus: { success: null, message: '' } });
        try {
            if (!USER_ID) throw new Error("User information not available.");

            const response = await fetch(`${API_BASE_URL}/api/v1/channels`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    channel_name: channelName,
                    user_id: USER_ID
                }),
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.detail || 'An error occurred');
            
            set({ addChannelStatus: { success: true, message: result.message }, isLoading: false });
            get().fetchData(); // Kanallar ro'yxatini yangilash
        } catch (error) {
            set({ addChannelStatus: { success: false, message: error.message }, isLoading: false });
        }
    },
}));

// Endi botdan xabar kutishimiz shart emas, ilova ochilishi bilan ma'lumotlarni so'raymiz
useAppStore.getState().fetchData();
