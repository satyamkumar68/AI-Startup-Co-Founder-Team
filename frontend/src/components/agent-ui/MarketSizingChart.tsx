import React from 'react';
import type { MarketMetric } from '../../types';

interface MarketSizingChartProps {
  tam?: MarketMetric;
  sam?: MarketMetric;
  som?: MarketMetric;
}

const parseNumber = (val?: string): number => {
  if (!val) return 0;
  const lower = val.toLowerCase().trim();
  const match = lower.match(/([0-9]+(?:\.[0-9]+)?)/);
  if (!match) return 0;
  const base = parseFloat(match[1]);
  if (lower.includes('trillion') || lower.includes('t')) return base * 1e12;
  if (lower.includes('billion') || lower.includes('b')) return base * 1e9;
  if (lower.includes('million') || lower.includes('m')) return base * 1e6;
  if (lower.includes('k')) return base * 1e3;
  return base;
};

export const MarketSizingChart: React.FC<MarketSizingChartProps> = ({ tam, sam, som }) => {
  const tamNum = parseNumber(tam?.value);
  const samNum = parseNumber(sam?.value);
  const somNum = parseNumber(som?.value);

  // Calculate proportional widths (fallback to 100%, 35%, 10% if unparseable)
  let samWidth = 35;
  let somWidth = 10;
  if (tamNum > 0 && samNum > 0) {
    samWidth = Math.min(Math.max((samNum / tamNum) * 100, 18), 75);
  }
  if (samNum > 0 && somNum > 0) {
    somWidth = Math.min(Math.max((somNum / samNum) * samWidth, 8), samWidth * 0.7);
  } else if (tamNum > 0 && somNum > 0) {
    somWidth = Math.min(Math.max((somNum / tamNum) * 100, 8), 25);
  }

  const tiers = [
    {
      label: 'TAM (Total Addressable Market)',
      sub: 'Entire global demand for the solution category',
      value: tam?.value || 'N/A',
      widthPercent: 100,
      color: '#0284C7',
      bg: 'rgba(2, 132, 199, 0.15)',
      border: 'rgba(2, 132, 199, 0.4)'
    },
    {
      label: 'SAM (Serviceable Addressable Market)',
      sub: 'Segment targeted by product reach & channel distribution',
      value: sam?.value || 'N/A',
      widthPercent: samWidth,
      color: '#38BDF8',
      bg: 'rgba(56, 189, 248, 0.18)',
      border: 'rgba(56, 189, 248, 0.45)'
    },
    {
      label: 'SOM (Serviceable Obtainable Market)',
      sub: 'Realistic Year 1-2 captured market share for MVP launch',
      value: som?.value || 'N/A',
      widthPercent: somWidth,
      color: '#34D399',
      bg: 'rgba(16, 185, 129, 0.2)',
      border: 'rgba(16, 185, 129, 0.5)'
    }
  ];

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
      aria-label="Market Sizing Visual Distribution"
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h4 style={{ margin: 0, fontSize: '0.95rem', color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span>📊</span> Market Sizing Opportunity Funnel
        </h4>
        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
          Bottom-Up Capture Model
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {tiers.map((tier, idx) => (
          <div key={idx}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '6px' }}>
              <div>
                <span style={{ fontWeight: 600, fontSize: '0.84rem', color: tier.color, marginRight: '8px' }}>
                  {tier.label}
                </span>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  {tier.sub}
                </span>
              </div>
              <span style={{ fontWeight: 700, fontSize: '0.96rem', color: 'var(--text-main)', fontFamily: 'var(--font-mono)' }}>
                {tier.value}
              </span>
            </div>

            {/* Visual Funnel Bar */}
            <div
              style={{
                width: '100%',
                height: '14px',
                background: 'var(--bg-subtle)',
                borderRadius: '7px',
                overflow: 'hidden',
                position: 'relative'
              }}
            >
              <div
                style={{
                  width: `${tier.widthPercent}%`,
                  height: '100%',
                  background: tier.color,
                  borderRadius: '7px',
                  boxShadow: `0 0 10px ${tier.color}40`,
                  transition: 'width 0.6s cubic-bezier(0.16, 1, 0.3, 1)'
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
