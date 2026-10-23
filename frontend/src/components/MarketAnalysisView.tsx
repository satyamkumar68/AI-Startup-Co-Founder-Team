import React from 'react';
import type { MarketAnalystOutput } from '../types';
import { MarketSizingChart } from './agent-ui/MarketSizingChart';

interface Props {
  data?: MarketAnalystOutput | null;
}

const isSafeUrl = (url?: string): boolean => {
  if (!url) return false;
  const trimmed = url.trim().toLowerCase();
  return trimmed.startsWith('http://') || trimmed.startsWith('https://');
};

export const MarketAnalysisView: React.FC<Props> = ({ data }) => {
  if (!data) {
    return <div style={{ color: 'var(--text-muted)', padding: '24px' }}>Market sizing and competitor research in progress...</div>;
  }

  return (
    <div className="market-analysis-container" id="market-analysis-container">
      {/* Visual Market Sizing Funnel (SKILL (3).md §12 Metrics) */}
      <MarketSizingChart tam={data.tam} sam={data.sam} som={data.som} />

      {/* Market Sizing Metrics */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">Total addressable market (TAM)</div>
          <div className="metric-value">{data.tam?.value || 'N/A'}</div>
          {data.tam?.source_url && isSafeUrl(data.tam.source_url) && (
            <a href={data.tam.source_url} target="_blank" rel="noopener noreferrer" className="metric-source">
              Source: {data.tam.source_url}
            </a>
          )}
          {data.tam?.estimated && <span style={{ fontSize: '0.75rem', color: 'var(--warning)', display: 'block', marginTop: '4px' }}>Bottom-up estimate</span>}
        </div>

        <div className="metric-card">
          <div className="metric-label">Serviceable addressable market (SAM)</div>
          <div className="metric-value">{data.sam?.value || 'N/A'}</div>
          {data.sam?.source_url && isSafeUrl(data.sam.source_url) && (
            <a href={data.sam.source_url} target="_blank" rel="noopener noreferrer" className="metric-source">
              Source: {data.sam.source_url}
            </a>
          )}
        </div>

        <div className="metric-card">
          <div className="metric-label">Serviceable obtainable market (SOM)</div>
          <div className="metric-value">{data.som?.value || 'N/A'}</div>
          {data.som?.source_url && isSafeUrl(data.som.source_url) && (
            <a href={data.som.source_url} target="_blank" rel="noopener noreferrer" className="metric-source">
              Source: {data.som.source_url}
            </a>
          )}
        </div>
      </div>

      {/* Competitor Analysis */}
      <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.1rem', fontWeight: 600, marginBottom: '14px' }}>
        Competitor landscape
      </h3>
      <div style={{ overflowX: 'auto', marginBottom: '28px' }}>
        <table className="custom-table" id="competitor-table">
          <thead>
            <tr>
              <th style={{ width: '180px' }}>Company</th>
              <th>Description</th>
              <th>Key strengths</th>
              <th>Vulnerabilities</th>
            </tr>
          </thead>
          <tbody>
            {(data.competitors || []).map((comp, idx) => (
              <tr key={idx}>
                <td style={{ fontWeight: 600, color: 'var(--text-main)' }}>{comp.name}</td>
                <td style={{ color: 'var(--text-muted)' }}>{comp.description}</td>
                <td style={{ color: 'var(--success)' }}>{comp.strengths?.join(', ')}</td>
                <td style={{ color: 'var(--warning)' }}>{comp.weaknesses?.join(', ')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Industry Trends and Risks */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
        <div style={{ background: 'var(--bg-subtle)', padding: '20px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
          <h4 style={{ color: 'var(--cyan)', marginBottom: '12px', fontSize: '0.95rem', fontWeight: 600 }}>
            Industry trends
          </h4>
          <ul style={{ paddingLeft: '18px', color: 'var(--text-main)', fontSize: '0.88rem' }}>
            {(data.trends || []).map((trend, i) => (
              <li key={i} style={{ marginBottom: '6px' }}>{trend}</li>
            ))}
          </ul>
        </div>

        <div style={{ background: 'var(--bg-subtle)', padding: '20px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
          <h4 style={{ color: 'var(--danger)', marginBottom: '12px', fontSize: '0.95rem', fontWeight: 600 }}>
            Market risks
          </h4>
          <ul style={{ paddingLeft: '18px', color: 'var(--text-main)', fontSize: '0.88rem' }}>
            {(data.risks || []).map((risk, i) => (
              <li key={i} style={{ marginBottom: '6px' }}>{risk}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};
