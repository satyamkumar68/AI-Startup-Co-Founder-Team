import React from 'react';
import type { ProductManagerOutput } from '../types';

interface Props {
  data?: ProductManagerOutput | null;
}

export const PRDView: React.FC<Props> = ({ data }) => {
  if (!data) {
    return <div style={{ color: 'var(--text-muted)', padding: '24px' }}>Product requirements document is being drafted...</div>;
  }

  const p0Features = (data.features || []).filter(f => f.priority === 'P0');
  const p1Features = (data.features || []).filter(f => f.priority === 'P1');
  const p2Features = (data.features || []).filter(f => f.priority === 'P2');

  return (
    <div className="prd-view-container" id="prd-view-container">
      {/* Problem Statement Section */}
      <div style={{
        background: 'var(--bg-subtle)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-md)',
        padding: '24px',
        marginBottom: '24px'
      }}>
        <h3 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 500, marginBottom: '8px' }}>
          Core problem
        </h3>
        <p style={{ fontSize: '1.05rem', color: 'var(--text-main)', lineHeight: '1.6', fontWeight: 500 }}>
          {data.problem_statement}
        </p>
      </div>

      {/* MVP Scope Box */}
      <div style={{
        background: 'var(--bg-subtle)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-md)',
        padding: '20px 24px',
        marginBottom: '28px',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 500 }}>
            MVP boundary
          </h3>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {p0Features.length} core features in initial release
          </span>
        </div>
        <p style={{ color: 'var(--text-main)', fontSize: '0.95rem' }}>
          {data.mvp_scope}
        </p>
      </div>

      {/* Target User Personas */}
      <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.1rem', fontWeight: 600, marginBottom: '16px' }}>
        Target user personas
      </h3>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
        gap: '16px',
        marginBottom: '32px'
      }}>
        {(data.personas || []).map((persona, idx) => (
          <div
            key={idx}
            style={{
              background: 'var(--bg-subtle)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-md)',
              padding: '20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '14px'
            }}
          >
            <div>
              <h4 style={{ color: 'var(--text-main)', fontSize: '1rem', fontWeight: 600 }}>{persona.name}</h4>
              <div style={{ color: 'var(--cyan)', fontSize: '0.84rem', marginTop: '2px' }}>{persona.role}</div>
            </div>

            <div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 500, marginBottom: '6px' }}>
                Pain points
              </div>
              <ul style={{ paddingLeft: '18px', color: 'var(--text-main)', fontSize: '0.86rem' }}>
                {persona.pain_points.map((pt, i) => (
                  <li key={i} style={{ marginBottom: '4px' }}>{pt}</li>
                ))}
              </ul>
            </div>

            <div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 500, marginBottom: '6px' }}>
                Desired outcomes
              </div>
              <ul style={{ paddingLeft: '18px', color: 'var(--text-main)', fontSize: '0.86rem' }}>
                {persona.goals.map((goal, i) => (
                  <li key={i} style={{ marginBottom: '4px' }}>{goal}</li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>

      {/* Feature Backlog Prioritization */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.1rem', fontWeight: 600 }}>
          Feature backlog
        </h3>
        <div style={{ display: 'flex', gap: '8px' }}>
          <span className="badge badge-danger">
            P0: {p0Features.length} core
          </span>
          <span className="badge badge-primary">
            P1: {p1Features.length}
          </span>
          <span className="badge badge-info">
            P2: {p2Features.length}
          </span>
        </div>
      </div>

      <div style={{ overflowX: 'auto', marginBottom: '32px' }}>
        <table className="custom-table" id="prd-features-table">
          <thead>
            <tr>
              <th style={{ width: '90px' }}>Priority</th>
              <th style={{ width: '220px' }}>Feature name</th>
              <th>Description and role</th>
            </tr>
          </thead>
          <tbody>
            {(data.features || []).map((feat, idx) => {
              const priorityClass =
                feat.priority === 'P0'
                  ? 'badge badge-danger'
                  : feat.priority === 'P1'
                  ? 'badge badge-primary'
                  : 'badge badge-info';

              return (
                <tr key={idx}>
                  <td>
                    <span className={priorityClass}>{feat.priority}</span>
                  </td>
                  <td style={{ fontWeight: 600, color: 'var(--text-main)' }}>{feat.name}</td>
                  <td style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>
                    {feat.description || 'Core capability for MVP launch.'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* User Stories & Success Metrics Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '20px' }}>
        {/* User Stories */}
        <div style={{
          background: 'var(--bg-subtle)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-md)',
          padding: '20px'
        }}>
          <h4 style={{ color: 'var(--text-main)', marginBottom: '14px', fontFamily: 'var(--font-display)', fontSize: '1rem', fontWeight: 600 }}>
            User stories
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {(data.user_stories || []).map((story, i) => (
              <div
                key={i}
                style={{
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '12px 14px',
                  fontSize: '0.86rem',
                  color: 'var(--text-main)'
                }}
              >
                {story}
              </div>
            ))}
          </div>
        </div>

        {/* Success Metrics */}
        <div style={{
          background: 'var(--bg-subtle)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-md)',
          padding: '20px'
        }}>
          <h4 style={{ color: 'var(--text-main)', marginBottom: '14px', fontFamily: 'var(--font-display)', fontSize: '1rem', fontWeight: 600 }}>
            Success metrics
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {(data.success_metrics || []).map((metric, i) => (
              <div
                key={i}
                style={{
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '12px 14px',
                  fontSize: '0.86rem',
                  color: 'var(--text-main)'
                }}
              >
                {metric}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
