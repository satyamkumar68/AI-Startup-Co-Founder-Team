import React, { useState, useEffect, useRef } from 'react';
import type {
  RunDetail,
  WebSocketEvent,
  DebateMessage
} from './types';
import { MarketAnalysisView } from './components/MarketAnalysisView';
import { PRDView } from './components/PRDView';
import { ArchitectureView } from './components/ArchitectureView';
import { PitchDeckView } from './components/PitchDeckView';
import { DebateView } from './components/DebateView';
import { TimelineView } from './components/TimelineView';
import { ThemeSelector } from './components/ThemeSelector';
import { ClassicMemoView } from './components/ClassicMemoView';

// Next-Gen Workspace Components (4-Archetype Synthesis)
import { TopMetricBanner } from './components/TopMetricBanner';
import { AgentRoster } from './components/AgentRoster';
import { VisualWorkflowPipeline } from './components/VisualWorkflowPipeline';
import { BoardroomChatFeed } from './components/BoardroomChatFeed';
import { AgentGraphView } from './components/agent-ui/AgentGraphView';
import { TaskBoardView } from './components/agent-ui/TaskBoardView';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_BASE = API_BASE.replace(/^http/, 'ws');

const SAMPLE_IDEAS = [
  {
    title: 'AI CBSE Class 10 Tutor',
    idea: 'An AI-powered tutor for CBSE Class 10 students in India that personalizes math and science practice based on past board exams.'
  },
  {
    title: 'Cloud FinOps Agent',
    idea: 'A lightweight autonomous agent that continuously analyzes AWS/GCP bills, identifies idle resources, and applies automated cost-reduction PRs.'
  },
  {
    title: 'Shopify SEO Optimizer',
    idea: 'AI tool that scans Shopify product catalogs and automatically rewrites descriptions, meta tags, and alt text to boost organic search ranking.'
  },
  {
    title: 'Compliance Evidence Collector',
    idea: 'Continuous compliance platform that connects to GitHub, AWS, and Slack to auto-generate audit-ready evidence for SOC2 and ISO27001.'
  },
  {
    title: 'Voice Dental Receptionist',
    idea: 'Voice AI assistant that answers after-hours phone calls for dental clinics, triages emergencies, and books appointments directly into EHR.'
  }
];

