import React from 'react';
import type { RunDetail } from '../../types';

interface AgentGraphViewProps {
  runData: RunDetail | null;
  currentAgent: string | null;
  onSelectAgent: (tab: 'market' | 'prd' | 'arch' | 'pitch' | 'debate') => void;
}

interface GraphNode {
  id: string;
  name: string;
  role: string;
  avatar: string;
  x: number;
  y: number;
  accent: string;
  tabTarget?: 'market' | 'prd' | 'arch' | 'pitch' | 'debate';
}

const NODES: GraphNode[] = [
  { id: 'founder', name: 'Founder', role: 'Idea Intake', avatar: '💡', x: 80, y: 180, accent: '#6366F1' },
  { id: 'market', name: 'Market Analyst', role: 'TAM/SAM/SOM & Intel', avatar: '🔍', x: 280, y: 80, accent: '#38BDF8', tabTarget: 'market' },
  { id: 'prd', name: 'Product Manager', role: 'PRD & MVP Scope', avatar: '📋', x: 480, y: 80, accent: '#34D399', tabTarget: 'prd' },
  { id: 'arch', name: 'Tech Architect', role: 'Architecture & Stack', avatar: '🏛️', x: 680, y: 80, accent: '#A855F7', tabTarget: 'arch' },
  { id: 'debate', name: 'Peer Debate', role: 'Critique & Rebuttal', avatar: '⚔️', x: 480, y: 220, accent: '#818CF8', tabTarget: 'debate' },
  { id: 'pitch', name: 'Pitch Writer', role: '10-12 Slide Deck', avatar: '🎯', x: 680, y: 320, accent: '#FBBF24', tabTarget: 'pitch' },
  { id: 'ceo', name: 'CEO / Critic', role: 'Score ≥ 7.0 Gate', avatar: '⚖️', x: 380, y: 320, accent: '#F43F5E' }
];

const EDGES = [
  { from: 'founder', to: 'market' },
  { from: 'market', to: 'prd' },
  { from: 'prd', to: 'arch' },
  { from: 'arch', to: 'debate' },
  { from: 'debate', to: 'pitch' },
  { from: 'pitch', to: 'ceo' },
  { from: 'ceo', to: 'founder' }
];

