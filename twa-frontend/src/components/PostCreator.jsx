import React, { useState, useEffect } from 'react';
import { useAppContext } from '../context/AppContext'; // Context hook'ini import qilamiz
import './PostCreator.css';

const webApp = window.Telegram.WebApp;

const PostCreator = () => {
    // Barcha kerakli ma'lumotlarni props o'rniga context'dan olamiz
    const { channels, isLoading, pendingMedia, schedulePost } = useAppContext();

    const [postText, setPostText] = useState('');
    const [channelId, setChannelId] = useState('');
    const [scheduleTime, setScheduleTime] = useState('');
  
    const mainButton = webApp.MainButton;

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
                text: postText,
                channel_id: channelId,
                schedule_time: scheduleTime,
                file_id: pendingMedia ? pendingMedia.file_id : null,
                file_type: pendingMedia ? pendingMedia.file_type : null,
            };
            // Endi schedulePost funksiyasini context'dan chaqiramiz
            schedulePost(dataToSend);
        };

        mainButton.onClick(handleSendData);

        return () => {
            mainButton.offClick(handleSendData);
        };
    }, [postText, channelId, scheduleTime, pendingMedia, schedulePost, mainButton]);

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
                            <option key={channel.id} value={channel.id}>{channel.name}</option>
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
                    placeholder={pendingMedia ? "Enter a caption..." : "Enter your post text..."}
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
