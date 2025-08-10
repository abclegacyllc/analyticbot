import React, { useState } from 'react';
import { TextField, Button, Box, Select, MenuItem, FormControl, InputLabel } from '@mui/material';

const ButtonConstructor = ({ onAddButton }) => {
    const [buttonText, setButtonText] = useState('');
    const [buttonUrl, setButtonUrl] = useState('');
    const [buttonType, setButtonType] = useState('url');
    // Xatolik holatini saqlash uchun yangi state
    const [urlError, setUrlError] = useState('');

    const validateUrl = (url) => {
        if (url && !url.startsWith('http://') && !url.startsWith('https://')) {
            setUrlError('URL must start with http:// or https://');
            return false;
        }
        setUrlError(''); // Xatolik bo'lmasa, matnni tozalaymiz
        return true;
    };

    const handleAddButton = () => {
        if (buttonType === 'url') {
            if (!validateUrl(buttonUrl)) {
                return; // Agar URL noto'g'ri bo'lsa, funksiyadan chiqib ketamiz
            }
        }
        
        onAddButton({ text: buttonText, url: buttonUrl });
        setButtonText('');
        setButtonUrl('');
    };

    const handleUrlChange = (e) => {
        const newUrl = e.target.value;
        setButtonUrl(newUrl);
        // Har bir o'zgarishda validatsiya qilamiz
        validateUrl(newUrl);
    };

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2, p: 2, border: '1px solid grey', borderRadius: '4px' }}>
            <TextField
                label="Button Text"
                value={buttonText}
                onChange={(e) => setButtonText(e.target.value)}
                size="small"
                required
            />
            <FormControl size="small">
                <InputLabel>Button Type</InputLabel>
                <Select
                    value={buttonType}
                    label="Button Type"
                    onChange={(e) => setButtonType(e.target.value)}
                >
                    <MenuItem value="url">URL</MenuItem>
                </Select>
            </FormControl>
            {buttonType === 'url' && (
                <TextField
                    label="Button URL"
                    value={buttonUrl}
                    onChange={handleUrlChange} // O'zgartirilgan handler
                    size="small"
                    required
                    // Xatolikni ko'rsatish uchun props'lar
                    error={!!urlError} // Agar urlError'da matn bo'lsa, 'true' bo'ladi
                    helperText={urlError} // Xatolik matnini ko'rsatish
                />
            )}
            <Button onClick={handleAddButton} variant="outlined" disabled={!buttonText}>
                Add Button
            </Button>
        </Box>
    );
};

export default ButtonConstructor;
