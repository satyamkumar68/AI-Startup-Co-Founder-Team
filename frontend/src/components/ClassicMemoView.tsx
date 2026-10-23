import { useState } from 'react';
import type { RunDetail } from '../types';

interface ClassicMemoViewProps {
  runData: RunDetail;
  onExport?: (format: 'pdf' | 'pptx' | 'md' | 'csv') => void;
}

export function ClassicMemoView({ runData, onExport }: ClassicMemoViewProps) {
  const [copied, setCopied] = useState(false);

  const {
    market,
    prd,
    architecture,
    pitch,
    scores,
    idea,
    status,
    created_at,
    total_tokens,
    total_cost_usd
  } = runData;

  const formattedDate = created_at
    ? new Date(created_at).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    : new Date().toLocaleDateString();

  // Average CEO Score calculation
  const allScores = Object.values(scores || {}).flat();
  const avgScore = allScores.length > 0
    ? (allScores.reduce((a, b) => a + b, 0) / allScores.length).toFixed(1)
    : null;

  const handleCopyMarkdown = () => {
    let md = `# EXECUTIVE MEMORANDUM\n\n`;
    md += `**TO:** Investment Committee & Founding Partners\n`;
    md += `**FROM:** Autonomous Co-Founder Team\n`;
    md += `**DATE:** ${formattedDate}\n`;
    md += `**SUBJECT:** Venture Evaluation: ${idea}\n\n`;
    
    if (prd?.problem_statement) {
      md += `## 1. Problem Statement\n${prd.problem_statement}\n\n`;
    }
    if (market) {
      md += `## 2. Market Sizing\n- TAM: ${market.tam.value} ${market.tam.unit || ''}\n- SAM: ${market.sam.value} ${market.sam.unit || ''}\n- SOM: ${market.som.value} ${market.som.unit || ''}\n\n`;
    }
    if (prd?.mvp_scope) {
      md += `## 3. MVP Scope\n${prd.mvp_scope}\n\n`;
    }
    if (architecture?.monthly_cost_estimate) {
      md += `## 4. Cloud Economics\nEstimated Monthly Cost: $${architecture.monthly_cost_estimate.total_usd}/mo\n\n`;
    }

    navigator.clipboard.writeText(md).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="classic-memo-doc">
      {/* Top Memorandum Header */}
      <div className="classic-memo-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.8rem',
              letterSpacing: '0.12em',
              color: 'var(--text-subtle)',
              marginBottom: '6px'
            }}>
              CONFIDENTIAL // VENTURE BRIEF
            </div>
            <h1 className="classic-memo-title">Executive Memorandum</h1>
          </div>

          {/* Action Toolbar */}
          <div className="no-print" style={{ display: 'flex', gap: '8px' }}>
            <button
              type="button"
              onClick={() => window.print()}
              className="btn btn-secondary"
              style={{ fontSize: '0.8rem', padding: '6px 12px' }}
              title="Print document or save directly as PDF"
            >
              Print / Save PDF
            </button>
            <button
              type="button"
              onClick={handleCopyMarkdown}
              className="btn btn-secondary"
              style={{ fontSize: '0.8rem', padding: '6px 12px' }}
            >
              {copied ? 'Copied brief' : 'Copy markdown'}
            </button>
            {onExport && (
              <>
                <button
                  type="button"
                  onClick={() => onExport('pdf')}
                  className="btn btn-primary"
                  style={{ fontSize: '0.8rem', padding: '6px 12px' }}
                >
                  Export PDF
                </button>
                <button
                  type="button"
                  onClick={() => onExport('csv')}
                  className="btn btn-secondary"
                  style={{ fontSize: '0.8rem', padding: '6px 12px' }}
                >
                  Export CSV
                </button>
              </>
            )}
          </div>
        </div>

        {/* Memo Metadata Block */}
        <div className="classic-memo-meta-grid">
          <div className="classic-memo-meta-item">
            <strong>DATE:</strong> {formattedDate}
          </div>
          <div className="classic-memo-meta-item">
            <strong>STATUS:</strong>{' '}
            <span style={{ textTransform: 'capitalize', fontWeight: 600 }}>{status}</span>
            {avgScore && (
              <span className={`badge ${Number(avgScore) >= 7 ? 'badge-success' : 'badge-warning'}`} style={{ marginLeft: '8px' }}>
                CEO Score {avgScore}/10
              </span>
            )}
          </div>
          <div className="classic-memo-meta-item">
            <strong>VENTURE CONCEPT:</strong> {idea}
          </div>
          <div className="classic-memo-meta-item">
            <strong>INFRASTRUCTURE USAGE:</strong> {total_tokens?.toLocaleString() || 0} tokens (${total_cost_usd?.toFixed(4) || '0.0000'})
          </div>
        </div>
      </div>

      {/* 1. Problem Statement & Core Thesis */}
      {prd?.problem_statement && (
        <section className="classic-memo-section">
          <h2 className="classic-memo-heading">
            <span>1. Problem Statement & Opportunity Thesis</span>
          </h2>
          <div className="classic-memo-callout">
            <p style={{ fontStyle: 'italic', fontSize: '1rem', lineHeight: 1.6 }}>
              "{prd.problem_statement}"
            </p>
          </div>

          {prd.personas && prd.personas.length > 0 && (
            <div style={{ marginTop: '20px' }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '10px' }}>
                Primary Target Personas
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '14px' }}>
                {prd.personas.map((p, idx) => (
                  <div key={idx} style={{
                    padding: '14px',
                    background: 'var(--bg-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border)'
                  }}>
                    <div style={{ fontWeight: 600, fontSize: '0.92rem', color: 'var(--text-main)' }}>{p.name}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--primary)', marginBottom: '8px' }}>{p.role}</div>
                    <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                      <strong>Pain Points:</strong> {p.pain_points?.join(', ')}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      )}

      {/* 2. Market Sizing & Competitive Landscape */}
      {market && (
        <section className="classic-memo-section">
          <h2 className="classic-memo-heading">
            <span>2. Market Sizing & Competitive Positioning</span>
          </h2>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '16px',
            marginBottom: '24px'
          }}>
            <div style={{ padding: '16px', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>TAM (TOTAL ADDRESSABLE)</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, fontFamily: 'var(--font-classic)', color: 'var(--text-main)', marginTop: '4px' }}>
                {market.tam?.value} {market.tam?.unit}
              </div>
              {market.tam?.notes && <div style={{ fontSize: '0.78rem', color: 'var(--text-subtle)', marginTop: '4px' }}>{market.tam.notes}</div>}
            </div>

            <div style={{ padding: '16px', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>SAM (SERVICEABLE ADDRESSABLE)</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, fontFamily: 'var(--font-classic)', color: 'var(--text-main)', marginTop: '4px' }}>
                {market.sam?.value} {market.sam?.unit}
              </div>
              {market.sam?.notes && <div style={{ fontSize: '0.78rem', color: 'var(--text-subtle)', marginTop: '4px' }}>{market.sam.notes}</div>}
            </div>

            <div style={{ padding: '16px', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>SOM (SERVICEABLE OBTAINABLE)</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, fontFamily: 'var(--font-classic)', color: 'var(--text-main)', marginTop: '4px' }}>
                {market.som?.value} {market.som?.unit}
              </div>
              {market.som?.notes && <div style={{ fontSize: '0.78rem', color: 'var(--text-subtle)', marginTop: '4px' }}>{market.som.notes}</div>}
            </div>
          </div>

          {market.competitors && market.competitors.length > 0 && (
            <div>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '10px' }}>
                Competitive Matrix
              </h3>
              <table className="classic-memo-table">
                <thead>
                  <tr>
                    <th>Competitor</th>
                    <th>Strengths</th>
                    <th>Weaknesses / Wedge Opportunity</th>
                  </tr>
                </thead>
                <tbody>
                  {market.competitors.map((c, idx) => (
                    <tr key={idx}>
                      <td style={{ fontWeight: 600 }}>{c.name}</td>
                      <td style={{ color: 'var(--text-muted)' }}>{c.strengths?.join('; ')}</td>
                      <td style={{ color: 'var(--text-main)' }}>{c.weaknesses?.join('; ')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      {/* 3. Product Scope & 8-Week MVP */}
      {prd && (
        <section className="classic-memo-section">
          <h2 className="classic-memo-heading">
            <span>3. Product Scope & 8-Week MVP Blueprint</span>
          </h2>

          {prd.mvp_scope && (
            <div style={{ marginBottom: '20px' }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px' }}>
                MVP Boundary Statement
              </h3>
              <p className="classic-memo-body">{prd.mvp_scope}</p>
            </div>
          )}

          {prd.features && prd.features.length > 0 && (
            <div style={{ marginBottom: '20px' }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '10px' }}>
                Feature Prioritization (P0 Deliverables)
              </h3>
              <table className="classic-memo-table">
                <thead>
                  <tr>
                    <th>Priority</th>
                    <th>Feature Specification</th>
                    <th>Rationale / Description</th>
                  </tr>
                </thead>
                <tbody>
                  {prd.features.map((f, idx) => (
                    <tr key={idx}>
                      <td>
                        <span className={`badge ${f.priority === 'P0' ? 'badge-primary' : 'badge-warning'}`}>
                          {f.priority}
                        </span>
                      </td>
                      <td style={{ fontWeight: 600 }}>{f.name}</td>
                      <td style={{ color: 'var(--text-muted)' }}>{f.description || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {prd.success_metrics && prd.success_metrics.length > 0 && (
            <div>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px' }}>
                Target Success Metrics
              </h3>
              <ul style={{ paddingLeft: '20px', color: 'var(--text-main)', fontSize: '0.9rem', lineHeight: 1.8 }}>
                {prd.success_metrics.map((m, idx) => (
                  <li key={idx}>{m}</li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

      {/* 4. Technical Architecture & Cloud Economics */}
      {architecture && (
        <section className="classic-memo-section">
          <h2 className="classic-memo-heading">
            <span>4. Systems Architecture & Infrastructure Economics</span>
          </h2>

          {architecture.monthly_cost_estimate && (
            <div className="classic-memo-callout" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>PROJECTED MONTHLY INFRASTRUCTURE RUNTIME</div>
                <div style={{ fontSize: '1.6rem', fontWeight: 700, fontFamily: 'var(--font-classic)', color: 'var(--text-main)' }}>
                  ${architecture.monthly_cost_estimate.total_usd.toLocaleString()} / month
                </div>
              </div>
              <div style={{ fontSize: '0.82rem', color: 'var(--text-subtle)', textAlign: 'right' }}>
                Managed services preference for MVP
              </div>
            </div>
          )}

          {architecture.stack && architecture.stack.length > 0 && (
            <div style={{ marginTop: '20px' }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '10px' }}>
                Selected Technology Stack
              </h3>
              <table className="classic-memo-table">
                <thead>
                  <tr>
                    <th>Category</th>
                    <th>Technology</th>
                    <th>Architectural Justification</th>
                  </tr>
                </thead>
                <tbody>
                  {architecture.stack.map((s, idx) => (
                    <tr key={idx}>
                      <td style={{ color: 'var(--text-muted)' }}>{s.category}</td>
                      <td style={{ fontWeight: 600 }}>{s.technology}</td>
                      <td style={{ color: 'var(--text-main)' }}>{s.justification}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      {/* 5. Investment Pitch Deck Summary */}
      {pitch?.slides && pitch.slides.length > 0 && (
        <section className="classic-memo-section">
          <h2 className="classic-memo-heading">
            <span>5. Pitch Deck Slide Narrative</span>
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
            {pitch.slides.map((s) => (
              <div key={s.slide_number} style={{
                padding: '16px',
                background: 'var(--bg-subtle)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border)'
              }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--primary)', fontWeight: 600 }}>SLIDE {s.slide_number}</div>
                <div style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--text-main)', margin: '4px 0 8px 0' }}>
                  {s.title}
                </div>
                <ul style={{ paddingLeft: '16px', fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                  {s.bullets.map((b, bIdx) => (
                    <li key={bIdx}>{b}</li>
                  ))}
                </ul>
                {s.speaker_notes && (
                  <div style={{
                    marginTop: '10px',
                    paddingTop: '8px',
                    borderTop: '1px dashed var(--border)',
                    fontSize: '0.78rem',
                    fontStyle: 'italic',
                    color: 'var(--text-subtle)'
                  }}>
                    "{s.speaker_notes.substring(0, 140)}..."
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Signature Sign-Off */}
      <div className="classic-memo-signature">
        <div>
          <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>Autonomous Co-Founder Taskforce</div>
          <div>Market Analyst • Product Manager • Technical Architect • Pitch Writer</div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>CEO / Critic Clearance</div>
          <div>Score: {avgScore || 'N/A'}/10 • Rubric Threshold: 7.0</div>
        </div>
      </div>
    </div>
  );
}
