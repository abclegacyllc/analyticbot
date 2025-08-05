import React from 'react';
import PostCreator from './components/PostCreator';
import ScheduledPostsList from './components/ScheduledPostsList';
import MediaPreview from './components/MediaPreview';
import { useAppContext } from './context/AppContext'; // Context hook'ini import qilamiz
import './App.css';

function App() {
    // Holatni to'g'ridan-to'g'ri context'dan olamiz
    const { pendingMedia, isLoading, error } = useAppContext();

    return (
        <div className="app-container">
            <h1>Bot Dashboard</h1>

            {/* Xatolik xabari uchun blok */}
            {error && <div className="error-message">{error}</div>}
            
            <MediaPreview media={pendingMedia} />
            
            {/* Komponentlarga endi ko'p props uzatish shart emas */}
            <PostCreator />
            
            <ScheduledPostsList />

            {/* Yuklanish indikatori */}
            {isLoading && <div className="loading-overlay">Loading...</div>}
        </div>
    );
}

export default App;
