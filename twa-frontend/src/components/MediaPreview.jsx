import React from 'react';
import './MediaPreview.css';

const MediaPreview = ({ media }) => {
  // If there's no media, this component renders nothing
  if (!media || !media.file_id) {
    return null;
  }

  return (
    <div className="media-preview-container">
      <h4>Media to Schedule</h4>
      <div className="media-item">
        <p>
            <strong>File Type:</strong> {media.file_type} <br />
            <strong>File ID:</strong> <span>{media.file_id.slice(0, 30)}...</span>
        </p>
        <div className="media-notice">
            A full preview is not available here, but the bot has saved your {media.file_type} and will post it correctly.
        </div>
      </div>
    </div>
  );
};

export default MediaPreview;
