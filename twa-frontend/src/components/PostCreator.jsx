import React, { useState } from 'react';
import { Box, TextField, Button, Typography, Select, MenuItem, FormControl, InputLabel, CircularProgress } from '@mui/material';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import PhotoCamera from '@mui/icons-material/PhotoCamera';
import { useAppStore } from '../store/appStore.js';
import ButtonConstructor from './ButtonConstructor.jsx';

const PostCreator = () => {
    const { channels, schedulePost, isLoading, uploadMedia, pendingMedia } = useAppStore();
    const [text, setText] = useState('');
    const [selectedChannel, setSelectedChannel] = useState('');
    const [scheduleTime, setScheduleTime] = useState(null);
    const [buttons, setButtons] = useState([]);

    const handleSchedulePost = () => {
        if ((text || pendingMedia.file_id) && selectedChannel && scheduleTime) {
            schedulePost({
                text,
                channel_id: selectedChannel,
                schedule_time: scheduleTime.toISOString(),
                inline_buttons: buttons.length > 0 ? { inline_keyboard: [buttons] } : null
            });
            setText('');
            setSelectedChannel('');
            setScheduleTime(null);
            setButtons([]);
        }
    };

    const handleFileChange = (event) => {
        const file = event.target.files[0];
        if (file) {
            uploadMedia(file);
        }
    };

    return (
        <Box sx={{ mb: 3, p: 2, border: '1px solid #30363d', borderRadius: '6px' }}>
            <Typography variant="h6" gutterBottom>Create New Post</Typography>

            <TextField
                fullWidth
                multiline
                rows={4}
                variant="outlined"
                placeholder="Write your post content here..."
                value={text}
                onChange={(e) => setText(e.target.value)}
                margin="normal"
            />

            <Box sx={{ mt: 1, mb: 2 }}>
                <Button
                    component="label"
                    role={undefined}
                    variant="outlined"
                    tabIndex={-1}
                    startIcon={<PhotoCamera />}
                    disabled={!!pendingMedia.file_id || isLoading}
                >
                    Upload Media
                    <input type="file" hidden accept="image/*,video/*" onChange={handleFileChange} />
                </Button>
            </Box>

            <ButtonConstructor buttons={buttons} setButtons={setButtons} />

            <FormControl fullWidth margin="normal">
                <InputLabel id="channel-select-label">Select Channel</InputLabel>
                <Select
                    labelId="channel-select-label"
                    value={selectedChannel}
                    label="Select Channel"
                    onChange={(e) => setSelectedChannel(e.target.value)}
                >
                    {channels.map((channel) => (
                        <MenuItem key={channel.id} value={channel.id}>
                            {channel.title} ({channel.username})
                        </MenuItem>
                    ))}
                </Select>
            </FormControl>

            <DateTimePicker
                label="Schedule Time"
                value={scheduleTime}
                onChange={(newValue) => setScheduleTime(newValue)}
                sx={{ width: '100%', mt: 2, mb: 2 }}
            />

            <Button
                variant="contained"
                fullWidth
                onClick={handleSchedulePost}
                disabled={(!text && !pendingMedia.file_id) || !selectedChannel || !scheduleTime || isLoading}
            >
                {isLoading ? <CircularProgress size={24} /> : 'Schedule Post'}
            </Button>
        </Box>
    );
};

export default PostCreator;