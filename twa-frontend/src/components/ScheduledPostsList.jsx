import React from 'react';
import { useAppStore } from '/src/store/appStore.js';
import './ScheduledPostsList.css';

const ScheduledPostsList = () => {
    // Ma'lumotlarni va amallarni to'g'ridan-to'g'ri do'kondan olamiz
    const { scheduledPosts, deletePost } = useAppStore();

    // isLoading holati endi App.jsx'da global boshqariladi, bu yerda kerak emas

    return (
        <div className="posts-list">
            <h2>Scheduled Posts</h2>
            {scheduledPosts.length === 0 ? (
                <p>You have no scheduled posts.</p>
            ) : (
                <ul>
                    {scheduledPosts.map((post) => (
                        <li key={post.id} className="post-item">
                            <div className="post-info">
                                <span className="channel-name">To: {post.channel_name}</span>
                                <p className="post-text">
                                    {post.file_type && `[${post.file_type.toUpperCase()}] `}
                                    {post.text || <em>(No caption)</em>}
                                </p>
                                <span className="schedule-time">
                                    At: {new Date(post.schedule_time).toLocaleString()}
                                </span>
                            </div>
                            <button 
                                className="delete-btn" 
                                onClick={() => deletePost(post.id)} // Amalni do'kondan chaqiramiz
                            >
                                Delete
                            </button>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
};

export default ScheduledPostsList;
