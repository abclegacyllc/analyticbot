import React from 'react';
import { Box, Typography, Chip } from '@mui/material';
import PhotoIcon from '@mui/icons-material/Photo';
import VideocamIcon from '@mui/icons-material/Videocam';

const MediaPreview = ({ media }) => {
    if (!media) {
        return null;
    }

    return (
        <Box sx={{ mb: 2, p: 2, border: '1px solid #30363d', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: 2 }}>
            {media.file_type === 'photo' ? <PhotoIcon /> : <VideocamIcon />}
            <Box>
                <Typography variant="subtitle1">Media Attached</Typography>
                <Typography variant="body2" color="text.secondary">
                    A {media.file_type} is ready to be scheduled. It will be sent with your post.
                </Typography>
            </Box>
        </Box>
    );
};

export default MediaPreview;
