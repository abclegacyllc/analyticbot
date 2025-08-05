import React from 'react';
import { useAppContext } from '../context/AppContext'; // Context hook'ini import qilamiz
import './ScheduledPostsList.css';

const ScheduledPostsList = () => {
    // Ma'lumotlarni props o'rniga context'dan olamiz
    const { posts, isLoading, deletePost } = useAppContext();

    if (isLoading) {
        return <div className="posts-list"><h2>Scheduled Posts</h2><p>Loading posts...</p></div>;
    }

    return (
        <div className="posts-list">
            <h2>Scheduled Posts</h2>
            {posts.length === 0 ? (
                <p>You have no scheduled posts.</p>
            ) : (
                <ul>
                    {posts.map((post) => (
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
                                onClick={() => deletePost(post.id)}
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
