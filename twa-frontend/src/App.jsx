import React from 'react';
import { Container, Box, Typography, Skeleton, Stack } from '@mui/material';
import PostCreator from './components/PostCreator';
import ScheduledPostsList from './components/ScheduledPostsList';
import MediaPreview from './components/MediaPreview';
import AddChannel from './components/AddChannel';
import { useAppStore } from './store/appStore.js';

const AppSkeleton = () => (
    <Stack spacing={3} sx={{ mt: 2 }}>
        <Skeleton variant="rounded" width="100%" height={110} />
        <Skeleton variant="rounded" width="100%" height={280} />
        <Skeleton variant="rounded" width="100%" height={200} />
    </Stack>
);

function App() {
    const { isLoading } = useAppStore();

    return (
        <Container maxWidth="sm">
            <Box sx={{ my: 2, textAlign: 'center' }}>
                <Typography variant="h4" component="h1" gutterBottom>
                    Bot Dashboard
                </Typography>
            </Box>

            {isLoading ? (
                <AppSkeleton />
            ) : (
                <Box>
                    <AddChannel />
                    <MediaPreview /> {/* Props olib tashlandi */}
                    <PostCreator />
                    <ScheduledPostsList />
                </Box>
            )}
        </Container>
    );
}

export default App;