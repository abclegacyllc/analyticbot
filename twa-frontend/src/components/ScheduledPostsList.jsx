import React from 'react';
import { useAppStore } from '../store/appStore.js';
import { Box, Typography, List, ListItem, ListItemText, IconButton, Chip } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';

const ScheduledPostsList = () => {
    const { scheduledPosts, deletePost } = useAppStore();

    return (
        <Box sx={{ mb: 3, p: 2, border: '1px solid #30363d', borderRadius: '6px' }}>
            <Typography variant="h6" gutterBottom>Scheduled Posts</Typography>
            {scheduledPosts.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                    You have no scheduled posts.
                </Typography>
            ) : (
                <List dense>
                    {scheduledPosts.map((post) => (
                        <ListItem
                            key={post.id}
                            secondaryAction={
                                <IconButton edge="end" aria-label="delete" onClick={() => deletePost(post.id)}>
                                    <DeleteIcon />
                                </IconButton>
                            }
                            sx={{ borderBottom: '1px solid #30363d', pb: 1, mb: 1 }}
                        >
                            <ListItemText
                                primary={
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                                        {post.file_type && <Chip label={post.file_type.toUpperCase()} size="small" />}
                                        <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                                            To: {post.channel_name}
                                        </Typography>
                                    </Box>
                                }
                                secondary={
                                    <>
                                        <Typography variant="body1" component="p" sx={{ mb: 0.5, wordBreak: 'break-word' }}>
                                            {post.text || <em>(No caption)</em>}
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary">
                                            At: {new Date(post.schedule_time).toLocaleString()}
                                        </Typography>
                                    </>
                                }
                            />
                        </ListItem>
                    ))}
                </List>
            )}
        </Box>
    );
};

export default ScheduledPostsList;
