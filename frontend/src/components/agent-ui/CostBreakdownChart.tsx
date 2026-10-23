import React from 'react';

interface CostBreakdownChartProps {
  totalUsd: number;
  breakdown: Record<string, number>;
}

const CATEGORY_COLORS: Record<string, string> = {
  compute: '#6366F1', // Indigo
  web: '#38BDF8',     // Sky
  api: '#A855F7',     // Purple
  db: '#10B981',      // Emerald
  postgres: '#10B981',
  database: '#10B981',
  cache: '#F59E0B',   // Amber
  redis: '#F59E0B',
  llm: '#EC4899',     // Pink
  ai: '#EC4899',
  storage: '#06B6D4', // Cyan
  s3: '#06B6D4'
};

const getColorForCategory = (name: string, index: number): string => {
  const lower = name.toLowerCase();
  for (const [key, color] of Object.entries(CATEGORY_COLORS)) {
    if (lower.includes(key)) return color;
  }
  const fallbackPalette = ['#6366F1', '#38BDF8', '#10B981', '#F59E0B', '#EC4899', '#8B5CF6'];
  return fallbackPalette[index % fallbackPalette.length];
};

export const CostBreakdownChart: React.FC<CostBreakdownChartProps> = ({
  totalUsd,
  breakdown
}) => {
  const entries = Object.entries(breakdown || {});
  if (entries.length === 0) return null;

  const validTotal = totalUsd > 0 ? totalUsd : entries.reduce((acc, [, val]) => acc + val, 0);

  const items = entries.map(([category, amount], idx) => {
    const percent = validTotal > 0 ? (amount / validTotal) * 100 : 0;
    const color = getColorForCategory(category, idx);
    return {
      category,
      amount,
      percent,
      color
    };
  });

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        borderRadius: '12px',
        border: '1px solid var(--border)',
        padding: '20px',
        marginBottom: '24px',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)'
      }}
      role="region"
      aria-label="Cloud Cost Allocation Distribution Chart"
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <h4 style={{ margin: 0, fontSize: '0.95rem', color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span>💰</span> Monthly Cloud Infrastructure Allocation
        </h4>
        <span style={{ fontWeight: 700, fontSize: '0.96rem', color: 'var(--primary)', fontFamily: 'var(--font-mono)' }}>
          ${validTotal.toFixed(2)} / mo
        </span>
      </div>

      {/* Multi-segment stacked distribution bar */}
      <div
        style={{
          width: '100%',
          height: '18px',
          background: 'var(--bg-subtle)',
          borderRadius: '9px',
          overflow: 'hidden',
          display: 'flex',
          marginBottom: '16px',
          boxShadow: 'inset 0 1px 3px rgba(0, 0, 0, 0.15)'
        }}
      >
        {items.map((item, idx) => (
          <div
            key={idx}
            style={{
              width: `${item.percent}%`,
              height: '100%',
              backgroundColor: item.color,
              transition: 'width 0.5s ease',
              position: 'relative'
            }}
            title={`${item.category}: $${item.amount.toFixed(2)} (${item.percent.toFixed(1)}%)`}
          />
        ))}
      </div>

      {/* Legend Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '10px'
        }}
      >
        {items.map((item, idx) => (
          <div
            key={idx}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '8px 12px',
              borderRadius: '8px',
              background: 'var(--bg-subtle)',
              border: '1px solid var(--border)',
              fontSize: '0.78rem'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span
                style={{
                  width: '10px',
                  height: '10px',
                  borderRadius: '3px',
                  backgroundColor: item.color,
                  display: 'inline-block'
                }}
              />
              <span style={{ color: 'var(--text-main)', fontWeight: 500 }}>{item.category}</span>
            </div>
            <div style={{ textAlign: 'right' }}>
              <span style={{ color: 'var(--text-main)', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                ${item.amount.toFixed(2)}
              </span>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem', marginLeft: '4px' }}>
                ({item.percent.toFixed(0)}%)
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
