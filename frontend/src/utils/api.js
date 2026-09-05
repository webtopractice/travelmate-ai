/**
 * API utility — fetch + SSE streaming to the backend.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Send a chat message and stream the response via SSE.
 *
 * @param {string} message  - User's message text
 * @param {string} threadId - Conversation thread ID (or empty for new)
 * @param {object} callbacks - Event callbacks
 * @param {function} callbacks.onToken   - (text) called for each streamed token
 * @param {function} callbacks.onToolCall - ({tool, input, status}) called when a tool starts
 * @param {function} callbacks.onToolResult - ({tool, result, status}) called when a tool finishes
 * @param {function} callbacks.onDone    - ({full_response, thread_id}) called when stream ends
 * @param {function} callbacks.onError   - (error) called on error
 * @param {function} callbacks.onThreadId - (thread_id) called with the assigned thread ID
 */
export async function streamChat(message, threadId, callbacks) {
  const { onToken, onToolCall, onToolResult, onDone, onError, onThreadId } = callbacks;

  try {
    const response = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        thread_id: threadId || undefined,
      }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ error: 'Request failed' }));
      onError?.(err.error || `HTTP ${response.status}`);
      return;
    }

    // Read the SSE stream
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Parse SSE events from buffer
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer

      let eventType = '';
      let eventData = '';

      for (const line of lines) {
        if (line.startsWith('event: ')) {
          eventType = line.slice(7).trim();
        } else if (line.startsWith('data: ')) {
          eventData = line.slice(6);

          try {
            const parsed = JSON.parse(eventData);

            switch (eventType) {
              case 'thread_id':
                onThreadId?.(parsed.thread_id);
                break;
              case 'token':
                onToken?.(parsed.content);
                break;
              case 'tool_call':
                onToolCall?.(parsed);
                break;
              case 'tool_result':
                onToolResult?.(parsed);
                break;
              case 'done':
                onDone?.(parsed);
                break;
              case 'error':
                onError?.(parsed.error);
                break;
            }
          } catch {
            // Skip non-JSON lines
          }

          eventType = '';
          eventData = '';
        }
      }
    }
  } catch (err) {
    onError?.(err.message || 'Network error');
  }
}

/**
 * Get conversation history for a thread.
 */
export async function getHistory(threadId) {
  try {
    const response = await fetch(`${API_BASE}/api/history/${threadId}`);
    if (!response.ok) return { messages: [] };
    return await response.json();
  } catch {
    return { messages: [] };
  }
}
