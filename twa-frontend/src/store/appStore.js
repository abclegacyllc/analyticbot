import { create } from 'zustand';

const webApp = window.Telegram.WebApp;

// --- 1. YANGI O'ZGARUVCHI: API MANZILI ---
// Skrinshotdan olingan manzilni shu yerga qo'yamiz
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL; 

export const useAppStore = create((set, get) => ({
    // State o'zgarishsiz qoladi
    channels: [],
    scheduledPosts: [],
    pendingMedia: null,
    isLoading: true,
    addChannelStatus: { success: null, message: '' },

    // Hozircha bu funksiyalarni o'zgartirmay turamiz
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
        webApp.showConfirm(`Are you sure you want to delete this post?`, (isConfirmed) => {
            if (isConfirmed) {
                webApp.sendData(JSON.stringify({ type: 'delete_post', post_id: postId }));
                setTimeout(() => get().fetchData(), 500);
            }
        });
    },

    // --- 2. TO'LIQ YANGILANGAN FUNKSIYA ---
    addChannel: async (channelName) => {
        set({ isLoading: true, addChannelStatus: { success: null, message: '' } });

        try {
            // Foydalanuvchi ma'lumotlarini Telegram'dan olamiz
            const initData = webApp.initDataUnsafe;
            const userId = initData?.user?.id;
            
            if (!userId) {
                throw new Error("Foydalanuvchi ma'lumotlari topilmadi. Ilovani qayta ishga tushiring.");
            }

            // Yangi API serverimizga standart HTTP so'rov yuboramiz
            const response = await fetch(`${API_BASE_URL}/api/v1/channels`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    channel_name: channelName,
                    user_id: userId
                }),
            });

            const result = await response.json();

            if (!response.ok) {
                // Agar API server xatolik qaytarsa, uni ko'rsatamiz
                throw new Error(result.detail || 'Noma\'lum xatolik yuz berdi');
            }

            // Muvaffaqiyatli javobni state'ga yozamiz
            set({ addChannelStatus: { success: true, message: result.message }, isLoading: false });
            
            // Kanallar ro'yxatini yangilash uchun vaqtinchalik eski usulni qoldiramiz
            setTimeout(() => get().fetchData(), 500);

        } catch (error) {
            // Har qanday xatolikni ushlab, foydalanuvchiga ko'rsatamiz
            set({ addChannelStatus: { success: false, message: error.message }, isLoading: false });
        }
    },

    // Bu funksiya keyinchalik API'ga o'tkaziladi
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
            } catch (e) { /* Ignore non-JSON messages */ }
        };

        webApp.onEvent('messageReceived', handleNewMessage);
        get().fetchData(); 
        
        return () => webApp.offEvent('messageReceived', handleNewMessage);
    },
}));

useAppStore.getState().initializeBotListener();
