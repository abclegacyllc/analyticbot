import React, { useState, useEffect } from 'react';
import './PostCreator.css';

const webApp = window.Telegram.WebApp;

// We receive channels, loading state, pendingMedia, and the onPostScheduled callback
const PostCreator = ({ channels, isLoading, pendingMedia, onPostScheduled }) => {
  const [postText, setPostText] = useState(''); // This serves as the caption for media
  const [channelId, setChannelId] = useState('');
  const [scheduleTime, setScheduleTime] = useState('');
  
  const mainButton = webApp.MainButton;

  // Effect to select the first channel by default when the list loads
  useEffect(() => {
    if (!isLoading && channels.length > 0 && !channelId) {
      setChannelId(channels[0].id);
    }
  }, [isLoading, channels, channelId]);

  // Effect to control the visibility and state of the main "Schedule" button
  useEffect(() => {
    // A post is considered ready if it has a channel, a time, AND (either text OR a pending media file)
    const isReady = channelId && scheduleTime && (postText.trim() !== '' || pendingMedia);

    if (isReady) {
      mainButton.setParams({
        text: 'Schedule Post',
        color: '#2481CC', // A standard blue color
        is_visible: true,
        is_active: true,
      });
    } else {
      mainButton.hide();
    }
  }, [postText, channelId, scheduleTime, pendingMedia, mainButton]);

  // Effect to handle sending the data when the main button is clicked
  useEffect(() => {
    const handleSendData = () => {
      const dataToSend = {
        type: 'new_post',
        text: postText,
        channel_id: channelId,
        schedule_time: scheduleTime,
        // Include media info only if it exists
        file_id: pendingMedia ? pendingMedia.file_id : null,
        file_type: pendingMedia ? pendingMedia.file_type : null,
      };
      webApp.sendData(JSON.stringify(dataToSend));
      // Notify the parent App component that scheduling is done
      onPostScheduled();
    };

    mainButton.onClick(handleSendData);

    // Cleanup the event listener when the component re-renders or unmounts
    return () => {
        mainButton.offClick(handleSendData);
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
            <option>No channels found. Use /add_channel in the bot.</option>
          )}
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="post-text">{pendingMedia ? "Caption (optional):" : "Text:"}</label>
        <textarea
          id="post-text"
          value={postText}
          onChange={(e) => setPostText(e.target.value)}
          placeholder={pendingMedia ? "Enter a caption for your media..." : "Enter your post text here..."}
          rows="6"
        />
      </div>

      <div className="form-group">
        <label htmlFor="schedule-time">Schedule Time:</label>
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
