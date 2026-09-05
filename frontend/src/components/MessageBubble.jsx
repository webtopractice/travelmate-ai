/**
 * MessageBubble — renders a single chat message (user or assistant).
 */

import { renderFormattedText } from '../utils/textFormat';

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  const isError = message.isError;

  return (
    <div className={`message ${isUser ? 'message-user' : 'message-assistant'}`}>
      <div className="message-avatar">
        {isUser ? '👤' : '✈️'}
      </div>
      <div
        className="message-content"
        style={isError ? { borderColor: 'var(--error)', background: 'rgba(239, 68, 68, 0.1)' } : undefined}
      >
        {renderFormattedText(message.content)}
      </div>
    </div>
  );
}
