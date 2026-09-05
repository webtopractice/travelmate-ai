/**
 * App — TravelMate AI main application layout.
 *
 * Layout: Sidebar (branding + itinerary) | Chat Window
 */

import { useChat } from './hooks/useChat';
import ChatWindow from './components/ChatWindow';
import ItineraryCard from './components/ItineraryCard';

export default function App() {
  const {
    messages,
    threadId,
    isLoading,
    activeTools,
    streamingContent,
    tripSummary,
    sendMessage,
    resetChat,
  } = useChat();

  return (
    <div className="app">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <div className="sidebar-logo-icon">✈️</div>
            <div>
              <h1>TravelMate AI</h1>
              <p>Your AI Travel Assistant</p>
            </div>
          </div>
        </div>

        <div className="sidebar-content">
          {/* New Chat Button */}
          <button
            onClick={resetChat}
            style={{
              width: '100%',
              padding: '10px 16px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-tertiary)',
              color: 'var(--text-primary)',
              fontSize: '0.85rem',
              fontWeight: 500,
              cursor: 'pointer',
              marginBottom: '20px',
              fontFamily: 'var(--font-family)',
              transition: 'all var(--transition-normal)',
            }}
            onMouseOver={(e) => {
              e.target.style.borderColor = 'var(--accent-primary)';
              e.target.style.background = 'var(--bg-glass-hover)';
            }}
            onMouseOut={(e) => {
              e.target.style.borderColor = 'var(--border-color)';
              e.target.style.background = 'var(--bg-tertiary)';
            }}
          >
            ➕ New Trip Conversation
          </button>

          {/* How It Works */}
          <div className="sidebar-section-title">How It Works</div>

          <div className="itinerary-item">
            <div className="itinerary-item-header">
              <span className="itinerary-item-icon">💬</span>
              <span className="itinerary-item-title">1. Tell Me Your Plans</span>
            </div>
            <div className="itinerary-item-detail">
              Share your destination, dates, budget, and interests
            </div>
          </div>

          <div className="itinerary-item">
            <div className="itinerary-item-header">
              <span className="itinerary-item-icon">🔍</span>
              <span className="itinerary-item-title">2. I Search & Compare</span>
            </div>
            <div className="itinerary-item-detail">
              Real-time flights, hotels, activities & weather
            </div>
          </div>

          <div className="itinerary-item">
            <div className="itinerary-item-header">
              <span className="itinerary-item-icon">✅</span>
              <span className="itinerary-item-title">3. You Confirm</span>
            </div>
            <div className="itinerary-item-detail">
              Review options and approve each step
            </div>
          </div>

          <div className="itinerary-item">
            <div className="itinerary-item-header">
              <span className="itinerary-item-icon">📋</span>
              <span className="itinerary-item-title">4. Get Your Itinerary</span>
            </div>
            <div className="itinerary-item-detail">
              Complete day-by-day travel plan
            </div>
          </div>

          {/* Running trip summary — populated as flights/hotels/activities/weather are found */}
          <ItineraryCard summary={tripSummary} />

          {/* Capabilities */}
          <div className="sidebar-section-title" style={{ marginTop: '20px' }}>
            Powered By
          </div>

          <div className="itinerary-item">
            <div className="itinerary-item-header">
              <span className="itinerary-item-icon">🧠</span>
              <span className="itinerary-item-title">Claude AI + LangGraph</span>
            </div>
            <div className="itinerary-item-detail">
              Agentic AI with tool calling & memory
            </div>
          </div>

          <div className="itinerary-item">
            <div className="itinerary-item-header">
              <span className="itinerary-item-icon">🎤</span>
              <span className="itinerary-item-title">Voice & Text</span>
            </div>
            <div className="itinerary-item-detail">
              Speak or type — multimodal input
            </div>
          </div>

          <div className="itinerary-item">
            <div className="itinerary-item-header">
              <span className="itinerary-item-icon">🌐</span>
              <span className="itinerary-item-title">Real APIs</span>
            </div>
            <div className="itinerary-item-detail">
              Kiwi.com flights, OpenTripMap, OpenWeather
            </div>
          </div>

          {/* Thread info */}
          {threadId && (
            <div style={{
              marginTop: '20px',
              padding: '10px',
              borderRadius: 'var(--radius-sm)',
              background: 'rgba(99, 102, 241, 0.08)',
              fontSize: '0.7rem',
              color: 'var(--text-muted)',
              wordBreak: 'break-all',
            }}>
              🧵 Thread: {threadId.slice(0, 8)}...
            </div>
          )}
        </div>
      </aside>

      {/* Main Chat */}
      <ChatWindow
        messages={messages}
        isLoading={isLoading}
        activeTools={activeTools}
        streamingContent={streamingContent}
        onSendMessage={sendMessage}
      />
    </div>
  );
}
