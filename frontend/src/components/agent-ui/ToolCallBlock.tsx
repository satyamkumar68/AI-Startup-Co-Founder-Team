import React, { useState } from 'react';

export interface ToolCallData {
  toolName: string;
  actionSummary: string;
  inputs?: Record<string, any> | string;
  outputs?: Record<string, any> | string;
  durationSeconds?: number;
  status?: 'success' | 'running' | 'error';
}

interface ToolCallBlockProps {
  tool: ToolCallData;
  defaultExpanded?: boolean;
}

export const ToolCallBlock: React.FC<ToolCallBlockProps> = ({
  tool,
  defaultExpanded = false
}) => {
  const [expanded, setExpanded] = useState<boolean>(defaultExpanded);

  const getToolIcon = (name: string) => {
    switch (name.toLowerCase()) {
      case 'web_search':
        return '🔍';
      case 'competitor_lookup':
        return '🏢';
      case 'cost_estimator':
        return '💰';
      case 'mermaid_validator':
        return '📐';
      default:
        return '⚙️';
    }
  };

  return (
    <div className="tool-call-block">
      <div
        className="tool-call-header"
        onClick={() => setExpanded(!expanded)}
        role="button"
        tabIndex={0}
        aria-expanded={expanded}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            setExpanded(!expanded);
          }
        }}
      >
        <div className="tool-call-title">
          <span>{getToolIcon(tool.toolName)}</span>
          <span className="tool-tag">{tool.toolName}</span>
          <span style={{ color: '#CBD5E1', fontSize: '0.78rem' }}>
            {tool.actionSummary}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.74rem', color: '#94A3B8' }}>
          {tool.durationSeconds !== undefined && (
            <span>{tool.durationSeconds.toFixed(1)}s</span>
          )}
          <span>{expanded ? '▲ Hide' : '▼ Inspect'}</span>
        </div>
      </div>

      {expanded && (
        <div className="tool-call-body">
          {tool.inputs && (
            <div style={{ marginBottom: '8px' }}>
              <strong style={{ color: '#E2E8F0', display: 'block', marginBottom: '4px' }}>Input Parameters:</strong>
              <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                {typeof tool.inputs === 'string' ? tool.inputs : JSON.stringify(tool.inputs, null, 2)}
              </pre>
            </div>
          )}

          {tool.outputs && (
            <div>
              <strong style={{ color: '#E2E8F0', display: 'block', marginBottom: '4px' }}>Tool Results:</strong>
              <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                {typeof tool.outputs === 'string' ? tool.outputs : JSON.stringify(tool.outputs, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
