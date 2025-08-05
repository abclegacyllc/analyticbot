import React, { useState } from 'react';
import './ButtonConstructor.css';

// Bu komponent `buttons` ro'yxatini va uni o'zgartiradigan funksiyalarni qabul qiladi
const ButtonConstructor = ({ buttons, onButtonsChange }) => {
    const [text, setText] = useState('');
    const [url, setUrl] = useState('');

    const handleAddButton = () => {
        // Maydonlar bo'sh emasligini va URL to'g'ri formatda ekanligini tekshiramiz
        if (text.trim() === '' || url.trim() === '') {
            alert('Button text and URL cannot be empty.');
            return;
        }
        if (!url.startsWith('http://') && !url.startsWith('https://')) {
            alert('URL must start with http:// or https://');
            return;
        }
        
        // Yangi tugmani ro'yxatga qo'shamiz
        onButtonsChange([...buttons, { text, url }]);
        
        // Kiritish maydonlarini tozalaymiz
        setText('');
        setUrl('');
    };

    const handleDeleteButton = (indexToDelete) => {
        // Tanlangan tugmani ro'yxatdan o'chiramiz
        onButtonsChange(buttons.filter((_, index) => index !== indexToDelete));
    };

    return (
        <div className="button-constructor">
            <h3>Inline Buttons</h3>
            
            {/* Mavjud tugmalar ro'yxati */}
            <ul className="button-list">
                {buttons.map((btn, index) => (
                    <li key={index} className="button-item">
                        <div>
                            <span className="button-item-text">{btn.text}</span>
                            <span className="button-item-url">{btn.url}</span>
                        </div>
                        <div className="button-item-actions">
                            <button onClick={() => handleDeleteButton(index)}>✖</button>
                        </div>
                    </li>
                ))}
            </ul>

            {/* Yangi tugma qo'shish formasi */}
            <div className="add-button-form">
                <input
                    type="text"
                    placeholder="Button Text"
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                />
                <input
                    type="text"
                    placeholder="https://example.com"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                />
                <button onClick={handleAddButton}>Add Button</button>
            </div>
        </div>
    );
};

export default ButtonConstructor;
