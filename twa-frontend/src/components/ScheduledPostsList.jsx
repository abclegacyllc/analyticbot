import React from 'react';
import './ScheduledPostsList.css';

// A helper function to format the date nicely
const formatScheduleTime = (isoString) => {
  const date = new Date(isoString);
  // Formats to "Aug 05, 2025, 10:30"
  return date.toLocaleString('en-US', {
    month: 'short',
    day: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });
};

const ScheduledPostsList = ({ posts, onDelete, isLoading }) => {
  // Show a loading message if data is not ready yet
  if (isLoading) {
    return (
        <div className="scheduled-posts-container">
            <h3>Scheduled Posts</h3>
            <p className="no-posts-message">Loading...</p>
        </div>
    );
  }

  // Show a different message if loading is finished but there are no posts
  if (posts.length === 0) {
    return (
      <div className="scheduled-posts-container">
        <h3>Scheduled Posts</h3>
        <p className="no-posts-message">You have no posts scheduled.</p>
      </div>
    );
  }

  return (
    <div className="scheduled-posts-container">
      <h3>Scheduled Posts</h3>
      <ul className="posts-list">
        {posts.map((post) => (
          <li key={post.id} className="post-item">
            <div className="post-info">
              <span className="post-text">
                {post.text.length > 80 ? `${post.text.substring(0, 80)}...` : post.text}
              </span>
              <span className="post-details">
                To: <strong>{post.channel_name}</strong> on {formatScheduleTime(post.schedule_time)}
              </span>
            </div>
            <button
              className="delete-button"
              onClick={() => onDelete(post.id)}
            >
              Delete
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ScheduledPostsList;
