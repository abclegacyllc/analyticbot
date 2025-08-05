import React, { useState, useEffect } from 'react';
import { useAppStore } from '../store/appStore.js';
import ButtonConstructor from './ButtonConstructor.jsx'; // Yangi komponentni import qilamiz
import './PostCreator.css';

const webApp = window.Telegram.WebApp;

const PostCreator = () => {
    const { channels, isLoading, pendingMedia, schedulePost } = useAppStore();

    const [postText, setPostText] = useState('');
    const [channelId, setChannelId] = useState('');
    const [scheduleTime, setScheduleTime] = useState('');
    const [buttons, setButtons] = useState([]); // Tugmalar uchun yangi holat (state)

    const mainButton = webApp.MainButton;

    useEffect(() => {
        if (!isLoading && channels.length > 0 && !channelId) {
            setChannelId(channels[0].id);
        }
    }, [isLoading, channels, channelId]);

    useEffect(() => {
        // Postda matn, media yoki tugmalar bo'lsa, uni yuborishga tayyor deb hisoblaymiz
        const isContentPresent = postText.trim() !== '' || pendingMedia || buttons.length > 0;
        const isReady = channelId && scheduleTime && isContentPresent;

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
    }, [postText, channelId, scheduleTime, pendingMedia, buttons, mainButton]);

    useEffect(() => {
        const handleSendData = () => {
            const dataToSend = {
                text: postText,
                channel_id: channelId,
                schedule_time: scheduleTime,
                file_id: pendingMedia ? pendingMedia.file_id : null,
                file_type: pendingMedia ? pendingMedia.file_type : null,
                inline_buttons: buttons, // Tugmalar ma'lumotini botga yuboramiz
            };
            schedulePost(dataToSend);
            
            // Ma'lumot yuborilgandan so'ng formani tozalaymiz
            setPostText('');
            setScheduleTime('');
            setButtons([]);
        };

        mainButton.onClick(handleSendData);

        return () => {
            mainButton.offClick(handleSendData);
        };
    }, [postText, channelId, scheduleTime, pendingMedia, buttons, schedulePost, mainButton]);

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

            {/* Yangi ButtonConstructor komponentini chaqiramiz */}
            <ButtonConstructor buttons={buttons} onButtonsChange={setButtons} />
        </div>
    );
};

export default PostCreator;
