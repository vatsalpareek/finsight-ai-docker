import React, { useState, useEffect } from 'react';
import { Shield, TrendingUp, RefreshCw, Users } from 'lucide-react';
import type { AnalysisSession } from '../types';
import { ApiService } from '../services/api';

interface PersonalizationComparisonProps {
  onSelectStock?: (symbol: string) => void;
}

export const PersonalizationComparison: React.FC<PersonalizationComparisonProps> = () => {
  const [selectedStock, setSelectedStock] = useState('RELIANCE');
  const [isLoading, setIsLoading] = useState(false);
  const [conservativeSession, setConservativeSession] = useState<AnalysisSession | null>(null);
  const [aggressiveSession, setAggressiveSession] = useState<AnalysisSession | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    runComparison(selectedStock);
  }, [selectedStock]);

  const runComparison = async (symbol: string) => {
    setIsLoading(true);
    setError(null);
    setConservativeSession(null);
    setAggressiveSession(null);
    try {
      // Run both profiles in parallel using the real /api/analyze endpoint
      const [consResult, aggResult] = await Promise.all([
        ApiService.runAnalysis(symbol, 'conservative', false),
        ApiService.runAnalysis(symbol, 'aggressive', false),
      ]);
      setConservativeSession(consResult.session);
      setAggressiveSession(aggResult.session);
    } catch (err) {
      setError('Failed to run comparison analysis. Ensure the backend is running.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const getSignalColor = (signal: string) => {
    if (signal === 'BULLISH' || signal === 'POSITIVE') return 'text-emerald-400';
    if (signal === 'BEARISH' || signal === 'NEGATIVE') return 'text-rose-400';
    return 'text-amber-400';
  };

  return (
    <div className="space-y-6">
      
      {/* Title Banner */}
      <div className="glass-panel rounded-2xl p-6 border-blue-500/40 bg-gradient-to-r from-blue-950/60 via-dark-900 to-indigo-950/60 space-y-3">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 text-xs font-mono border border-blue-500/20 font-bold mb-2">
              <Users className="w-3.5 h-3.5" />
              <span>PROFILE COMPARISON — LIVE AI ANALYSIS</span>
            </div>
            <h2 className="text-2xl font-extrabold text-white">
              Same Market Data → Different Personalized Output
            </h2>
            <p className="text-xs text-slate-300 max-w-3xl mt-1">
              Runs identical technical, fundamental RAG, and sentiment analysis — then tailors final advice to each investor's risk profile and portfolio.
            </p>
          </div>

          {/* Stock Selector */}
          <div className="flex items-center gap-2 bg-dark-950 p-2 rounded-xl border border-dark-700">
            <span className="text-xs text-slate-400 font-mono">Stock:</span>
            {['RELIANCE', 'TCS', 'INFY', 'SBIN'].map((sym) => (
              <button
                key={sym}
                onClick={() => setSelectedStock(sym)}
                className={`px-3 py-1 rounded-lg text-xs font-mono font-bold transition-all ${
                  selectedStock === sym ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                {sym}
              </button>
            ))}
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="h-64 flex flex-col items-center justify-center text-slate-400 font-mono space-y-3 glass-panel rounded-2xl">
          <RefreshCw className="w-8 h-8 animate-spin text-cyan-400" />
          <p className="text-sm">Running Dual-Profile AI Analysis for {selectedStock}...</p>
          <p className="text-xs text-slate-500">Both Conservative and Aggressive agents running in parallel</p>
        </div>
      ) : error ? (
        <div className="terminal-card p-8 text-center text-rose-400 font-mono text-sm space-y-2">
          <p>{error}</p>
        </div>
      ) : conservativeSession && aggressiveSession ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* CONSERVATIVE */}
          <div className="terminal-card border-blue-500/30 space-y-4 bg-gradient-to-b from-dark-900 via-dark-900 to-blue-950/20">
            <div className="flex items-center justify-between border-b border-dark-700 pb-3">
              <div className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-blue-400" />
                <div>
                  <h3 className="font-extrabold text-white text-base">ARJUN SHARMA: CONSERVATIVE</h3>
                  <p className="text-xs text-slate-400 font-mono">Low Risk Tolerance • Long-Term Horizon</p>
                </div>
              </div>
              <span className={`px-2.5 py-1 rounded-md text-xs font-mono font-bold border ${
                conservativeSession.synthesis.overall_signal === 'BULLISH' 
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                  : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
              }`}>
                {conservativeSession.synthesis.overall_signal} ({conservativeSession.synthesis.overall_confidence}%)
              </span>
            </div>

            {/* Signal Matrix */}
            <div className="p-3 rounded-xl bg-dark-950 border border-dark-800 space-y-1">
              <span className="text-[10px] font-mono text-slate-500 uppercase">Market Signals (Live Data)</span>
              <div className="flex flex-wrap gap-2 pt-1">
                {conservativeSession.synthesis.signal_matrix.map((item) => (
                  <span key={item.dimension} className="text-xs font-mono">
                    <span className="text-slate-400">{item.dimension}: </span>
                    <strong className={getSignalColor(item.signal)}>{item.signal} ({item.confidence}%)</strong>
                  </span>
                ))}
              </div>
            </div>

            {/* Recommendation */}
            <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 space-y-2">
              <span className="text-xs font-mono font-bold text-amber-300 uppercase block">Personalized Recommendation</span>
              <p className="text-sm font-bold text-amber-200 font-mono">
                {conservativeSession.risk_output?.recommendation}
              </p>
              <p className="text-xs text-slate-300 font-sans leading-relaxed pt-1">
                {conservativeSession.synthesis.personalized_interpretation}
              </p>
            </div>

            <div className="text-xs font-mono text-slate-400 space-y-1">
              <p>• Sizing: <strong className="text-white">{conservativeSession.risk_output?.suggested_position_size}</strong></p>
              <p>• Portfolio Impact: <strong className="text-slate-300">{conservativeSession.risk_output?.portfolio_impact}</strong></p>
              <p>• Executive Summary: <span className="text-slate-300">{conservativeSession.synthesis.executive_summary}</span></p>
            </div>
          </div>

          {/* AGGRESSIVE */}
          <div className="terminal-card border-emerald-500/30 space-y-4 bg-gradient-to-b from-dark-900 via-dark-900 to-emerald-950/20">
            <div className="flex items-center justify-between border-b border-dark-700 pb-3">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-emerald-400" />
                <div>
                  <h3 className="font-extrabold text-white text-base">PRIYA PATEL: AGGRESSIVE</h3>
                  <p className="text-xs text-slate-400 font-mono">High Volatility Tolerance • Short-Term Horizon</p>
                </div>
              </div>
              <span className={`px-2.5 py-1 rounded-md text-xs font-mono font-bold border ${
                aggressiveSession.synthesis.overall_signal === 'BULLISH'
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                  : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
              }`}>
                {aggressiveSession.synthesis.overall_signal} ({aggressiveSession.synthesis.overall_confidence}%)
              </span>
            </div>

            {/* Signal Matrix */}
            <div className="p-3 rounded-xl bg-dark-950 border border-dark-800 space-y-1">
              <span className="text-[10px] font-mono text-slate-500 uppercase">Market Signals (Live Data)</span>
              <div className="flex flex-wrap gap-2 pt-1">
                {aggressiveSession.synthesis.signal_matrix.map((item) => (
                  <span key={item.dimension} className="text-xs font-mono">
                    <span className="text-slate-400">{item.dimension}: </span>
                    <strong className={getSignalColor(item.signal)}>{item.signal} ({item.confidence}%)</strong>
                  </span>
                ))}
              </div>
            </div>

            {/* Recommendation */}
            <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 space-y-2">
              <span className="text-xs font-mono font-bold text-emerald-300 uppercase block">Personalized Recommendation</span>
              <p className="text-sm font-bold text-emerald-300 font-mono">
                {aggressiveSession.risk_output?.recommendation}
              </p>
              <p className="text-xs text-slate-300 font-sans leading-relaxed pt-1">
                {aggressiveSession.synthesis.personalized_interpretation}
              </p>
            </div>

            <div className="text-xs font-mono text-slate-400 space-y-1">
              <p>• Sizing: <strong className="text-emerald-400">{aggressiveSession.risk_output?.suggested_position_size}</strong></p>
              <p>• Portfolio Impact: <strong className="text-slate-300">{aggressiveSession.risk_output?.portfolio_impact}</strong></p>
              <p>• Executive Summary: <span className="text-slate-300">{aggressiveSession.synthesis.executive_summary}</span></p>
            </div>
          </div>

        </div>
      ) : null}

    </div>
  );
};
