import React from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface TextBubbleProps {
  content: string;
  isStreaming?: boolean;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const TextBubble: React.FC<TextBubbleProps> = ({ content, isStreaming }) => {
  if (!content && !isStreaming) return null;

  return (
    <div className="text-bubble">
      <div className="text-bubble__header">Assistant</div>
      <div className="text-bubble__content">
        <pre className="text-bubble__text">{content}</pre>
        {isStreaming && <span className="text-bubble__cursor">|</span>}
      </div>
    </div>
  );
};

export default TextBubble;
