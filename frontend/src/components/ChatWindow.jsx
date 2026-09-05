/**
 * ChatWindow — main chat interface with messages, input, voice, and streaming.
 */

import { useState, useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import VoiceButton from './VoiceButton';
import FlightCard from './FlightCard';
import HotelCard from './HotelCard';
import ConfirmationModal from './ConfirmationModal';

const TOOL_LABELS = {
  'search_flights': '✈️ Searching flights...',
  'search_hotels': '🏨 Searching hotels...',
  'search_activities': '🎯 Finding activities...',
  'get_weather': '🌤️ Checking weather...',
};

const SUGGESTIONS = [
  '✈️ Plan a 5-day trip to Goa',
  '🏔️ Weekend getaway to Manali',
  '🌍 Budget trip to Thailand',
  '🏖️ Honeymoon in Maldives',
  '🎭 Cultural tour of Rajasthan',
  '🗼 Week in Paris on a budget',
];

export default function ChatWindow({
  messages,
  isLoading,
  activeTools,
  streamingContent,
  onSendMessage,
}) {
  const [input, setInput] = useState('');
  const [pendingChoice, setPendingChoice] = useState(null); // { kind: 'flight'|'hotel', item, index }
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Import voice hook
  const [voiceState, setVoiceState] = useState({
    isListening: false,
    isSupported: false,
    transcript: '',
  });

  // Initialize voice on mount
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      setVoiceState(prev => ({ ...prev, isSupported: true }));
    }
  }, []);

  // Voice recognition setup
  const recognitionRef = useRef(null);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
      let finalTranscript = '';
      let interimTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }

      const text = finalTranscript || interimTranscript;
      setInput(text);

      // Auto-send on final result
      if (finalTranscript) {
        setTimeout(() => {
          handleSend(finalTranscript);
        }, 300);
      }
    };

    recognition.onend = () => {
      setVoiceState(prev => ({ ...prev, isListening: false }));
    };

    recognition.onerror = () => {
      setVoiceState(prev => ({ ...prev, isListening: false }));
    };

    recognitionRef.current = recognition;

    return () => {
      try { recognition.stop(); } catch {}
    };
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent, activeTools]);

  // TTS for assistant messages
  useEffect(() => {
    if (messages.length === 0) return;
    const lastMsg = messages[messages.length - 1];
    if (lastMsg.role === 'assistant' && !lastMsg.isError && window.speechSynthesis) {
      // Only speak short responses automatically
      if (lastMsg.content.length < 500) {
        const cleanText = lastMsg.content
          .replace(/\*\*(.*?)\*\*/g, '$1')
          .replace(/[✈️🏨🎯🌤️📋💰⭐]/g, '')
          .replace(/#{1,6}\s/g, '')
          .trim();

        if (cleanText.length > 10) {
          const utterance = new SpeechSynthesisUtterance(cleanText);
          utterance.rate = 1.0;
          utterance.pitch = 1.0;
          window.speechSynthesis.speak(utterance);
        }
      }
    }
  }, [messages]);

  const handleSend = (text) => {
    const msg = text || input;
    if (!msg.trim() || isLoading) return;
    onSendMessage(msg.trim());
    setInput('');
    inputRef.current?.focus();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleVoice = () => {
    if (!recognitionRef.current) return;

    if (voiceState.isListening) {
      recognitionRef.current.stop();
      setVoiceState(prev => ({ ...prev, isListening: false }));
    } else {
      setInput('');
      try {
        recognitionRef.current.start();
        setVoiceState(prev => ({ ...prev, isListening: true }));
      } catch {}
    }
  };

  const handleSuggestion = (text) => {
    // Remove emoji prefix
    const clean = text.replace(/^[^\w]+/, '').trim();
    onSendMessage(clean);
  };

  const openChoice = (kind, item, index) => {
    setPendingChoice({ kind, item, index });
  };

  const approveChoice = () => {
    if (!pendingChoice || isLoading) return;
    const { kind, item, index } = pendingChoice;
    const text =
      kind === 'flight'
        ? `I'll go with the flight option: ${item.airline || `Option ${index + 1}`}${item.price ? ` (${item.price})` : ''}. Please proceed.`
        : `I'll go with the hotel: ${item.name}${item.price_estimate ? ` (${item.price_estimate})` : ''}. Please proceed.`;
    setPendingChoice(null);
    onSendMessage(text);
  };

  const showWelcome = messages.length === 0;

  return (
    <>
    <div className="main-content">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-header-title">💬 Chat with TravelMate AI</div>
        <div className="chat-header-status">
          <div className="status-dot"></div>
          Online
        </div>
      </div>

      {/* Messages */}
      <div className="messages-container">
        {showWelcome ? (
          <div className="welcome-screen">
            <div className="welcome-icon">🌍</div>
            <h2>Where to next?</h2>
            <p>
              I'm your AI travel assistant. Tell me where you want to go, and I'll find
              flights, hotels, activities, and weather — all in one conversation.
            </p>
            <div className="welcome-suggestions">
              {SUGGESTIONS.map((s, i) => (
                <button
                  key={i}
                  className="suggestion-chip"
                  onClick={() => handleSuggestion(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, i) => (
              <div key={i} className="message-block">
                <MessageBubble message={msg} />
                {msg.role === 'assistant' &&
                  msg.toolResults?.map((tr, j) => {
                    if (tr.tool === 'search_flights') {
                      return (
                        <FlightCard
                          key={j}
                          data={tr.data}
                          onChoose={(item, idx) => openChoice('flight', item, idx)}
                        />
                      );
                    }
                    if (tr.tool === 'search_hotels') {
                      return (
                        <HotelCard
                          key={j}
                          data={tr.data}
                          onChoose={(item, idx) => openChoice('hotel', item, idx)}
                        />
                      );
                    }
                    return null;
                  })}
              </div>
            ))}

            {/* Tool call notifications */}
            {activeTools.map((tool, i) => (
              <div key={`tool-${i}`} className="tool-notification">
                {tool.status === 'running' && <div className="spinner"></div>}
                {tool.status === 'completed' ? '✅' : ''}
                {TOOL_LABELS[tool.tool] || `🔧 Running ${tool.tool}...`}
              </div>
            ))}

            {/* Streaming content */}
            {streamingContent && (
              <MessageBubble
                message={{ role: 'assistant', content: streamingContent }}
              />
            )}

            {/* Typing indicator */}
            {isLoading && !streamingContent && activeTools.length === 0 && (
              <div className="typing-indicator">
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
              </div>
            )}
          </>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="input-area">
        <div className="input-wrapper">
          <input
            ref={inputRef}
            type="text"
            placeholder={voiceState.isListening ? '🎤 Listening...' : 'Plan your next adventure...'}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            autoFocus
          />
          <VoiceButton
            isListening={voiceState.isListening}
            isSupported={voiceState.isSupported}
            onToggle={toggleVoice}
          />
          <button
            className="btn-icon btn-send"
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
            title="Send message"
          >
            ➤
          </button>
        </div>
      </div>
    </div>

    {pendingChoice && (
      <ConfirmationModal
        icon={pendingChoice.kind === 'flight' ? '✈️' : '🏨'}
        title={pendingChoice.kind === 'flight' ? 'this flight' : 'this hotel'}
        detail={
          pendingChoice.kind === 'flight' ? (
            <>
              <strong>{pendingChoice.item.airline || `Option ${pendingChoice.index + 1}`}</strong>
              {pendingChoice.item.price && <div>{pendingChoice.item.price}</div>}
              <div>
                {[pendingChoice.item.duration, pendingChoice.item.stops].filter(Boolean).join(' · ')}
              </div>
            </>
          ) : (
            <>
              <strong>{pendingChoice.item.name}</strong>
              {pendingChoice.item.rating && <div>⭐ {pendingChoice.item.rating}</div>}
              <div>
                {[pendingChoice.item.price_estimate, pendingChoice.item.location].filter(Boolean).join(' · ')}
              </div>
            </>
          )
        }
        onApprove={approveChoice}
        onCancel={() => setPendingChoice(null)}
      />
    )}
    </>
  );
}
