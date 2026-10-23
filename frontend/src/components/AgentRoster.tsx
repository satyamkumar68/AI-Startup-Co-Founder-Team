import React from 'react';
import type { RunDetail } from '../types';

interface AgentRosterProps {
  runData: RunDetail | null;
  currentAgent: string | null;
  activeTab: string;
  onSelectAgent: (tab: 'market' | 'prd' | 'arch' | 'pitch' | 'debate') => void;
  defaultModel: string;
}

interface AgentItem {
  id: 'market' | 'prd' | 'arch' | 'pitch' | 'debate' | 'ceo';
  name: string;
  role: string;
  avatar: string;
  accent: string;
  description: string;
}

const AGENTS: AgentItem[] = [
  {
    id: 'market',
    name: 'Market Analyst',
    role: 'Market Sizing & Competitor Intel',
    avatar: '🔍',
    accent: '#38bdf8', // sky blue
    description: 'Calculates TAM/SAM/SOM with source URLs and profiles ≥5 competitors.'
  },
  {
    id: 'prd',
    name: 'Product Manager',
    role: 'PRD & MVP Scope Boundary',
    avatar: '📋',
    accent: '#34d399', // emerald green
    description: 'Defines target personas, problem statement, and max 8 P0 features.'
  },
  {
    id: 'arch',
    name: 'Tech Architect',
    role: 'System Architecture & Cloud Costs',
    avatar: '🏛️',
    accent: '#a855f7', // purple
    description: 'Designs stack with 1-line justifications, Mermaid diagram & monthly cost.'
  },
  {
    id: 'pitch',
    name: 'Pitch Writer',
    role: 'Investor Pitch Deck & Script',
    avatar: '🎯',
    accent: '#fbbf24', // amber
    description: 'Crafts 10-12 slide investor deck with slide body bullets and speaker notes.'
  },
  {
    id: 'ceo',
    name: 'CEO / Critic',
    role: 'Executive Quality Gatekeeper',
    avatar: '⚖️',
    accent: '#f43f5e', // rose
    description: 'Scores deliverables against 5 rubric criteria; enforces score ≥ 7.0 threshold.'
  },
  {
    id: 'debate',
    name: 'Debate Engine',
    role: 'Peer Critique & Rebuttal Protocol',
    avatar: '⚔️',
    accent: '#818cf8', // indigo
    description: 'Orchestrates peer challenges (Analyst ↔ PM ↔ Architect) resolved by CEO.'
  }
];

export const AgentRoster: React.FC<AgentRosterProps> = ({
  runData,
  currentAgent,
  activeTab,
  onSelectAgent,
  defaultModel
}) => {
  const getAgentStatus = (agentId: string) => {
    if (!runData) return { label: 'Idle', state: 'idle' };

    // Check if currently executing
    if (runData.status === 'running') {
      if (
        (agentId === 'market' && (currentAgent === 'market_analyst' || currentAgent === 'market')) ||
        (agentId === 'prd' && (currentAgent === 'product_manager' || currentAgent === 'pm')) ||
        (agentId === 'arch' && (currentAgent === 'tech_architect' || currentAgent === 'architect')) ||
        (agentId === 'pitch' && (currentAgent === 'pitch_writer' || currentAgent === 'pitch')) ||
        (agentId === 'ceo' && currentAgent?.includes('review')) ||
        (agentId === 'debate' && currentAgent?.includes('debate'))
      ) {
        return { label: 'Thinking...', state: 'running' };
      }
    }

    // Check completed deliverables & scores
    if (agentId === 'market' && runData.market) {
      const s = runData.scores?.market?.slice(-1)[0];
      return { label: s ? `Passed (${s})` : 'Completed', state: 'completed', score: s };
    }
    if (agentId === 'prd' && runData.prd) {
      const s = runData.scores?.prd?.slice(-1)[0];
      return { label: s ? `Passed (${s})` : 'Completed', state: 'completed', score: s };
    }
    if (agentId === 'arch' && runData.architecture) {
      const s = runData.scores?.architecture?.slice(-1)[0];
      return { label: s ? `Passed (${s})` : 'Completed', state: 'completed', score: s };
    }
    if (agentId === 'pitch' && runData.pitch) {
      const s = runData.scores?.pitch?.slice(-1)[0];
      return { label: s ? `Passed (${s})` : 'Completed', state: 'completed', score: s };
    }
    if (agentId === 'debate') {
      const rounds = runData.debate_messages?.length || 0;
      if (rounds > 0) {
        return { label: `Resolved (${rounds} msgs)`, state: 'completed' };
      }
    }
    if (agentId === 'ceo') {
      const hasScores = Object.values(runData.scores || {}).some((arr) => arr && arr.length > 0);
      if (hasScores) {
        return { label: 'Active Evaluator', state: 'completed' };
      }
    }

    return { label: 'Pending', state: 'pending' };
  };

  return (
    <aside className="agent-roster-sidebar">
      <div className="roster-header">
        <div className="roster-header-title">
          <span className="roster-icon">💼</span>
          <span className="roster-title">Co-Founder Roster</span>
        </div>
        <span className="roster-count">5 Agents + Debate</span>
      </div>

      <div className="roster-list">
        {AGENTS.map((agent) => {
          const status = getAgentStatus(agent.id);
          const isSelected =
            (agent.id === 'market' && activeTab === 'market') ||
            (agent.id === 'prd' && activeTab === 'prd') ||
            (agent.id === 'arch' && activeTab === 'arch') ||
            (agent.id === 'pitch' && activeTab === 'pitch') ||
            (agent.id === 'debate' && activeTab === 'debate');

          return (
            <div
              key={agent.id}
              className={`roster-agent-card ${status.state} ${isSelected ? 'selected' : ''}`}
              onClick={() => {
                if (agent.id !== 'ceo') {
                  onSelectAgent(agent.id as any);
                }
              }}
              style={{ '--agent-accent': agent.accent } as React.CSSProperties}
            >
              <div className="card-top-row">
                <div className="agent-avatar-badge" style={{ backgroundColor: `${agent.accent}20`, borderColor: agent.accent }}>
                  <span>{agent.avatar}</span>
                </div>
                <div className="agent-title-col">
                  <div className="agent-name">{agent.name}</div>
                  <div className="agent-role">{agent.role}</div>
                </div>
                <span className={`status-pill ${status.state}`}>
                  {status.state === 'running' && <span className="status-spinner" />}
                  {status.label}
                </span>
              </div>

              <div className="agent-desc">{agent.description}</div>

              <div className="card-footer-meta">
                <span className="model-tag">
                  {defaultModel.replace('ollama:', '').replace('openrouter/', '')}
                </span>
                {status.score && (
                  <span className={`mini-score ${status.score >= 7.0 ? 'pass' : 'fail'}`}>
                    Score: {status.score}/10
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </aside>
  );
};
