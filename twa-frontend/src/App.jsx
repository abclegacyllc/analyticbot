import React from 'react';
import { Container, Box, Typography, CircularProgress } from '@mui/material';
import PostCreator from './components/PostCreator';
import ScheduledPostsList from './components/ScheduledPostsList';
import MediaPreview from './components/MediaPreview';
import AddChannel from './components/AddChannel';
import { useAppStore } from './store/appStore.js';

function App() {
    const { pendingMedia, isLoading } = useAppStore();

    return (
        <Container maxWidth="sm">
            <Box sx={{ my: 2, textAlign: 'center' }}>
                <Typography variant="h4" component="h1" gutterBottom>
                    Bot Dashboard
                </Typography>
            </Box>

            {isLoading && (
                <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
                    <CircularProgress />
                </Box>
            )}

            <Box sx={{ 
                transition: 'opacity 0.3s ease-in-out',
                opacity: isLoading ? 0.5 : 1, 
                pointerEvents: isLoading ? 'none' : 'auto' 
            }}>
                <AddChannel />
                <MediaPreview media={pendingMedia} />
                <PostCreator />
                <ScheduledPostsList />
            </Box>
        </Container>
    );
}

export default App;
