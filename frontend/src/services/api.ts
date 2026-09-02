import type {
  UserProfile, MarketSnapshot, DocumentChunk, AnalysisSession,
  PerformanceMetric
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD ? '/api' : 'http://localhost:8080/api');

export class ApiService {
  static async checkHealth(): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE_URL}/health`);
      return res.ok;
    } catch {
      return false;
    }
  }

  static async getProfile(profileId: string = 'conservative'): Promise<UserProfile> {
    const res = await fetch(`${API_BASE_URL}/profile/${profileId}`);
    if (!res.ok) throw new Error('Failed to fetch user profile');
    return res.json();
  }

  static async updateProfile(profile: UserProfile): Promise<UserProfile> {
    const res = await fetch(`${API_BASE_URL}/profile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profile)
    });
    if (!res.ok) throw new Error('Failed to update profile');
    return res.json();
  }

  static async getMarketData(symbol: string, simulateFailure: boolean = false): Promise<{ snapshot: MarketSnapshot; historical_chart: any[] }> {
    const res = await fetch(`${API_BASE_URL}/market/${symbol}?simulate_failure=${simulateFailure}`);
    if (!res.ok) throw new Error(`Failed to fetch market data for ${symbol}`);
    return res.json();
  }

  static async searchDocuments(symbol: string, simulateFailure: boolean = false): Promise<{ count: number; documents: DocumentChunk[] }> {
    const res = await fetch(`${API_BASE_URL}/documents/${symbol}?simulate_failure=${simulateFailure}`);
    if (!res.ok) throw new Error(`Failed to fetch document corpus for ${symbol}`);
    return res.json();
  }

  static async runAnalysis(
    symbol: string,
    profileId: string = 'conservative',
    simulateDataFailure: boolean = false
  ): Promise<{ session: AnalysisSession; performance: PerformanceMetric }> {
    const res = await fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        symbol,
        profile_id: profileId,
        simulate_data_failure: simulateDataFailure
      })
    });
    if (!res.ok) throw new Error('Multi-agent analysis failed');
    return res.json();
  }

  static async getHistory(): Promise<{ count: number; sessions: AnalysisSession[] }> {
    const res = await fetch(`${API_BASE_URL}/history`);
    if (!res.ok) throw new Error('Failed to fetch session history');
    return res.json();
  }

  static async getPerformance(): Promise<{ total_sessions_logged: number; avg_latency_ms: number; avg_signal_accuracy_pct: number; metrics: PerformanceMetric[] }> {
    const res = await fetch(`${API_BASE_URL}/performance`);
    if (!res.ok) throw new Error('Failed to fetch performance metrics');
    return res.json();
  }

  // -------------------------------------------------------------
  // Web-Slinger Research Pipeline APIs
  // -------------------------------------------------------------

  static async runResearch(asset: string, investorId: string, horizonDays: number = 90): Promise<import('../types').ResearchState> {
    const res = await fetch(`${API_BASE_URL}/research`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        asset,
        investor_id: investorId,
        horizon_days: horizonDays
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail?.message || 'Research pipeline failed');
    return data;
  }

  static async getResearchRuns(limit: number = 25): Promise<any[]> {
    const res = await fetch(`${API_BASE_URL}/research/runs?limit=${limit}`);
    if (!res.ok) throw new Error('Failed to fetch research runs');
    return res.json();
  }

  static async getResearchHistory(asset: string, limit: number = 20): Promise<any[]> {
    const res = await fetch(`${API_BASE_URL}/research/history/${asset}?limit=${limit}`);
    if (!res.ok) throw new Error(`Failed to fetch history for ${asset}`);
    return res.json();
  }

  static async getPriceSeries(asset: string, days: number = 180): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/price/${asset}?days=${days}`);
    if (!res.ok) throw new Error(`Failed to fetch price series for ${asset}`);
    return res.json();
  }

}
