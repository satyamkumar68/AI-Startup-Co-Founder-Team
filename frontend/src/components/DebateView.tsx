import React, { useState } from 'react';
import type { DebateMessage } from '../types';
import { CEORubricChart } from './agent-ui/CEORubricChart';

interface Props {
  messages: DebateMessage[];
  scores?: Record<string, number[]>;
}

export const DebateView: React.FC<Props> = ({ messages, scores }) => {
  const [selectedRound, setSelectedRound] = useState<number | 'all'>('all');

  if (!messages || messages.length === 0) {
    return (
      <div style={{
        background: 'var(--bg-subtle)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-md)',
        padding: '36px 24px',
        textAlign: 'center',
        color: 'var(--text-muted)'
      }}>
        <h4 style={{ color: 'var(--text-main)', fontSize: '1.05rem', fontWeight: 600, marginBottom: '8px' }}>
          Peer debate
        </h4>
        <p style={{ fontSize: '0.9rem', maxWidth: '520px', margin: '0 auto', lineHeight: '1.5' }}>
          When debate is enabled, peer critiques between analyst, product manager, and technical architect are recorded here alongside CEO arbitration reviews.
        </p>
      </div>
    );
  }

  const rounds = Array.from(new Set(messages.map((m) => m.round))).sort();
  const filteredMessages =
    selectedRound === 'all' ? messages : messages.filter((m) => m.round === selectedRound);

  return (
    <div className="debate-view-container" id="debate-view-container">
      {/* Summary Banner */}
      <div style={{
        background: 'var(--bg-subtle)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-md)',
        padding: '18px 22px',
        marginBottom: '20px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '14px'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span className="badge badge-primary">Debate protocol</span>
            <span style={{ fontSize: '0.84rem', color: 'var(--text-muted)' }}>
              Triangular peer critique and arbitration
            </span>
          </div>
          <div style={{ fontSize: '0.88rem', color: 'var(--text-main)' }}>
            Each agent critiques a peer deliverable before the CEO evaluates the revised scope.
          </div>
        </div>

        {/* CEO Scores Summary */}
        {scores && Object.keys(scores).length > 0 && (
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {Object.entries(scores).map(([agent, scoreList]) => {
              const latestScore = scoreList[scoreList.length - 1];
              const passed = latestScore >= 7.0;
              return (
                <div
                  key={agent}
                  style={{
                    background: passed ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)',
                    border: `1px solid ${passed ? 'rgba(16, 185, 129, 0.25)' : 'rgba(239, 68, 68, 0.25)'}`,
                    borderRadius: 'var(--radius-sm)',
                    padding: '6px 12px',
                    fontSize: '0.82rem'
                  }}
                >
                  <span style={{ textTransform: 'capitalize', color: 'var(--text-muted)', marginRight: '6px' }}>
                    {agent.replace('_', ' ')}:
                  </span>
                  <span style={{ fontWeight: 600, color: passed ? 'var(--success)' : 'var(--danger)' }}>
                    {latestScore.toFixed(1)} / 10
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Filter by Round */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
        <button
          id="btn-debate-all"
          type="button"
          className={`btn ${selectedRound === 'all' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setSelectedRound('all')}
          style={{ padding: '6px 14px', fontSize: '0.82rem' }}
        >
          All exchanges ({messages.length})
        </button>
        {rounds.map((rnd) => (
          <button
            key={rnd}
            id={`btn-debate-round-${rnd}`}
            type="button"
            className={`btn ${selectedRound === rnd ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setSelectedRound(rnd)}
            style={{ padding: '6px 14px', fontSize: '0.82rem' }}
          >
            Round {rnd}
          </button>
        ))}
      </div>

      {/* Messages Timeline */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {filteredMessages.map((msg, idx) => {
          const isCritique = msg.content?.issues !== undefined;
          const isRebuttal = msg.content?.accepted !== undefined || msg.content?.rejected !== undefined;
          const isCeo = msg.from_agent.toLowerCase().includes('ceo') || msg.content?.verdict !== undefined || msg.content?.score !== undefined;

          return (
            <div
              key={idx}
              style={{
                background: 'var(--bg-subtle)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-md)',
                padding: '20px',
                position: 'relative'
              }}
            >
              {/* Header */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '14px',
                borderBottom: '1px solid var(--border)',
                paddingBottom: '10px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                  <span className={`badge ${isCeo ? 'badge-warning' : isRebuttal ? 'badge-success' : 'badge-primary'}`}>
                    Round {msg.round}
                  </span>
                  <span style={{ fontWeight: 600, color: 'var(--text-main)', textTransform: 'capitalize' }}>
                    {msg.from_agent.replace('_', ' ')}
                  </span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.84rem' }}>
                    {isRebuttal ? 'responding to' : 'critiquing'}
                  </span>
                  <span style={{ color: 'var(--cyan)', textTransform: 'capitalize' }}>
                    {msg.to_agent.replace('_', ' ')}
                  </span>
                </div>

                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  {isCeo ? 'CEO evaluation' : isRebuttal ? 'Rebuttal and resolution' : 'Peer critique'}
                </span>
              </div>

              {/* CEO Verdict Content */}
              {isCeo && (
                <div>
                  {msg.content?.score !== undefined && (
                    <CEORubricChart
                      score={typeof msg.content.score === 'number' ? msg.content.score : parseFloat(String(msg.content.score) || '7.0')}
                      strengths={msg.content?.strengths}
                      weaknesses={msg.content?.weaknesses}
                    />
                  )}

                  {msg.content?.verdict && (
                    <p style={{ color: 'var(--text-main)', fontSize: '0.92rem', marginBottom: '12px', lineHeight: '1.5' }}>
                      {msg.content.verdict}
                    </p>
                  )}

                  {msg.content?.required_changes && msg.content.required_changes.length > 0 && (
                    <div style={{ marginTop: '10px' }}>
                      <div style={{ fontSize: '0.82rem', color: 'var(--warning)', fontWeight: 600, marginBottom: '6px' }}>
                        Required modifications:
                      </div>
                      <ul style={{ paddingLeft: '20px', color: 'var(--text-muted)', fontSize: '0.86rem' }}>
                        {msg.content.required_changes.map((change: string, cIdx: number) => (
                          <li key={cIdx} style={{ marginBottom: '4px' }}>{change}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Peer Critique Content */}
              {isCritique && !isCeo && (
                <div>
                  {msg.content?.issues && msg.content.issues.length > 0 && (
                    <div style={{ marginBottom: '14px' }}>
                      <div style={{ fontSize: '0.82rem', color: 'var(--danger)', fontWeight: 600, marginBottom: '6px' }}>
                        Identified gaps and inconsistencies:
                      </div>
                      <ul style={{ paddingLeft: '20px', color: 'var(--text-main)', fontSize: '0.88rem' }}>
                        {msg.content.issues.map((issue: string, iIdx: number) => (
                          <li key={iIdx} style={{ marginBottom: '4px' }}>{issue}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {msg.content?.suggestions && msg.content.suggestions.length > 0 && (
                    <div>
                      <div style={{ fontSize: '0.82rem', color: 'var(--cyan)', fontWeight: 600, marginBottom: '6px' }}>
                        Recommendations:
                      </div>
                      <ul style={{ paddingLeft: '20px', color: 'var(--text-muted)', fontSize: '0.88rem' }}>
                        {msg.content.suggestions.map((sug: string, sIdx: number) => (
                          <li key={sIdx} style={{ marginBottom: '4px' }}>{sug}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Rebuttal Content */}
              {isRebuttal && !isCeo && (
                <div>
                  {msg.content?.accepted && msg.content.accepted.length > 0 && (
                    <div style={{ marginBottom: '12px' }}>
                      <div style={{ fontSize: '0.82rem', color: 'var(--success)', fontWeight: 600, marginBottom: '6px' }}>
                        Accepted modifications:
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        {msg.content.accepted.map((item: any, aIdx: number) => (
                          <div
                            key={aIdx}
                            style={{
                              background: 'var(--bg-surface)',
                              border: '1px solid var(--border)',
                              borderRadius: 'var(--radius-sm)',
                              padding: '8px 12px',
                              fontSize: '0.85rem'
                            }}
                          >
                            <span style={{ color: 'var(--success)', fontWeight: 600, marginRight: '6px' }}>Accepted:</span>
                            <span style={{ color: 'var(--text-main)' }}>{typeof item === 'string' ? item : item.issue || item.resolution || JSON.stringify(item)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {msg.content?.rejected && msg.content.rejected.length > 0 && (
                    <div style={{ marginBottom: '12px' }}>
                      <div style={{ fontSize: '0.82rem', color: 'var(--warning)', fontWeight: 600, marginBottom: '6px' }}>
                        Declined suggestions and rationale:
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        {msg.content.rejected.map((item: any, rIdx: number) => (
                          <div
                            key={rIdx}
                            style={{
                              background: 'var(--bg-surface)',
                              border: '1px solid var(--border)',
                              borderRadius: 'var(--radius-sm)',
                              padding: '8px 12px',
                              fontSize: '0.85rem'
                            }}
                          >
                            <span style={{ color: 'var(--warning)', fontWeight: 600, marginRight: '6px' }}>Declined:</span>
                            <span style={{ color: 'var(--text-main)' }}>{typeof item === 'string' ? item : item.issue || item.reason || JSON.stringify(item)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {msg.content?.output_updated !== undefined && (
                    <div style={{ marginTop: '8px' }}>
                      <span className="badge badge-info" style={{ fontSize: '0.75rem' }}>
                        {msg.content.output_updated ? 'Deliverable updated with revisions' : 'No revisions required'}
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
