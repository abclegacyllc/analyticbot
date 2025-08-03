import React, { useState, useEffect } from 'react';
import './PostCreator.css';

const webApp = window.Telegram.WebApp;
const mainButton = webApp.MainButton;

const PostCreator = () => {
  const [postText, setPostText] = useState('');
  const [channelId, setChannelId] = useState('1'); // Default to the first channel
  const [scheduleTime, setScheduleTime] = useState('');

  // Dummy channel data for now. We will fetch this from the bot later.
  const channels = [
    { id: '1', name: 'Test Channel 1' },
    { id: '2', name: 'Another Cool Channel' },
    { id: '3', name: 'My Blog' },
  ];

  // This effect runs when component loads or state changes
  useEffect(() => {
    // Show main button only if all required fields are filled
    if (postText.trim() !== '' && channelId && scheduleTime) {
      mainButton.setText('Schedule Post');
      mainButton.show();
    } else {
      mainButton.hide();
    }
  }, [postText, channelId, scheduleTime]); // Dependencies array

  const handleSendData = () => {
    // Create a data object to send to the bot
    const dataToSend = {
      type: 'new_post',
      text: postText,
      channel_id: channelId,
      schedule_time: scheduleTime, // Will be in "YYYY-MM-DDTHH:MM" format
    };

    // Send the data to the bot
    webApp.sendData(JSON.stringify(dataToSend));
  };

  // Set the onClick handler for the main button
  mainButton.onClick(handleSendData);

  return (
    <div className="post-creator">
      <h2>Create New Post</h2>
      
      <div className="form-group">
        <label htmlFor="channel-select">Channel:</label>
        <select 
          id="channel-select"
          value={channelId} 
          onChange={(e) => setChannelId(e.target.value)}
        >
          {channels.map((channel) => (
            <option key={channel.id} value={channel.id}>
              {channel.name}
            </option>
          ))}
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
