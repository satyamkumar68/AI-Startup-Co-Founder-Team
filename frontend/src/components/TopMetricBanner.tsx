import React from 'react';
import type { RunDetail } from '../types';

interface TopMetricBannerProps {
  runData: RunDetail | null;
  serverConnected: boolean | null;
  isLaunching: boolean;
  onNewIdeaClick: () => void;
  onHistoryClick: () => void;
  onExport: (format: 'pdf' | 'pptx' | 'md' | 'csv') => void;
  themeSelectorNode?: React.ReactNode;
}

export const TopMetricBanner: React.FC<TopMetricBannerProps> = ({
  runData,
  serverConnected,
  isLaunching,
  onNewIdeaClick,
  onHistoryClick,
  onExport,
  themeSelectorNode
}) => {
  // Calculate average CEO score from all latest scores
  let avgCeoScore: number | null = null;
  let ceoPassed = true;
  if (runData && runData.scores) {
    const scores: number[] = [];
    Object.values(runData.scores).forEach((arr) => {
      if (arr && arr.length > 0) {
        scores.push(arr[arr.length - 1]);
      }
    });
    if (scores.length > 0) {
      const sum = scores.reduce((acc, curr) => acc + curr, 0);
      avgCeoScore = Number((sum / scores.length).toFixed(1));
      ceoPassed = avgCeoScore >= 7.0;
    }
  }

  // Count active/completed agents
  const agentsDone = [
    runData?.market ? 1 : 0,
    runData?.prd ? 1 : 0,
    runData?.architecture ? 1 : 0,
    runData?.pitch ? 1 : 0
  ].reduce((a, b) => a + b, 0);

  const statusLabel = isLaunching
    ? 'Initializing...'
    : runData?.status === 'running'
    ? 'Executing Pipeline'
    : runData?.status === 'completed'
    ? 'All Deliverables Ready'
    : runData?.status === 'needs_review'
    ? 'Needs Review (<7.0)'
    : runData?.status === 'failed'
    ? 'Execution Error'
    : 'System Ready';

  const debateRoundsCompleted = runData?.debate_messages && runData.debate_messages.length > 0
    ? Math.max(0, ...runData.debate_messages.map((m) => m.round || 0))
    : 0;

  return (
    <header className="top-metric-header">
      {/* Brand & Connection State */}
      <div className="top-brand-row">
        <div className="brand-group">
          <div className="brand-icon-wrapper">
            <span className="brand-robot-icon">🤖</span>
            <span className={`connection-dot ${serverConnected ? 'connected' : serverConnected === false ? 'disconnected' : 'checking'}`} />
          </div>
          <div className="brand-text">
            <div className="brand-title-badge">
              <h1 className="brand-title">AI Startup Co-Founder Team</h1>
              <span className="brand-tag">Autonomous Multi-Agent System</span>
            </div>
            <p className="brand-sub">
              5 Specialized Co-Founders · Peer Debate Protocol · CEO Quality Gatekeeper
            </p>
          </div>
        </div>

        {/* Global Action CTAs */}
        <div className="top-actions-group">
          <button
            type="button"
            className="action-pill-btn primary"
            onClick={onNewIdeaClick}
            id="btn-new-startup"
          >
            <span className="btn-icon">⚡</span>
            <span>+ New Startup</span>
          </button>

          <button
            type="button"
            className="action-pill-btn outline"
            onClick={onHistoryClick}
            id="btn-history-runs"
          >
            <span className="btn-icon">📂</span>
            <span>Past Runs</span>
          </button>

          {runData?.status === 'completed' && (
            <div className="export-pills-group">
              <button
                type="button"
                className="export-pill-btn"
                onClick={() => onExport('pdf')}
                title="Download Executive PDF Report"
              >
                📄 PDF
              </button>
              <button
                type="button"
                className="export-pill-btn"
                onClick={() => onExport('pptx')}
                title="Download 16:9 Pitch Deck (PPTX)"
              >
                📊 PPTX
              </button>
              <button
                type="button"
                className="export-pill-btn"
                onClick={() => onExport('md')}
                title="Download Markdown Report"
              >
                📝 MD
              </button>
              <button
                type="button"
                className="export-pill-btn"
                onClick={() => onExport('csv')}
                title="Download Tabular CSV Data"
              >
                📈 CSV
              </button>
            </div>
          )}

          {themeSelectorNode && <div className="theme-wrapper">{themeSelectorNode}</div>}
        </div>
      </div>

      {/* 5 Top KPI Cards (Reference Example 4) */}
      <div className="kpi-banner-grid">
        {/* KPI 1: Total Agents */}
        <div className="kpi-card">
          <div className="kpi-header">
            <span className="kpi-icon blue">👥</span>
            <span className="kpi-label">Co-Founders</span>
          </div>
          <div className="kpi-body">
            <div className="kpi-value">5 Co-Founders</div>
            <div className="kpi-subtext">
              {agentsDone === 4 ? 'All 4 Core Outputs Produced' : `${agentsDone} / 4 Deliverables`}
            </div>
          </div>
        </div>

        {/* KPI 2: Pipeline State */}
        <div className={`kpi-card ${runData?.status === 'running' ? 'active-pulse' : ''}`}>
          <div className="kpi-header">
            <span className={`kpi-icon ${runData?.status === 'running' ? 'indigo spin' : runData?.status === 'completed' ? 'green' : 'dim'}`}>
              ⚙️
            </span>
            <span className="kpi-label">Pipeline Status</span>
          </div>
          <div className="kpi-body">
            <div className={`kpi-value status-tag ${runData?.status || 'idle'}`}>
              {statusLabel}
            </div>
            <div className="kpi-subtext">
              {runData?.status === 'running' ? 'Live WebSocket streaming active' : 'LangGraph deterministic state'}
            </div>
          </div>
        </div>

        {/* KPI 3: CEO Quality Score */}
        <div className="kpi-card">
          <div className="kpi-header">
            <span className={`kpi-icon ${avgCeoScore && avgCeoScore >= 7.0 ? 'emerald' : 'amber'}`}>
              ⚖️
            </span>
            <span className="kpi-label">CEO Quality Score</span>
          </div>
          <div className="kpi-body">
            <div className="kpi-value">
              {avgCeoScore !== null ? (
                <>
                  <span className={`score-digit ${ceoPassed ? 'pass' : 'fail'}`}>
                    {avgCeoScore}
                  </span>
                  <span className="score-denom">/10.0</span>
                  <span className={`score-pill ${ceoPassed ? 'pass' : 'fail'}`}>
                    {ceoPassed ? 'PASSED ≥7.0' : 'NEEDS REVISION'}
                  </span>
                </>
              ) : (
                <span className="text-dim">Pending Review</span>
              )}
            </div>
            <div className="kpi-subtext">5 Rubric Criteria Evaluation</div>
          </div>
        </div>

        {/* KPI 4: Debate Protocol */}
        <div className="kpi-card">
          <div className="kpi-header">
            <span className="kpi-icon purple">⚔️</span>
            <span className="kpi-label">Peer Debate</span>
          </div>
          <div className="kpi-body">
            <div className="kpi-value">
              {debateRoundsCompleted > 0 ? (
                `Round ${debateRoundsCompleted} Concluded`
              ) : runData?.status === 'running' ? (
                'Critique In Progress'
              ) : (
                'Max 2 Rounds'
              )}
            </div>
            <div className="kpi-subtext">
              Analyst ↔ PM ↔ Tech Architect
            </div>
          </div>
        </div>

        {/* KPI 5: Efficiency Metrics */}
        <div className="kpi-card">
          <div className="kpi-header">
            <span className="kpi-icon amber">⚡</span>
            <span className="kpi-label">Token & Cloud Cost</span>
          </div>
          <div className="kpi-body">
            <div className="kpi-value">
              {runData?.total_tokens
                ? `${(runData.total_tokens / 1000).toFixed(1)}k tokens`
                : '0 tokens'}
            </div>
            <div className="kpi-subtext">
              {runData?.total_cost_usd !== undefined
                ? `$${runData.total_cost_usd.toFixed(4)} USD`
                : '$0.0000'}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
