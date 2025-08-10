import { create } from 'zustand';

const VITE_API_URL = import.meta.env.VITE_API_URL;

/**
 * Har bir so'rov uchun autentifikatsiya sarlavhalarini (headers) tayyorlaydi.
 * @returns {HeadersInit}
 */
const getAuthHeaders = () => {
  // Telegram Web App'dan initData'ni olamiz. Agar mavjud bo'lmasa, bo'sh satr qaytaramiz.
  const twaInitData = window.Telegram?.WebApp?.initData || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `TWA ${twaInitData}` // initData'ni "TWA" prefiksi bilan yuboramiz
  };
};

/**
 * API so'rovlarini yuborish uchun markazlashtirilgan funksiya.
 * @param {string} endpoint - API endpoint (masalan, '/initial-data')
 * @param {RequestInit} options - Fetch uchun qo'shimcha opsiyalar (method, body, etc.)
 * @returns {Promise<any>}
 */
const apiFetch = async (endpoint, options = {}) => {
    const response = await fetch(`${VITE_API_URL}${endpoint}`, {
        ...options,
        headers: getAuthHeaders(),
    });

    const responseData = await response.json();

    if (!response.ok) {
        // Xatolikni serverdan kelgan xabar bilan birga chiqarish
        const errorMessage = responseData.detail || 'An unknown error occurred.';
        console.error(`API Error on ${endpoint}:`, errorMessage);
        alert(`Error: ${errorMessage}`); // Foydalanuvchiga xatolik haqida xabar berish
        throw new Error(errorMessage);
    }

    return responseData;
};


export const useAppStore = create((set, get) => ({
  user: null,
  plan: null,
  channels: [],
  scheduledPosts: [],

  // Boshlang'ich ma'lumotlarni backend'dan yuklash
  fetchData: async () => {
    try {
      const data = await apiFetch('/initial-data');
      set({
        channels: data.channels,
        scheduledPosts: data.scheduled_posts,
        plan: data.plan,
        user: data.user,
      });
    } catch (error) {
      console.error("Error fetching initial data:", error);
    }
  },

  // Yangi kanal qo'shish
  addChannel: async (channelUsername) => {
    try {
      const newChannel = await apiFetch('/channels', {
        method: 'POST',
        body: JSON.stringify({ channel_username: channelUsername }),
      });
      set((state) => ({ channels: [...state.channels, newChannel] }));
    } catch (error) {
      console.error("Error adding channel:", error);
    }
  },

  // Postni rejalashtirish
  schedulePost: async (postData) => {
    try {
        const newPost = await apiFetch('/schedule-post', {
            method: 'POST',
            body: JSON.stringify(postData)
        });
        set(state => ({
            scheduledPosts: [...state.scheduledPosts, newPost].sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at))
        }));
    } catch (error) {
        console.error('Error scheduling post:', error);
    }
  },

  // Rejalashtirilgan postni o'chirish
  deletePost: async (postId) => {
    try {
        await apiFetch(`/posts/${postId}`, {
            method: 'DELETE'
        });
        set(state => ({
            scheduledPosts: state.scheduledPosts.filter(post => post.id !== postId)
        }));
    } catch (error) {
        console.error('Error deleting post:', error);
    }
  },

  // Kanalni o'chirish
  deleteChannel: async (channelId) => {
    try {
      await apiFetch(`/channels/${channelId}`, {
        method: 'DELETE'
      });
      set(state => ({
        channels: state.channels.filter(channel => channel.id !== channelId)
      }));
    } catch (error) {
      console.error('Error deleting channel:', error);
    }
  }
}));