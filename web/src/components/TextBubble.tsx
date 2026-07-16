import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Check } from 'lucide-react';

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
  const [copied, setCopied] = useState(false);

  if (!content && !isStreaming) return null;

  const handleCopy = async () => {
    if (!content) return;
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = content;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="text-bubble">
      <div className="text-bubble__header">
        <span>Assistant</span>
        {content && !isStreaming && (
          <button
            className="text-bubble__copy-btn"
            onClick={handleCopy}
            title={copied ? 'Copied!' : 'Copy'}
            type="button"
          >
            {copied ? <Check size={14} /> : <Copy size={14} />}
          </button>
        )}
      </div>
      <div className="text-bubble__content">
        <div className="text-bubble__markdown">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code({ className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '');
                const codeString = String(children).replace(/\n$/, '');
                // Inline code
                if (!match) {
                  return (
                    <code className="text-bubble__inline-code" {...props}>
                      {children}
                    </code>
                  );
                }
                // Code block with syntax highlighting
                return (
                  <div className="text-bubble__code-block">
                    <div className="text-bubble__code-header">
                      <span className="text-bubble__code-lang">{match[1]}</span>
                      <button
                        className="text-bubble__code-copy"
                        onClick={() => {
                          navigator.clipboard.writeText(codeString);
                        }}
                        type="button"
                      >
                        Copy
                      </button>
                    </div>
                    <SyntaxHighlighter
                      style={oneLight}
                      language={match[1]}
                      PreTag="div"
                    >
                      {codeString}
                    </SyntaxHighlighter>
                  </div>
                );
              },
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
        {isStreaming && <span className="text-bubble__cursor">✦</span>}
      </div>
    </div>
  );
};

export default TextBubble;
