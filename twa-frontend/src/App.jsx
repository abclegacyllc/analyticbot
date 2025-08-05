import React from 'react';
import PostCreator from './components/PostCreator';
import ScheduledPostsList from './components/ScheduledPostsList';
import MediaPreview from './components/MediaPreview';
import { useAppStore } from '/src/store/appStore.js';
import './App.css';

function App() {
    // Barcha kerakli ma'lumotlarni to'g'ridan-to'g'ri do'kondan olamiz
    const { pendingMedia, isLoading, error } = useAppStore();

    return (
        <div className="app-container">
            <h1>Bot Dashboard</h1>

            {error && <div className="error-message">{error}</div>}
            
            <MediaPreview media={pendingMedia} />
            
            <PostCreator />
            
            <ScheduledPostsList />

            {/* Global yuklanish indikatori */}
            {isLoading && (
                <div className="loading-overlay">
                    <div className="loading-spinner"></div>
                    <p>Loading...</p>
                </div>
            )}
        </div>
    );
}

export default App;