export function App() {
  // Input states
  const [ideaText, setIdeaText] = useState('');
  const [modelOverride, setModelOverride] = useState('ollama:qwen2.5-coder:1.5b');
  const [debateRounds, setDebateRounds] = useState(2);
  const [scoreThreshold, setScoreThreshold] = useState(7.0);
  const [showOptions, setShowOptions] = useState(false);

  // Active run states
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [runData, setRunData] = useState<RunDetail | null>(null);
  const [currentAgent, setCurrentAgent] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'timeline' | 'market' | 'prd' | 'arch' | 'pitch' | 'debate'>('timeline');
  const [viewMode, setViewMode] = useState<'workspace' | 'classic'>('workspace');
  const [canvasMode, setCanvasMode] = useState<'boardroom' | 'graph' | 'kanban' | 'studio'>(() => {
    try {
      const saved = localStorage.getItem('cofounder_canvas_mode');
      if (saved && ['boardroom', 'graph', 'kanban', 'studio'].includes(saved)) {
        return saved as any;
      }
    } catch {
      // ignore
    }
    return 'boardroom';
  });

  const handleSetCanvasMode = (mode: 'boardroom' | 'graph' | 'kanban' | 'studio') => {
    setCanvasMode(mode);
    try {
      localStorage.setItem('cofounder_canvas_mode', mode);
    } catch {
      // ignore
    }
  };
  const [events, setEvents] = useState<WebSocketEvent[]>([]);
  const [debateMessages, setDebateMessages] = useState<DebateMessage[]>([]);
  const [isLaunching, setIsLaunching] = useState(false);
  const [serverConnected, setServerConnected] = useState<boolean | null>(null);

  // Model Failover Notification
  const [modelSwitchAlert, setModelSwitchAlert] = useState<{
    previous: string;
    current: string;
    reason: string;
  } | null>(null);

  // Dynamic Model Catalog
  const [modelCatalog, setModelCatalog] = useState<{
    openrouter_free: Array<{ id: string; name: string; context_length?: number; pricing_description?: string }>;
    ollama_local: Array<{ id: string; name: string; size?: string; size_bytes?: number }>;
    flagship: Array<{ id: string; name: string; provider: string }>;
  } | null>(null);
  const [isLoadingModels, setIsLoadingModels] = useState(false);

  // Past runs drawer
  const [showHistory, setShowHistory] = useState(false);
  const [pastRuns, setPastRuns] = useState<RunDetail[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // WebSocket reference & Input Ref
  const wsRef = useRef<WebSocket | null>(null);
  const ideaInputRef = useRef<HTMLTextAreaElement | null>(null);
  const [isExporting, setIsExporting] = useState<string | null>(null);
  const [exportNotice, setExportNotice] = useState<string | null>(null);

  const fetchModelCatalog = async (forceRefresh = false) => {
    setIsLoadingModels(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/models${forceRefresh ? '?refresh=true' : ''}`);
      if (res.ok) {
        const data = await res.json();
        setModelCatalog(data);
      }
    } catch (err) {
      console.warn('Failed to load model catalog:', err);
    } finally {
      setIsLoadingModels(false);
    }
  };

  // Check backend health & fetch models on mount
  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then((res) => {
        if (res.ok) setServerConnected(true);
        else setServerConnected(false);
      })
      .catch(() => setServerConnected(false));

    fetchModelCatalog();
  }, []);

  // Keyboard navigation shortcuts (SKILL (3).md §10)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
        return;
      }

      if (e.key === '1') {
        handleSetCanvasMode('boardroom');
      } else if (e.key === '2') {
        handleSetCanvasMode('graph');
      } else if (e.key === '3') {
        handleSetCanvasMode('kanban');
      } else if (e.key === '4') {
        handleSetCanvasMode('studio');
      } else if (e.key === 'Escape') {
        setShowHistory(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Fetch past runs list
  const loadPastRuns = async () => {
    setLoadingHistory(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/runs?limit=20`);
      if (res.ok) {
        const data = await res.json();
        setPastRuns(data);
      }
    } catch (err) {
      console.error('Failed to load past runs:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    if (showHistory) {
      loadPastRuns();
    }
  }, [showHistory]);

  // Load a specific run detail
  const loadRunDetail = async (runId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/runs/${runId}`);
      if (res.ok) {
        const data: RunDetail = await res.json();
        setRunData(data);
        setActiveRunId(runId);
        fetchDebateTranscript(runId);
      }
    } catch (err) {
      console.error('Failed to load run detail:', err);
    }
  };

  // Fetch debate transcript
  const fetchDebateTranscript = async (runId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/runs/${runId}/debate`);
      if (res.ok) {
        const data = await res.json();
        if (data.messages) {
          setDebateMessages(data.messages);
        }
      }
    } catch (err) {
      console.error('Failed to load debate transcript:', err);
    }
  };

  // WebSocket connection handler
  useEffect(() => {
    if (!activeRunId) return;

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    const wsUrl = `${WS_BASE}/ws/runs/${activeRunId}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log(`WebSocket connected to ${wsUrl}`);
    };

    ws.onmessage = (evt) => {
      try {
        const packet: WebSocketEvent = JSON.parse(evt.data);
        setEvents((prev) => [...prev, packet]);

        if (packet.type === 'agent:started' || packet.type === 'agent_started') {
          const agentName = (packet as any).agent || (packet as any).node || null;
          setCurrentAgent(agentName);
        }

        if (packet.type === 'agent:completed' || packet.type === 'agent_completed') {
          loadRunDetail(activeRunId);
        }

        if (packet.type === 'debate:message' || packet.type === 'debate_critique' || packet.type === 'debate_response') {
          fetchDebateTranscript(activeRunId);
        }

        if (packet.type === 'model_switched') {
          setModelSwitchAlert({
            previous: (packet as any).previous_model || 'Primary model',
            current: (packet as any).new_model || 'Fallback model',
            reason: (packet as any).reason || 'Request failure'
          });
        }

        if (packet.type === 'run:completed' || packet.type === 'run_completed' || packet.type === 'run:failed') {
          setCurrentAgent(null);
          loadRunDetail(activeRunId);
        }
      } catch (e) {
        console.error('WS parse error:', e);
      }
    };

    ws.onerror = (err) => {
      console.error('WS error:', err);
    };

    ws.onclose = () => {
      console.log('WS connection closed');
    };

    return () => {
      ws.close();
    };
  }, [activeRunId]);

  // Launch a new run
  const handleLaunch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ideaText.trim() || isLaunching) return;

    setIsLaunching(true);
    setEvents([]);
    setDebateMessages([]);
    setModelSwitchAlert(null);
    setCurrentAgent('market_analyst');
    setCanvasMode('boardroom');

    try {
      let detectedProvider = 'openrouter';
      const cleanModel = modelOverride.trim();

      if (cleanModel.startsWith('ollama:') || cleanModel.startsWith('ollama/')) {
        detectedProvider = 'ollama';
      } else if (cleanModel.startsWith('openrouter/')) {
        detectedProvider = 'openrouter';
      } else if (cleanModel.includes(':') && !cleanModel.includes('/')) {
        detectedProvider = 'ollama';
      }

      const payload = {
        idea: ideaText.trim(),
        options: {
          provider: detectedProvider,
          debate_rounds: Number(debateRounds),
          score_threshold: Number(scoreThreshold),
          model_override: cleanModel || undefined
        }
      };

      const res = await fetch(`${API_BASE}/api/v1/runs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errData = await res.json();
        alert(`Error starting run: ${errData.detail?.error?.message || res.statusText}`);
        return;
      }

      const resData = await res.json();
      const newRunId = resData.run_id;
      setActiveRunId(newRunId);
      setActiveTab('timeline');

      // Seed initial run state
      setRunData({
        run_id: newRunId,
        idea: ideaText.trim(),
        status: 'running',
        scores: {},
        created_at: new Date().toISOString(),
        total_tokens: 0,
        total_cost_usd: 0
      });
    } catch (err: any) {
      alert(`Network error: ${err.message}`);
    } finally {
      setIsLaunching(false);
    }
  };

  // Cancel active run
  const handleCancel = async () => {
    if (!activeRunId) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/runs/${activeRunId}/cancel`, {
        method: 'POST'
      });
      if (res.ok) {
        setRunData((prev) => (prev ? { ...prev, status: 'cancelled' } : null));
        setCurrentAgent(null);
      }
    } catch (err) {
      console.error('Failed to cancel run:', err);
    }
  };

  // Clean TitleCase brand & deliverable filename generator (matches backend canonical format)
  const getProductionExportFilename = (idea: string | undefined, runId: string, format: 'pdf' | 'pptx' | 'md' | 'csv'): string => {
    const acronyms = new Set(['ai', 'seo', 'ehr', 'cbse', 'b2b', 'b2c', 'saas', 'crm', 'api', 'ml', 'llm', 'ui', 'ux', 'ar', 'vr', 'iot']);
    const stopWords = new Set([
      'that', 'this', 'and', 'or', 'for', 'to', 'in', 'on', 'with', 'by', 'at',
      'from', 'into', 'an', 'a', 'the', 'is', 'are', 'using', 'used', 'of',
      'automatically', 'directly'
    ]);

    let cleanTitle = 'Startup_Venture';
    if (idea && idea.trim()) {
      let text = idea.trim();
      const leadPatterns = [
        /^(a|an|the)\s+/i,
        /^(build|create|design|develop|make|launch)\s+(a|an|the)?\s*/i,
        /^(an?\s+)?(ai|voice\s+ai|autonomous|smart|automated)\s+(tool|assistant|agent|platform|copilot|system|app|service|solution)\s+(that|to|for|which)?\s*/i,
        /^(platform|tool|app|software|system|service|solution)\s+(that|to|for|which)\s+/i,
        /^(scans|answers|automates|provides|enables|helps|generates)\s+/i,
      ];
      for (const pat of leadPatterns) {
        text = text.replace(pat, '').trim();
      }
      const words = text.match(/[A-Za-z0-9]+/g) || idea.match(/[A-Za-z0-9]+/g) || [];
      const meaningful: string[] = [];
      for (const w of words) {
        const low = w.toLowerCase();
        if (stopWords.has(low) && meaningful.length > 0) continue;
        if (acronyms.has(low)) {
          meaningful.push(w.toUpperCase());
        } else {
          meaningful.push(w.charAt(0).toUpperCase() + w.slice(1).toLowerCase());
        }
        if (meaningful.length === 4) break;
      }
      if (meaningful.length > 0) {
        cleanTitle = meaningful.join('_');
      }
    } else if (runId) {
      cleanTitle = `Startup_${runId.slice(0, 8)}`;
    }

    const suffixMap = {
      pdf: 'Executive_Report.pdf',
      pptx: 'Pitch_Deck.pptx',
      md: 'Venture_Plan.md',
      csv: 'Financial_Model.csv',
    };

    return `${cleanTitle}_${suffixMap[format]}`;
  };

  // Trigger export download (via direct path endpoint + Blob to guarantee exact filename & extension)
  const handleExport = async (format: 'pdf' | 'pptx' | 'md' | 'csv') => {
    if (!activeRunId || isExporting) return;
    setIsExporting(format);
    try {
      const targetFilename = getProductionExportFilename(runData?.idea, activeRunId, format);
      // Direct path URL guarantees filename and extension even on direct clicks or Swagger
      const url = `${API_BASE}/api/v1/runs/${activeRunId}/download/${encodeURIComponent(targetFilename)}`;

      let response = await fetch(url);
      if (!response.ok) {
        // Fallback to query param endpoint if path route fails
        const fallbackUrl = `${API_BASE}/api/v1/runs/${activeRunId}/export?format=${format}`;
        response = await fetch(fallbackUrl);
        if (!response.ok) {
          throw new Error(`Export request failed with status: ${response.status}`);
        }
      }

      // 1. Read filename from Content-Disposition header if available
      let filename = targetFilename;
      const disposition = response.headers.get('Content-Disposition');
      if (disposition) {
        const utf8Match = disposition.match(/filename\*=UTF-8''([^;\r\n]+)/i);
        const quoteMatch = disposition.match(/filename="?([^";\r\n]+)"?/i);
        const match = (utf8Match && utf8Match[1]) || (quoteMatch && quoteMatch[1]);
        if (match) {
          try {
            filename = decodeURIComponent(match.trim());
          } catch {
            filename = match.trim();
          }
        }
      }

      // 2. Strict guarantee that file extension is attached
      const expectedExt = format === 'md' ? '.md' : `.${format}`;
      if (!filename.toLowerCase().endsWith(expectedExt)) {
        filename = `${filename}${expectedExt}`;
      }

      // 3. Convert to same-origin Blob URL so the browser strictly respects the download attribute
      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);

      setExportNotice(`Downloaded ${filename}`);
      setTimeout(() => setExportNotice(null), 5000);
    } catch (err) {
      console.error('Export download error:', err);
      alert(`Could not download ${format.toUpperCase()} export. Please verify the backend is running.`);
    } finally {
      setIsExporting(null);
    }
  };

  // Focus and jump to idea intake dock
  const handleNewIdeaClick = () => {
    if (ideaInputRef.current) {
      ideaInputRef.current.focus();
      ideaInputRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // Step/Tab navigation helper
  const handleNavigateToTab = (tab: 'market' | 'prd' | 'arch' | 'pitch' | 'debate') => {
    setActiveTab(tab);
    setCanvasMode('studio');
  };

  return (
    <div className="app-container">
      {/* 1. Top KPI Summary Banner (4-Archetype Synthesis: Example 4) */}
      <TopMetricBanner
        runData={runData}
        serverConnected={serverConnected}
        isLaunching={isLaunching}
        onNewIdeaClick={handleNewIdeaClick}
        onHistoryClick={() => setShowHistory(true)}
        onExport={handleExport}
        themeSelectorNode={<ThemeSelector />}
      />

      {/* 2. Visual Workflow Pipeline Flow (Example 2 & 4) */}
      <VisualWorkflowPipeline
        runData={runData}
        currentAgent={currentAgent}
        onNavigateToTab={handleNavigateToTab}
      />

      {/* 3. Main Workspace Split Layout: Left Roster + Right Canvas */}
      <div className="workspace-split-layout">
        {/* Left Column: Co-Founder Roster & Live Status Drawer (Examples 2, 3, 4) */}
        <AgentRoster
          runData={runData}
          currentAgent={currentAgent}
          activeTab={activeTab}
          onSelectAgent={handleNavigateToTab}
          defaultModel={modelOverride}
        />

        {/* Right Column: Dual-Mode Canvas (Mode A: Boardroom Chat Stream / Mode B: Deliverables Studio) */}
        <main className="canvas-container">
          <div className="canvas-top-bar">
            {/* Multi-Agent Orchestrator View Selector */}
            <div className="mode-toggle-group">
              <button
                type="button"
                id="btn-mode-boardroom"
                className={`mode-toggle-btn ${canvasMode === 'boardroom' ? 'active' : ''}`}
                onClick={() => handleSetCanvasMode('boardroom')}
                title="Conversational Co-Founder Boardroom Stream (Shortcut: 1)"
              >
                <span>💬</span>
                <span>Boardroom</span>
              </button>
              <button
                type="button"
                id="btn-mode-graph"
                className={`mode-toggle-btn ${canvasMode === 'graph' ? 'active' : ''}`}
                onClick={() => handleSetCanvasMode('graph')}
                title="Interactive Co-Founder Topology Graph (Shortcut: 2)"
              >
                <span>🕸️</span>
                <span>Agent Graph</span>
              </button>
              <button
                type="button"
                id="btn-mode-kanban"
                className={`mode-toggle-btn ${canvasMode === 'kanban' ? 'active' : ''}`}
                onClick={() => handleSetCanvasMode('kanban')}
                title="Kanban Task Board by Status (Shortcut: 3)"
              >
                <span>📋</span>
                <span>Task Board</span>
              </button>
              <button
                type="button"
                id="btn-mode-studio"
                className={`mode-toggle-btn ${canvasMode === 'studio' ? 'active' : ''}`}
                onClick={() => handleSetCanvasMode('studio')}
                title="Full-Screen Executive Deliverables Studio (Shortcut: 4)"
              >
                <span>📊</span>
                <span>Studio</span>
              </button>
            </div>

            {/* Right Canvas Actions: View Mode (Studio vs Classic) & Quick Exports */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              {canvasMode === 'studio' && (
                <div className="view-mode-pill">
                  <button
                    id="btn-view-workspace"
                    type="button"
                    className={`view-mode-btn ${viewMode === 'workspace' ? 'active' : ''}`}
                    onClick={() => setViewMode('workspace')}
                  >
                    Interactive Tabs
                  </button>
                  <button
                    id="btn-view-classic"
                    type="button"
                    className={`view-mode-btn ${viewMode === 'classic' ? 'active' : ''}`}
                    onClick={() => setViewMode('classic')}
                  >
                    Classic Memo
                  </button>
                </div>
              )}

              {activeRunId && (
                <>
                  <button
                    id="btn-export-pdf"
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => handleExport('pdf')}
                    disabled={!!isExporting}
                    title={activeRunId ? `Download ${getProductionExportFilename(runData?.idea, activeRunId, 'pdf')}` : "Download Executive Summary PDF Report"}
                    style={{ padding: '6px 12px', fontSize: '0.8rem', opacity: isExporting && isExporting !== 'pdf' ? 0.6 : 1 }}
                  >
                    {isExporting === 'pdf' ? 'Exporting...' : '📄 PDF'}
                  </button>
                  <button
                    id="btn-export-pptx"
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => handleExport('pptx')}
                    disabled={!!isExporting}
                    title={activeRunId ? `Download ${getProductionExportFilename(runData?.idea, activeRunId, 'pptx')}` : "Download 16:9 Pitch Deck PPTX"}
                    style={{ padding: '6px 12px', fontSize: '0.8rem', opacity: isExporting && isExporting !== 'pptx' ? 0.6 : 1 }}
                  >
                    {isExporting === 'pptx' ? 'Exporting...' : '📊 PPTX'}
                  </button>
                  <button
                    id="btn-export-md"
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => handleExport('md')}
                    disabled={!!isExporting}
                    title={activeRunId ? `Download ${getProductionExportFilename(runData?.idea, activeRunId, 'md')}` : "Download Full Markdown Report"}
                    style={{ padding: '6px 12px', fontSize: '0.8rem', opacity: isExporting && isExporting !== 'md' ? 0.6 : 1 }}
                  >
                    {isExporting === 'md' ? 'Exporting...' : '📝 MD'}
                  </button>
                  <button
                    id="btn-export-csv"
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => handleExport('csv')}
                    disabled={!!isExporting}
                    title={activeRunId ? `Download ${getProductionExportFilename(runData?.idea, activeRunId, 'csv')}` : "Download Tabular CSV Data"}
                    style={{ padding: '6px 12px', fontSize: '0.8rem', opacity: isExporting && isExporting !== 'csv' ? 0.6 : 1 }}
                  >
                    {isExporting === 'csv' ? 'Exporting...' : '📈 CSV'}
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Export Success Notification Banner */}
          {exportNotice && (
            <div
              className="export-success-banner"
              style={{
                marginBottom: '16px',
                padding: '10px 16px',
                borderRadius: '8px',
                backgroundColor: 'rgba(16, 185, 129, 0.12)',
                border: '1px solid rgba(16, 185, 129, 0.35)',
                color: '#10b981',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                fontSize: '0.875rem',
                boxShadow: '0 2px 8px rgba(16, 185, 129, 0.15)'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '1.1rem' }}>✅</span>
                <span><strong>Export Ready:</strong> {exportNotice}</span>
              </div>
              <button
                type="button"
                onClick={() => setExportNotice(null)}
                style={{ background: 'transparent', border: 'none', color: '#10b981', cursor: 'pointer', fontSize: '1rem', padding: '0 4px' }}
                title="Dismiss"
              >
                ✕
              </button>
            </div>
          )}

          {/* Model Failover Alert Banner */}
          {modelSwitchAlert && (
            <div className="failover-banner" style={{ marginBottom: '16px' }}>
              <div className="failover-banner-icon">⚡</div>
              <div style={{ flex: 1 }}>
                <div className="failover-banner-text">
                  <strong>Automatic Failover Activated:</strong> Model <code>{modelSwitchAlert.previous}</code> encountered an issue ({modelSwitchAlert.reason}). Execution seamlessly switched to <code>{modelSwitchAlert.current}</code>.
                </div>
              </div>
              <button
                type="button"
                onClick={() => setModelSwitchAlert(null)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1rem', padding: '0 4px' }}
                title="Dismiss"
              >
                ✕
              </button>
            </div>
          )}

          {/* Mode A: Boardroom Chat Feed Stream */}
          {canvasMode === 'boardroom' && (
            <BoardroomChatFeed
              runData={runData}
              debateMessages={debateMessages}
              currentAgent={currentAgent}
              onNavigateToTab={handleNavigateToTab}
              onExport={handleExport}
            />
          )}

          {/* Mode B: Interactive Agent Graph Topology */}
          {canvasMode === 'graph' && (
            <AgentGraphView
              runData={runData}
              currentAgent={currentAgent}
              onSelectAgent={handleNavigateToTab}
            />
          )}

          {/* Mode C: Kanban TaskBoard */}
          {canvasMode === 'kanban' && (
            <TaskBoardView
              runData={runData}
              currentAgent={currentAgent}
              onNavigateToTab={handleNavigateToTab}
            />
          )}

          {/* Mode D: Deliverables Studio */}
          {canvasMode === 'studio' && (
            viewMode === 'classic' && runData ? (
              <ClassicMemoView runData={runData} onExport={handleExport} />
            ) : (
              <>
                  {/* Deliverable Sub-tabs Navigation */}
                  <div className="canvas-subtabs" style={{ borderBottom: '1px solid var(--border)', paddingBottom: '12px', marginBottom: '20px' }}>
                    <button
                      id="tab-timeline"
                      type="button"
                      className={`btn ${activeTab === 'timeline' ? 'btn-primary' : 'btn-secondary'}`}
                      onClick={() => setActiveTab('timeline')}
                      style={{ fontSize: '0.84rem', padding: '6px 12px' }}
                    >
                      Live Activity
                    </button>
                    <button
                      id="tab-market"
                      type="button"
                      className={`btn ${activeTab === 'market' ? 'btn-primary' : 'btn-secondary'}`}
                      onClick={() => setActiveTab('market')}
                      style={{ fontSize: '0.84rem', padding: '6px 12px' }}
                    >
                      Market Analysis
                    </button>
                    <button
                      id="tab-prd"
                      type="button"
                      className={`btn ${activeTab === 'prd' ? 'btn-primary' : 'btn-secondary'}`}
                      onClick={() => setActiveTab('prd')}
                      style={{ fontSize: '0.84rem', padding: '6px 12px' }}
                    >
                      Product Scoping (PRD)
                    </button>
                    <button
                      id="tab-arch"
                      type="button"
                      className={`btn ${activeTab === 'arch' ? 'btn-primary' : 'btn-secondary'}`}
                      onClick={() => setActiveTab('arch')}
                      style={{ fontSize: '0.84rem', padding: '6px 12px' }}
                    >
                      Architecture & Cloud Cost
                    </button>
                    <button
                      id="tab-pitch"
                      type="button"
                      className={`btn ${activeTab === 'pitch' ? 'btn-primary' : 'btn-secondary'}`}
                      onClick={() => setActiveTab('pitch')}
                      style={{ fontSize: '0.84rem', padding: '6px 12px' }}
                    >
                      Pitch Presentation
                    </button>
                    <button
                      id="tab-debate"
                      type="button"
                      className={`btn ${activeTab === 'debate' ? 'btn-primary' : 'btn-secondary'}`}
                      onClick={() => setActiveTab('debate')}
                      style={{ fontSize: '0.84rem', padding: '6px 12px' }}
                    >
                      Partner Debate Transcript
                    </button>
                  </div>

                  {/* Active Tab Deliverable Panes */}
                  <div>
                    {activeTab === 'timeline' && (
                      <TimelineView
                        status={runData?.status || 'queued'}
                        events={events}
                        totalTokens={runData?.total_tokens || 0}
                        totalCostUsd={runData?.total_cost_usd || 0}
                      />
                    )}

                    {activeTab === 'market' && (
                      <MarketAnalysisView data={runData?.market} />
                    )}

                    {activeTab === 'prd' && (
                      <PRDView data={runData?.prd} />
                    )}

                    {activeTab === 'arch' && (
                      <ArchitectureView data={runData?.architecture} />
                    )}

                    {activeTab === 'pitch' && (
                      <PitchDeckView data={runData?.pitch} />
                    )}

                    {activeTab === 'debate' && (
                      <DebateView
                        messages={debateMessages}
                        scores={runData?.scores}
                      />
                    )}
                  </div>
                </>
              )
            )
          }
        </main>
      </div>

      {/* 4. Bottom Dock: Idea Intake & Execution Bar (Archetypes 1, 3, 4) */}
      <section className="dock-panel">
        <form onSubmit={handleLaunch}>
          <div className="dock-header-row">
            <label htmlFor="idea-input" style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '0.96rem' }}>
              Startup Concept Intake Dock
            </label>
            <span style={{ fontSize: '0.78rem', color: ideaText.length > 500 ? 'var(--danger)' : 'var(--text-muted)' }}>
              {ideaText.length} / 500 characters
            </span>
          </div>

          <textarea
            ref={ideaInputRef}
            id="idea-input"
            className="custom-textarea"
            rows={2}
            value={ideaText}
            onChange={(e) => setIdeaText(e.target.value)}
            placeholder="Describe your startup concept (e.g. An AI tutor for CBSE Class 10 students that personalizes math and science practice)..."
            style={{
              width: '100%',
              background: 'var(--bg-subtle)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-sm)',
              padding: '12px 14px',
              color: 'var(--text-main)',
              fontSize: '0.94rem',
              fontFamily: 'var(--font-body)',
              resize: 'vertical',
              marginBottom: '10px',
              outline: 'none'
            }}
          />

          {/* Quick-fill Benchmark Pills */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', marginBottom: '14px' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Sample ideas:</span>
            {SAMPLE_IDEAS.map((sample, i) => (
              <button
                key={i}
                type="button"
                className="chip-btn"
                onClick={() => setIdeaText(sample.idea)}
                style={{
                  background: 'var(--bg-subtle)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '4px 10px',
                  fontSize: '0.76rem',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                {sample.title}
              </button>
            ))}
          </div>

          {/* Configuration Collapsible Row */}
          <div style={{ marginBottom: '16px' }}>
            <button
              id="btn-toggle-options"
              type="button"
              onClick={() => setShowOptions(!showOptions)}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--primary)',
                fontSize: '0.82rem',
                cursor: 'pointer',
                padding: '2px 0'
              }}
            >
              {showOptions ? '▾ Hide Model and Debate Options' : '▸ Configure Model, Debate Rounds & CEO Threshold'}
            </button>

            {showOptions && (
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                gap: '14px',
                padding: '14px',
                marginTop: '10px',
                background: 'var(--bg-subtle)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border)'
              }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <label htmlFor="model-select" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      Model Engine
                    </label>
                    <button
                      type="button"
                      onClick={() => fetchModelCatalog(true)}
                      style={{ background: 'transparent', border: 'none', color: 'var(--cyan)', fontSize: '0.75rem', cursor: 'pointer' }}
                      title="Refresh available models"
                    >
                      {isLoadingModels ? 'Refreshing...' : '🔄 Refresh'}
                    </button>
                  </div>
                  <select
                    id="model-select"
                    value={modelOverride}
                    onChange={(e) => setModelOverride(e.target.value)}
                    style={{
                      width: '100%',
                      background: 'var(--bg-surface)',
                      color: 'var(--text-main)',
                      border: '1px solid var(--border)',
                      padding: '7px 10px',
                      borderRadius: 'var(--radius-sm)',
                      outline: 'none',
                      fontSize: '0.84rem'
                    }}
                  >
                    {modelCatalog ? (
                      <>
                        {((modelCatalog.openrouter_free || (modelCatalog as any).free_openrouter || []) as any[]).length > 0 && (
                          <optgroup label="🟢 OpenRouter Free Models">
                            {((modelCatalog.openrouter_free || (modelCatalog as any).free_openrouter) as any[]).map((m: any) => {
                              const val = m.id.startsWith('openrouter/') ? m.id : `openrouter/${m.id}`;
                              return (
                                <option key={m.id} value={val}>
                                  {m.name || m.id} ({m.pricing_description || 'Free'})
                                </option>
                              );
                            })}
                          </optgroup>
                        )}
                        {((modelCatalog.ollama_local || (modelCatalog as any).local_ollama || []) as any[]).length > 0 && (
                          <optgroup label="⚡ Local Ollama Engines">
                            {((modelCatalog.ollama_local || (modelCatalog as any).local_ollama) as any[]).map((m: any) => {
                              const val = m.id.startsWith('ollama:') ? m.id : `ollama:${m.id}`;
                              return (
                                <option key={m.id} value={val}>
                                  {m.name || m.id} {m.size_bytes ? `(${Math.round(m.size_bytes / 1e9 * 10) / 10}GB)` : m.size ? `(${m.size})` : ''}
                                </option>
                              );
                            })}
                          </optgroup>
                        )}
                        {modelCatalog.flagship && modelCatalog.flagship.length > 0 && (
                          <optgroup label="💎 Flagship Frontier Models">
                            {modelCatalog.flagship.map((m) => (
                              <option key={m.id} value={m.provider === 'openrouter' && !m.id.startsWith('openrouter/') ? `openrouter/${m.id}` : m.id}>
                                {m.name} ({m.provider})
                              </option>
                            ))}
                          </optgroup>
                        )}
                      </>
                    ) : (
                      <>
                        <optgroup label="Local Ollama">
                          <option value="ollama:qwen2.5-coder:1.5b">Local Ollama: qwen2.5-coder:1.5b (Fast)</option>
                          <option value="ollama:qwen3:4b">Local Ollama: qwen3:4b (Free)</option>
                        </optgroup>
                        <optgroup label="OpenRouter Free">
                          <option value="openrouter/meta-llama/llama-3.3-70b-instruct:free">OpenRouter: Llama-3.3-70B (Free)</option>
                          <option value="openrouter/google/gemini-2.0-flash-exp:free">OpenRouter: Gemini 2.0 Flash (Free)</option>
                        </optgroup>
                      </>
                    )}
                  </select>
                </div>

                <div>
                  <label htmlFor="debate-rounds" style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                    Peer Debate Protocol
                  </label>
                  <select
                    id="debate-rounds"
                    value={debateRounds}
                    onChange={(e) => setDebateRounds(Number(e.target.value))}
                    style={{
                      width: '100%',
                      background: 'var(--bg-surface)',
                      color: 'var(--text-main)',
                      border: '1px solid var(--border)',
                      padding: '7px 10px',
                      borderRadius: 'var(--radius-sm)',
                      outline: 'none',
                      fontSize: '0.84rem'
                    }}
                  >
                    <option value={2}>2 rounds (Triangular peer debate)</option>
                    <option value={1}>1 round (Critique and rebuttal)</option>
                    <option value={0}>0 rounds (Linear flow without debate)</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="ceo-threshold" style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                    CEO Quality Threshold
                  </label>
                  <input
                    id="ceo-threshold"
                    type="number"
                    step="0.5"
                    min="1.0"
                    max="10.0"
                    value={scoreThreshold}
                    onChange={(e) => setScoreThreshold(Number(e.target.value))}
                    style={{
                      width: '100%',
                      background: 'var(--bg-surface)',
                      color: 'var(--text-main)',
                      border: '1px solid var(--border)',
                      padding: '7px 10px',
                      borderRadius: 'var(--radius-sm)',
                      outline: 'none',
                      fontSize: '0.84rem'
                    }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Action Row */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
            {runData?.status === 'running' && (
              <button
                id="btn-cancel-run"
                type="button"
                className="btn btn-secondary"
                onClick={handleCancel}
                style={{ color: 'var(--danger)', borderColor: 'rgba(239, 68, 68, 0.4)' }}
              >
                Stop Pipeline
              </button>
            )}

            <button
              id="btn-launch-run"
              type="submit"
              className="btn btn-primary"
              disabled={!ideaText.trim() || isLaunching || runData?.status === 'running'}
              style={{ padding: '9px 24px', fontSize: '0.92rem', fontWeight: 600 }}
            >
              {isLaunching ? (
                <>
                  <span className="spinner" />
                  <span>Launching Co-Founders...</span>
                </>
              ) : (
                <span>⚡ Start Co-Founder Pipeline</span>
              )}
            </button>
          </div>
        </form>
      </section>

      {/* Past Runs Drawer Modal */}
      {showHistory && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          background: 'rgba(0, 0, 0, 0.65)',
          backdropFilter: 'blur(6px)',
          zIndex: 9999,
          display: 'flex',
          justifyContent: 'flex-end'
        }}>
          <div style={{
            width: '100%',
            maxWidth: '460px',
            height: '100%',
            background: 'var(--bg-subtle)',
            borderLeft: '1px solid var(--border)',
            padding: '24px',
            display: 'flex',
            flexDirection: 'column'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ fontFamily: 'var(--font-display)', color: 'var(--text-main)', fontSize: '1.15rem', fontWeight: 600 }}>
                Run history
              </h3>
              <button
                id="btn-close-history"
                type="button"
                onClick={() => setShowHistory(false)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-muted)',
                  fontSize: '1.2rem',
                  cursor: 'pointer'
                }}
              >
                ✕
              </button>
            </div>

            <div style={{ flexGrow: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {loadingHistory ? (
                <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '32px' }}>Loading historical runs...</div>
              ) : pastRuns.length === 0 ? (
                <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '32px' }}>No runs recorded yet.</div>
              ) : (
                pastRuns.map((r) => (
                  <div
                    key={r.run_id}
                    onClick={() => {
                      loadRunDetail(r.run_id);
                      setShowHistory(false);
                    }}
                    style={{
                      background: 'var(--bg-surface)',
                      border: '1px solid var(--border)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '14px',
                      cursor: 'pointer',
                      transition: 'border-color 0.15s ease'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = 'var(--border-focus)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = 'var(--border)';
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <span className={`badge ${
                        r.status === 'completed'
                          ? 'badge-success'
                          : r.status === 'running'
                          ? 'badge-primary'
                          : r.status === 'failed'
                          ? 'badge-danger'
                          : 'badge-warning'
                      }`} style={{ fontSize: '0.74rem' }}>
                        {r.status === 'completed' ? 'Completed' : r.status === 'running' ? 'In progress' : r.status === 'failed' ? 'Failed' : r.status}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {r.run_id.slice(0, 8)}
                      </span>
                    </div>

                    <div style={{
                      fontWeight: 600,
                      color: 'var(--text-main)',
                      fontSize: '0.88rem',
                      marginBottom: '8px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical'
                    }}>
                      {r.idea}
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      <span>Tokens: {r.total_tokens?.toLocaleString() || 0}</span>
                      <span>Cost: ${r.total_cost_usd?.toFixed(4) || '0.0000'}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
