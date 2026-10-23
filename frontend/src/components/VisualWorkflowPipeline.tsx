import React from 'react';
import type { RunDetail } from '../types';

interface VisualWorkflowPipelineProps {
  runData: RunDetail | null;
  currentAgent: string | null;
  onNavigateToTab: (tab: 'market' | 'prd' | 'arch' | 'pitch' | 'debate') => void;
}

interface WorkflowStep {
  id: string;
  label: string;
  icon: string;
  tabTarget?: 'market' | 'prd' | 'arch' | 'pitch' | 'debate';
}

const STEPS: WorkflowStep[] = [
  { id: 'intake', label: 'Idea Intake', icon: '💡' },
  { id: 'market', label: 'Market Analyst', icon: '🔍', tabTarget: 'market' },
  { id: 'ceo_market', label: 'CEO Gate 1', icon: '⚖️', tabTarget: 'market' },
  { id: 'prd', label: 'Product Manager', icon: '📋', tabTarget: 'prd' },
  { id: 'ceo_prd', label: 'CEO Gate 2', icon: '⚖️', tabTarget: 'prd' },
  { id: 'arch', label: 'Tech Architect', icon: '🏛️', tabTarget: 'arch' },
  { id: 'ceo_arch', label: 'CEO Gate 3', icon: '⚖️', tabTarget: 'arch' },
  { id: 'debate', label: 'Peer Debate', icon: '⚔️', tabTarget: 'debate' },
  { id: 'pitch', label: 'Pitch Deck', icon: '🎯', tabTarget: 'pitch' },
  { id: 'ceo_pitch', label: 'Final Review', icon: '🏆', tabTarget: 'pitch' }
];

export const VisualWorkflowPipeline: React.FC<VisualWorkflowPipelineProps> = ({
  runData,
  currentAgent,
  onNavigateToTab
}) => {
  const getStepStatus = (stepId: string): 'completed' | 'active' | 'pending' | 'rejected' => {
    if (!runData) return 'pending';

    const status = runData.status;

    // Intake step
    if (stepId === 'intake') {
      return status !== 'queued' ? 'completed' : 'active';
    }

    // Market step
    if (stepId === 'market') {
      if (runData.market) return 'completed';
      if (currentAgent === 'market_analyst' || currentAgent === 'market') return 'active';
      return 'pending';
    }

    // CEO Market gate
    if (stepId === 'ceo_market') {
      const s = runData.scores?.market?.slice(-1)[0];
      if (s !== undefined) return s >= 7.0 ? 'completed' : 'rejected';
      if (currentAgent === 'review_market') return 'active';
      return runData.market ? 'active' : 'pending';
    }

    // PRD step
    if (stepId === 'prd') {
      if (runData.prd) return 'completed';
      if (currentAgent === 'product_manager' || currentAgent === 'pm') return 'active';
      return 'pending';
    }

    // CEO PRD gate
    if (stepId === 'ceo_prd') {
      const s = runData.scores?.prd?.slice(-1)[0];
      if (s !== undefined) return s >= 7.0 ? 'completed' : 'rejected';
      if (currentAgent === 'review_pm') return 'active';
      return runData.prd ? 'active' : 'pending';
    }

    // Architecture step
    if (stepId === 'arch') {
      if (runData.architecture) return 'completed';
      if (currentAgent === 'tech_architect' || currentAgent === 'architect') return 'active';
      return 'pending';
    }

    // CEO Arch gate
    if (stepId === 'ceo_arch') {
      const s = runData.scores?.architecture?.slice(-1)[0];
      if (s !== undefined) return s >= 7.0 ? 'completed' : 'rejected';
      if (currentAgent === 'review_architect') return 'active';
      return runData.architecture ? 'active' : 'pending';
    }

    // Debate step
    if (stepId === 'debate') {
      if (runData.debate_messages && runData.debate_messages.length > 0) return 'completed';
      if (currentAgent === 'debate_round' || currentAgent === 'debate') return 'active';
      if (runData.architecture && !runData.pitch) return 'active';
      return runData.pitch ? 'completed' : 'pending';
    }

    // Pitch step
    if (stepId === 'pitch') {
      if (runData.pitch) return 'completed';
      if (currentAgent === 'pitch_writer' || currentAgent === 'pitch') return 'active';
      return 'pending';
    }

    // CEO Final pitch gate
    if (stepId === 'ceo_pitch') {
      const s = runData.scores?.pitch?.slice(-1)[0];
      if (s !== undefined) return s >= 7.0 ? 'completed' : 'rejected';
      if (currentAgent === 'review_pitch') return 'active';
      return runData.pitch ? 'active' : 'pending';
    }

    return 'pending';
  };

  return (
    <div className="visual-workflow-container">
      <div className="workflow-title-row">
        <div className="workflow-title-left">
          <span className="workflow-icon">⚡</span>
          <span className="workflow-title">Autonomous Co-Founder Pipeline Flow</span>
          <span className="workflow-sub">LangGraph Orchestration & Quality Gates</span>
        </div>
        <div className="workflow-legend">
          <span className="legend-item"><span className="dot completed" /> Completed</span>
          <span className="legend-item"><span className="dot active" /> In Progress</span>
          <span className="legend-item"><span className="dot pending" /> Pending</span>
        </div>
      </div>

      <div className="workflow-steps-track">
        {STEPS.map((step, idx) => {
          const status = getStepStatus(step.id);
          const isClickable = Boolean(step.tabTarget);

          return (
            <React.Fragment key={step.id}>
              <div
                className={`pipeline-node ${status} ${isClickable ? 'clickable' : ''}`}
                onClick={() => {
                  if (step.tabTarget) {
                    onNavigateToTab(step.tabTarget);
                  }
                }}
                title={isClickable ? `Jump to ${step.label} Output` : step.label}
              >
                <div className="node-icon-bubble">
                  {status === 'completed' ? (
                    <span className="check-icon">✓</span>
                  ) : status === 'active' ? (
                    <span className="spinner-icon">◌</span>
                  ) : (
                    <span>{step.icon}</span>
                  )}
                </div>
                <div className="node-label-col">
                  <span className="node-step-num">0{idx + 1}</span>
                  <span className="node-label-text">{step.label}</span>
                </div>
              </div>

              {idx < STEPS.length - 1 && (
                <div className={`pipeline-connector ${status === 'completed' ? 'completed' : ''}`}>
                  <div className="connector-arrow">›</div>
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
