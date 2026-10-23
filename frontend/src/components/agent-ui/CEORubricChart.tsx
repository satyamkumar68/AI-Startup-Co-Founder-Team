import React from 'react';

interface CEORubricChartProps {
  score: number;
  breakdown?: {
    completeness?: number;
    specificity?: number;
    evidence?: number;
    feasibility?: number;
    consistency?: number;
  };
  strengths?: string[];
  weaknesses?: string[];
}

export const CEORubricChart: React.FC<CEORubricChartProps> = ({
  score,
  breakdown,
  strengths = [],
  weaknesses = []
}) => {
  // Generate baseline rubric breakdown derived from overall score if not explicitly itemized
  const baseScore = Math.max(1, Math.min(10, score));
  const criteria = [
    { name: 'Completeness', value: breakdown?.completeness ?? Math.min(10, Number((baseScore * 0.98).toFixed(1))), weight: '20%' },
    { name: 'Specificity', value: breakdown?.specificity ?? Math.min(10, Number((baseScore * 1.02).toFixed(1))), weight: '20%' },
    { name: 'Evidence & Citations', value: breakdown?.evidence ?? Math.min(10, Number((baseScore * 0.95).toFixed(1))), weight: '20%' },
    { name: 'Feasibility (≤8 wks)', value: breakdown?.feasibility ?? Math.min(10, Number((baseScore * 1.04).toFixed(1))), weight: '20%' },
    { name: 'Consistency Across Stack', value: breakdown?.consistency ?? Math.min(10, Number((baseScore * 1.01).toFixed(1))), weight: '20%' }
  ];

  const isPassed = baseScore >= 7.0;

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        borderRadius: '12px',
        border: `1px solid ${isPassed ? 'rgba(16, 185, 129, 0.35)' : 'rgba(245, 158, 11, 0.35)'}`,
        padding: '20px',
        marginBottom: '20px',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)'
      }}
      role="region"
      aria-label="CEO Quality Scorecard & Rubric Breakdown"
    >
      {/* Header with overall score gauge */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h4 style={{ margin: 0, fontSize: '0.96rem', color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>⚖️</span> CEO Quality Audit Rubric
          </h4>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
            5-Point Evaluation Standard (AGENTS.md §5)
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span
            style={{
              padding: '4px 10px',
              borderRadius: '6px',
              fontSize: '0.78rem',
              fontWeight: 700,
              background: isPassed ? 'rgba(16, 185, 129, 0.18)' : 'rgba(245, 158, 11, 0.18)',
              color: isPassed ? '#10B981' : '#F59E0B',
              border: `1px solid ${isPassed ? 'rgba(16, 185, 129, 0.4)' : 'rgba(245, 158, 11, 0.4)'}`
            }}
          >
            {isPassed ? '✓ PASSED (≥7.0)' : '⚠ NEEDS REVISION'}
          </span>
          <span style={{ fontSize: '1.25rem', fontWeight: 800, color: isPassed ? '#10B981' : '#F59E0B', fontFamily: 'var(--font-mono)' }}>
            {baseScore.toFixed(1)} <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>/ 10</span>
          </span>
        </div>
      </div>

      {/* 5-Criteria Progress Bars */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {criteria.map((crit, idx) => {
          const critScore = Math.min(10, Math.max(0, crit.value));
          const critPercent = (critScore / 10) * 100;
          const critPassed = critScore >= 7.0;

          return (
            <div key={idx}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: '4px' }}>
                <span style={{ color: 'var(--text-main)', fontWeight: 500 }}>{crit.name}</span>
                <span style={{ color: critPassed ? '#10B981' : '#F59E0B', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                  {critScore.toFixed(1)} / 10
                </span>
              </div>
              <div
                style={{
                  width: '100%',
                  height: '8px',
                  background: 'var(--bg-subtle)',
                  borderRadius: '4px',
                  overflow: 'hidden',
                  position: 'relative'
                }}
              >
                {/* 7.0 Threshold Marker line */}
                <div
                  style={{
                    position: 'absolute',
                    left: '70%',
                    top: 0,
                    bottom: 0,
                    width: '2px',
                    background: 'var(--border-focus)',
                    zIndex: 2
                  }}
                  title="Pass Threshold (7.0)"
                />
                <div
                  style={{
                    width: `${critPercent}%`,
                    height: '100%',
                    background: critPassed ? 'linear-gradient(90deg, #059669 0%, #10B981 100%)' : 'linear-gradient(90deg, #D97706 0%, #F59E0B 100%)',
                    borderRadius: '4px',
                    transition: 'width 0.5s ease'
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Strengths & Weaknesses chips if available */}
      {(strengths.length > 0 || weaknesses.length > 0) && (
        <div style={{ marginTop: '16px', paddingTop: '14px', borderTop: '1px solid var(--border)', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          {strengths.length > 0 && (
            <div>
              <span style={{ fontSize: '0.74rem', color: '#10B981', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
                Key Strengths:
              </span>
              <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '0.74rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
                {strengths.slice(0, 2).map((s, idx) => (
                  <li key={idx}>{s}</li>
                ))}
              </ul>
            </div>
          )}

          {weaknesses.length > 0 && (
            <div>
              <span style={{ fontSize: '0.74rem', color: '#F59E0B', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
                Opportunities for Improvement:
              </span>
              <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '0.74rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
                {weaknesses.slice(0, 2).map((w, idx) => (
                  <li key={idx}>{w}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
