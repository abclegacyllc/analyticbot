import { useEffect, useState, useCallback } from 'react';
import PostCreator from './components/PostCreator';
import ScheduledPostsList from './components/ScheduledPostsList';
import MediaPreview from './components/MediaPreview'; // <-- Import the new component
import './App.css';

const webApp = window.Telegram.WebApp;

function App() {
    // State for all our data
    const [channels, setChannels] = useState([]);
    const [scheduledPosts, setScheduledPosts] = useState([]);
    const [pendingMedia, setPendingMedia] = useState(null); // <-- New state for media

    // Loading states
    const [isCreatorLoading, setIsCreatorLoading] = useState(true);
    const [isListLoading, setIsListLoading] = useState(true);

    const fetchData = useCallback(() => {
        setIsCreatorLoading(true);
        setIsListLoading(true);
        // We now fetch everything with a single command
        webApp.sendData(JSON.stringify({ type: 'get_initial_data' }));
    }, []);

    const handleDeletePost = useCallback((postId) => {
        webApp.showAlert(`Are you sure you want to delete post ${postId}?`, (isConfirmed) => {
            if (isConfirmed) {
                setScheduledPosts(prev => prev.filter(p => p.id !== postId));
                webApp.sendData(JSON.stringify({ type: 'delete_post', post_id: postId }));
                setTimeout(fetchData, 500);
            }
        });
    }, [fetchData]);

    useEffect(() => {
        const handleNewMessage = (event) => {
            const messageText = event.data;
            if (messageText && messageText.includes('__TWA_RESPONSE__')) {
                try {
                    const parts = messageText.replace(/<pre>|<\/pre>/g, '').split('||');
                    const responseType = parts[1];
                    const data = JSON.parse(parts[2]);

                    // Handle the new unified response
                    if (responseType === "initial_data_response") {
                        setChannels(data.channels);
                        setScheduledPosts(data.posts);
                        setPendingMedia(data.media.file_id ? data.media : null);
                        
                        // Stop all loading spinners
                        setIsCreatorLoading(false);
                        setIsListLoading(false);
                    }
                } catch (error) {
                    console.error("Failed to parse message from bot:", error);
                    setIsCreatorLoading(false);
                    setIsListLoading(false);
                }
            }
        };

        webApp.onEvent('messageReceived', handleNewMessage);
        
        webApp.ready();
        fetchData(); // Fetch initial data on load

        return () => {
            webApp.offEvent('messageReceived', handleNewMessage);
        };
    }, [fetchData]);

    const onPostScheduled = useCallback(() => {
        webApp.showAlert('Your post has been scheduled successfully!');
        setPendingMedia(null); // Clear the pending media after scheduling
        setTimeout(fetchData, 500);
    }, [fetchData]);

    return (
        <div className="app-container">
            <h1>Bot Dashboard</h1>
            
            {/* The MediaPreview component will only show if there's media */}
            <MediaPreview media={pendingMedia} />

            <PostCreator 
                channels={channels}
                isLoading={isCreatorLoading}
                pendingMedia={pendingMedia} // Pass media to the creator
                onPostScheduled={onPostScheduled}
            />
            
            <ScheduledPostsList
                posts={scheduledPosts}
                onDelete={handleDeletePost}
                isLoading={isListLoading}
            />
        </div>
    );
}

export default App;
