import { useEffect, useState, useCallback } from 'react';
import PostCreator from './components/PostCreator';
import ScheduledPostsList from './components/ScheduledPostsList';
import MediaPreview from './components/MediaPreview';
import './App.css';

const webApp = window.Telegram.WebApp;

function App() {
    const [channels, setChannels] = useState([]);
    const [scheduledPosts, setScheduledPosts] = useState([]);
    const [pendingMedia, setPendingMedia] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    const fetchData = useCallback(() => {
        console.log("Requesting initial data...");
        setIsLoading(true);
        webApp.sendData(JSON.stringify({ type: 'get_initial_data' }));
    }, []);

    useEffect(() => {
        const handleNewMessage = (event) => {
            const messageText = event.data;
            console.log("Received raw message from bot:", messageText);

            // --- JAVOBNI QABUL QILISH MANTIG'INI TO'LIQ O'ZGARTIRDIK ---
            try {
                // Botdan kelgan javob to'g'ridan-to'g'ri JSON bo'lishi kerak
                const response = JSON.parse(messageText);
                console.log("Parsed JSON successfully:", response);

                if (response.type === "initial_data_response") {
                    const data = response.data;
                    setChannels(data.channels || []);
                    setScheduledPosts(data.posts || []);
                    setPendingMedia(data.media && data.media.file_id ? data.media : null);

                    setIsLoading(false);
                    console.log("Data processed. Loading is now false.");
                }
            } catch (error) {
                // Agar kelgan xabar JSON bo'lmasa, bu xato emas, shunchaki e'tibor bermaymiz
                console.log("Received a non-JSON message, ignoring it.");
            }
        };

        webApp.onEvent('messageReceived', handleNewMessage);
        webApp.ready();
        fetchData();

        return () => {
            webApp.offEvent('messageReceived', handleNewMessage);
        };
    }, [fetchData]);

    const onPostScheduled = useCallback(() => {
        webApp.showAlert('Your post has been scheduled successfully!');
        setPendingMedia(null);
        setTimeout(fetchData, 500); 
    }, [fetchData]);

    const handleDeletePost = useCallback((postId) => {
        webApp.showAlert(`Are you sure you want to delete post ${postId}?`, (isConfirmed) => {
            if (isConfirmed) {
                webApp.sendData(JSON.stringify({ type: 'delete_post', post_id: postId }));
                setTimeout(fetchData, 500); 
            }
        });
    }, [fetchData]);

    return (
        <div className="app-container">
            <h1>Bot Dashboard</h1>
            <MediaPreview media={pendingMedia} />
            <PostCreator 
                channels={channels}
                isLoading={isLoading}
                pendingMedia={pendingMedia}
                onPostScheduled={onPostScheduled}
            />
            <ScheduledPostsList
                posts={scheduledPosts}
                onDelete={handleDeletePost}
                isLoading={isLoading}
            />
        </div>
    );
}

export default App;
