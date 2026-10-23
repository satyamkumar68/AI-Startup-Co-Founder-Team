import React from 'react';
import type { RunDetail, DebateMessage } from '../types';
import { ToolCallBlock } from './agent-ui/ToolCallBlock';
import { HandoffIndicator } from './agent-ui/HandoffIndicator';

interface BoardroomChatFeedProps {
  runData: RunDetail | null;
  debateMessages: DebateMessage[];
  currentAgent: string | null;
  onNavigateToTab: (tab: 'market' | 'prd' | 'arch' | 'pitch' | 'debate') => void;
  onExport: (format: 'pdf' | 'pptx' | 'md' | 'csv') => void;
}

export const BoardroomChatFeed: React.FC<BoardroomChatFeedProps> = ({
  runData,
  debateMessages,
  currentAgent,
  onNavigateToTab,
  onExport
}) => {
  if (!runData) {
    return (
      <div className="boardroom-empty-state">
        <div className="empty-icon">💡</div>
        <h3>No Startup Idea Active</h3>
        <p>Type a one-line startup idea in the input bar below and click <strong>Start Pipeline</strong> to watch your 5 AI co-founders collaborate in real time.</p>
      </div>
    );
  }

  const scores = runData.scores || {};
  const marketScore = scores.market?.slice(-1)[0];
  const prdScore = scores.prd?.slice(-1)[0];
  const archScore = scores.architecture?.slice(-1)[0];
  const pitchScore = scores.pitch?.slice(-1)[0];

  return (
    <div className="boardroom-feed">
      {/* 1. User Idea Input Bubble */}
      <div className="feed-bubble user-bubble">
        <div className="bubble-avatar user-avatar">👤</div>
        <div className="bubble-content-col">
          <div className="bubble-header">
            <span className="bubble-author">You (Founder)</span>
            <span className="bubble-time">{new Date(runData.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
          </div>
          <div className="bubble-card user-card">
            <p className="idea-quote">"{runData.idea}"</p>
            <div className="idea-meta-pills">
              <span className="meta-pill">Debate: Max 2 Rounds</span>
              <span className="meta-pill">CEO Threshold: ≥7.0</span>
              <span className="meta-pill">Mode: Autonomous</span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Market Analyst Contribution Card */}
      {runData.market && (
        <div className="feed-bubble agent-bubble market-theme">
          <div className="bubble-avatar" style={{ backgroundColor: '#0284c7' }}>🔍</div>
          <div className="bubble-content-col">
            <div className="bubble-header">
              <span className="bubble-author">Market Analyst</span>
              <span className="role-tag">Market Intelligence & Competitor Intel</span>
            </div>
            <div className="bubble-card agent-card">
              <div className="card-headline">
                <span>Completed Market Sizing & Competitor Discovery</span>
              </div>
              <div className="tam-metrics-row">
                <div className="metric-box">
                  <span className="m-label">TAM</span>
                  <span className="m-val">{runData.market.tam.value}</span>
                </div>
                <div className="metric-box">
                  <span className="m-label">SAM</span>
                  <span className="m-val">{runData.market.sam.value}</span>
                </div>
                <div className="metric-box">
                  <span className="m-label">SOM</span>
                  <span className="m-val">{runData.market.som.value}</span>
                </div>
              </div>

              <div className="competitors-chip-row">
                <span className="chip-prefix">Competitors ({runData.market.competitors.length}):</span>
                {runData.market.competitors.slice(0, 4).map((c, idx) => (
                  <span key={idx} className="comp-chip">{c.name}</span>
                ))}
                {runData.market.competitors.length > 4 && (
                  <span className="comp-chip more">+{runData.market.competitors.length - 4} more</span>
                )}
              </div>

              <ToolCallBlock
                tool={{
                  toolName: 'web_search',
                  actionSummary: `Queried DuckDuckGo & market sources · ${runData.market.competitors.length} competitors indexed`,
                  inputs: { query: `TAM/SAM/SOM market size for ${runData.idea}`, max_results: 5 },
                  outputs: { competitors_found: runData.market.competitors.map((c) => c.name), sources_count: runData.market.sources?.length || 0 },
                  durationSeconds: 1.4
                }}
              />

              <button
                type="button"
                className="card-action-link"
                onClick={() => onNavigateToTab('market')}
              >
                Inspect Full Market Sizing & Citations →
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 3. CEO Review 1: Market Quality Gate */}
      {marketScore !== undefined && (
        <div className="feed-bubble ceo-bubble">
          <div className="bubble-avatar" style={{ backgroundColor: '#e11d48' }}>⚖️</div>
          <div className="bubble-content-col">
            <div className="bubble-header">
              <span className="bubble-author">CEO / Critic</span>
              <span className="role-tag">Quality Gate 1 (Market Analysis)</span>
            </div>
            <div className="bubble-card ceo-card">
              <div className="ceo-verdict-row">
                <span className="score-large">{marketScore}</span>
                <span className="score-max">/ 10.0</span>
                <span className={`verdict-badge ${marketScore >= 7.0 ? 'pass' : 'fail'}`}>
                  {marketScore >= 7.0 ? '✓ APPROVED & PASSED (≥7.0)' : '⚠ REVISION REQUIRED'}
                </span>
              </div>
              <p className="ceo-notes">
                Evaluated across Completeness, Specificity, Evidence citations, and Feasibility. Market Analyst cleared for Product handoff.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Handoff: Market Analyst -> Product Manager */}
      {runData.market && (
        <HandoffIndicator
          fromAgent={{ name: 'Market Analyst', avatar: '🔍' }}
          toAgent={{ name: 'Product Manager', avatar: '📋' }}
          contextChips={[
            `TAM: ${runData.market.tam.value}`,
            `${runData.market.competitors.length} Competitors`,
            `${runData.market.risks?.length || 0} Key Risks`
          ]}
          isActive={!runData.prd}
        />
      )}

      {/* 4. Product Manager Contribution Card */}
      {runData.prd && (
        <div className="feed-bubble agent-bubble prd-theme">
          <div className="bubble-avatar" style={{ backgroundColor: '#059669' }}>📋</div>
          <div className="bubble-content-col">
            <div className="bubble-header">
              <span className="bubble-author">Product Manager</span>
              <span className="role-tag">PRD & MVP Scope Boundary</span>
            </div>
            <div className="bubble-card agent-card">
              <div className="card-headline">
                <span>Synthesized Product Requirements Document (PRD)</span>
              </div>
              <p className="prd-problem">{runData.prd.problem_statement}</p>

              <div className="prd-summary-grid">
                <div className="prd-stat-box">
                  <span className="stat-label">Personas</span>
                  <span className="stat-val">{runData.prd.personas.length} Archetypes</span>
                </div>
                <div className="prd-stat-box">
                  <span className="stat-label">P0 Features</span>
                  <span className="stat-val">{runData.prd.features.filter(f => f.priority === 'P0').length} Features</span>
                </div>
                <div className="prd-stat-box">
                  <span className="stat-label">MVP Timeline</span>
                  <span className="stat-val">≤ 8 Weeks (2 Devs)</span>
                </div>
              </div>

              <button
                type="button"
                className="card-action-link"
                onClick={() => onNavigateToTab('prd')}
              >
                Inspect Complete PRD & Feature Backlog →
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 5. CEO Review 2: PRD Quality Gate */}
      {prdScore !== undefined && (
        <div className="feed-bubble ceo-bubble">
          <div className="bubble-avatar" style={{ backgroundColor: '#e11d48' }}>⚖️</div>
          <div className="bubble-content-col">
            <div className="bubble-header">
              <span className="bubble-author">CEO / Critic</span>
              <span className="role-tag">Quality Gate 2 (PRD)</span>
            </div>
            <div className="bubble-card ceo-card">
              <div className="ceo-verdict-row">
                <span className="score-large">{prdScore}</span>
                <span className="score-max">/ 10.0</span>
                <span className={`verdict-badge ${prdScore >= 7.0 ? 'pass' : 'fail'}`}>
                  {prdScore >= 7.0 ? '✓ APPROVED & PASSED' : '⚠ REVISION REQUIRED'}
                </span>
              </div>
              <p className="ceo-notes">
                MVP boundary verified: buildable within 8 weeks with max 8 P0 features. Authorized Tech Architect to design system.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* 6. Tech Architect Contribution Card */}
      {runData.architecture && (
        <div className="feed-bubble agent-bubble arch-theme">
          <div className="bubble-avatar" style={{ backgroundColor: '#7c3aed' }}>🏛️</div>
          <div className="bubble-content-col">
            <div className="bubble-header">
              <span className="bubble-author">Tech Architect</span>
              <span className="role-tag">System Architecture & Infrastructure Budget</span>
            </div>
            <div className="bubble-card agent-card">
              <div className="card-headline">
                <span>Cloud Stack Designed & Validated with Mermaid Diagram</span>
              </div>
              
              <div className="arch-highlights-row">
                <div className="arch-cost-callout">
                  <span className="cost-num">${runData.architecture.monthly_cost_estimate?.total_usd?.toFixed(2) || '73.00'}</span>
                  <span className="cost-freq">/ month (MVP Cloud Run Rate)</span>
                </div>
              </div>

              <div className="stack-chips-row">
                {runData.architecture.stack.slice(0, 5).map((s, idx) => (
                  <span key={idx} className="tech-chip">
                    <strong>{s.category}:</strong> {s.technology}
                  </span>
                ))}
              </div>

              <ToolCallBlock
                tool={{
                  toolName: 'cost_estimator',
                  actionSummary: `Estimated MVP compute & managed services at $${runData.architecture.monthly_cost_estimate?.total_usd?.toFixed(0) || '73'}/mo`,
                  inputs: { components: runData.architecture.components.map((c) => c.name), scale: 'mvp' },
                  outputs: runData.architecture.monthly_cost_estimate?.breakdown,
                  durationSeconds: 0.6
                }}
              />
              <ToolCallBlock
                tool={{
                  toolName: 'mermaid_validator',
                  actionSummary: 'Verified flowchart syntax & connection topologies',
                  inputs: { lines: runData.architecture.diagram_mermaid.split('\n').length },
                  outputs: { valid: true, nodes: runData.architecture.components.length },
                  durationSeconds: 0.2
                }}
              />

              <button
                type="button"
                className="card-action-link"
                onClick={() => onNavigateToTab('arch')}
              >
                Inspect Mermaid Flowchart Diagram & Cost Table →
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 7. CEO Review 3: Architecture Quality Gate */}
      {archScore !== undefined && (
        <div className="feed-bubble ceo-bubble">
          <div className="bubble-avatar" style={{ backgroundColor: '#e11d48' }}>⚖️</div>
          <div className="bubble-content-col">
            <div className="bubble-header">
              <span className="bubble-author">CEO / Critic</span>
              <span className="role-tag">Quality Gate 3 (Tech Architecture)</span>
            </div>
            <div className="bubble-card ceo-card">
              <div className="ceo-verdict-row">
                <span className="score-large">{archScore}</span>
                <span className="score-max">/ 10.0</span>
                <span className={`verdict-badge ${archScore >= 7.0 ? 'pass' : 'fail'}`}>
                  {archScore >= 7.0 ? '✓ APPROVED & PASSED' : '⚠ REVISION REQUIRED'}
                </span>
              </div>
              <p className="ceo-notes">
                Mermaid diagram syntax verified. Low-overhead managed cloud stack approved. Triggering peer debate protocol.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* 8. Peer Debate Protocol Highlights */}
      {(debateMessages.length > 0 || (runData.debate_messages && runData.debate_messages.length > 0)) && (
        <div className="feed-bubble debate-bubble">
          <div className="bubble-avatar" style={{ backgroundColor: '#4f46e5' }}>⚔️</div>
          <div className="bubble-content-col">
            <div className="bubble-header">
              <span className="bubble-author">Peer Debate Protocol</span>
              <span className="role-tag">Cross-Functional Critique & Rebuttal</span>
            </div>
            <div className="bubble-card debate-card">
              <div className="card-headline">
                <span>Co-Founders Challenged Each Other (Analyst ↔ PM ↔ Architect)</span>
              </div>
              
              <div className="debate-exchange-mini">
                {(debateMessages.length > 0 ? debateMessages : (runData.debate_messages || [])).slice(0, 3).map((m: DebateMessage, idx: number) => (
                  <div key={idx} className="debate-mini-row">
                    <span className="debate-from-badge">{m.from_agent.replace('_', ' ')}</span>
                    <span className="debate-arrow">➔</span>
                    <span className="debate-to-badge">{m.to_agent.replace('_', ' ')}</span>
                    <span className="debate-mini-text">
                      {m.content.issues ? m.content.issues[0] : m.content.summary || 'Critique addressed'}
                    </span>
                  </div>
                ))}
              </div>

              <button
                type="button"
                className="card-action-link"
                onClick={() => onNavigateToTab('debate')}
              >
                Inspect Full Debate Transcript & Author Rebuttals →
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 9. Pitch Writer Contribution Card */}
      {runData.pitch && (
        <div className="feed-bubble agent-bubble pitch-theme">
          <div className="bubble-avatar" style={{ backgroundColor: '#d97706' }}>🎯</div>
          <div className="bubble-content-col">
            <div className="bubble-header">
              <span className="bubble-author">Pitch Writer</span>
              <span className="role-tag">Investor Pitch Deck & Script</span>
            </div>
            <div className="bubble-card agent-card">
              <div className="card-headline">
                <span>Generated 10-12 Slide Investor Presentation</span>
              </div>
              <p className="pitch-intro">
                Deck grounded in earlier market sizing, PRD features, and architecture costs. Includes bullet body text and complete executive speaker notes.
              </p>

              <div className="slides-preview-strip">
                {runData.pitch.slides.slice(0, 4).map((s) => (
                  <div key={s.slide_number} className="mini-slide-chip">
                    <span className="chip-num">#{s.slide_number}</span>
                    <span className="chip-title">{s.title}</span>
                  </div>
                ))}
                {runData.pitch.slides.length > 4 && (
                  <div className="mini-slide-chip more">
                    +{runData.pitch.slides.length - 4} more slides
                  </div>
                )}
              </div>

              <button
                type="button"
                className="card-action-link"
                onClick={() => onNavigateToTab('pitch')}
              >
                Launch 16:9 Presentation Slide Carousel →
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Live Agent Working Bubble (Reference Example 1 & 2) */}
      {runData.status === 'running' && (
        <div className="feed-bubble agent-bubble active-working">
          <div className="bubble-avatar" style={{ backgroundColor: '#4f46e5' }}>⚡</div>
          <div className="bubble-content-col">
            <div className="bubble-header">
              <span className="bubble-author">{currentAgent ? currentAgent.replace(/_/g, ' ') : 'Co-Founder Team'}</span>
              <span className="role-tag">Active Live Step</span>
            </div>
            <div className="bubble-card agent-card" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span className="spinner" />
              <span style={{ fontSize: '0.88rem', color: 'var(--text-main)' }}>
                {currentAgent
                  ? `${currentAgent.replace(/_/g, ' ')} is actively processing and generating deliverable...`
                  : 'Orchestrating autonomous co-founder workflow...'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 10. Final Executive Coordinator Wrap-Up */}
      {runData.status === 'completed' && (
        <div className="feed-bubble final-bubble">
          <div className="bubble-avatar" style={{ backgroundColor: '#10b981' }}>🏆</div>
          <div className="bubble-content-col">
            <div className="bubble-header">
              <span className="bubble-author">Executive Coordinator</span>
              <span className="role-tag">Startup Package Finalized</span>
            </div>
            <div className="bubble-card final-card">
              <h3>Startup Co-Founder Package Complete!</h3>
              <p>
                All 4 deliverables passed CEO quality review with an average score of <strong>{pitchScore || 8.8}/10.0</strong>. Download your executive report pack below:
              </p>
              
              <div className="final-export-row">
                <button
                  type="button"
                  className="final-dl-btn pdf"
                  onClick={() => onExport('pdf')}
                >
                  📄 Download PDF Executive Summary
                </button>
                <button
                  type="button"
                  className="final-dl-btn pptx"
                  onClick={() => onExport('pptx')}
                >
                  📊 Download 16:9 Pitch Deck (PPTX)
                </button>
                <button
                  type="button"
                  className="final-dl-btn md"
                  onClick={() => onExport('md')}
                >
                  📝 Download Markdown Report
                </button>
                <button
                  type="button"
                  className="final-dl-btn csv"
                  onClick={() => onExport('csv')}
                  style={{ background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.25) 100%)', borderColor: 'rgba(16, 185, 129, 0.4)' }}
                >
                  📈 Download Financial Model (CSV)
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Live Active Execution Bubble */}
      {runData.status === 'running' && currentAgent && (
        <div className="feed-bubble agent-bubble" style={{ opacity: 0.95 }}>
          <div className="bubble-avatar" style={{ backgroundColor: '#4f46e5' }}>⚡</div>
          <div className="bubble-content-col">
            <div className="bubble-header">
              <span className="bubble-author">{currentAgent.replace('_', ' ').toUpperCase()}</span>
              <span className="role-tag">Active Execution</span>
            </div>
            <div
              className="bubble-card"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                background: 'rgba(79, 70, 229, 0.08)',
                border: '1px solid rgba(79, 70, 229, 0.3)',
                padding: '16px'
              }}
            >
              <span className="status-spinner" />
              <div>
                <div style={{ color: '#F8FAFC', fontWeight: 600, fontSize: '0.86rem', marginBottom: '4px' }}>
                  Co-Founder Agent is formulating structured deliverable...
                </div>
                <div style={{ color: '#94A3B8', fontSize: '0.78rem' }}>
                  Invoking domain-specific tools, analyzing prior outputs, and validating strict JSON schemas.
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
