import React, { useState } from 'react';
import type { TechArchitectOutput } from '../types';
import { MermaidDiagram } from './MermaidDiagram';
import { CostBreakdownChart } from './agent-ui/CostBreakdownChart';

interface Props {
  data?: TechArchitectOutput | null;
}

export const ArchitectureView: React.FC<Props> = ({ data }) => {
  const [activeTab, setActiveTab] = useState<'diagram' | 'data_model' | 'scalability'>('diagram');

  if (!data) {
    return <div style={{ color: 'var(--text-muted)', padding: '24px' }}>System architecture is being designed...</div>;
  }

  const breakdownEntries = Object.entries(data.monthly_cost_estimate?.breakdown || {});
  const totalCost = data.monthly_cost_estimate?.total_usd || 0;

  return (
    <div className="arch-view-container" id="arch-view-container">
      {/* Visual Cost Allocation Chart (SKILL (3).md §12 Metrics) */}
      <CostBreakdownChart totalUsd={totalCost} breakdown={data.monthly_cost_estimate?.breakdown || {}} />
      {/* Cost Estimate Callout */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '16px',
        marginBottom: '24px'
      }}>
        <div className="metric-card">
          <div className="metric-label">Estimated monthly cloud cost (MVP scale)</div>
          <div className="metric-value" style={{ color: 'var(--cyan)' }}>
            ${totalCost.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginLeft: '6px' }}>per month</span>
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '6px' }}>
            Favors managed serverless and standard tier services
          </div>
        </div>

        <div style={{
          background: 'var(--bg-subtle)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-md)',
          padding: '16px 20px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center'
        }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 500, marginBottom: '6px' }}>
            Cost assumptions
          </div>
          <ul style={{ paddingLeft: '18px', color: 'var(--text-main)', fontSize: '0.84rem' }}>
            {(data.monthly_cost_estimate?.assumptions || []).map((assump, idx) => (
              <li key={idx} style={{ marginBottom: '4px' }}>{assump}</li>
            ))}
          </ul>
        </div>
      </div>

      {/* Cost Breakdown Table */}
      {breakdownEntries.length > 0 && (
        <div style={{
          background: 'var(--bg-subtle)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-md)',
          padding: '20px',
          marginBottom: '28px'
        }}>
          <h4 style={{ fontFamily: 'var(--font-display)', fontSize: '0.96rem', fontWeight: 600, marginBottom: '14px', color: 'var(--text-main)' }}>
            Cost breakdown by component
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' }}>
            {breakdownEntries.map(([service, amount]) => {
              const pct = totalCost > 0 ? Math.round((amount / totalCost) * 100) : 0;
              return (
                <div
                  key={service}
                  style={{
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '12px 14px'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                      {service.replace(/_/g, ' ')}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--cyan)' }}>{pct}%</span>
                  </div>
                  <div style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-main)' }}>
                    ${amount.toFixed(2)}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* View Switcher: Mermaid Diagram vs Data Model vs Scalability */}
      <div style={{ marginBottom: '16px', display: 'flex', gap: '8px' }}>
        <button
          id="btn-arch-diagram"
          type="button"
          className={`btn ${activeTab === 'diagram' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('diagram')}
          style={{ padding: '7px 14px', fontSize: '0.84rem' }}
        >
          System diagram
        </button>
        <button
          id="btn-arch-datamodel"
          type="button"
          className={`btn ${activeTab === 'data_model' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('data_model')}
          style={{ padding: '7px 14px', fontSize: '0.84rem' }}
        >
          Data model and schema
        </button>
        <button
          id="btn-arch-scalability"
          type="button"
          className={`btn ${activeTab === 'scalability' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('scalability')}
          style={{ padding: '7px 14px', fontSize: '0.84rem' }}
        >
          Scalability roadmap
        </button>
      </div>

      {/* Tab Panels */}
      {activeTab === 'diagram' && (
        <div style={{ marginBottom: '32px' }}>
          <MermaidDiagram chart={data.diagram_mermaid} />
        </div>
      )}

      {activeTab === 'data_model' && (
        <div style={{
          background: 'var(--bg-subtle)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-md)',
          padding: '20px',
          marginBottom: '32px'
        }}>
          <h4 style={{ color: 'var(--cyan)', marginBottom: '12px', fontFamily: 'var(--font-display)', fontSize: '0.96rem' }}>
            Data entities and relationships
          </h4>
          <pre style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.85rem',
            color: 'var(--text-main)',
            lineHeight: '1.6',
            whiteSpace: 'pre-wrap',
            background: 'var(--bg-surface)',
            padding: '16px',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border)'
          }}>
            {data.data_model}
          </pre>
        </div>
      )}

      {activeTab === 'scalability' && (
        <div style={{
          background: 'var(--bg-subtle)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-md)',
          padding: '24px',
          marginBottom: '32px'
        }}>
          <h4 style={{ color: 'var(--text-main)', marginBottom: '12px', fontFamily: 'var(--font-display)', fontSize: '1rem', fontWeight: 600 }}>
            Growth and scalability path (0 to 100k users)
          </h4>
          <div style={{ color: 'var(--text-main)', fontSize: '0.92rem', lineHeight: '1.7', whiteSpace: 'pre-line' }}>
            {data.scalability_notes}
          </div>
        </div>
      )}

      {/* Tech Stack Choices */}
      <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.1rem', fontWeight: 600, marginBottom: '14px' }}>
        Technology stack choices
      </h3>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '14px',
        marginBottom: '28px'
      }}>
        {(data.stack || []).map((item, idx) => (
          <div
            key={idx}
            style={{
              background: 'var(--bg-subtle)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-sm)',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span className="badge badge-primary">
                {item.category}
              </span>
              <span style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '0.96rem' }}>
                {item.technology}
              </span>
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.84rem', marginTop: '4px' }}>
              {item.justification}
            </p>
          </div>
        ))}
      </div>

      {/* Architecture Components */}
      <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.1rem', fontWeight: 600, marginBottom: '14px' }}>
        System components
      </h3>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '14px',
        marginBottom: '28px'
      }}>
        {(data.components || []).map((comp, idx) => (
          <div
            key={idx}
            style={{
              background: 'var(--bg-subtle)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-sm)',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px'
            }}
          >
            <h4 style={{ color: 'var(--cyan)', fontSize: '0.95rem', fontWeight: 600 }}>{comp.name}</h4>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', flexGrow: 1 }}>{comp.responsibility}</p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '4px' }}>
              {(comp.technologies || []).map((t, i) => (
                <span
                  key={i}
                  style={{
                    background: 'var(--bg-surface)',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    fontSize: '0.74rem',
                    color: 'var(--text-muted)',
                    border: '1px solid var(--border)'
                  }}
                >
                  {t}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Technical Risks */}
      <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.1rem', fontWeight: 600, marginBottom: '12px', color: 'var(--danger)' }}>
        Architectural risks and mitigations
      </h3>
      <div style={{
        background: 'var(--bg-subtle)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-sm)',
        padding: '18px 20px'
      }}>
        <ul style={{ paddingLeft: '18px', color: 'var(--text-main)', fontSize: '0.88rem' }}>
          {(data.risks || []).map((risk, i) => (
            <li key={i} style={{ marginBottom: '6px' }}>{risk}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};
