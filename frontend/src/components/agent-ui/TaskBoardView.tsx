import React from 'react';
import type { RunDetail } from '../../types';

interface TaskBoardViewProps {
  runData: RunDetail | null;
  currentAgent: string | null;
  onNavigateToTab: (tab: 'market' | 'prd' | 'arch' | 'pitch' | 'debate') => void;
}

interface TaskItem {
  id: string;
  title: string;
  agentName: string;
  avatar: string;
  column: 'intake' | 'progress' | 'review' | 'debate' | 'done';
  tabTarget?: 'market' | 'prd' | 'arch' | 'pitch' | 'debate';
  summary?: string;
  score?: number;
}

export const TaskBoardView: React.FC<TaskBoardViewProps> = ({
  runData,
  currentAgent,
  onNavigateToTab
}) => {
  if (!runData) {
    return (
      <div style={{ padding: '32px', textAlign: 'center', color: '#94A3B8' }}>
        <p>No active run loaded. Enter an idea below and click Start Pipeline to see tasks populate the board.</p>
      </div>
    );
  }

  const scores = runData.scores || {};
  const marketScore = scores.market?.slice(-1)[0];
  const prdScore = scores.prd?.slice(-1)[0];
  const archScore = scores.architecture?.slice(-1)[0];
  const pitchScore = scores.pitch?.slice(-1)[0];

  const tasks: TaskItem[] = [
    {
      id: 'task-intake',
      title: 'Founder Venture Thesis',
      agentName: 'Founder',
      avatar: '💡',
      column: 'done',
      summary: runData.idea
    },
    {
      id: 'task-market',
      title: 'TAM/SAM/SOM & Competitor Intel',
      agentName: 'Market Analyst',
      avatar: '🔍',
      column: runData.market ? (marketScore !== undefined ? 'done' : 'review') : currentAgent?.includes('market') ? 'progress' : 'intake',
      tabTarget: 'market',
      score: marketScore,
      summary: runData.market ? `TAM: ${runData.market.tam} · ${runData.market.competitors?.length || 0} competitors profiled` : undefined
    },
    {
      id: 'task-prd',
      title: 'Product Scope & MVP Boundaries',
      agentName: 'Product Manager',
      avatar: '📋',
      column: runData.prd ? (prdScore !== undefined ? 'done' : 'review') : currentAgent?.includes('prd') ? 'progress' : 'intake',
      tabTarget: 'prd',
      score: prdScore,
      summary: runData.prd ? `${runData.prd.features?.length || 0} features prioritized · ${runData.prd.personas?.length || 0} target personas` : undefined
    },
    {
      id: 'task-arch',
      title: 'System Architecture & Cloud Budget',
      agentName: 'Tech Architect',
      avatar: '🏛️',
      column: runData.architecture ? (archScore !== undefined ? 'done' : 'review') : currentAgent?.includes('arch') ? 'progress' : 'intake',
      tabTarget: 'arch',
      score: archScore,
      summary: runData.architecture ? `Est. $${runData.architecture.monthly_cost_estimate?.total_usd || 65}/mo · Mermaid diagram validated` : undefined
    },
    {
      id: 'task-debate',
      title: 'Peer Critique & Rebuttal Protocol',
      agentName: 'Debate Engine',
      avatar: '⚔️',
      column: runData.debate_messages && runData.debate_messages.length > 0 ? 'done' : currentAgent?.includes('debate') ? 'debate' : 'intake',
      tabTarget: 'debate',
      summary: runData.debate_messages ? `${runData.debate_messages.length} debate exchanges recorded` : undefined
    },
    {
      id: 'task-pitch',
      title: 'Investor Deck & Talking Points',
      agentName: 'Pitch Writer',
      avatar: '🎯',
      column: runData.pitch ? (pitchScore !== undefined ? 'done' : 'review') : currentAgent?.includes('pitch') ? 'progress' : 'intake',
      tabTarget: 'pitch',
      score: pitchScore,
      summary: runData.pitch ? `${runData.pitch.slides?.length || 0} slides crafted with speaker notes` : undefined
    }
  ];

  const columns = [
    { id: 'intake', title: 'Pending Queue', icon: '📥' },
    { id: 'progress', title: 'In Execution', icon: '⚡' },
    { id: 'review', title: 'CEO Quality Gate', icon: '⚖️' },
    { id: 'done', title: 'Verified Deliverable', icon: '✓' }
  ];

  return (
    <div className="taskboard-container" role="region" aria-label="Kanban Task Board">
      {columns.map((col) => {
        const colTasks = tasks.filter((t) => t.column === col.id);

        return (
          <div key={col.id} className="taskboard-column">
            <div className="column-header">
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span>{col.icon}</span>
                <span>{col.title}</span>
              </span>
              <span
                style={{
                  background: 'rgba(255,255,255,0.08)',
                  padding: '2px 7px',
                  borderRadius: '10px',
                  fontSize: '0.72rem'
                }}
              >
                {colTasks.length}
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', minHeight: '120px' }}>
              {colTasks.length === 0 ? (
                <div style={{ color: 'var(--text-subtle)', fontSize: '0.76rem', fontStyle: 'italic', padding: '12px 0' }}>
                  No tasks in this lane
                </div>
              ) : (
                colTasks.map((task) => (
                  <div
                    key={task.id}
                    className="taskboard-card"
                    onClick={() => task.tabTarget && onNavigateToTab(task.tabTarget)}
                    style={{ cursor: task.tabTarget ? 'pointer' : 'default' }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <span style={{ fontSize: '1.1rem' }} aria-hidden="true">{task.avatar}</span>
                      {task.score !== undefined && (
                        <span
                          style={{
                            fontSize: '0.72rem',
                            fontWeight: 700,
                            padding: '2px 6px',
                            borderRadius: '4px',
                            background: task.score >= 7.0 ? 'rgba(16, 185, 129, 0.18)' : 'rgba(245, 158, 11, 0.18)',
                            color: task.score >= 7.0 ? 'var(--success, #10B981)' : 'var(--warning, #F59E0B)'
                          }}
                        >
                          {task.score.toFixed(1)}/10
                        </span>
                      )}
                    </div>

                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-main)' }}>
                        {task.title}
                      </div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        {task.agentName}
                      </div>
                    </div>

                    {task.summary && (
                      <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
                        {task.summary}
                      </div>
                    )}

                    {task.tabTarget && (
                      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '4px' }}>
                        <span style={{ fontSize: '0.72rem', color: 'var(--primary)', fontWeight: 500 }}>
                          Inspect Deliverable ➔
                        </span>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
