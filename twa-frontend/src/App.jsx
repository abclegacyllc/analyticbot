import { useEffect, useState, useCallback } from 'react';
import PostCreator from './components/PostCreator';
import ScheduledPostsList from './components/ScheduledPostsList';
import './App.css';

const webApp = window.Telegram.WebApp;

function App() {
    const [channels, setChannels] = useState([]);
    const [isCreatorLoading, setIsCreatorLoading] = useState(true);
    const [scheduledPosts, setScheduledPosts] = useState([]);
    const [isListLoading, setIsListLoading] = useState(true);

    const fetchData = useCallback((requestType) => {
        webApp.sendData(JSON.stringify({ type: requestType }));
    }, []);

    const handleDeletePost = useCallback((postId) => {
        webApp.showAlert(`Are you sure you want to delete post ${postId}?`, (isConfirmed) => {
            if (isConfirmed) {
                setScheduledPosts(prevPosts => prevPosts.filter(p => p.id !== postId));
                webApp.sendData(JSON.stringify({ type: 'delete_post', post_id: postId }));
                // After deleting, we need to refresh the list to be sure
                setTimeout(() => fetchData('get_scheduled_posts'), 500);
            }
        });
    }, [fetchData]);

    useEffect(() => {
        // This is the message listener communication method
        const handleNewMessage = (event) => {
            const messageText = event.data;
            if (messageText && messageText.includes('__TWA_RESPONSE__')) {
                try {
                    const parts = messageText.replace(/<pre>|<\/pre>/g, '').split('||');
                    const responseType = parts[1];
                    const data = JSON.parse(parts[2]);

                    if (responseType === "channels_response") {
                        setChannels(data);
                        setIsCreatorLoading(false);
                    } else if (responseType === "scheduled_posts_response") {
                        setScheduledPosts(data);
                        setIsListLoading(false);
                    }
                } catch (error) {
                    console.error("Failed to parse message from bot:", error);
                }
            }
        };

        // Listen for new messages sent in the chat
        webApp.onEvent('messageReceived', handleNewMessage);
        
        webApp.ready();
        // Fetch initial data when the app loads
        fetchData('get_channels');
        fetchData('get_scheduled_posts');

        // Cleanup the listener when the component is unmounted
        return () => {
            webApp.offEvent('messageReceived', handleNewMessage);
        };
    }, [fetchData]);

    const onPostScheduled = useCallback(() => {
        webApp.showAlert('Your post has been scheduled successfully!');
        // Refresh the list after a new post is scheduled
        setTimeout(() => fetchData('get_scheduled_posts'), 500);
    }, [fetchData]);

    return (
        <div className="app-container">
            <h1>Bot Dashboard</h1>
            <PostCreator 
                channels={channels}
                isLoading={isCreatorLoading}
                onPostScheduled={onPostScheduled}
            />
            
            <ScheduledPostsList
                posts={scheduledPosts}
                onDelete={handleDeletePost}
                isLoading={isListLoading} // Pass the loading state
            />
        </div>
    );
}

export default App;
