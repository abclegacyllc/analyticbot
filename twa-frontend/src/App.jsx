import { useEffect, useState, useCallback } from 'react';
import PostCreator from './components/PostCreator';
import ScheduledPostsList from './components/ScheduledPostsList';
import './App.css';

// Initialize the Telegram Web App object
const webApp = window.Telegram.WebApp;

function App() {
    // State for the Post Creator component
    const [channels, setChannels] = useState([]);
    const [isCreatorLoading, setIsCreatorLoading] = useState(true);

    // State for the Scheduled Posts List component
    const [scheduledPosts, setScheduledPosts] = useState([]);
    const [isListLoading, setIsListLoading] = useState(true);

    // --- SENDS REQUESTS TO THE BOT ---
    // A memoized function to send a request for data to the bot.
    const fetchData = useCallback((requestType) => {
        webApp.sendData(JSON.stringify({ type: requestType }));
    }, []);

    // --- HANDLES POST DELETION ---
    const handleDeletePost = useCallback((postId) => {
        // Show a native Telegram confirmation dialog
        webApp.showAlert(`Are you sure you want to delete post ${postId}?`, (isConfirmed) => {
            if (isConfirmed) {
                // Optimistically remove the post from the UI for a faster user experience
                setScheduledPosts(prevPosts => prevPosts.filter(p => p.id !== postId));
                // Send the delete command to the bot
                webApp.sendData(JSON.stringify({ type: 'delete_post', post_id: postId }));
                // Automatically refresh the list to ensure data consistency
                setTimeout(() => fetchData('get_scheduled_posts'), 500);
            }
        });
    }, [fetchData]);

    // --- THE MAIN EFFECT FOR BOT COMMUNICATION ---
    useEffect(() => {
        // This is the core listener for our reliable communication method.
        // It listens for any new message sent in the private chat with the bot.
        const handleNewMessage = (event) => {
            const messageText = event.data;
            // We check for our unique prefix to ensure the message is intended for the TWA
            if (messageText && messageText.includes('__TWA_RESPONSE__')) {
                try {
                    // Parse the message format: <pre>__TWA_RESPONSE__||<type>||<json_data></pre>
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
                    // Stop loading states on error to prevent infinite spinners
                    setIsCreatorLoading(false);
                    setIsListLoading(false);
                }
            }
        };

        // Register the event listener
        webApp.onEvent('messageReceived', handleNewMessage);
        
        // When the app is ready, fetch all necessary initial data
        webApp.ready();
        fetchData('get_channels');
        fetchData('get_scheduled_posts');

        // Cleanup function to remove the listener when the component unmounts
        return () => {
            webApp.offEvent('messageReceived', handleNewMessage);
        };
    }, [fetchData]); // The effect depends on the memoized fetchData function

    // --- CALLBACK FOR THE POST CREATOR ---
    // This function is passed to the PostCreator and is called when a post is scheduled.
    const onPostScheduled = useCallback(() => {
        webApp.showAlert('Your post has been scheduled successfully!');
        // Refresh the list after a new post is scheduled to show the new item
        setTimeout(() => fetchData('get_scheduled_posts'), 500);
    }, [fetchData]);

    // --- RENDER THE COMPONENT ---
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
                isLoading={isListLoading}
            />
        </div>
    );
}

export default App;
