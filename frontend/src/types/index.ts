export interface MarketMetric {
  value: string;
  unit?: string;
  estimated?: boolean;
  source_url?: string;
  notes?: string;
}

export interface CompetitorItem {
  name: string;
  description: string;
  strengths: string[];
  weaknesses: string[];
  url?: string;
}

export interface MarketAnalystOutput {
  tam: MarketMetric;
  sam: MarketMetric;
  som: MarketMetric;
  competitors: CompetitorItem[];
  trends: string[];
  risks: string[];
  sources: string[];
}

export interface Persona {
  name: string;
  role: string;
  pain_points: string[];
  goals: string[];
}

export interface FeatureItem {
  name: string;
  priority: 'P0' | 'P1' | 'P2';
  description?: string;
}

export interface ProductManagerOutput {
  personas: Persona[];
  problem_statement: string;
  features: FeatureItem[];
  mvp_scope: string;
  user_stories: string[];
  success_metrics: string[];
}

export interface StackChoice {
  technology: string;
  category: string;
  justification: string;
}

export interface ArchitectureComponent {
  name: string;
  responsibility: string;
  technologies: string[];
}

export interface MonthlyCostEstimate {
  total_usd: number;
  breakdown: Record<string, number>;
  assumptions: string[];
}

export interface TechArchitectOutput {
  stack: StackChoice[];
  components: ArchitectureComponent[];
  diagram_mermaid: string;
  data_model: string;
  scalability_notes: string;
  monthly_cost_estimate: MonthlyCostEstimate;
  risks: string[];
}

export interface PitchSlide {
  slide_number: number;
  title: string;
  bullets: string[];
  speaker_notes: string;
}

export interface PitchWriterOutput {
  slides: PitchSlide[];
}

export interface RunDetail {
  run_id: string;
  idea: string;
  status: 'queued' | 'running' | 'awaiting_approval' | 'completed' | 'failed' | 'cancelled' | 'needs_review' | 'budget_exceeded';
  market?: MarketAnalystOutput | null;
  prd?: ProductManagerOutput | null;
  architecture?: TechArchitectOutput | null;
  pitch?: PitchWriterOutput | null;
  scores: Record<string, number[]>;
  created_at: string;
  completed_at?: string | null;
  debate_messages?: DebateMessage[];
  total_tokens: number;
  total_cost_usd: number;
  fact_check?: any | null;
  telemetry?: any | null;
  options?: any;
}

export interface DebateMessage {
  round: number;
  from_agent: string;
  to_agent: string;
  content: {
    issues?: string[];
    suggestions?: string[];
    accepted?: any[];
    rejected?: any[];
    output_updated?: boolean;
    score?: number;
    pass?: boolean;
    verdict?: string;
    strengths?: string[];
    weaknesses?: string[];
    required_changes?: string[];
    [key: string]: any;
  };
  created_at?: string;
}

export interface CEOCriticReview {
  target_agent: string;
  version: number;
  score: number;
  strengths: string[];
  weaknesses: string[];
  required_changes: string[];
  pass: boolean;
}

export interface WebSocketEvent {
  type: string;
  agent?: string;
  target?: string;
  score?: number;
  pass?: boolean;
  text?: string;
  output?: any;
  content?: any;
  from?: string;
  to?: string;
  run_id?: string;
  error?: string;
  ts?: string;
}

