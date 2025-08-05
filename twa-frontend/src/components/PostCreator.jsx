import React, { useState, useEffect } from 'react';
import { useAppStore } from '../store/appStore.js';
import ButtonConstructor from './ButtonConstructor.jsx';
import { Box, TextField, FormControl, InputLabel, Select, MenuItem, Typography } from '@mui/material';

const webApp = window.Telegram.WebApp;

const PostCreator = () => {
    const { channels, isLoading, pendingMedia, schedulePost } = useAppStore();
    const [postText, setPostText] = useState('');
    const [channelId, setChannelId] = useState('');
    const [scheduleTime, setScheduleTime] = useState('');
    const [buttons, setButtons] = useState([]);

    const mainButton = webApp.MainButton;

    useEffect(() => {
        if (!isLoading && channels.length > 0 && !channelId) {
            setChannelId(channels[0].id);
        }
    }, [isLoading, channels, channelId]);

    useEffect(() => {
        const isContentPresent = postText.trim() !== '' || pendingMedia || buttons.length > 0;
        const isReady = channelId && scheduleTime && isContentPresent;

        if (isReady) {
            mainButton.setParams({
                text: 'Schedule Post',
                color: '#58a6ff', // MUI primary color
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
                inline_buttons: buttons,
            };
            schedulePost(dataToSend);
            
            setPostText('');
            setScheduleTime('');
            setButtons([]);
        };

        mainButton.onClick(handleSendData);
        return () => mainButton.offClick(handleSendData);
    }, [postText, channelId, scheduleTime, pendingMedia, buttons, schedulePost, mainButton]);

    return (
        <Box sx={{ mb: 3, p: 2, bgcolor: 'background.paper', borderRadius: '6px' }}>
            <Typography variant="h6" gutterBottom>Create New Post</Typography>
            <Box component="form" noValidate autoComplete="off" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <FormControl fullWidth size="small">
                    <InputLabel id="channel-select-label">Channel</InputLabel>
                    <Select
                        labelId="channel-select-label"
                        id="channel-select"
                        value={channelId}
                        label="Channel"
                        onChange={(e) => setChannelId(e.target.value)}
                        disabled={isLoading || channels.length === 0}
                    >
                        {isLoading ? (
                            <MenuItem value=""><em>Loading channels...</em></MenuItem>
                        ) : channels.length > 0 ? (
                            channels.map((channel) => (
                                <MenuItem key={channel.id} value={channel.id}>{channel.name}</MenuItem>
                            ))
                        ) : (
                            <MenuItem value=""><em>No channels found</em></MenuItem>
                        )}
                    </Select>
                </FormControl>
                <TextField
                    label={pendingMedia ? "Caption (optional)" : "Text"}
                    multiline
                    rows={4}
                    value={postText}
                    onChange={(e) => setPostText(e.target.value)}
                    variant="outlined"
                    fullWidth
                />
                <TextField
                    label="Schedule Time"
                    type="datetime-local"
                    value={scheduleTime}
                    onChange={(e) => setScheduleTime(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                    fullWidth
                    size="small"
                />
                <ButtonConstructor buttons={buttons} onButtonsChange={setButtons} />
            </Box>
        </Box>
    );
};

export default PostCreator;
