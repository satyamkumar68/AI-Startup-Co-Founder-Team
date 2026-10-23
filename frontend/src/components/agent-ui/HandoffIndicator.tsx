import React from 'react';

interface AgentSummary {
  name: string;
  avatar: string;
  accent?: string;
}

interface HandoffIndicatorProps {
  fromAgent: AgentSummary;
  toAgent: AgentSummary;
  contextChips?: string[];
  isActive?: boolean;
}

export const HandoffIndicator: React.FC<HandoffIndicatorProps> = ({
  fromAgent,
  toAgent,
  contextChips = [],
  isActive = false
}) => {
  return (
    <div
      className="handoff-container"
      style={{
        borderColor: isActive ? 'rgba(129, 140, 248, 0.45)' : 'rgba(255, 255, 255, 0.12)',
        background: isActive ? 'rgba(49, 46, 129, 0.18)' : 'rgba(30, 41, 59, 0.35)'
      }}
    >
      <div className="handoff-flow">
        <span aria-hidden="true">{fromAgent.avatar}</span>
        <span>{fromAgent.name}</span>
        <span className="handoff-arrow" aria-hidden="true">
          {isActive ? '⚡➔' : '➔'}
        </span>
        <span aria-hidden="true">{toAgent.avatar}</span>
        <span>{toAgent.name}</span>
      </div>

      {contextChips.length > 0 && (
        <div className="handoff-chips">
          {contextChips.map((chip, idx) => (
            <span key={idx} className="context-chip">
              {chip}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};
