import React from 'react';
import type { PendingGuardrail } from '../hooks/useSession';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface GuardrailModalProps {
  guardrail: PendingGuardrail | null;
  onApprove: () => void;
  onReject: () => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const GuardrailModal: React.FC<GuardrailModalProps> = ({
  guardrail,
  onApprove,
  onReject,
}) => {
  if (!guardrail) return null;

  return (
    <div className="guardrail-overlay">
      <div className="guardrail-modal">
        <div className="guardrail-modal__header">
          <span className="guardrail-modal__icon">&#9888;</span>
          <h2 className="guardrail-modal__title">Guardrail Triggered</h2>
        </div>

        <div className="guardrail-modal__body">
          <div className="guardrail-modal__field">
            <span className="guardrail-modal__label">Action</span>
            <span className="guardrail-modal__value guardrail-modal__value--action">
              {guardrail.action}
            </span>
          </div>

          <div className="guardrail-modal__field">
            <span className="guardrail-modal__label">Reason</span>
            <p className="guardrail-modal__value">{guardrail.reason}</p>
          </div>

          {guardrail.tool && (
            <div className="guardrail-modal__field">
              <span className="guardrail-modal__label">Tool</span>
              <span className="guardrail-modal__value">
                {guardrail.tool}
              </span>
            </div>
          )}

          {guardrail.args && Object.keys(guardrail.args).length > 0 && (
            <div className="guardrail-modal__field">
              <span className="guardrail-modal__label">Arguments</span>
              <pre className="guardrail-modal__code">
                {JSON.stringify(guardrail.args, null, 2)}
              </pre>
            </div>
          )}
        </div>

        <div className="guardrail-modal__actions">
          <button
            className="guardrail-modal__btn guardrail-modal__btn--reject"
            onClick={onReject}
            type="button"
          >
            Reject
          </button>
          <button
            className="guardrail-modal__btn guardrail-modal__btn--approve"
            onClick={onApprove}
            type="button"
          >
            Approve
          </button>
        </div>
      </div>
    </div>
  );
};

export default GuardrailModal;
