/**
 * ConfirmationModal — human-in-the-loop approval for a single flight/hotel pick.
 *
 * Approving sends a normal follow-up chat message via the existing
 * onSendMessage pipeline — no backend graph/interrupt changes required,
 * so this can't desync from the agent's actual conversation state.
 */

export default function ConfirmationModal({ icon, title, detail, onApprove, onCancel }) {
  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <span>
            {icon} Confirm {title}
          </span>
          <button className="modal-close" onClick={onCancel} title="Close">
            ✕
          </button>
        </div>

        <div className="modal-body">{detail}</div>

        <div className="modal-actions">
          <button className="btn-modal-secondary" onClick={onCancel}>
            Cancel
          </button>
          <button className="btn-modal-primary" onClick={onApprove}>
            ✅ Approve
          </button>
        </div>
      </div>
    </div>
  );
}
