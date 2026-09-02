export type RiskTolerance = 'Conservative' | 'Moderate' | 'Aggressive';
export type InvestmentHorizon = 'Short-term' | 'Medium-term' | 'Long-term';
export type SignalType = 'BULLISH' | 'NEUTRAL' | 'BEARISH' | 'POSITIVE' | 'NEGATIVE';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';

export interface PortfolioHolding {
  symbol: string;
  company_name: string;
  shares: number;
  avg_cost: number;
  current_price: number;
  value: number;
  sector: string;
  allocation_pct: number;
  profit_loss: number;
  profit_loss_pct: number;
}

export interface UserProfile {
  user_id: string;
  name: string;
  risk_tolerance: RiskTolerance;
  investment_horizon: InvestmentHorizon;
  portfolio_holdings: PortfolioHolding[];
  total_portfolio_value: number;
  risk_score: number;
  watchlist: string[];
  previous_decisions_count: number;
}

export interface MarketSnapshot {
  symbol: string;
  company_name: string;
  sector: string;
  price: number;
  change_amount: number;
  change_percent: number;
  open_price: number;
  high_price: number;
  low_price: number;
  prev_close: number;
  volume: number;
  avg_volume_20d: number;
  rsi_14: number;
  sma_20: number;
  sma_50: number;
  sma_200: number;
  ema_20: number;
  volatility_pct: number;
  volume_anomaly: boolean;
  is_simulated: boolean;
}

export interface DocumentChunk {
  doc_id: string;
  symbol: string;
  title: string;
  document_type: string;
  date: string;
  source: string;
  excerpt: string;
  relevance_score: number;
  why_it_matters: string;
}

export interface TechnicalAgentOutput {
  signal: SignalType;
  confidence: number;
  key_findings: string[];
  evidence: string[];
  risks: string[];
  indicators: Record<string, any>;
}

export interface FundamentalAgentOutput {
  signal: SignalType;
  confidence: number;
  key_findings: string[];
  sources: DocumentChunk[];
  risks: string[];
  metrics: Record<string, any>;
}

export interface SentimentAgentOutput {
  signal: SignalType;
  confidence: number;
  key_findings: string[];
  sources: string[];
  headline_sentiment_score: number;
}

export interface RiskAgentOutput {
  risk_level: RiskLevel;
  portfolio_impact: string;
  recommendation: string;
  confidence: number;
  reasons: string[];
  concentration_warning?: string;
  suggested_position_size: string;
}

export interface AgentStatus {
  agent_name: string;
  status: 'WAITING' | 'RUNNING' | 'COMPLETED' | 'DEGRADED' | 'ERROR';
  latency_ms: number;
  message: string;
}

export interface SignalSummaryItem {
  dimension: string;
  signal: string;
  confidence: number;
}

export interface ReasoningNode {
  step_number: number;
  title: string;
  input_summary: string;
  agent_name: string;
  finding: string;
  confidence: number;
  evidence: string;
}

export interface SynthesizedIntelligence {
  stock_symbol: string;
  company_name: string;
  overall_signal: SignalType;
  overall_confidence: number;
  executive_summary: string;
  signal_matrix: SignalSummaryItem[];
  why_points: string[];
  conflicting_signals: string[];
  personalized_interpretation: string;
  portfolio_impact: string;
  risk_factors: string[];
  citations: DocumentChunk[];
  reasoning_chain: ReasoningNode[];
}

export interface AnalysisSession {
  session_id: string;
  timestamp: string;
  symbol: string;
  user_profile: UserProfile;
  technical_output?: TechnicalAgentOutput;
  fundamental_output?: FundamentalAgentOutput;
  sentiment_output?: SentimentAgentOutput;
  risk_output?: RiskAgentOutput;
  synthesis: SynthesizedIntelligence;
  is_degraded: boolean;
  degraded_reason?: string;
  agent_statuses: AgentStatus[];
}

export interface PerformanceMetric {
  session_id: string;
  timestamp: string;
  symbol: string;
  total_latency_ms: number;
  agent_latencies: Record<string, number>;
  signal_accuracy_pct: number;
  portfolio_risk_concentration_score: number;
}

export interface DemoScenarioResponse {
  symbol: string;
  conservative_analysis: AnalysisSession;
  aggressive_analysis: AnalysisSession;
  demo_summary: string;
}

// -------------------------------------------------------------
// Web-Slinger Research Pipeline Types
// -------------------------------------------------------------

export interface ResearchRequest {
  asset: string;
  investor_id: string;
  horizon_days: number;
}

export interface ModuleResult {
  module: string;
  status: 'SUCCESS' | 'PARTIAL' | 'FAILED' | 'DEGRADED' | 'UNAVAILABLE';
  message: string;
  payload?: any;
}

export interface ResearchHealth {
  component: string;
  status: 'SUCCESS' | 'PARTIAL' | 'FAILED';
  detail: string;
}

export interface Thesis {
  direction: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  confidence: number;
  horizon_days: number;
  statement: string;
  catalysts: any[];
  risks: any[];
}

export interface Decision {
  action: 'BUY' | 'ACCUMULATE' | 'HOLD' | 'REDUCE' | 'SELL';
  conviction: number;
  headline: string;
  rationale: string[];
}

export interface Scenario {
  name: string;
  probability: number;
  price_target: number;
  return_pct: number;
  conditions: string[];
}

export interface ActionImpact {
  action: string;
  size_pct: number;
  new_position_weight: number;
  new_sector_weight: number;
  new_concentration_hhi: number;
  cash_after: number;
  breaches: string[];
  note: string;
}

export interface Personalization {
  interpretation: string;
  fit: number;
  constraint_hits: string[];
  tone_notes: string[];
}

export interface ResearchState {
  request: ResearchRequest;
  trace: ModuleResult[];
  health: ResearchHealth[];
  thesis?: Thesis;
  decision?: Decision;
  scenarios?: Scenario[];
  action_impacts?: ActionImpact[];
  personalization?: Personalization;
  metrics?: { label: string; value: number; unit: string }[];
}
