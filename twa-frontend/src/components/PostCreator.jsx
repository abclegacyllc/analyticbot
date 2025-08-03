import React, { useState, useEffect } from 'react';
import './PostCreator.css';

const webApp = window.Telegram.WebApp;
const mainButton = webApp.MainButton;

const PostCreator = () => {
  const [postText, setPostText] = useState('');
  const [channels, setChannels] = useState([]); // Start with an empty array
  const [channelId, setChannelId] = useState(''); // Start with no channel selected
  const [scheduleTime, setScheduleTime] = useState('');
  const [isLoading, setIsLoading] = useState(true); // To show a loading state

  // --- NEW LOGIC TO FETCH CHANNELS ---
  useEffect(() => {
    // 1. Define a function to handle the response from the bot
    const handleQueryResponse = (data) => {
      // Check if the received data is not empty
      if (data.data) {
        try {
          // The channel list is in the 'description' of the first result item
          const receivedChannels = JSON.parse(data.data[0].description);
          setChannels(receivedChannels);
          // If there are channels, select the first one by default
          if (receivedChannels.length > 0) {
            setChannelId(receivedChannels[0].id);
          }
        } catch (error) {
          console.error("Failed to parse channels data:", error);
          webApp.showAlert("Could not load your channels.");
        }
      }
      setIsLoading(false);
      // Remove the event listener after getting the data to avoid duplicates
      webApp.offEvent('webAppQueryResponse', handleQueryResponse);
    };

    // 2. Add an event listener to wait for the bot's response
    webApp.onEvent('webAppQueryResponse', handleQueryResponse);

    // 3. Send a request to the bot to get the channel list
    webApp.sendData(JSON.stringify({ type: 'get_channels' }));

    // Cleanup listener on component unmount
    return () => {
      webApp.offEvent('webAppQueryResponse', handleQueryResponse);
    };
  }, []); // The empty array ensures this runs only once when the component loads

  // --- LOGIC TO CONTROL THE MAIN BUTTON ---
  useEffect(() => {
    if (postText.trim() !== '' && channelId && scheduleTime) {
      mainButton.setText('Schedule Post');
      mainButton.show();
    } else {
      mainButton.hide();
    }
  }, [postText, channelId, scheduleTime]);

  // --- LOGIC TO SEND DATA TO BOT ---
  const handleSendData = () => {
    const dataToSend = {
      type: 'new_post',
      text: postText,
      channel_id: channelId,
      schedule_time: scheduleTime,
    };
    webApp.sendData(JSON.stringify(dataToSend));
  };
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
          disabled={isLoading} // Disable while loading
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
            <option>No channels found</option>
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
