import React from 'react';

export type AgentState =
  | 'idle'
  | 'thinking'
  | 'working'
  | 'waiting-for-user'
  | 'blocked'
  | 'done'
  | 'failed';

interface StatusBadgeProps {
  state: AgentState;
  label?: string;
  elapsedSeconds?: number;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  state,
  label,
  elapsedSeconds
}) => {
  const getBadgeDetails = (): { defaultLabel: string; icon: string; ariaText: string } => {
    switch (state) {
      case 'idle':
        return { defaultLabel: 'Idle', icon: '●', ariaText: 'Agent is idle' };
      case 'thinking':
        return { defaultLabel: 'Thinking…', icon: '⏳', ariaText: 'Agent is reasoning' };
      case 'working':
        return { defaultLabel: 'Working', icon: '⚡', ariaText: 'Agent is executing task' };
      case 'waiting-for-user':
        return { defaultLabel: 'Needs Approval', icon: '👤', ariaText: 'Agent waiting for founder decision' };
      case 'blocked':
        return { defaultLabel: 'Blocked', icon: '⛔', ariaText: 'Agent blocked by dependencies' };
      case 'done':
        return { defaultLabel: 'Complete', icon: '✓', ariaText: 'Agent deliverable completed' };
      case 'failed':
        return { defaultLabel: 'Failed', icon: '⚠️', ariaText: 'Agent execution encountered an error' };
      default:
        return { defaultLabel: 'Unknown', icon: '●', ariaText: 'Agent status unknown' };
    }
  };

  const { defaultLabel, icon, ariaText } = getBadgeDetails();
  const displayLabel = label || defaultLabel;

  return (
    <span
      className={`status-badge status-${state}`}
      role="status"
      aria-label={ariaText}
    >
      <span className={`badge-icon ${state === 'working' ? 'spin-icon' : ''}`} aria-hidden="true">
        {icon}
      </span>
      <span>{displayLabel}</span>
      {elapsedSeconds !== undefined && elapsedSeconds >= 3 && (
        <span style={{ opacity: 0.75, fontSize: '0.68rem', marginLeft: '2px' }}>
          ({elapsedSeconds}s)
        </span>
      )}
    </span>
  );
};
