/**
 * FlightCard — displays flight search results.
 *
 * The Kiwi.com MCP response is free-form text (we don't parse it into
 * structured fields), so this renders the formatted summary inside a
 * styled card. If structured `items` ever are present, they're rendered
 * as individual selectable rows instead.
 */

import { renderFormattedText } from '../utils/textFormat';

export default function FlightCard({ data, onChoose }) {
  if (!data) return null;
  const items = Array.isArray(data.items) ? data.items : [];

  return (
    <div className="result-card">
      <div className="result-card-header">
        <span className="result-card-icon">✈️</span>
        <span className="result-card-title">Flight Options</span>
      </div>

      {items.length > 0 ? (
        <div className="result-card-items">
          {items.map((item, i) => (
            <div key={i} className="result-card-item">
              <div className="result-card-item-main">
                <strong>{item.airline || `Option ${i + 1}`}</strong>
                {item.price && <span className="result-card-tag">{item.price}</span>}
              </div>
              <div className="result-card-item-detail">
                {[item.duration, item.stops, item.departure && item.arrival ? `${item.departure} → ${item.arrival}` : null]
                  .filter(Boolean)
                  .join(' · ')}
              </div>
              {onChoose && (
                <button className="btn-choose" onClick={() => onChoose(item, i)}>
                  Select
                </button>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="result-card-summary">{renderFormattedText(data.summary)}</div>
      )}
    </div>
  );
}
