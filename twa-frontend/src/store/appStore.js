import { create } from 'zustand';

const webApp = window.Telegram.WebApp;
const LOADING_TIMEOUT = 5000; // 5 sekund

export const useAppStore = create((set, get) => ({
    // State
    channels: [],
    scheduledPosts: [],
    pendingMedia: null,
    isLoading: true,
    addChannelStatus: { success: null, message: '' },
    loadingTimeoutId: null, // Timeout ID'sini saqlash uchun

    // Actions
    setLoading: (loading) => {
        const currentTimeout = get().loadingTimeoutId;
        if (currentTimeout) {
            clearTimeout(currentTimeout);
        }

        if (loading) {
            const newTimeout = setTimeout(() => {
                set({ isLoading: false, loadingTimeoutId: null });
                console.warn('Loading timeout reached.');
            }, LOADING_TIMEOUT);
            set({ isLoading: true, loadingTimeoutId: newTimeout });
        } else {
            set({ isLoading: false, loadingTimeoutId: null });
        }
    },

    fetchData: () => {
        get().setLoading(true);
        set({ addChannelStatus: { success: null, message: '' } });
        webApp.sendData(JSON.stringify({ type: 'get_initial_data' }));
    },

    schedulePost: (postData) => {
        webApp.sendData(JSON.stringify({ type: 'new_post', ...postData }));
        webApp.showAlert('Post scheduled successfully!');
        set({ pendingMedia: null });
        setTimeout(() => get().fetchData(), 500); // Ma'lumotlarni yangilash
    },

    deletePost: (postId) => {
        // Telegramning o'z confirm oynasidan foydalanamiz
        webApp.showConfirm(`Are you sure you want to delete this post?`, (isConfirmed) => {
            if (isConfirmed) {
                webApp.sendData(JSON.stringify({ type: 'delete_post', post_id: postId }));
                setTimeout(() => get().fetchData(), 500); // Ma'lumotlarni yangilash
            }
        });
    },

    addChannel: (channelName) => {
        get().setLoading(true);
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
                    });
                    get().setLoading(false); // Loadingni to'xtatish
                } 
                else if (response.type === "add_channel_response") {
                    set({ addChannelStatus: response.data });
                    get().setLoading(false); // Loadingni to'xtatish
                    // Agar muvaffaqiyatli bo'lsa, kanallar ro'yxatini yangilaymiz
                    if (response.data.success) {
                        setTimeout(() => get().fetchData(), 500);
                    }
                }

            } catch (e) {
                console.error("Failed to parse message from bot:", e);
                get().setLoading(false);
             }
        };

        webApp.onEvent('messageReceived', handleNewMessage);
        get().fetchData(); // Birinchi marta ma'lumotlarni so'raymiz
        
        // Cleanup function
        return () => webApp.offEvent('messageReceived', handleNewMessage);
    },
}));

// Listener'ni bir marta ishga tushiramiz
useAppStore.getState().initializeBotListener();
