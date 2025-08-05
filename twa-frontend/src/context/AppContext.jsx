import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';

const webApp = window.Telegram.WebApp;
const AppContext = createContext();

// Bu bizning asosiy holat provayderimiz bo'ladi
export const AppProvider = ({ children }) => {
    const [channels, setChannels] = useState([]);
    const [scheduledPosts, setScheduledPosts] = useState([]);
    const [pendingMedia, setPendingMedia] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null); // Xatoliklar uchun yangi holat

    // Ma'lumotlarni botdan olish funksiyasi
    const fetchData = useCallback(() => {
        console.log("Requesting initial data...");
        setIsLoading(true);
        setError(null); // Har so'rovda eski xatolikni tozalaymiz
        webApp.sendData(JSON.stringify({ type: 'get_initial_data' }));
    }, []);

    // Botdan kelgan xabarlarni qayta ishlash logikasi
    useEffect(() => {
        const handleNewMessage = (event) => {
            const messageText = event.data;
            try {
                const response = JSON.parse(messageText);
                if (response.type === "initial_data_response") {
                    const data = response.data;
                    setChannels(data.channels || []);
                    setScheduledPosts(data.posts || []);
                    setPendingMedia(data.media && data.media.file_id ? data.media : null);
                    setIsLoading(false);
                }
            } catch (e) {
                // Bu JSON bo'lmagan xabar, e'tibor bermaymiz
            }
        };

        webApp.onEvent('messageReceived', handleNewMessage);
        webApp.ready();
        fetchData();

        return () => {
            webApp.offEvent('messageReceived', handleNewMessage);
        };
    }, [fetchData]);

    // Postni rejalashtirish funksiyasi
    const schedulePost = useCallback((postData) => {
        webApp.sendData(JSON.stringify({ type: 'new_post', ...postData }));
        webApp.showAlert('Your post has been scheduled successfully!');
        setPendingMedia(null);
        setTimeout(fetchData, 500);
    }, [fetchData]);

    // Postni o'chirish funksiyasi
    const deletePost = useCallback((postId) => {
        webApp.showAlert(`Are you sure you want to delete this post?`, (isConfirmed) => {
            if (isConfirmed) {
                webApp.sendData(JSON.stringify({ type: 'delete_post', post_id: postId }));
                setTimeout(fetchData, 500);
            }
        });
    }, [fetchData]);

    // Barcha holat va funksiyalarni bitta obyektga joylaymiz
    const value = {
        channels,
        scheduledPosts,
        pendingMedia,
        isLoading,
        error,
        schedulePost,
        deletePost,
    };

    return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

// Boshqa komponentlarda oson foydalanish uchun maxsus hook
export const useAppContext = () => {
    return useContext(AppContext);
};