export const AgentGraphView: React.FC<AgentGraphViewProps> = ({
  runData,
  currentAgent,
  onSelectAgent
}) => {
  const getNodeStatus = (nodeId: string): 'completed' | 'active' | 'pending' => {
    if (!runData) return 'pending';
    if (nodeId === 'founder') return 'completed';
    if (nodeId === 'market') {
      if (runData.market) return 'completed';
      if (currentAgent?.includes('market')) return 'active';
      return 'pending';
    }
    if (nodeId === 'prd') {
      if (runData.prd) return 'completed';
      if (currentAgent?.includes('prd') || currentAgent?.includes('product')) return 'active';
      return 'pending';
    }
    if (nodeId === 'arch') {
      if (runData.architecture) return 'completed';
      if (currentAgent?.includes('arch') || currentAgent?.includes('tech')) return 'active';
      return 'pending';
    }
    if (nodeId === 'debate') {
      if (runData.debate_messages && runData.debate_messages.length > 0) return 'completed';
      if (currentAgent?.includes('debate')) return 'active';
      return 'pending';
    }
    if (nodeId === 'pitch') {
      if (runData.pitch) return 'completed';
      if (currentAgent?.includes('pitch')) return 'active';
      return 'pending';
    }
    if (nodeId === 'ceo') {
      const avgScore = runData.scores?.final_verdict?.slice(-1)[0];
      if (avgScore !== undefined) return 'completed';
      if (currentAgent?.includes('ceo') || currentAgent?.includes('review')) return 'active';
      return 'pending';
    }
    return 'pending';
  };

  return (
    <div className="agent-graph-canvas" role="region" aria-label="Interactive Multi-Agent Collaboration Graph">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '1rem', color: '#F8FAFC', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>🕸️</span> Multi-Agent Orchestration Topology
          </h3>
          <p style={{ margin: '4px 0 0 0', fontSize: '0.78rem', color: '#94A3B8' }}>
            Real-time handoff network connecting your 5 AI co-founders and CEO gatekeeper.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px', fontSize: '0.72rem', color: '#94A3B8' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10B981' }} />
            Completed
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#38BDF8' }} />
            Active Handoff
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#475569' }} />
            Pending
          </span>
        </div>
      </div>

      <div style={{ width: '100%', overflowX: 'auto', display: 'flex', justifyContent: 'center' }}>
        <svg viewBox="0 0 820 400" style={{ width: '100%', maxWidth: '820px', height: 'auto', minHeight: '380px' }}>
          {/* Defs for gradients and glow filters */}
          <defs>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
            <marker id="arrow" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="var(--text-subtle, #64748B)" />
            </marker>
            <marker id="arrow-active" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="var(--primary, #38BDF8)" />
            </marker>
          </defs>

          {/* Edges */}
          {EDGES.map((edge, idx) => {
            const source = NODES.find((n) => n.id === edge.from)!;
            const target = NODES.find((n) => n.id === edge.to)!;
            const sourceStatus = getNodeStatus(source.id);
            const targetStatus = getNodeStatus(target.id);
            const isEdgeActive = (sourceStatus === 'completed' && targetStatus === 'active') || targetStatus === 'active';

            return (
              <g key={`edge-${idx}`}>
                <line
                  x1={source.x}
                  y1={source.y}
                  x2={target.x}
                  y2={target.y}
                  stroke={isEdgeActive ? 'var(--primary, #38BDF8)' : 'var(--border, #334155)'}
                  strokeWidth={isEdgeActive ? 2.5 : 1.5}
                  strokeDasharray={isEdgeActive ? '5,5' : undefined}
                  markerEnd={isEdgeActive ? 'url(#arrow-active)' : 'url(#arrow)'}
                />
              </g>
            );
          })}

          {/* Nodes */}
          {NODES.map((node) => {
            const status = getNodeStatus(node.id);
            const isActive = status === 'active';
            const isCompleted = status === 'completed';

            return (
              <g
                key={node.id}
                transform={`translate(${node.x}, ${node.y})`}
                onClick={() => node.tabTarget && onSelectAgent(node.tabTarget)}
                style={{ cursor: node.tabTarget ? 'pointer' : 'default' }}
              >
                {/* Node outer glow if active */}
                {isActive && (
                  <circle
                    r="34"
                    fill="none"
                    stroke={node.accent}
                    strokeWidth="2"
                    opacity="0.6"
                    filter="url(#glow)"
                  >
                    <animate attributeName="r" values="30;38;30" dur="2s" repeatCount="indefinite" />
                    <animate attributeName="opacity" values="0.8;0.2;0.8" dur="2s" repeatCount="indefinite" />
                  </circle>
                )}

                {/* Node background circle */}
                <circle
                  r="26"
                  fill="var(--bg-surface, #1E293B)"
                  stroke={isActive ? node.accent : isCompleted ? 'var(--success, #10B981)' : 'var(--border, #334155)'}
                  strokeWidth={isActive ? '2.5' : '1.5'}
                />

                {/* Node icon */}
                <text
                  textAnchor="middle"
                  dy="6"
                  fontSize="18"
                  style={{ userSelect: 'none' }}
                >
                  {node.avatar}
                </text>

                {/* Node label */}
                <text
                  y="40"
                  textAnchor="middle"
                  fill="var(--text-main, #F8FAFC)"
                  fontSize="11"
                  fontWeight="600"
                  style={{ userSelect: 'none' }}
                >
                  {node.name}
                </text>

                {/* Node role */}
                <text
                  y="53"
                  textAnchor="middle"
                  fill="var(--text-muted, #94A3B8)"
                  fontSize="9"
                  style={{ userSelect: 'none' }}
                >
                  {node.role}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
};
