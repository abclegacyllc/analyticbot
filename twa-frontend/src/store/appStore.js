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
        set({ isLoading: true }); // Amal boshlanganda loadingni yoqamiz
        webApp.sendData(JSON.stringify({ type: 'new_post', ...postData }));
        // Javobni endi listener kutib oladi
    },

    // Postni o'chirish amali
    deletePost: (postId) => {
        // Tasdiqlash uchun "showConfirm" ishlatamiz
        webApp.showConfirm(`Siz haqiqatan ham ushbu postni o'chirmoqchimisiz?`, (isConfirmed) => {
            if (isConfirmed) {
                set({ isLoading: true }); // Amal boshlanganda loadingni yoqamiz
                webApp.sendData(JSON.stringify({ type: 'delete_post', post_id: postId }));
                // Javobni endi listener kutib oladi
            }
        });
    },

    // Botdan kelgan xabarlarni qabul qilish uchun ichki funksiya
    initializeBotListener: () => {
        const handleNewMessage = (event) => {
            try {
                // Faqat JSON formatidagi ma'lumotlarni tekshiramiz
                if (typeof event.data === 'string' && event.data.startsWith('{')) {
                    const response = JSON.parse(event.data);

                    // Ma'lumotlar so'roviga javob
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
                    // Amal muvaffaqiyatli bajarilganda
                    else if (response.type === "action_success") {
                        console.log("Zustand Store: Amal muvaffaqiyatli:", response.message);
                        webApp.showAlert(response.message);
                        if (response.action === 'new_post') {
                             set({ pendingMedia: null }); // Mediani tozalaymiz
                        }
                        get().fetchData(); // Ma'lumotlarni yangilaymiz
                    }
                    // Xatolik yuz berganda
                    else if (response.type === "action_error") {
                        console.error("Zustand Store: Xatolik yuz berdi:", response.message);
                        set({ isLoading: false, error: response.message });
                        webApp.showAlert(`Xatolik: ${response.message}`);
                    }
                }
            } catch (e) {
                console.warn("Could not parse message from bot:", e);
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
