import React from 'react';
import { Box, IconButton, Tooltip } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { useAppStore } from '../store/appStore';

const MediaPreview = () => {
    const { pendingMedia, clearPendingMedia } = useAppStore();

    // If there is no media with a preview URL, render nothing
    if (!pendingMedia?.previewUrl) {
        return null;
    }

    return (
        <Box sx={{ position: 'relative', mb: 2, border: '1px solid #30363d', borderRadius: '6px', overflow: 'hidden', maxWidth: '200px' }}>
             <Tooltip title="Remove Photo">
                <IconButton
                    onClick={clearPendingMedia}
                    size="small"
                    sx={{
                        position: 'absolute',
                        top: 4,
                        right: 4,
                        backgroundColor: 'rgba(0, 0, 0, 0.6)',
                        '&:hover': { backgroundColor: 'rgba(0, 0, 0, 0.8)' }
                    }}
                >
                    <CloseIcon sx={{ color: 'white', fontSize: '1rem' }} />
                </IconButton>
            </Tooltip>
            <img 
                src={pendingMedia.previewUrl} 
                alt="Media Preview" 
                style={{ width: '100%', display: 'block' }} 
            />
        </Box>
    );
};

export default MediaPreview;