import React from 'react';
import { StatusBadge, type AgentState } from './StatusBadge';

export interface AgentCardProps {
  id: string;
  name: string;
  role: string;
  roleLine?: string;
  avatar: string;
  accent: string;
  state: AgentState;
  currentAction?: string;
  elapsedSeconds?: number;
  isSelected?: boolean;
  score?: number;
  onSelect?: () => void;
}

export const AgentCard: React.FC<AgentCardProps> = ({
  name,
  role,
  roleLine,
  avatar,
  accent,
  state,
  currentAction,
  elapsedSeconds,
  isSelected,
  score,
  onSelect
}) => {
  return (
    <div
      onClick={onSelect}
      style={{
        background: isSelected ? 'rgba(55, 48, 163, 0.25)' : 'rgba(15, 23, 42, 0.65)',
        border: `1px solid ${isSelected ? accent : 'rgba(255, 255, 255, 0.08)'}`,
        borderLeft: `4px solid ${accent}`,
        borderRadius: '10px',
        padding: '12px 14px',
        marginBottom: '10px',
        cursor: onSelect ? 'pointer' : 'default',
        transition: 'all 0.2s ease',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px'
      }}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          onSelect?.();
        }
      }}
      aria-pressed={isSelected}
    >
      {/* Top row: Avatar + Name + Status */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '1.25rem', lineHeight: 1 }} aria-hidden="true">
            {avatar}
          </span>
          <div>
            <div style={{ fontWeight: 600, fontSize: '0.88rem', color: '#F8FAFC' }}>
              {name}
            </div>
            <div style={{ fontSize: '0.72rem', color: '#94A3B8' }}>
              {roleLine || role}
            </div>
          </div>
        </div>

        <StatusBadge state={state} elapsedSeconds={elapsedSeconds} />
      </div>

      {/* Middle row: Live Action or Score Callout */}
      {currentAction && state === 'working' && (
        <div
          style={{
            fontSize: '0.74rem',
            color: '#38BDF8',
            background: 'rgba(56, 189, 248, 0.08)',
            padding: '4px 8px',
            borderRadius: '6px',
            border: '1px solid rgba(56, 189, 248, 0.2)'
          }}
        >
          {currentAction}
        </div>
      )}

      {score !== undefined && state === 'done' && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '0.72rem',
            color: '#94A3B8',
            borderTop: '1px solid rgba(255, 255, 255, 0.05)',
            paddingTop: '6px'
          }}
        >
          <span>CEO Quality Score:</span>
          <span
            style={{
              fontWeight: 700,
              color: score >= 7.0 ? '#34D399' : '#F59E0B'
            }}
          >
            {score.toFixed(1)} / 10
          </span>
        </div>
      )}
    </div>
  );
};
