import React from 'react';
// Skeleton va Stack'ni import qilamiz
import { Container, Box, Typography, Skeleton, Stack } from '@mui/material'; 
import PostCreator from './components/PostCreator';
import ScheduledPostsList from './components/ScheduledPostsList';
import MediaPreview from './components/MediaPreview';
import AddChannel from './components/AddChannel';
import { useAppStore } from './store/appStore.js';

// Skelet komponenti
const AppSkeleton = () => (
    <Stack spacing={3} sx={{ mt: 2 }}>
        {/* AddChannel uchun skelet */}
        <Skeleton variant="rounded" width="100%" height={110} />
        {/* PostCreator uchun skelet */}
        <Skeleton variant="rounded" width="100%" height={280} />
        {/* ScheduledPostsList uchun skelet */}
        <Skeleton variant="rounded" width="100%" height={200} />
    </Stack>
);


function App() {
    const { pendingMedia, isLoading } = useAppStore();

    return (
        <Container maxWidth="sm">
            <Box sx={{ my: 2, textAlign: 'center' }}>
                <Typography variant="h4" component="h1" gutterBottom>
                    Bot Dashboard
                </Typography>
            </Box>

            {/* Endi bu yerda CircularProgress o'rniga AppSkeleton'ni ishlatamiz */}
            {isLoading ? (
                <AppSkeleton />
            ) : (
                <Box>
                    <AddChannel />
                    <MediaPreview media={pendingMedia} />
                    <PostCreator />
                    <ScheduledPostsList />
                </Box>
            )}
        </Container>
    );
}

export default App;
