import { create } from 'zustand';

const webApp = window.Telegram.WebApp;

export const useAppStore = create((set, get) => ({
    // State
    channels: [],
    scheduledPosts: [],
    pendingMedia: null,
    isLoading: true,
    // Kanal qo'shish holati uchun yangi state
    addChannelStatus: { success: null, message: '' },

    // Actions
    fetchData: () => {
        set({ isLoading: true, addChannelStatus: { success: null, message: '' } });
        webApp.sendData(JSON.stringify({ type: 'get_initial_data' }));
    },

    schedulePost: (postData) => {
        webApp.sendData(JSON.stringify({ type: 'new_post', ...postData }));
        webApp.showAlert('Post scheduled successfully!');
        set({ pendingMedia: null });
        setTimeout(() => get().fetchData(), 500);
    },

    deletePost: (postId) => {
        webApp.showAlert(`Are you sure you want to delete this post?`, (isConfirmed) => {
            if (isConfirmed) {
                webApp.sendData(JSON.stringify({ type: 'delete_post', post_id: postId }));
                setTimeout(() => get().fetchData(), 500);
            }
        });
    },

    // Kanal qo'shish uchun yangi amal
    addChannel: (channelName) => {
        set({ isLoading: true });
        webApp.sendData(JSON.stringify({ type: 'add_channel', channel_name: channelName }));
    },

    initializeBotListener: () => {
        const handleNewMessage = (event) => {
            try {
                const response = JSON.parse(event.data);
                
                if (response.type === "initial_data_response") {
                    const data = response.data;
                    set({
                        channels: data.channels || [],
                        scheduledPosts: data.posts || [],
                        pendingMedia: data.media && data.media.file_id ? data.media : null,
                        isLoading: false,
                    });
                } 
                // Kanal qo'shish javobini qayta ishlash
                else if (response.type === "add_channel_response") {
                    set({ addChannelStatus: response.data, isLoading: false });
                    // Agar muvaffaqiyatli bo'lsa, kanallar ro'yxatini yangilaymiz
                    if (response.data.success) {
                        setTimeout(() => get().fetchData(), 500);
                    }
                }

            } catch (e) { /* Ignore non-JSON messages */ }
        };

        webApp.onEvent('messageReceived', handleNewMessage);
        get().fetchData(); // Birinchi marta ma'lumotlarni so'raymiz
        
        return () => webApp.offEvent('messageReceived', handleNewMessage);
    },
}));

// Listener'ni bir marta ishga tushiramiz
useAppStore.getState().initializeBotListener();
