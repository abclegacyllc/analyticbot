import React, { useState, useEffect } from 'react';
import './PostCreator.css';

const webApp = window.Telegram.WebApp;

// We pass channels, isLoading, and the new callback as props
const PostCreator = ({ channels, isLoading, onPostScheduled }) => {
  const [postText, setPostText] = useState('');
  const [channelId, setChannelId] = useState('');
  const [scheduleTime, setScheduleTime] = useState('');
  
  const mainButton = webApp.MainButton;

  // When channels are loaded, select the first one by default
  useEffect(() => {
    if (!isLoading && channels.length > 0) {
      setChannelId(channels[0].id);
    }
  }, [isLoading, channels]);

  // Logic to control the main button
  useEffect(() => {
    if (postText.trim() !== '' && channelId && scheduleTime) {
      mainButton.setParams({
        text: 'Schedule Post',
        color: '#2481CC', // A nice blue color
        is_visible: true,
        is_active: true,
      });
    } else {
      mainButton.hide();
    }
  }, [postText, channelId, scheduleTime, mainButton]);

  // Logic to send data to the bot
  useEffect(() => {
    const handleSendData = () => {
      const dataToSend = {
        type: 'new_post',
        text: postText,
        channel_id: channelId,
        schedule_time: scheduleTime,
      };
      webApp.sendData(JSON.stringify(dataToSend));
      // Call the callback function passed from App.jsx
      onPostScheduled();
    };

    mainButton.onClick(handleSendData);

    // Cleanup the event listener
    return () => {
        mainButton.offClick(handleSendData);
    };
  }, [postText, channelId, scheduleTime, onPostScheduled, mainButton]);


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
        <label htmlFor="post-text">Text:</label>
        <textarea
          id="post-text"
          value={postText}
          onChange={(e) => setPostText(e.target.value)}
          placeholder="Enter your post text here..."
          rows="8"
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
