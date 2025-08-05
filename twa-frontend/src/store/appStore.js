import { create } from 'zustand';

const webApp = window.Telegram.WebApp;

// Bu bizning markaziy "do'konimiz" (store)
export const useAppStore = create((set, get) => ({
    // --- State (Holat) ---
    channels: [],
    scheduledPosts: [],
    pendingMedia: null,
    isLoading: true,
    error: null,

    // --- Actions (Amallar) ---

    // Botdan asosiy ma'lumotlarni so'rash amali
    fetchData: () => {
        console.log("Zustand Store: Botdan ma'lumot so'ralmoqda...");
        set({ isLoading: true, error: null });
        webApp.sendData(JSON.stringify({ type: 'get_initial_data' }));
    },

    // Postni rejalashtirish amali
    schedulePost: (postData) => {
        webApp.sendData(JSON.stringify({ type: 'new_post', ...postData }));
        webApp.showAlert('Your post has been scheduled successfully!');
        set({ pendingMedia: null }); // Mediani tozalaymiz
        setTimeout(() => get().fetchData(), 500); // Ma'lumotlarni yangilaymiz
    },

    // Postni o'chirish amali
    deletePost: (postId) => {
        webApp.showAlert(`Are you sure you want to delete this post?`, (isConfirmed) => {
            if (isConfirmed) {
                webApp.sendData(JSON.stringify({ type: 'delete_post', post_id: postId }));
                setTimeout(() => get().fetchData(), 500); // Ma'lumotlarni yangilaymiz
            }
        });
    },

    // Botdan kelgan xabarlarni qabul qilish uchun ichki funksiya
    // Bu funksiya faqat bir marta, ilova ilk bor ishga tushganda chaqiriladi
    initializeBotListener: () => {
        const handleNewMessage = (event) => {
            try {
                const response = JSON.parse(event.data);
                if (response.type === "initial_data_response") {
                    const data = response.data;
                    console.log("Zustand Store: Botdan ma'lumot qabul qilindi:", data);
                    set({
                        channels: data.channels || [],
                        scheduledPosts: data.posts || [],
                        pendingMedia: data.media && data.media.file_id ? data.media : null,
                        isLoading: false,
                    });
                }
            } catch (e) {
                // JSON bo'lmagan xabarlarga e'tibor bermaymiz
            }
        };

        webApp.onEvent('messageReceived', handleNewMessage);
        
        // Cleanup funksiyasi
        return () => {
            webApp.offEvent('messageReceived', handleNewMessage);
        };
    },
}));

// Ilova ilk bor ishga tushganda botni eshitishni boshlaymiz
useAppStore.getState().initializeBotListener();
// Va birinchi marta ma'lumotlarni so'raymiz
useAppStore.getState().fetchData();

