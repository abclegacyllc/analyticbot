import React, { useState, useEffect } from 'react';
import {
    Box,
    TextField,
    Button,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Typography,
    CircularProgress,
    List,
    ListItem,
    ListItemText,
    Chip
} from '@mui/material';
import { LocalizationProvider, DateTimePicker } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import useAppStore from '../store/appStore';
import ButtonConstructor from './ButtonConstructor';
import MediaPreview from "./MediaPreview.jsx";

const PostCreator = () => {
    const {
        channels,
        schedulePost,
        uploadMedia,
        isLoading,
        error,
        pendingMedia,
        clearPendingMedia,
    } = useAppStore();

    const [text, setText] = useState('');
    const [selectedChannel, setSelectedChannel] = useState('');
    const [scheduleTime, setScheduleTime] = useState(null);
    const [buttons, setButtons] = useState([]); // Tugmalar uchun state

    // --- YANGI FUNKSIYA ---
    // ButtonConstructor'dan kelgan yangi tugmani state'ga qo'shadi
    const handleAddButton = (newButton) => {
        setButtons(prevButtons => [...prevButtons, newButton]);
    };

    const handleFileChange = (event) => {
        const file = event.target.files[0];
        if (file) {
            uploadMedia(file);
        }
    };

    const handleSchedulePost = () => {
        if ((text || pendingMedia.file_id) && selectedChannel && scheduleTime) {
            // Tugmalarni to'g'ri formatga o'tkazish
            const inline_buttons = buttons.length > 0 ? { inline_keyboard: [buttons] } : null;

            schedulePost({
                text: text,
                channel_id: selectedChannel,
                schedule_time: scheduleTime.toISOString(),
                media_file_id: pendingMedia.file_id,
                media_type: pendingMedia.file_type,
                inline_buttons: inline_buttons // Formatlangan tugmalarni yuborish
            });
            setText('');
            setSelectedChannel('');
            setScheduleTime(null);
            setButtons([]); // Tugmalarni tozalash
            clearPendingMedia(); // Mediani tozalash
        }
    };

    return (
        <LocalizationProvider dateAdapter={AdapterDateFns}>
            <Box sx={{ p: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Typography variant="h6">Post Yaratish</Typography>
                <TextField
                    label="Post matni"
                    multiline
                    rows={4}
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    variant="outlined"
                    fullWidth
                />
                <FormControl fullWidth>
                    <InputLabel id="channel-select-label">Kanalni tanlang</InputLabel>
                    <Select
                        labelId="channel-select-label"
                        value={selectedChannel}
                        label="Kanalni tanlang"
                        onChange={(e) => setSelectedChannel(e.target.value)}
                    >
                        {channels.map((channel) => (
                            <MenuItem key={channel.id} value={channel.id}>
                                {channel.title} (@{channel.username})
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>
                <DateTimePicker
                    label="Yuborish vaqti"
                    value={scheduleTime}
                    onChange={(newValue) => setScheduleTime(newValue)}
                    renderInput={(params) => <TextField {...params} />}
                />

                <Button variant="contained" component="label">
                    Media Yuklash
                    <input type="file" hidden onChange={handleFileChange} />
                </Button>

                {pendingMedia.file_id && <MediaPreview media={pendingMedia} onClear={clearPendingMedia}/>}

                {/* --- O'ZGARTIRILGAN QATOR --- */}
                {/* ButtonConstructor'ga onAddButton funksiyasini uzatamiz */}
                <ButtonConstructor onAddButton={handleAddButton} />

                {/* Qo'shilgan tugmalarni ko'rsatish */}
                {buttons.length > 0 && (
                    <Box>
                        <Typography variant="subtitle2">Qo'shilgan tugmalar:</Typography>
                        <List dense>
                            {buttons.map((button, index) => (
                                <ListItem key={index}>
                                    <Chip label={`${button.text} -> ${button.url}`} onDelete={() => {
                                        setButtons(buttons.filter((_, i) => i !== index));
                                    }}/>
                                </ListItem>
                            ))}
                        </List>
                    </Box>
                )}


                <Button
                    variant="contained"
                    color="primary"
                    onClick={handleSchedulePost}
                    disabled={isLoading || !selectedChannel || !scheduleTime || (!text && !pendingMedia.file_id)}
                >
                    {isLoading ? <CircularProgress size={24} /> : 'Postni Rejalashtirish'}
                </Button>
                {error && <Typography color="error">{error}</Typography>}
            </Box>
        </LocalizationProvider>
    );
};

export default PostCreator;
