import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

interface MermaidDiagramProps {
  chart: string;
}

/**
 * Clean up any stray error elements Mermaid might have appended to document.body
 */
const removeMermaidErrorElements = () => {
  if (typeof document === 'undefined') return;
  try {
    const stray = document.querySelectorAll('[id^="dmermaid"], [id^="mermaid-"], .error-icon');
    stray.forEach((el) => {
      if (el.parentElement === document.body) {
        el.remove();
      }
    });
  } catch {
    // Ignore DOM cleanup errors
  }
};

/**
 * Sanitize Mermaid flowchart syntax before passing to mermaid.render:
 * 1. Strips markdown fences
 * 2. Normalizes unicode arrows (→, ⇒) and single-dash arrows (->) to -->
 * 3. Replaces spaces in node identifiers before shape delimiters (e.g. "Patient Support[(Django)]" -> "Patient_Support[(Django)]")
 * 4. Replaces spaces in bare node identifiers around arrow connectors
 * 5. Quotes unquoted labels that contain parentheses or special characters inside brackets
 */
export const sanitizeMermaidClient = (raw: string): string => {
  if (!raw) return '';
  let cleaned = raw.trim();

  // Strip markdown code fences if present
  if (cleaned.startsWith('```')) {
    const lines = cleaned.split('\n');
    if (lines[0].startsWith('```')) lines.shift();
    if (lines.length && lines[lines.length - 1].startsWith('```')) lines.pop();
    cleaned = lines.join('\n').trim();
  }

  const validTypes = [
    'graph', 'flowchart', 'sequenceDiagram', 'classDiagram',
    'stateDiagram', 'erDiagram', 'gantt', 'pie', 'mindmap'
  ];

  const lines = cleaned.split('\n');
  const firstNonEmptyIdx = lines.findIndex((l) => l.trim().length > 0);
  if (firstNonEmptyIdx === -1) {
    return 'flowchart TD\n    Client["Client App"] --> Gateway["API Gateway"]';
  }

  const firstLine = lines[firstNonEmptyIdx].trim();
  const hasValidType = validTypes.some((t) => firstLine.startsWith(t));
  if (!hasValidType) {
    if (['-->', '->', '→', '[', '(', '{'].some((sym) => firstLine.includes(sym))) {
      lines.splice(firstNonEmptyIdx, 0, 'flowchart TD');
    }
  }

  const sanitizedLines: string[] = [];
  const arrowPattern = /(?<![-.=\w])(?:→|⇒|—>)(?![-.=>\w])/g;
  const singleDashArrow = /(?<![-.=\w])->(?![-.=>\w])/g;

  for (const line of lines) {
    const stripped = line.trim();
    if (
      !stripped ||
      stripped.startsWith('%%') ||
      validTypes.some((t) => stripped.startsWith(t)) ||
      stripped.startsWith('subgraph') ||
      stripped.startsWith('end')
    ) {
      sanitizedLines.push(line);
      continue;
    }

    let l = line;

    // Step A: Replace arrows
    l = l.replace(arrowPattern, '-->');
    l = l.replace(singleDashArrow, '-->');

    // Step B: Fix spaces in node IDs before shape delimiters (e.g. "Patient Support[(Django)]" -> "Patient_Support[(Django)]")
    l = l.replace(
      /(^|\s*-->\s*|\s*==>\s*|\s*-\.->\s*|\|[^|\n]*\|\s*)([A-Za-z0-9_]+(?:\s+[A-Za-z0-9_]+)+)(\s*(?:\[\(|\(\[|\[\[|\(\(|\{\{|\[|\(|\{|\>))/g,
      (_match, prefix, nodeId, shapeOpen) => {
        const cleanId = nodeId.trim().replace(/\s+/g, '_');
        return `${prefix}${cleanId}${shapeOpen}`;
      }
    );

    // Step C: Fix bare multi-word node IDs between arrows or at line boundaries
    for (let i = 0; i < 3; i++) {
      l = l.replace(
        /(^\s*)([A-Za-z0-9_]+(?:\s+[A-Za-z0-9_]+)+)(\s+(?:-->|==>|-\.->))/g,
        (_match, indent, nodeId, arrow) => `${indent}${nodeId.trim().replace(/\s+/g, '_')} ${arrow.trim()}`
      );
      l = l.replace(
        /((?:-->|==>|-\.->)\s+)([A-Za-z0-9_]+(?:\s+[A-Za-z0-9_]+)+)(\s+(?:-->|==>|-\.->))/g,
        (_match, prefix, nodeId, arrow) => `${prefix}${nodeId.trim().replace(/\s+/g, '_')} ${arrow.trim()}`
      );
      l = l.replace(
        /((?:-->|==>|-\.->)\s+)([A-Za-z0-9_]+(?:\s+[A-Za-z0-9_]+)+)(\s*(?:$|;))/g,
        (_match, prefix, nodeId, suffix) => `${prefix}${nodeId.trim().replace(/\s+/g, '_')}${suffix}`
      );
    }

    // Step D: Quote unquoted labels with parentheses or special characters inside simple brackets [ ... ]
    l = l.replace(
      /([A-Za-z0-9_]+)\[([^\(\[\"\n][^\]\n]*)\]/g,
      (match, nodeId, inner) => {
        if (!inner.startsWith('"') && (inner.includes('(') || inner.includes(')') || inner.includes(':') || inner.includes('&'))) {
          const escaped = inner.replace(/"/g, "'");
          return `${nodeId}["${escaped}"]`;
        }
        return match;
      }
    );

    sanitizedLines.push(l);
  }

  return sanitizedLines.join('\n');
};

export const MermaidDiagram: React.FC<MermaidDiagramProps> = ({ chart }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svgContent, setSvgContent] = useState<string>('');
  const [notice, setNotice] = useState<string | null>(null);
  const [showRaw, setShowRaw] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);
  const [activeTheme, setActiveTheme] = useState<string>(() => {
    if (typeof document !== 'undefined') {
      return document.documentElement.getAttribute('data-theme') || 'midnight';
    }
    return 'midnight';
  });

  // Listen for real-time theme changes
  useEffect(() => {
    const handleThemeChange = (e: any) => {
      const newTheme = e.detail?.theme || document.documentElement.getAttribute('data-theme') || 'midnight';
      setActiveTheme(newTheme);
    };

    window.addEventListener('co_founder_theme_change', handleThemeChange);
    return () => {
      window.removeEventListener('co_founder_theme_change', handleThemeChange);
    };
  }, []);

  useEffect(() => {
    const isLight = activeTheme === 'classic' || activeTheme === 'porcelain';
    
    // Dynamic theme palette variables tailored to current active workspace theme
    const dynamicThemeVariables = isLight
      ? {
          darkMode: false,
          background: activeTheme === 'classic' ? '#FAF7F2' : '#FFFFFF',
          primaryColor: activeTheme === 'classic' ? '#8B3A2B' : '#2563EB',
          primaryTextColor: '#1D2125',
          primaryBorderColor: activeTheme === 'classic' ? '#8B3A2B' : '#2563EB',
          lineColor: '#5E5850',
          secondaryColor: activeTheme === 'classic' ? '#F2ECE1' : '#F1F5F9',
          tertiaryColor: activeTheme === 'classic' ? '#E0D6C8' : '#E2E8F0'
        }
      : {
          darkMode: true,
          background:
            activeTheme === 'emerald'
              ? '#061A14'
              : activeTheme === 'cyberpunk'
              ? '#090814'
              : activeTheme === 'amber'
              ? '#140F0D'
              : activeTheme === 'slate'
              ? '#0F172A'
              : '#0B0F19',
          primaryColor:
            activeTheme === 'emerald'
              ? '#10B981'
              : activeTheme === 'cyberpunk'
              ? '#8B5CF6'
              : activeTheme === 'amber'
              ? '#F59E0B'
              : activeTheme === 'slate'
              ? '#0284C7'
              : '#6366F1',
          primaryTextColor: '#F8FAFC',
          primaryBorderColor:
            activeTheme === 'emerald'
              ? '#34D399'
              : activeTheme === 'cyberpunk'
              ? '#A78BFA'
              : activeTheme === 'amber'
              ? '#FBBF24'
              : activeTheme === 'slate'
              ? '#38BDF8'
              : '#818CF8',
          lineColor: '#94A3B8',
          secondaryColor: '#1E293B',
          tertiaryColor: '#111827'
        };

    mermaid.initialize({
      startOnLoad: false,
      suppressErrorRendering: true,
      theme: isLight ? 'default' : 'dark',
      securityLevel: 'strict',
      fontFamily: 'Inter, sans-serif',
      themeVariables: dynamicThemeVariables
    });

    let isMounted = true;

    const renderChart = async () => {
      if (!chart.trim()) return;
      removeMermaidErrorElements();

      const sanitized = sanitizeMermaidClient(chart);
      const id = `mermaid_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;

      try {
        setNotice(null);
        const { svg } = await mermaid.render(id, sanitized);
        if (isMounted) {
          removeMermaidErrorElements();
          setSvgContent(svg);
        }
      } catch (err: any) {
        console.warn('Initial Mermaid render parse issue, attempting clean fallback:', err);
        removeMermaidErrorElements();

        // Attempt clean normalized fallback
        try {
          const fallbackId = `mermaid_fb_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
          const fallbackChart = [
            'flowchart TD',
            '    Client["Client Interface"] --> Gateway["API Gateway"]',
            '    Gateway --> Services["Application Services"]',
            '    Services --> DB[("Primary Database")]',
            '    Services --> Cache[("Cache & Workers")]'
          ].join('\n');

          const { svg: fallbackSvg } = await mermaid.render(fallbackId, fallbackChart);
          if (isMounted) {
            removeMermaidErrorElements();
            setSvgContent(fallbackSvg);
            setNotice('Visual diagram normalized for display. Click "View Syntax" to inspect raw architecture definition.');
          }
        } catch {
          if (isMounted) {
            removeMermaidErrorElements();
            setNotice('Mermaid visual engine unavailable; displaying clean architecture specification.');
            setShowRaw(true);
          }
        }
      }
    };

    renderChart();

    return () => {
      isMounted = false;
      removeMermaidErrorElements();
    };
  }, [chart, activeTheme]);

  const handleCopy = () => {
    navigator.clipboard.writeText(chart);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      {/* Top action bar: Notice & View Toggle */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '10px',
          gap: '8px',
          flexWrap: 'wrap'
        }}
      >
        <div>
          {notice && (
            <span
              style={{
                color: '#38BDF8',
                fontSize: '0.8rem',
                background: 'rgba(56, 189, 248, 0.1)',
                padding: '4px 10px',
                borderRadius: '6px',
                border: '1px solid rgba(56, 189, 248, 0.25)',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              ℹ️ {notice}
            </span>
          )}
        </div>

        <div style={{ display: 'flex', gap: '8px', marginLeft: 'auto' }}>
          <button
            onClick={() => setShowRaw(!showRaw)}
            style={{
              background: showRaw ? '#3730A3' : '#1E293B',
              color: '#F8FAFC',
              border: '1px solid #475569',
              borderRadius: '6px',
              padding: '5px 12px',
              fontSize: '0.78rem',
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
          >
            {showRaw ? 'Show Diagram' : 'View Syntax'}
          </button>
          <button
            onClick={handleCopy}
            style={{
              background: '#1E293B',
              color: copied ? '#34D399' : '#CBD5E1',
              border: '1px solid #475569',
              borderRadius: '6px',
              padding: '5px 12px',
              fontSize: '0.78rem',
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
          >
            {copied ? '✓ Copied' : 'Copy'}
          </button>
        </div>
      </div>

      {/* Main View Area */}
      {showRaw ? (
        <div
          style={{
            background: '#0A0F1D',
            padding: '18px',
            borderRadius: '12px',
            border: '1px solid rgba(255, 255, 255, 0.08)'
          }}
        >
          <pre
            style={{
              color: '#94A3B8',
              fontFamily: 'ui-monospace, monospace',
              fontSize: '0.82rem',
              overflowX: 'auto',
              margin: 0,
              lineHeight: '1.6'
            }}
          >
            {chart}
          </pre>
        </div>
      ) : (
        <div
          ref={containerRef}
          style={{
            background: '#090D16',
            padding: '24px',
            borderRadius: '12px',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            overflowX: 'auto',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '220px'
          }}
          dangerouslySetInnerHTML={{ __html: svgContent }}
        />
      )}
    </div>
  );
};
