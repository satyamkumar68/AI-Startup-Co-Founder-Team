import React from 'react';

interface AuditRecord {
  claim: string;
  value: string;
  source: string;
  status: string;
  date: string;
}

interface FactCheckData {
  verified_count?: number;
  assumption_count?: number;
  unverified_count?: number;
  flagged_claims?: string[];
  appendix_markdown?: string;
  audit_records?: AuditRecord[];
}

interface FactCheckViewProps {
  data?: FactCheckData | null;
}

export const FactCheckView: React.FC<FactCheckViewProps> = ({ data }) => {
  if (!data) {
    return (
      <div className="card" style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
        <div style={{ fontSize: '2rem', marginBottom: '12px' }}>🔎</div>
        <h3 style={{ marginBottom: '8px', color: 'var(--text-main)' }}>Fact-Check Audit Pending</h3>
        <p style={{ maxWidth: '480px', margin: '0 auto', fontSize: '0.9rem' }}>
          Verification analysis runs automatically after deliverables are generated to audit external source URLs and pinned cloud pricing.
        </p>
      </div>
    );
  }

  const verified = data.verified_count || 0;
  const assumptions = data.assumption_count || 0;
  const unverified = data.unverified_count || 0;
  const records = data.audit_records || [];
  const flagged = data.flagged_claims || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Audit Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        <div className="metric-card" style={{ borderLeft: '4px solid var(--success, #10B981)' }}>
          <div className="metric-label">Verified External Sources</div>
          <div className="metric-value" style={{ color: 'var(--success, #10B981)' }}>{verified}</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Backed by URLs & Pinned Pricing</div>
        </div>

        <div className="metric-card" style={{ borderLeft: '4px solid var(--warning, #F59E0B)' }}>
          <div className="metric-label">Explicit Assumptions</div>
          <div className="metric-value" style={{ color: 'var(--warning, #F59E0B)' }}>{assumptions}</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Transparently marked as hypotheses</div>
        </div>

        <div className="metric-card" style={{ borderLeft: `4px solid ${unverified > 0 ? 'var(--danger, #EF4444)' : 'var(--text-muted)'}` }}>
          <div className="metric-label">Ungrounded Claims</div>
          <div className="metric-value" style={{ color: unverified > 0 ? 'var(--danger, #EF4444)' : 'var(--text-main)' }}>{unverified}</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{unverified === 0 ? 'Zero hallucinated metrics' : 'Requires source citation'}</div>
        </div>
      </div>

      {/* Flagged Claims Notice (if any) */}
      {flagged.length > 0 ? (
        <div style={{ padding: '16px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--danger, #EF4444)', borderRadius: 'var(--radius-md, 8px)' }}>
          <strong style={{ color: 'var(--danger, #EF4444)', display: 'block', marginBottom: '8px' }}>
            ⚠️ Unsupported Numerical Claims Detected:
          </strong>
          <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '0.86rem', color: 'var(--text-main)' }}>
            {flagged.map((item, idx) => (
              <li key={idx} style={{ marginBottom: '4px' }}>{item}</li>
            ))}
          </ul>
        </div>
      ) : (
        <div style={{ padding: '14px 18px', background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: 'var(--radius-md, 8px)', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '1.2rem' }}>🛡️</span>
          <div style={{ fontSize: '0.88rem', color: 'var(--text-main)' }}>
            <strong>100% Grounded Figures:</strong> All TAM/SAM figures and cloud infrastructure costs in this venture package are corroborated by live search URLs or the version-controlled cloud catalog (<code>data/cloud_pricing.json</code>).
          </div>
        </div>
      )}

      {/* Itemized Audit Table */}
      <div className="card" style={{ padding: '20px' }}>
        <h4 style={{ margin: '0 0 16px 0', fontSize: '1.05rem', color: 'var(--text-main)' }}>Itemized Citation & Grounding Records</h4>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.86rem', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-muted)' }}>
                <th style={{ padding: '10px 12px' }}>Claim / Deliverable Metric</th>
                <th style={{ padding: '10px 12px' }}>Reported Value</th>
                <th style={{ padding: '10px 12px' }}>Source / Catalog</th>
                <th style={{ padding: '10px 12px' }}>Status</th>
                <th style={{ padding: '10px 12px' }}>Retrieved</th>
              </tr>
            </thead>
            <tbody>
              {records.map((rec, idx) => {
                const isVerified = rec.status.includes('VERIFIED') || rec.status.includes('PINNED');
                const isAssumption = rec.status.includes('ASSUMPTION') || rec.status.includes('PARTIAL') || rec.status.includes('ASSUMED');
                const badgeColor = isVerified ? 'var(--success, #10B981)' : (isAssumption ? 'var(--warning, #F59E0B)' : 'var(--danger, #EF4444)');
                const isUrl = rec.source.startsWith('http');

                return (
                  <tr key={idx} style={{ borderBottom: '1px solid var(--border, #334155)' }}>
                    <td style={{ padding: '10px 12px', fontWeight: 500, color: 'var(--text-main)' }}>{rec.claim}</td>
                    <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono, monospace)', color: 'var(--text-main)' }}>{rec.value}</td>
                    <td style={{ padding: '10px 12px', color: 'var(--text-muted)', maxWidth: '280px', wordBreak: 'break-all' }}>
                      {isUrl ? (
                        <a href={rec.source} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--primary, #38BDF8)', textDecoration: 'underline' }}>
                          {rec.source}
                        </a>
                      ) : (
                        rec.source
                      )}
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      <span style={{
                        display: 'inline-block',
                        padding: '3px 8px',
                        borderRadius: '4px',
                        fontSize: '0.74rem',
                        fontWeight: 600,
                        backgroundColor: `color-mix(in srgb, ${badgeColor} 15%, transparent)`,
                        color: badgeColor,
                        border: `1px solid color-mix(in srgb, ${badgeColor} 30%, transparent)`
                      }}>
                        {rec.status}
                      </span>
                    </td>
                    <td style={{ padding: '10px 12px', color: 'var(--text-muted)', fontSize: '0.8rem' }}>{rec.date}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
