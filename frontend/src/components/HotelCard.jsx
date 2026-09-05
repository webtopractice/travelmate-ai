/**
 * HotelCard — displays hotel search results as selectable rows.
 */

import { renderFormattedText } from '../utils/textFormat';

export default function HotelCard({ data, onChoose }) {
  if (!data) return null;
  const items = Array.isArray(data.items) ? data.items : [];

  return (
    <div className="result-card">
      <div className="result-card-header">
        <span className="result-card-icon">🏨</span>
        <span className="result-card-title">
          Hotels{data.destination ? ` in ${data.destination}` : ''}
        </span>
      </div>

      {items.length > 0 ? (
        <div className="result-card-items">
          {items.map((item, i) => (
            <div key={i} className="result-card-item">
              <div className="result-card-item-main">
                <strong>{item.name}</strong>
                {item.rating && <span className="result-card-tag">⭐ {item.rating}</span>}
              </div>
              <div className="result-card-item-detail">
                {[item.price_estimate, item.location, item.type].filter(Boolean).join(' · ')}
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
