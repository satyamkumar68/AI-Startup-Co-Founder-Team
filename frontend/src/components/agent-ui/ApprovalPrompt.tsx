import React, { useState } from 'react';

interface ApprovalPromptProps {
  stageName: string;
  agentName: string;
  avatar: string;
  summary: string;
  score?: number;
  onApprove: () => void;
  onRetryWithGuidance: (guidance: string) => void;
  onManualEdit?: () => void;
}

export const ApprovalPrompt: React.FC<ApprovalPromptProps> = ({
  stageName,
  agentName,
  avatar,
  summary,
  score,
  onApprove,
  onRetryWithGuidance,
  onManualEdit
}) => {
  const [showGuidanceInput, setShowGuidanceInput] = useState(false);
  const [guidanceText, setGuidanceText] = useState('');

  const handleSendGuidance = () => {
    if (!guidanceText.trim()) return;
    onRetryWithGuidance(guidanceText.trim());
    setGuidanceText('');
    setShowGuidanceInput(false);
  };

  return (
    <div className="approval-prompt-card" role="region" aria-label={`Approval prompt for ${stageName}`}>
      <div className="approval-header">
        <div className="approval-title">
          <span style={{ fontSize: '1.2rem' }} aria-hidden="true">{avatar}</span>
          <div>
            <span style={{ color: '#FCD34D', fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block' }}>
              Founder Review Gate · {stageName}
            </span>
            <span style={{ fontSize: '0.92rem', color: '#F8FAFC', fontWeight: 600 }}>
              {agentName} has delivered stage output
            </span>
          </div>
        </div>

        {score !== undefined && (
          <span
            style={{
              padding: '4px 10px',
              borderRadius: '6px',
              fontSize: '0.78rem',
              fontWeight: 700,
              background: score >= 7.0 ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)',
              color: score >= 7.0 ? '#34D399' : '#FCD34D',
              border: `1px solid ${score >= 7.0 ? 'rgba(16, 185, 129, 0.4)' : 'rgba(245, 158, 11, 0.4)'}`
            }}
          >
            CEO Score: {score.toFixed(1)}/10
          </span>
        )}
      </div>

      <p style={{ color: '#CBD5E1', fontSize: '0.84rem', margin: '8px 0 12px 0', lineHeight: 1.5 }}>
        {summary}
      </p>

      {showGuidanceInput ? (
        <div style={{ marginTop: '12px', background: 'rgba(0,0,0,0.25)', padding: '12px', borderRadius: '8px' }}>
          <label style={{ fontSize: '0.78rem', color: '#94A3B8', display: 'block', marginBottom: '6px' }}>
            Enter steering feedback for {agentName}:
          </label>
          <textarea
            value={guidanceText}
            onChange={(e) => setGuidanceText(e.target.value)}
            placeholder="e.g. Focus specifically on tier-2 cities and emphasize low-bandwidth offline sync..."
            rows={3}
            style={{
              width: '100%',
              background: '#0F172A',
              border: '1px solid #475569',
              borderRadius: '6px',
              color: '#F8FAFC',
              padding: '8px',
              fontSize: '0.82rem',
              resize: 'vertical',
              boxSizing: 'border-box'
            }}
          />
          <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
            <button
              onClick={handleSendGuidance}
              style={{
                background: '#4F46E5',
                color: '#FFF',
                border: 'none',
                borderRadius: '6px',
                padding: '6px 14px',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              Submit & Retry Stage
            </button>
            <button
              onClick={() => setShowGuidanceInput(false)}
              style={{
                background: 'transparent',
                color: '#94A3B8',
                border: '1px solid #475569',
                borderRadius: '6px',
                padding: '6px 12px',
                fontSize: '0.8rem',
                cursor: 'pointer'
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="approval-actions">
          <button
            onClick={onApprove}
            style={{
              background: '#10B981',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: '6px',
              padding: '7px 16px',
              fontSize: '0.82rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              boxShadow: '0 2px 6px rgba(16, 185, 129, 0.3)'
            }}
          >
            <span>✓</span> Approve & Proceed
          </button>

          <button
            onClick={() => setShowGuidanceInput(true)}
            style={{
              background: 'rgba(245, 158, 11, 0.15)',
              color: '#FCD34D',
              border: '1px solid rgba(245, 158, 11, 0.4)',
              borderRadius: '6px',
              padding: '7px 14px',
              fontSize: '0.82rem',
              fontWeight: 500,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <span>✏️</span> Add Guidance & Retry
          </button>

          {onManualEdit && (
            <button
              onClick={onManualEdit}
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                color: '#CBD5E1',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                borderRadius: '6px',
                padding: '7px 14px',
                fontSize: '0.82rem',
                cursor: 'pointer'
              }}
            >
              Edit in Studio
            </button>
          )}
        </div>
      )}
    </div>
  );
};
