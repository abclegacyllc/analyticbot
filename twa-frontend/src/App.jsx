import { useEffect, useState, useCallback } from 'react';
import PostCreator from './components/PostCreator';
import ScheduledPostsList from './components/ScheduledPostsList'; // <-- Import the new component
import './App.css';

const webApp = window.Telegram.WebApp;

function App() {
  // State for the Post Creator
  const [channels, setChannels] = useState([]);
  const [isCreatorLoading, setIsCreatorLoading] = useState(true);

  // State for the Scheduled Posts List
  const [scheduledPosts, setScheduledPosts] = useState([]);
  const [isListLoading, setIsListLoading] = useState(true);

  // --- FUNCTION TO FETCH DATA FROM THE BOT ---
  const fetchData = useCallback((requestType) => {
    if (requestType === 'get_channels') {
      setIsCreatorLoading(true);
    }
    if (requestType === 'get_scheduled_posts') {
      setIsListLoading(true);
    }
    webApp.sendData(JSON.stringify({ type: requestType }));
  }, []);

  // --- FUNCTION TO DELETE A POST ---
  const handleDeletePost = useCallback((postId) => {
    webApp.showAlert(`Are you sure you want to delete post ${postId}?`, (isConfirmed) => {
        if (isConfirmed) {
            // Optimistically update the UI by removing the post immediately
            setScheduledPosts(prevPosts => prevPosts.filter(p => p.id !== postId));
            // Send the delete request to the backend
            webApp.sendData(JSON.stringify({ type: 'delete_post', post_id: postId }));
        }
    });
  }, []);


  // --- MAIN EFFECT TO HANDLE RESPONSES FROM THE BOT ---
  useEffect(() => {
    const handleQueryResponse = (response) => {
      try {
        const data = JSON.parse(response.data[0].description);
        const queryType = response.data[0].title; // We'll use the title to differentiate

        if (queryType === "Channels Response") {
          setChannels(data);
          setIsCreatorLoading(false);
        } else if (queryType === "Scheduled Posts Response") {
          setScheduledPosts(data);
          setIsListLoading(false);
        }
      } catch (error) {
        console.error("Failed to parse data:", error);
        setIsCreatorLoading(false);
        setIsListLoading(false);
      }
    };

    webApp.onEvent('webAppQueryResponse', handleQueryResponse);
    
    // Initial data fetch when the app loads
    webApp.ready();
    fetchData('get_channels');
    fetchData('get_scheduled_posts');

    // Cleanup listener on component unmount
    return () => {
      webApp.offEvent('webAppQueryResponse', handleQueryResponse);
    };
  }, [fetchData]);

  // --- A callback for the PostCreator to trigger a refresh ---
  const onPostScheduled = useCallback(() => {
    // Show a confirmation and then refresh the list
    webApp.showAlert('Your post has been scheduled successfully!');
    // Add a small delay to give the backend time to process
    setTimeout(() => fetchData('get_scheduled_posts'), 500);
  }, [fetchData]);


  return (
    <div className="app-container">
      <h1>Bot Dashboard</h1>
      
      {/* --- Pass data and handlers down to components --- */}
      
      <PostCreator 
        channels={channels}
        isLoading={isCreatorLoading}
        onPostScheduled={onPostScheduled}
      />
      
      {isListLoading ? (
        <p>Loading scheduled posts...</p>
      ) : (
        <ScheduledPostsList
          posts={scheduledPosts}
          onDelete={handleDeletePost}
        />
      )}
    </div>
  );
}

export default App;
