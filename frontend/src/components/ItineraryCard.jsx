/**
 * ItineraryCard — running trip summary shown in the sidebar.
 *
 * Aggregates the latest flights/hotels/activities/weather results seen
 * anywhere in the conversation so far. Purely derived from SSE tool_result
 * events on the frontend — no backend itinerary-building step required.
 */

export default function ItineraryCard({ summary }) {
  if (!summary) return null;
  const { flights, hotels, activities, weather } = summary;

  if (!flights && !hotels && !activities && !weather) return null;

  return (
    <div className="itinerary-card">
      <div className="sidebar-section-title" style={{ marginTop: '20px' }}>
        📋 Trip So Far
      </div>

      {flights && (
        <div className="itinerary-card-section">
          <div className="itinerary-card-section-title">✈️ Flights</div>
          {flights.items && flights.items.length > 0 ? (
            <div className="itinerary-card-line">{flights.items.length} option(s) found</div>
          ) : (
            <div className="itinerary-card-line">Options shared in chat</div>
          )}
        </div>
      )}

      {hotels && (
        <div className="itinerary-card-section">
          <div className="itinerary-card-section-title">🏨 Hotels{hotels.destination ? ` — ${hotels.destination}` : ''}</div>
          {(hotels.items || []).slice(0, 3).map((h, i) => (
            <div key={i} className="itinerary-card-line">
              {h.name}
              {h.rating ? ` (⭐${h.rating})` : ''}
            </div>
          ))}
        </div>
      )}

      {activities && (
        <div className="itinerary-card-section">
          <div className="itinerary-card-section-title">🎯 Activities{activities.destination ? ` — ${activities.destination}` : ''}</div>
          {(activities.items || []).slice(0, 4).map((a, i) => (
            <div key={i} className="itinerary-card-line">{a.name}</div>
          ))}
        </div>
      )}

      {weather && weather.current && (
        <div className="itinerary-card-section">
          <div className="itinerary-card-section-title">🌤️ Weather{weather.city ? ` — ${weather.city}` : ''}</div>
          <div className="itinerary-card-line">
            {weather.current.temp}°C, {weather.current.description}
          </div>
        </div>
      )}
    </div>
  );
}
