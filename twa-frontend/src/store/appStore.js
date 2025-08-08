import { create } from 'zustand';

export const useAppStore = create((set, get) => ({
    channels: [],
    scheduledPosts: [],
    isLoading: false,
    addChannelStatus: { success: false, message: '' },
    pendingMedia: { file_id: null, media_type: null, previewUrl: null },

    fetchData: async () => {
        set({ isLoading: true });
        try {
            const [channelsRes, postsRes] = await Promise.all([
                fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/channels`),
                fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/posts`)
            ]);
            const channelsData = await channelsRes.json();
            const postsData = await postsRes.json();

            set({
                channels: channelsData.data || [],
                scheduledPosts: postsData.data || [],
            });
        } catch (error) {
            console.error('Error fetching data:', error);
        } finally {
            set({ isLoading: false });
        }
    },

    addChannel: async (channelName) => {
        set({ isLoading: true, addChannelStatus: { success: false, message: '' } });
        try {
            const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/channels`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: channelName }),
            });
            const data = await response.json();
            set({ addChannelStatus: { success: data.ok, message: data.message } });
            if (data.ok) {
                get().fetchData(); // Re-fetch data to update channel list
            }
        } catch (error) {
            set({ addChannelStatus: { success: false, message: 'An unexpected error occurred.' } });
        } finally {
            set({ isLoading: false });
        }
    },

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
                        previewUrl: URL.createObjectURL(file) // Create a local URL for image preview
                    }
                });
            } else {
                console.error("File upload failed:", data.error);
                // Optionally, set an error state to show in the UI
            }
        } catch (error) {
            console.error("Error uploading file:", error);
        } finally {
            set({ isLoading: false });
        }
    },

    clearPendingMedia: () => {
        // Revoke the object URL to free up memory
        const { previewUrl } = get().pendingMedia;
        if (previewUrl) {
            URL.revokeObjectURL(previewUrl);
        }
        set({ pendingMedia: { file_id: null, media_type: null, previewUrl: null } });
    },

    schedulePost: async (postData) => {
        set({ isLoading: true });
        const { pendingMedia, clearPendingMedia } = get();

        const body = {
            channel_id: postData.channel_id,
            post_text: postData.text,
            schedule_time: postData.schedule_time,
            inline_buttons: postData.inline_buttons, // Make sure to pass buttons
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
                clearPendingMedia(); // Clear media after successful scheduling
                get().fetchData();
            } else {
                console.error('Error scheduling post:', data.message);
            }
        } catch (error) {
            console.error('Network error:', error);
        } finally {
            set({ isLoading: false });
        }
    },

    deleteScheduledPost: async (postId) => {
        set({ isLoading: true });
        try {
            const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/posts/${postId}`, {
                method: 'DELETE',
            });
            const data = await response.json();
            if (data.ok) {
                get().fetchData();
            } else {
                console.error('Error deleting post:', data.message);
            }
        } catch (error) {
            console.error('Network error:', error);
        } finally {
            set({ isLoading: false });
        }
    },
}));