import React, { useState } from 'react';
import { Box, TextField, Button, Typography, Alert } from '@mui/material';
import { useAppStore } from '../store/appStore.js';

const AddChannel = () => {
    const { addChannel, addChannelStatus } = useAppStore();
    const [channelName, setChannelName] = useState('');

    const handleAdd = () => {
        if (channelName.trim()) {
            addChannel(channelName.trim());
            setChannelName('');
        }
    };

    return (
        <Box sx={{ mb: 3, p: 2, border: '1px solid #30363d', borderRadius: '6px' }}>
            <Typography variant="h6" gutterBottom>Add New Channel</Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                    fullWidth
                    variant="outlined"
                    size="small"
                    placeholder="@channel_username"
                    value={channelName}
                    onChange={(e) => setChannelName(e.target.value)}
                />
                <Button variant="contained" onClick={handleAdd}>Add</Button>
            </Box>
            {addChannelStatus.message && (
                <Alert severity={addChannelStatus.success ? 'success' : 'error'} sx={{ mt: 2 }}>
                    {addChannelStatus.message}
                </Alert>
            )}
        </Box>
    );
};

export default AddChannel;
