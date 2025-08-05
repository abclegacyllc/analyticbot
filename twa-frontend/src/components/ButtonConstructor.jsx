import React, { useState } from 'react';
import { Box, TextField, Button, List, ListItem, ListItemText, IconButton, Typography } from '@mui/material';
import AddCircleIcon from '@mui/icons-material/AddCircle';
import DeleteIcon from '@mui/icons-material/Delete';

const ButtonConstructor = ({ buttons, onButtonsChange }) => {
    const [text, setText] = useState('');
    const [url, setUrl] = useState('');

    const handleAddButton = () => {
        if (text.trim() === '' || url.trim() === '') return;
        if (!url.startsWith('http://') && !url.startsWith('https://')) {
            alert('URL must start with http:// or https://');
            return;
        }
        onButtonsChange([...buttons, { text, url }]);
        setText('');
        setUrl('');
    };

    const handleDeleteButton = (indexToDelete) => {
        onButtonsChange(buttons.filter((_, index) => index !== indexToDelete));
    };

    return (
        <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle1" gutterBottom>Inline Buttons</Typography>
            <List dense>
                {buttons.map((btn, index) => (
                    <ListItem
                        key={index}
                        disableGutters
                        secondaryAction={
                            <IconButton edge="end" onClick={() => handleDeleteButton(index)}>
                                <DeleteIcon />
                            </IconButton>
                        }
                    >
                        <ListItemText primary={btn.text} secondary={btn.url} />
                    </ListItem>
                ))}
            </List>
            <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                <TextField
                    label="Button Text"
                    variant="outlined"
                    size="small"
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    fullWidth
                />
                <TextField
                    label="URL"
                    variant="outlined"
                    size="small"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    fullWidth
                />
                <Button variant="contained" onClick={handleAddButton} sx={{ minWidth: 'auto', px: 2 }}>
                    <AddCircleIcon />
                </Button>
            </Box>
        </Box>
    );
};

export default ButtonConstructor;
