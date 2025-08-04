import React, { useState, useEffect } from 'react';
import './PostCreator.css';

const webApp = window.Telegram.WebApp;

// We now receive pendingMedia from App.jsx
const PostCreator = ({ channels, isLoading, pendingMedia, onPostScheduled }) => {
  const [postText, setPostText] = useState(''); // This now serves as the caption
  const [channelId, setChannelId] = useState('');
  const [scheduleTime, setScheduleTime] = useState('');
  
  const mainButton = webApp.MainButton;

  useEffect(() => {
    if (!isLoading && channels.length > 0) {
      setChannelId(channels[0].id);
    }
  }, [isLoading, channels]);

  // Logic to control the main "Schedule" button
  useEffect(() => {
    // A post is valid if it has a channel, a time, AND (either text OR pending media)
    const isReady = channelId && scheduleTime && (postText.trim() !== '' || pendingMedia);

    if (isReady) {
      mainButton.setParams({
        text: 'Schedule Post',
        color: '#2481CC',
        is_visible: true,
        is_active: true,
      });
    } else {
      mainButton.hide();
    }
  }, [postText, channelId, scheduleTime, pendingMedia, mainButton]);

  // Logic to send data to the bot
  useEffect(() => {
    const handleSendData = () => {
      const dataToSend = {
        type: 'new_post',
        text: postText,
        channel_id: channelId,
        schedule_time: scheduleTime,
        // Include media info if it exists
        file_id: pendingMedia ? pendingMedia.file_id : null,
        file_type: pendingMedia ? pendingMedia.file_type : null,
      };
      webApp.sendData(JSON.stringify(dataToSend));
      onPostScheduled();
    };

    mainButton.on('click', handleSendData);

    return () => {
        mainButton.off('click', handleSendData);
    };
  }, [postText, channelId, scheduleTime, pendingMedia, onPostScheduled, mainButton]);

  return (
    <div className="post-creator">
      <h2>Create New Post</h2>
      
      <div className="form-group">
        <label htmlFor="channel-select">Channel:</label>
        <select 
          id="channel-select"
          value={channelId} 
          onChange={(e) => setChannelId(e.target.value)}
          disabled={isLoading}
        >
          {isLoading ? (
            <option>Loading channels...</option>
          ) : channels.length > 0 ? (
            channels.map((channel) => (
              <option key={channel.id} value={channel.id}>
                {channel.name}
              </option>
            ))
          ) : (
            <option>No channels found.</option>
          )}
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="post-text">Caption (optional for media):</label>
        <textarea
          id="post-text"
          value={postText}
          onChange={(e) => setPostText(e.target.value)}
          placeholder="Enter your post text or caption here..."
          rows="6"
        />
      </div>

      <div className="form-group">
        <label htmlFor="schedule-time">Schedule Time (UTC):</label>
        <input
          id="schedule-time"
          type="datetime-local"
          value={scheduleTime}
          onChange={(e) => setScheduleTime(e.target.value)}
        />
      </div>
    </div>
  );
};

export default PostCreator;
