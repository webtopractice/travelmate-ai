/**
 * useChat hook — manages chat state, message streaming, and thread persistence.
 */

import { useState, useCallback, useRef } from 'react';
import { streamChat } from '../utils/api';

const TOOL_TO_SUMMARY_KEY = {
  search_flights: 'flights',
  search_hotels: 'hotels',
  search_activities: 'activities',
  get_weather: 'weather',
};

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [threadId, setThreadId] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeTools, setActiveTools] = useState([]);
  const [streamingContent, setStreamingContent] = useState('');
  const [tripSummary, setTripSummary] = useState({
    flights: null,
    hotels: null,
    activities: null,
    weather: null,
  });
  const abortRef = useRef(false);
  const activeToolsRef = useRef([]);

  /**
   * Send a message and stream the AI response.
   */
  const sendMessage = useCallback(async (text) => {
    if (!text.trim() || isLoading) return;

    abortRef.current = false;

    // Add user message immediately
    const userMsg = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);
    setStreamingContent('');
    setActiveTools([]);
    activeToolsRef.current = [];

    let accumulated = '';

    await streamChat(text, threadId, {
      onThreadId: (id) => {
        setThreadId(id);
      },

      onToken: (content) => {
        if (abortRef.current) return;
        accumulated += content;
        setStreamingContent(accumulated);
      },

      onToolCall: (data) => {
        if (abortRef.current) return;
        setActiveTools(prev => {
          const next = [...prev, { tool: data.tool, status: 'running', input: data.input }];
          activeToolsRef.current = next;
          return next;
        });
      },

      onToolResult: (data) => {
        if (abortRef.current) return;
        setActiveTools(prev => {
          const next = prev.map(t =>
            t.tool === data.tool && t.status === 'running'
              ? { ...t, status: 'completed', result: data.result, data: data.data }
              : t
          );
          activeToolsRef.current = next;
          return next;
        });

        // Update the running trip summary with the latest structured result
        const summaryKey = TOOL_TO_SUMMARY_KEY[data.tool];
        if (summaryKey && data.data) {
          setTripSummary(prev => ({ ...prev, [summaryKey]: data.data }));
        }
      },

      onDone: (data) => {
        if (abortRef.current) return;
        // Add the full assistant message
        const finalContent = accumulated || data.full_response || '';
        const toolResults = activeToolsRef.current
          .filter(t => t.data)
          .map(t => ({ tool: t.tool, data: t.data }));

        if (finalContent) {
          setMessages(prev => [
            ...prev,
            { role: 'assistant', content: finalContent, toolResults },
          ]);
        }
        setStreamingContent('');
        setActiveTools([]);
        activeToolsRef.current = [];
        setIsLoading(false);
      },

      onError: (error) => {
        console.error('Chat error:', error);
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `⚠️ Sorry, something went wrong: ${error}. Please try again.`,
          isError: true,
        }]);
        setStreamingContent('');
        setActiveTools([]);
        setIsLoading(false);
      },
    });
  }, [threadId, isLoading]);

  /**
   * Start a new conversation.
   */
  const resetChat = useCallback(() => {
    abortRef.current = true;
    setMessages([]);
    setThreadId('');
    setIsLoading(false);
    setStreamingContent('');
    setActiveTools([]);
    activeToolsRef.current = [];
    setTripSummary({ flights: null, hotels: null, activities: null, weather: null });
  }, []);

  return {
    messages,
    threadId,
    isLoading,
    activeTools,
    streamingContent,
    tripSummary,
    sendMessage,
    resetChat,
  };
}
