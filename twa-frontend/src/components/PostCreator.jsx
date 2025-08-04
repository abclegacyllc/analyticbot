import React, { useState, useEffect } from 'react';
import './PostCreator.css';

const webApp = window.Telegram.WebApp;

const PostCreator = ({ channels, isLoading, pendingMedia, onPostScheduled }) => {
  const [postText, setPostText] = useState('');
  const [channelId, setChannelId] = useState('');
  const [scheduleTime, setScheduleTime] = useState('');
  
  const mainButton = webApp.MainButton;

  // TUZATISH: Bu effekt endi faqat kanallar birinchi marta yuklanganda ishlaydi
  // va tanlangan kanalni qayta-qayta o'zgartirib yubormaydi.
  useEffect(() => {
    if (!isLoading && channels.length > 0 && !channelId) {
      setChannelId(channels[0].id);
    }
  }, [isLoading, channels, channelId]);

  useEffect(() => {
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

  useEffect(() => {
    const handleSendData = () => {
      const dataToSend = {
        type: 'new_post',
        text: postText,
        channel_id: channelId,
        schedule_time: scheduleTime,
        file_id: pendingMedia ? pendingMedia.file_id : null,
        file_type: pendingMedia ? pendingMedia.file_type : null,
      };
      webApp.sendData(JSON.stringify(dataToSend));
      onPostScheduled();
    };

    mainButton.onClick(handleSendData);

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
