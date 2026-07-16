import React from 'react';

interface UserBubbleProps {
  content: string;
}

const UserBubble: React.FC<UserBubbleProps> = ({ content }) => (
  <div className="user-bubble">
    <div className="user-bubble__header">You</div>
    <div className="user-bubble__content">
      <pre className="user-bubble__text">{content}</pre>
    </div>
  </div>
);

export default UserBubble;
