import React, { useState } from 'react';
import { Box, TextField, Button, Typography, Alert, CircularProgress } from '@mui/material'; // CircularProgress qo'shildi
import { useAppStore } from '../store/appStore.js';

const AddChannel = () => {
    // isLoading holatini ham store'dan olamiz
    const { addChannel, addChannelStatus, isLoading } = useAppStore();
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
                    disabled={isLoading} // So'rov paytida nofaol
                />
                <Button 
                    variant="contained" 
                    onClick={handleAdd} 
                    disabled={isLoading} // So'rov paytida nofaol
                    sx={{ minWidth: '80px' }} // Tugma o'lchami o'zgarib ketmasligi uchun
                >
                    {isLoading ? <CircularProgress size={24} color="inherit" /> : 'Add'}
                </Button>
            </Box>
            {addChannelStatus.message && !isLoading && (
                <Alert severity={addChannelStatus.success ? 'success' : 'error'} sx={{ mt: 2 }}>
                    {addChannelStatus.message}
                </Alert>
            )}
        </Box>
    );
};

export default AddChannel;
