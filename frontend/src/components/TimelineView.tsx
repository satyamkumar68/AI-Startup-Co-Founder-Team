import React, { useRef, useEffect } from 'react';
import type { WebSocketEvent } from '../types';

interface Props {
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled' | 'needs_review';
  events: WebSocketEvent[];
  totalTokens: number;
  totalCostUsd: number;
}

interface StepItem {
  id: string;
  name: string;
  agentName: string;
  role: string;
}

const WORKFLOW_STEPS: StepItem[] = [
  { id: 'market', name: 'Market analyst', agentName: 'market_analyst', role: 'TAM, SAM, SOM and competitors' },
  { id: 'prd', name: 'Product manager', agentName: 'pm', role: 'Personas, scope, and prioritized PRD' },
  { id: 'arch', name: 'Tech architect', agentName: 'architect', role: 'Stack, diagram, and cost model' },
  { id: 'pitch', name: 'Pitch writer', agentName: 'pitch_writer', role: 'Investor presentation slides' },
  { id: 'ceo', name: 'CEO review', agentName: 'ceo_critic', role: 'Quality rubric and gate check' },
  { id: 'debate', name: 'Peer debate', agentName: 'debate', role: 'Critiques and rebuttals' }
];

export const TimelineView: React.FC<Props> = ({ status, events, totalTokens, totalCostUsd }) => {
  const consoleBottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    consoleBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  const getStepStatus = (step: StepItem): 'pending' | 'running' | 'completed' | 'failed' => {
    if (status === 'completed') return 'completed';
    if (status === 'failed') return 'failed';

    const hasCompletedEvent = events.some(
      (e) => (e.type === 'agent:completed' || e.type === 'agent_completed') && (e.agent === step.agentName || e.agent === step.id)
    );
    if (hasCompletedEvent) return 'completed';

    const isRunningEvent = events.some(
      (e) => (e.type === 'agent:started' || e.type === 'agent_started') && (e.agent === step.agentName || e.agent === step.id)
    );
    if (isRunningEvent) return 'running';

    return 'pending';
  };

  const statusLabel =
    status === 'completed'
      ? 'Completed'
      : status === 'running'
      ? 'In progress'
      : status === 'failed'
      ? 'Needs attention'
      : status === 'cancelled'
      ? 'Cancelled'
      : 'Queued';

  return (
    <div className="timeline-view-container" id="timeline-view-container">
      {/* Metrics Ticker Bar */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '14px',
        marginBottom: '24px'
      }}>
        <div className="metric-card">
          <div className="metric-label">Execution status</div>
          <div style={{ marginTop: '4px' }}>
            <span className={`badge ${
              status === 'completed'
                ? 'badge-success'
                : status === 'running'
                ? 'badge-primary'
                : status === 'failed'
                ? 'badge-danger'
                : 'badge-warning'
            }`} style={{ fontSize: '0.86rem' }}>
              {statusLabel}
            </span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Total tokens used</div>
          <div className="metric-value" style={{ color: 'var(--text-main)', fontSize: '1.4rem' }}>
            {totalTokens.toLocaleString()}
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Estimated AI cost</div>
          <div className="metric-value" style={{ color: 'var(--success)', fontSize: '1.4rem' }}>
            ${totalCostUsd.toFixed(4)}
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Activity updates</div>
          <div className="metric-value" style={{ color: 'var(--text-main)', fontSize: '1.4rem' }}>
            {events.length}
          </div>
        </div>
      </div>

      {/* Visual Workflow Stepper */}
      <div style={{
        background: 'var(--bg-subtle)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-md)',
        padding: '20px 24px',
        marginBottom: '28px'
      }}>
        <h4 style={{ fontFamily: 'var(--font-display)', fontSize: '1rem', fontWeight: 600, marginBottom: '16px', color: 'var(--text-main)' }}>
          Partner collaboration workflow
        </h4>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
          gap: '12px'
        }}>
          {WORKFLOW_STEPS.map((step, idx) => {
            const stepState = getStepStatus(step);
            const isCompleted = stepState === 'completed';
            const isRunning = stepState === 'running';

            return (
              <div
                key={step.id}
                style={{
                  background: isRunning
                    ? 'rgba(79, 70, 229, 0.1)'
                    : isCompleted
                    ? 'rgba(16, 185, 129, 0.06)'
                    : 'var(--bg-surface)',
                  border: isRunning
                    ? '1px solid var(--primary)'
                    : isCompleted
                    ? '1px solid rgba(16, 185, 129, 0.3)'
                    : '1px solid var(--border)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '14px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                  transition: 'border-color 0.15s ease'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.78rem', color: isRunning ? 'var(--primary)' : 'var(--text-muted)' }}>
                    Step {idx + 1}
                  </span>
                  <span>
                    {isCompleted && <span style={{ color: 'var(--success)', fontSize: '0.85rem' }}>Done</span>}
                    {isRunning && <span className="spinner" style={{ width: '10px', height: '10px' }} />}
                  </span>
                </div>

                <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-main)' }}>
                  {step.name}
                </div>
                <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                  {step.role}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Live Event Stream Console */}
      <div style={{
        background: 'var(--bg-subtle)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-md)',
        overflow: 'hidden'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '12px 18px',
          borderBottom: '1px solid var(--border)'
        }}>
          <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-main)' }}>
            Live activity stream
          </h4>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            {events.length} messages
          </span>
        </div>

        <div style={{
          maxHeight: '300px',
          overflowY: 'auto',
          padding: '16px 18px',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          fontSize: '0.84rem'
        }}>
          {events.length === 0 ? (
            <div style={{ color: 'var(--text-muted)', padding: '12px 0' }}>
              Waiting for analysis to begin. Start an idea to observe live execution.
            </div>
          ) : (
            events.map((ev, i) => {
              const isError = ev.type?.includes('error') || ev.error;
              const isScore = ev.type?.includes('score') || ev.score !== undefined;
              const isComplete = ev.type?.includes('completed');

              return (
                <div
                  key={i}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '10px',
                    color: isError ? 'var(--danger)' : isScore ? 'var(--warning)' : isComplete ? 'var(--success)' : 'var(--text-main)'
                  }}
                >
                  <span style={{ color: 'var(--text-muted)', minWidth: '36px', flexShrink: 0, fontSize: '0.78rem' }}>
                    {i + 1}.
                  </span>
                  <span style={{
                    background: 'var(--bg-surface)',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    fontSize: '0.74rem',
                    color: 'var(--text-muted)',
                    border: '1px solid var(--border)'
                  }}>
                    {ev.type?.replace(/_/g, ' ')}
                  </span>
                  <span style={{ flexGrow: 1, wordBreak: 'break-word' }}>
                    {ev.text || ev.error || (ev.score !== undefined ? `${ev.target || ev.agent} score: ${ev.score} (passed: ${ev.pass ? 'yes' : 'no'})` : JSON.stringify(ev.output || ev.content || ev))}
                  </span>
                </div>
              );
            })
          )}
          <div ref={consoleBottomRef} />
        </div>
      </div>
    </div>
  );
};
