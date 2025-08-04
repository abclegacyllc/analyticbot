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
        console.log("Requesting data from bot...");
        setIsLoading(true);
        webApp.sendData(JSON.stringify({ type: 'get_initial_data' }));
    }, []);

    const handleDeletePost = useCallback((postId) => {
        webApp.showAlert(`Are you sure you want to delete post ${postId}?`, (isConfirmed) => {
            if (isConfirmed) {
                webApp.sendData(JSON.stringify({ type: 'delete_post', post_id: postId }));
                // Ma'lumotni qayta yuklash uchun 500ms kutamiz
                setTimeout(fetchData, 500); 
            }
        });
    }, [fetchData]);

    useEffect(() => {
        const handleNewMessage = (event) => {
            const messageText = event.data;
            console.log("Received message from bot:", messageText);

            if (messageText && messageText.includes('__TWA_RESPONSE__')) {
                try {
                    const parts = messageText.replace(/<pre>|<\/pre>/g, '').split('||');
                    const responseType = parts[1];
                    const data = JSON.parse(parts[2]);

                    console.log("Parsed data:", data);

                    if (responseType === "initial_data_response") {
                        setChannels(data.channels || []);
                        setScheduledPosts(data.posts || []);
                        setPendingMedia(data.media && data.media.file_id ? data.media : null);

                        // --- ENG MUHIM TUZATISH ---
                        // Ma'lumotlar kelganidan keyin "loading"ni to'xtatamiz
                        setIsLoading(false);
                        console.log("Data loaded, isLoading set to false.");
                    }
                } catch (error) {
                    console.error("Failed to parse message from bot:", error);
                    setIsLoading(false); // Xatolik bo'lsa ham "loading"ni to'xtatamiz
                }
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

    return (
        <div className="app-container">
            <h1>Bot Dashboard</h1>
            <MediaPreview media={pendingMedia} />
            <PostCreator 
                channels={channels}
                isLoading={isLoading} // Yagona isLoading'dan foydalanamiz
                pendingMedia={pendingMedia}
                onPostScheduled={onPostScheduled}
            />
            <ScheduledPostsList
                posts={scheduledPosts}
                onDelete={handleDeletePost}
                isLoading={isLoading} // Yagona isLoading'dan foydalanamiz
            />
        </div>
    );
}

export default App;
