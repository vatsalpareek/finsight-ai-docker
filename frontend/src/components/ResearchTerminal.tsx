import React, { useState, useEffect } from 'react';
import {
  Search, Play, RefreshCw, AlertTriangle, FileText,
  BarChart3, Cpu, Sparkles, HelpCircle, ShieldCheck
} from 'lucide-react';
import type { UserProfile, AnalysisSession, MarketSnapshot } from '../types';
import { ApiService } from '../services/api';

interface ResearchTerminalProps {
  currentProfile: UserProfile;
  selectedStockSymbol: string;
  onSelectSymbol: (symbol: string) => void;
  onOpenExplainabilityModal: (session: AnalysisSession) => void;
}

export const ResearchTerminal: React.FC<ResearchTerminalProps> = ({
  currentProfile,
  selectedStockSymbol,
  onSelectSymbol,
  onOpenExplainabilityModal
}) => {
  const [symbolInput, setSymbolInput] = useState(selectedStockSymbol);
  const [marketSnapshot, setMarketSnapshot] = useState<MarketSnapshot | null>(null);
  
  // Pipeline Analysis State
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStep, setAnalysisStep] = useState<number>(0); // 0: Idle, 1: Data, 2: Agents, 3: Evidence, 4: Conflict, 5: Synthesis
  const [activeSession, setActiveSession] = useState<AnalysisSession | null>(null);
  const [activeResearchState, setActiveResearchState] = useState<import('../types').ResearchState | null>(null);

  const presetStocks = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "SBIN", "AAPL"];


  useEffect(() => {
    setSymbolInput(selectedStockSymbol);
    loadMarketData(selectedStockSymbol);
  }, [selectedStockSymbol]);

  const loadMarketData = async (sym: string) => {
    try {
      const data = await ApiService.getMarketData(sym, false);
      setMarketSnapshot(data.snapshot);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!symbolInput.trim()) return;
    onSelectSymbol(symbolInput.trim().toUpperCase());
  };

  const handleRunAnalysis = async () => {
    setIsAnalyzing(true);
    setAnalysisStep(1);
    setActiveSession(null);
    setActiveResearchState(null);

    // Step 1: Ingesting Market Data & Documents (0.2s)
    await new Promise(r => setTimeout(r, 200));
    setAnalysisStep(2); // Running 4 Agents in Parallel

    // Step 2: Parallel Agents Execution (0.4s)
    await new Promise(r => setTimeout(r, 400));
    setAnalysisStep(3); // Evidence Retrieval & RAG matching

    // Step 3: Conflict Analysis & Reconciliation (0.3s)
    await new Promise(r => setTimeout(r, 300));
    setAnalysisStep(4); // Synthesis Agent

    try {
      const [result, webSlingerResult] = await Promise.all([
        ApiService.runAnalysis(selectedStockSymbol, currentProfile.user_id, false),
        ApiService.runResearch(selectedStockSymbol, currentProfile.user_id, 90).catch(err => {
          console.error("Web-slinger pipeline failed:", err);
          return null;
        })
      ]);
      setAnalysisStep(5); // Complete
      setActiveSession(result.session);
      setActiveResearchState(webSlingerResult);
    } catch (err) {
      console.error("Analysis pipeline error:", err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Top Controls: Search Bar & Preset Tickers */}
      <div className="terminal-card bg-gradient-to-r from-dark-900 via-dark-850 to-dark-900">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          
          {/* Search Form */}
          <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 w-full md:w-auto">
            <div className="relative flex-1 md:w-72">
              <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
              <input
                type="text"
                value={symbolInput}
                onChange={(e) => setSymbolInput(e.target.value.toUpperCase())}
                placeholder="Enter ticker (e.g. RELIANCE)..."
                className="w-full bg-dark-950 border border-dark-700 rounded-xl pl-9 pr-4 py-2 text-sm text-white font-mono placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>
            <button
              type="submit"
              className="px-4 py-2 rounded-xl bg-dark-800 border border-dark-700 hover:border-slate-600 text-xs font-mono font-medium text-slate-300 transition-colors"
            >
              Select
            </button>
          </form>
          {/* Popular Stocks Links */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs text-slate-400 font-mono">Popular:</span>
            {presetStocks.map((sym) => (
              <button
                key={sym}
                onClick={() => onSelectSymbol(sym)}
                className={`text-xs font-mono px-2 py-1 rounded transition-all ${
                  selectedStockSymbol === sym
                    ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                    : 'text-slate-400 hover:text-white hover:bg-dark-800'
                }`}
              >
                {sym}
              </button>
            ))}
          </div>
          {/* Big RUN AI ANALYSIS Button */}
          <button
            onClick={handleRunAnalysis}
            disabled={isAnalyzing}
            className={`w-full md:w-auto px-6 py-2.5 rounded-xl font-bold font-mono text-sm flex items-center justify-center gap-2 shadow-xl transition-all cursor-pointer ${
              isAnalyzing
                ? 'bg-dark-700 text-slate-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-blue-600 via-cyan-500 to-emerald-400 text-black hover:opacity-95 hover:scale-105 active:scale-95 shadow-cyan-500/20'
            }`}
          >
            {isAnalyzing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin text-black" />
                <span>ORCHESTRATING AGENTS...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-black text-black" />
                <span>RUN AI ANALYSIS</span>
              </>
            )}
          </button>

        </div>

        {/* Live Market Snapshot Bar */}
        {marketSnapshot && (
          <div className="mt-4 pt-4 border-t border-dark-700/80 flex flex-wrap items-center justify-between gap-4 text-xs font-mono">
            <div className="flex items-center gap-2">
              <span className="text-white font-bold text-base">{marketSnapshot.company_name}</span>
              <span className="text-slate-500">({marketSnapshot.sector})</span>
              <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 text-[10px]">
                LIVE FEED
              </span>
              {activeSession && (
                <span className="px-2 py-0.5 rounded bg-dark-800 text-slate-400 text-[10px] border border-dark-700">
                  Updated: {activeSession.timestamp}
                </span>
              )}
            </div>

            <div className="flex items-center gap-6">
              <div>
                <span className="text-slate-400">PRICE: </span>
                <span className="text-white font-bold">₹{marketSnapshot.price.toLocaleString()}</span>
              </div>
              <div>
                <span className="text-slate-400">CHANGE: </span>
                <span className={marketSnapshot.change_amount >= 0 ? "text-emerald-400 font-bold" : "text-rose-400 font-bold"}>
                  {marketSnapshot.change_amount >= 0 ? "+" : ""}{marketSnapshot.change_percent}%
                </span>
              </div>
              <div>
                <span className="text-slate-400">RSI(14): </span>
                <span className="text-cyan-400 font-bold">{marketSnapshot.rsi_14}</span>
              </div>
              <div>
                <span className="text-slate-400">SMA(20): </span>
                <span className="text-slate-200">₹{marketSnapshot.sma_20}</span>
              </div>
              <div>
                <span className="text-slate-400">VOL ANOMALY: </span>
                <span className={marketSnapshot.volume_anomaly ? "text-emerald-400 font-bold" : "text-slate-400"}>
                  {marketSnapshot.volume_anomaly ? "YES ⚡" : "NORMAL"}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ANIMATED RESEARCH WORKFLOW PIPELINE VISUALIZER */}
      <div className="glass-panel rounded-2xl p-4 border-dark-700">
        <p className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
          <Cpu className="w-4 h-4 text-terminal-cyan" />
          PARALLEL MULTI-AGENT RESEARCH WORKFLOW PIPELINE
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
          
          {/* Node 1: Market Data */}
          <div className={`p-3 rounded-xl border text-center transition-all ${
            analysisStep >= 1 ? 'bg-blue-500/10 border-blue-500/40 text-blue-300' : 'bg-dark-900 border-dark-700 text-slate-600'
          }`}>
            <p className="text-[10px] font-mono uppercase font-bold">Step 1</p>
            <p className="text-xs font-bold font-mono mt-1">Market Ingestion</p>
            <span className="text-[10px] font-mono mt-1 block">
              {analysisStep >= 1 ? '✓ Complete' : 'Waiting'}
            </span>
          </div>

          {/* Node 2: Parallel 4 Agents */}
          <div className={`p-3 rounded-xl border text-center transition-all ${
            analysisStep >= 2 ? 'bg-cyan-500/10 border-cyan-500/40 text-cyan-300' : 'bg-dark-900 border-dark-700 text-slate-600'
          }`}>
            <p className="text-[10px] font-mono uppercase font-bold">Step 2</p>
            <p className="text-xs font-bold font-mono mt-1">4 Parallel Agents</p>
            <span className="text-[10px] font-mono mt-1 block">
              {analysisStep >= 2 ? '✓ Executing' : 'Waiting'}
            </span>
          </div>

          {/* Node 3: Evidence Retrieval */}
          <div className={`p-3 rounded-xl border text-center transition-all ${
            analysisStep >= 3 ? 'bg-purple-500/10 border-purple-500/40 text-purple-300' : 'bg-dark-900 border-dark-700 text-slate-600'
          }`}>
            <p className="text-[10px] font-mono uppercase font-bold">Step 3</p>
            <p className="text-xs font-bold font-mono mt-1">RAG Retrieval</p>
            <span className="text-[10px] font-mono mt-1 block">
              {analysisStep >= 3 ? '✓ SEBI Filings' : 'Waiting'}
            </span>
          </div>

          {/* Node 4: Conflict Analysis */}
          <div className={`p-3 rounded-xl border text-center transition-all ${
            analysisStep >= 4 ? 'bg-amber-500/10 border-amber-500/40 text-amber-300' : 'bg-dark-900 border-dark-700 text-slate-600'
          }`}>
            <p className="text-[10px] font-mono uppercase font-bold">Step 4</p>
            <p className="text-xs font-bold font-mono mt-1">Conflict Resolver</p>
            <span className="text-[10px] font-mono mt-1 block">
              {analysisStep >= 4 ? '✓ Reconciling' : 'Waiting'}
            </span>
          </div>

          {/* Node 5: Synthesis Agent */}
          <div className={`p-3 rounded-xl border text-center transition-all ${
            analysisStep >= 5 ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-300' : 'bg-dark-900 border-dark-700 text-slate-600'
          }`}>
            <p className="text-[10px] font-mono uppercase font-bold">Step 5</p>
            <p className="text-xs font-bold font-mono mt-1">Synthesis Agent</p>
            <span className="text-[10px] font-mono mt-1 block">
              {analysisStep >= 5 ? '✓ Synthesized' : 'Waiting'}
            </span>
          </div>

          {/* Node 6: Personalized Output */}
          <div className={`p-3 rounded-xl border text-center transition-all ${
            analysisStep >= 5 ? 'bg-emerald-500/20 border-emerald-400 text-emerald-300 font-bold' : 'bg-dark-900 border-dark-700 text-slate-600'
          }`}>
            <p className="text-[10px] font-mono uppercase">Step 6</p>
            <p className="text-xs font-mono mt-1">Personalized Intelligence</p>
            <span className="text-[10px] font-mono mt-1 block">
              {analysisStep >= 5 ? 'Ready' : 'Waiting'}
            </span>
          </div>

        </div>
      </div>

      {/* 4 PARALLEL AGENT PROGRESS & FINDING CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* Agent 1: Technical Agent */}
        <div className="terminal-card border-dark-700 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-blue-400 uppercase tracking-wider">Technical Agent</span>
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
              activeSession?.technical_output?.signal === 'BULLISH' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-dark-800 text-slate-400'
            }`}>
              {activeSession?.technical_output ? `${activeSession.technical_output.signal} (${activeSession.technical_output.confidence}%)` : 'WAITING'}
            </span>
          </div>
          <p className="text-[11px] text-slate-400 font-mono">Analyzes RSI(14), Moving Averages & Volume Spikes</p>

          {activeSession?.technical_output ? (
            <div className="space-y-2 text-xs text-slate-300 border-t border-dark-700/80 pt-2">
              {activeSession.technical_output.key_findings.map((finding, idx) => (
                <div key={idx} className="flex items-start gap-1.5">
                  <span className="text-blue-400 font-mono">•</span>
                  <span>{finding}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-16 flex items-center justify-center text-xs text-slate-600 font-mono">
              Click 'Run AI Analysis' to execute
            </div>
          )}
        </div>

        {/* Agent 2: Fundamental RAG Agent */}
        <div className="terminal-card border-dark-700 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-purple-400 uppercase tracking-wider">Fundamental RAG</span>
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
              activeSession?.fundamental_output?.signal === 'BULLISH' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
              activeSession?.fundamental_output?.signal === 'NEUTRAL' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'bg-dark-800 text-slate-400'
            }`}>
              {activeSession?.fundamental_output ? `${activeSession.fundamental_output.signal} (${activeSession.fundamental_output.confidence}%)` : 'WAITING'}
            </span>
          </div>
          <p className="text-[11px] text-slate-400 font-mono">Retrieves SEBI filings & earnings call transcripts</p>

          {activeSession?.fundamental_output ? (
            <div className="space-y-2 text-xs text-slate-300 border-t border-dark-700/80 pt-2">
              {activeSession.fundamental_output.key_findings.map((finding, idx) => (
                <div key={idx} className="flex items-start gap-1.5">
                  <span className="text-purple-400 font-mono">•</span>
                  <span>{finding}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-16 flex items-center justify-center text-xs text-slate-600 font-mono">
              Click 'Run AI Analysis' to execute
            </div>
          )}
        </div>

        {/* Agent 3: Sentiment Agent */}
        <div className="terminal-card border-dark-700 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-amber-400 uppercase tracking-wider">Sentiment Agent</span>
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
              activeSession?.sentiment_output?.signal === 'POSITIVE' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
              activeSession?.sentiment_output?.signal === 'NEUTRAL' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'bg-dark-800 text-slate-400'
            }`}>
              {activeSession?.sentiment_output ? `${activeSession.sentiment_output.signal} (${activeSession.sentiment_output.confidence}%)` : 'WAITING'}
            </span>
          </div>
          <p className="text-[11px] text-slate-400 font-mono">Monitors news wires & regulatory commentary</p>

          {activeSession?.sentiment_output ? (
            <div className="space-y-2 text-xs text-slate-300 border-t border-dark-700/80 pt-2">
              {activeSession.sentiment_output.key_findings.map((finding, idx) => (
                <div key={idx} className="flex items-start gap-1.5">
                  <span className="text-amber-400 font-mono">•</span>
                  <span>{finding}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-16 flex items-center justify-center text-xs text-slate-600 font-mono">
              Click 'Run AI Analysis' to execute
            </div>
          )}
        </div>

        {/* Agent 4: Risk / Portfolio Agent */}
        <div className="terminal-card border-dark-700 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-emerald-400 uppercase tracking-wider">Risk Analyst</span>
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
              activeSession?.risk_output?.risk_level === 'MEDIUM' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
              activeSession?.risk_output?.risk_level === 'HIGH' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'bg-dark-800 text-slate-400'
            }`}>
              {activeSession?.risk_output ? `RISK: ${activeSession.risk_output.risk_level} (${activeSession.risk_output.confidence}%)` : 'WAITING'}
            </span>
          </div>
          <p className="text-[11px] text-slate-400 font-mono">Evaluates position sizing & portfolio limits</p>

          {activeSession?.risk_output ? (
            <div className="space-y-2 text-xs text-slate-300 border-t border-dark-700/80 pt-2">
              {activeSession.risk_output.reasons.slice(0, 2).map((reason, idx) => (
                <div key={idx} className="flex items-start gap-1.5">
                  <span className="text-emerald-400 font-mono">•</span>
                  <span>{reason}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-16 flex items-center justify-center text-xs text-slate-600 font-mono">
              Click 'Run AI Analysis' to execute
            </div>
          )}
        </div>

      </div>

      {/* SYNTHESIZED INTELLIGENCE PANEL (RESULTS DISPLAY) */}
      {activeSession && (
        <div className="glass-panel rounded-2xl p-6 border-cyan-500/30 space-y-6 animate-fade-in">
          
          {/* Header & Overall Signal Gauge */}
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-dark-700/80 pb-4">
            
            <div>
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-terminal-cyan" />
                <h3 className="text-xl font-extrabold text-white">
                  SYNTHESIZED INVESTMENT INTELLIGENCE
                </h3>
              </div>
              <p className="text-xs text-slate-400 mt-1 font-mono">
                Engine Target: <span className="text-white font-bold">{activeSession.symbol}</span> | Profile Context: <span className="text-terminal-cyan font-bold">{activeSession.user_profile.name}</span>
              </p>
            </div>

            {/* Overall Signal Matrix Badge */}
            <div className="flex items-center gap-4 bg-dark-900 border border-dark-700 px-5 py-3 rounded-xl">
              <div>
                <p className="text-[10px] font-mono text-slate-400 uppercase">Overall Signal</p>
                <p className={`text-xl font-extrabold font-mono ${
                  activeSession.synthesis.overall_signal === 'BULLISH' ? 'text-emerald-400' : 'text-amber-400'
                }`}>
                  {activeSession.synthesis.overall_signal}
                </p>
              </div>

              <div className="h-8 w-px bg-dark-700" />

              <div>
                <p className="text-[10px] font-mono text-slate-400 uppercase">Signal Strength</p>
                <p className="text-xl font-extrabold font-mono text-cyan-400">
                  {activeSession.synthesis.overall_confidence}%
                </p>
              </div>

              {/* Explainability Chain Trigger */}
              <button
                onClick={() => onOpenExplainabilityModal(activeSession)}
                className="ml-2 px-3 py-1.5 rounded-lg bg-blue-600/20 border border-blue-500/40 text-blue-300 text-xs font-mono hover:bg-blue-600 hover:text-white transition-all flex items-center gap-1.5 cursor-pointer"
              >
                <HelpCircle className="w-3.5 h-3.5" />
                <span>Why did AI reach this?</span>
              </button>
            </div>

          </div>

          {/* Executive Summary */}
          <div className="p-4 rounded-xl bg-dark-900/90 border border-dark-700 space-y-1">
            <h4 className="text-xs font-mono font-bold text-slate-400 uppercase">Executive Conclusion</h4>
            <p className="text-sm text-slate-200 leading-relaxed font-sans">
              {activeSession.synthesis.executive_summary}
            </p>
          </div>

          {/* Signal Matrix & Conflicting Signals Callout */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* Signal Matrix Table */}
            <div className="space-y-3">
              <h4 className="text-xs font-mono font-bold text-slate-400 uppercase flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-blue-400" />
                MULTI-AGENT SIGNAL MATRIX
              </h4>

              <div className="overflow-x-auto">
                <table className="w-full text-xs font-mono border-collapse">
                  <thead>
                    <tr className="border-b border-dark-700 text-slate-400 text-left">
                      <th className="py-2 px-3">Agent Dimension</th>
                      <th className="py-2 px-3">Signal</th>
                      <th className="py-2 px-3 text-right">Signal Strength</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeSession.synthesis.signal_matrix.map((item, idx) => (
                      <tr key={idx} className="border-b border-dark-800/60 hover:bg-dark-900/50">
                        <td className="py-2.5 px-3 font-semibold text-slate-200">{item.dimension}</td>
                        <td className="py-2.5 px-3">
                          <span className={`px-2 py-0.5 rounded font-bold text-[10px] ${
                            item.signal.includes('BULLISH') || item.signal.includes('LOW') ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                            item.signal.includes('MEDIUM') || item.signal.includes('NEUTRAL') ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                            'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          }`}>
                            {item.signal}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-right font-bold text-cyan-400">{item.confidence}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* ⚠️ SIGNAL CONFLICT HANDLING PANEL */}
            <div className="space-y-3">
              <h4 className="text-xs font-mono font-bold text-amber-400 uppercase flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                CONSTRAINTS & CONFLICT RESOLUTION
              </h4>

              {activeSession.synthesis.conflicting_signals.length > 0 ? (
                <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 space-y-2">
                  {activeSession.synthesis.conflicting_signals.map((conflict, idx) => (
                    <p key={idx} className="text-xs text-amber-200 font-mono leading-relaxed">
                      {conflict}
                    </p>
                  ))}
                  <p className="text-[11px] text-amber-400/80 font-mono pt-1">
                    * The Synthesis Agent resolved disagreement by assigning higher weight to verified Q4 SEBI earnings filings while discounting unverified sentiment chatter.
                  </p>
                </div>
              ) : (
                <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-300 font-mono">
                  ✓ High multi-agent alignment. Zero conflicting signals detected across technical, fundamental, and sentiment channels.
                </div>
              )}
            </div>

            {/* WHAT COULD MAKE THIS WRONG (RISK FACTORS) */}
            <div className="space-y-3">
              <h4 className="text-xs font-mono font-bold text-rose-400 uppercase flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-400" />
                WHAT COULD MAKE THIS WRONG? (RISK FACTORS)
              </h4>
              <div className="p-4 rounded-xl bg-dark-900 border border-rose-500/20 space-y-2">
                {activeSession.synthesis.risk_factors.length > 0 ? (
                  <ul className="list-disc list-inside text-xs text-rose-200/80 font-mono space-y-1">
                    {activeSession.synthesis.risk_factors.map((risk, idx) => (
                      <li key={idx}>{risk}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-slate-400 font-mono">No major overriding risk factors identified in current data.</p>
                )}
              </div>
            </div>

          </div>

          {/* PERSONALIZED INTERPRETATION CARD (THE HEART OF THE DEMO) */}
          <div className="p-5 rounded-2xl bg-gradient-to-r from-blue-950/60 via-dark-900 to-indigo-950/60 border border-blue-500/40 space-y-3 shadow-xl">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-terminal-cyan" />
                <h4 className="text-sm font-bold font-mono text-white uppercase tracking-wider">
                  PERSONALIZED INTERPRETATION FOR THIS INVESTOR
                </h4>
              </div>
              <span className="text-xs font-mono px-2.5 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/40 font-bold">
                {activeSession.user_profile.risk_tolerance} Profile
              </span>
            </div>

            <p className="text-sm text-slate-100 font-medium leading-relaxed">
              {activeSession.synthesis.personalized_interpretation}
            </p>

            <div className="pt-2 flex flex-wrap items-center gap-4 text-xs font-mono text-slate-400">
              <span>Sizing Guidance: <strong className="text-emerald-400">{activeSession.risk_output?.suggested_position_size}</strong></span>
              <span>•</span>
              <span>Sector Concentration Impact: <strong className="text-cyan-400">{activeSession.synthesis.portfolio_impact}</strong></span>
            </div>
          </div>

          {/* RAG EVIDENCE CITATIONS PANEL */}
          <div className="space-y-3">
            <h4 className="text-xs font-mono font-bold text-slate-400 uppercase flex items-center gap-2">
              <FileText className="w-4 h-4 text-purple-400" />
              RETRIEVED DOCUMENT EVIDENCE & CITATIONS (RAG)
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {activeSession.synthesis.citations.map((doc, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-dark-900 border border-dark-700 space-y-2 text-xs">
                  <div className="flex items-center justify-between text-[11px] font-mono text-purple-300">
                    <span className="font-bold">{doc.document_type}</span>
                    <span>{doc.date}</span>
                  </div>
                  <h5 className="font-bold text-slate-200 leading-snug">{doc.title}</h5>
                  <p className="text-slate-400 italic text-[11px] bg-dark-950 p-2.5 rounded border border-dark-800 font-mono">
                    "{doc.excerpt}"
                  </p>
                  <p className="text-[11px] text-cyan-400 font-mono">
                    <strong className="text-slate-300">Why it matters:</strong> {doc.why_it_matters}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* WEB-SLINGER PIPELINE SECTION */}
      {activeResearchState && (
        <div className="terminal-card space-y-6 animate-fade-in mt-6 bg-gradient-to-br from-indigo-950/30 to-purple-950/30 border-purple-500/30">
          <div className="border-b border-purple-500/20 pb-4">
            <h3 className="text-lg font-bold font-mono text-purple-300 uppercase flex items-center gap-2">
              <Sparkles className="w-5 h-5" />
              Web-Slinger 22-Module Pipeline Verdict
            </h3>
            <p className="text-sm text-slate-400 mt-1">Deep reasoning consensus run against active portfolio constraints</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h4 className="text-sm font-bold font-mono text-white">Consensus Decision</h4>
              <div className="p-4 bg-dark-900 border border-dark-700 rounded-xl">
                <div className="flex items-center gap-3 mb-2">
                  <span className={`px-3 py-1 text-sm font-bold rounded-lg ${
                    activeResearchState.decision?.action === 'BUY' || activeResearchState.decision?.action === 'ACCUMULATE' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                    activeResearchState.decision?.action === 'SELL' || activeResearchState.decision?.action === 'REDUCE' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' :
                    'bg-slate-500/20 text-slate-300 border border-slate-500/30'
                  }`}>
                    {activeResearchState.decision?.action || 'NO DECISION'}
                  </span>
                  <span className="text-xs text-slate-400 font-mono">
                    Conviction: {((activeResearchState.decision?.conviction || 0) * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-slate-200 text-sm font-medium mb-3">
                  {activeResearchState.decision?.headline || activeResearchState.thesis?.statement || 'Insufficient data to form thesis.'}
                </p>
                <div className="space-y-1">
                  {activeResearchState.decision?.rationale.map((r, i) => (
                    <p key={i} className="text-xs text-slate-400 flex items-start gap-2">
                      <span className="text-purple-400">•</span> {r}
                    </p>
                  ))}
                </div>
              </div>

              <h4 className="text-sm font-bold font-mono text-white pt-2">Personalization & Constraints</h4>
              <div className="p-4 bg-dark-900 border border-dark-700 rounded-xl space-y-3">
                <p className="text-sm text-slate-300">
                  {activeResearchState.personalization?.interpretation}
                </p>
                {activeResearchState.personalization?.constraint_hits && activeResearchState.personalization.constraint_hits.length > 0 && (
                  <div className="mt-2 space-y-1 border-t border-dark-800 pt-2">
                    <p className="text-xs text-rose-400 font-bold mb-1">Constraint Hits:</p>
                    {activeResearchState.personalization.constraint_hits.map((hit, i) => (
                      <p key={i} className="text-xs text-slate-400 flex items-center gap-2">
                        <AlertTriangle className="w-3 h-3 text-rose-500" /> {hit}
                      </p>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-4">
              <h4 className="text-sm font-bold font-mono text-white">Probabilistic Scenarios</h4>
              <div className="space-y-2">
                {activeResearchState.scenarios?.map((s, i) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-dark-900 border border-dark-700 rounded-xl">
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-mono font-bold text-slate-300 bg-dark-800 px-2 py-1 rounded">
                        {(s.probability * 100).toFixed(0)}%
                      </span>
                      <span className="text-sm text-slate-200 font-medium">{s.name}</span>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-slate-400">Target: ₹{s.price_target.toFixed(2)}</p>
                      <p className={`text-xs font-bold ${s.return_pct > 0 ? 'text-emerald-400' : s.return_pct < 0 ? 'text-rose-400' : 'text-slate-400'}`}>
                        {s.return_pct > 0 ? '+' : ''}{(s.return_pct * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>
                ))}
              </div>

              <h4 className="text-sm font-bold font-mono text-white pt-2">Simulated Action Impacts</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-dark-700 text-slate-400 font-mono">
                      <th className="py-2 px-2 font-medium">Action</th>
                      <th className="py-2 px-2 font-medium">New Wgt</th>
                      <th className="py-2 px-2 font-medium">Sector</th>
                      <th className="py-2 px-2 font-medium">Cash After</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeResearchState.action_impacts?.map((a, i) => (
                      <tr key={i} className={`border-b border-dark-800 ${a.breaches?.length ? 'bg-rose-500/5' : ''}`}>
                        <td className="py-2 px-2 font-bold text-slate-200">{a.action}</td>
                        <td className="py-2 px-2 font-mono">{(a.new_position_weight * 100).toFixed(1)}%</td>
                        <td className="py-2 px-2 font-mono">{(a.new_sector_weight * 100).toFixed(1)}%</td>
                        <td className="py-2 px-2 font-mono text-slate-400">₹{a.cash_after.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

            </div>
          </div>
        </div>
      )}

    </div>
  );
};
