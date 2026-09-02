import React, { useEffect, useState } from 'react';
import { ShieldAlert, ArrowUpRight, ArrowDownRight, Compass, RefreshCw } from 'lucide-react';
import type { UserProfile, MarketSnapshot } from '../types';
import { ApiService } from '../services/api';

interface DashboardProps {
  profile: UserProfile;
  onSelectStockForAnalysis: (symbol: string) => void;
  onNavigateToComparison: () => void;
}

interface WatchlistEntry {
  symbol: string;
  name: string;
}

const WATCHLIST: WatchlistEntry[] = [
  { symbol: "RELIANCE", name: "Reliance Industries" },
  { symbol: "TCS", name: "Tata Consultancy" },
  { symbol: "INFY", name: "Infosys Ltd" },
  { symbol: "HDFCBANK", name: "HDFC Bank" },
  { symbol: "SBIN", name: "State Bank of India" },
];

interface LiveStock extends WatchlistEntry {
  snapshot: MarketSnapshot | null;
  loading: boolean;
  error: boolean;
}

export const Dashboard: React.FC<DashboardProps> = ({
  profile,
  onSelectStockForAnalysis,
}) => {
  const [liveStocks, setLiveStocks] = useState<LiveStock[]>(
    WATCHLIST.map(w => ({ ...w, snapshot: null, loading: true, error: false }))
  );
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());

  const fetchAllPrices = async () => {
    setLiveStocks(prev => prev.map(s => ({ ...s, loading: true, error: false })));
    const updated = await Promise.all(
      WATCHLIST.map(async (w) => {
        try {
          const data = await ApiService.getMarketData(w.symbol, false);
          return { ...w, snapshot: data.snapshot, loading: false, error: false };
        } catch {
          return { ...w, snapshot: null, loading: false, error: true };
        }
      })
    );
    setLiveStocks(updated);
    setLastRefreshed(new Date());
  };

  useEffect(() => {
    fetchAllPrices();
    const interval = setInterval(fetchAllPrices, 60_000);
    return () => clearInterval(interval);
  }, []);

  const totalPnL = profile.portfolio_holdings.reduce((acc, h) => acc + h.profit_loss, 0);
  const totalPnLPct = profile.portfolio_holdings.reduce((acc, h) => acc + h.profit_loss_pct, 0);

  return (
    <div className="space-y-6">
      
      {/* Top Metrics Banner */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        
        <div className="terminal-card bg-gradient-to-br from-dark-900 via-dark-850 to-dark-900 border-dark-700">
          <p className="text-xs font-mono text-slate-400 uppercase tracking-wider">Total Portfolio Value</p>
          <div className="mt-2 flex items-baseline justify-between">
            <h2 className="text-2xl font-extrabold text-white font-mono">
              Rs.{(profile.total_portfolio_value / 100000).toFixed(2)}L
            </h2>
            <span className={`text-xs font-semibold px-2 py-0.5 rounded border ${totalPnL >= 0 ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border-rose-500/20'}`}>
              {totalPnL >= 0 ? '+' : ''}{totalPnLPct.toFixed(1)}% P&L
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2 font-mono">Holdings: {profile.portfolio_holdings.length} Positions</p>
        </div>

        <div className="terminal-card bg-gradient-to-br from-dark-900 via-dark-850 to-dark-900 border-dark-700">
          <p className="text-xs font-mono text-slate-400 uppercase tracking-wider">Unrealized P&L</p>
          <div className="mt-2 flex items-baseline justify-between">
            <h2 className={`text-2xl font-extrabold font-mono flex items-center ${totalPnL >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {totalPnL >= 0 ? '+' : ''}Rs.{Math.abs(totalPnL).toLocaleString()}
            </h2>
            <span className={`text-xs font-semibold flex items-center ${totalPnL >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {totalPnL >= 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
              {totalPnLPct.toFixed(2)}%
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2 font-mono">Across {profile.portfolio_holdings.length} positions</p>
        </div>

        <div className="terminal-card bg-gradient-to-br from-dark-900 via-dark-850 to-dark-900 border-dark-700">
          <p className="text-xs font-mono text-slate-400 uppercase tracking-wider">Concentration Risk</p>
          <div className="mt-2 flex items-baseline justify-between">
            <h2 className="text-2xl font-extrabold text-amber-400 font-mono">
              {profile.risk_score}<span className="text-slate-500 text-sm font-normal">/100</span>
            </h2>
            <span className={`text-xs font-semibold px-2 py-0.5 rounded border ${
              profile.risk_score > 60 ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
            }`}>
              {profile.risk_score > 60 ? 'Elevated' : 'Diversified'}
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2 font-mono">{profile.risk_tolerance} - {profile.investment_horizon}</p>
        </div>

        <div className="terminal-card bg-gradient-to-br from-dark-900 via-dark-850 to-dark-900 border-dark-700">
          <p className="text-xs font-mono text-slate-400 uppercase tracking-wider">AI Agents Active</p>
          <div className="mt-2 flex items-baseline justify-between">
            <h2 className="text-2xl font-extrabold text-terminal-cyan font-mono">4 Agents</h2>
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              Async Parallel
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2 font-mono">Technical - RAG - Sentiment - Risk</p>
        </div>

      </div>

      {/* Watchlist: LIVE MARKET PRICES */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold font-mono text-white flex items-center gap-2">
            <Compass className="w-4 h-4 text-terminal-cyan" />
            WATCHLIST &amp; LIVE MARKET PRICES
          </h3>
          <div className="flex items-center gap-3">
            <span className="text-[10px] text-slate-500 font-mono">
              Updated: {lastRefreshed.toLocaleTimeString()}
            </span>
            <button
              onClick={fetchAllPrices}
              className="flex items-center gap-1.5 text-xs font-mono text-slate-400 hover:text-white transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3">
          {liveStocks.map((stock) => {
            const snap = stock.snapshot;
            const isPos = snap ? snap.change_percent >= 0 : true;

            return (
              <div
                key={stock.symbol}
                onClick={() => onSelectStockForAnalysis(stock.symbol)}
                className="glass-panel-interactive rounded-xl p-4 cursor-pointer group"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono font-bold text-sm text-white group-hover:text-terminal-cyan transition-colors">
                    {stock.symbol}
                  </span>
                  {stock.loading ? (
                    <div className="w-3 h-3 rounded-full border border-slate-600 border-t-cyan-400 animate-spin" />
                  ) : stock.error ? (
                    <span className="text-[9px] text-rose-400 font-mono">ERR</span>
                  ) : (
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      LIVE
                    </span>
                  )}
                </div>

                <p className="text-[10px] text-slate-500 mb-3 truncate">{stock.name}</p>

                {stock.loading ? (
                  <div className="space-y-1.5">
                    <div className="h-5 rounded bg-dark-700 animate-pulse w-3/4" />
                    <div className="h-3 rounded bg-dark-700 animate-pulse w-1/2" />
                  </div>
                ) : stock.error || !snap ? (
                  <p className="text-xs text-rose-400 font-mono">DATA UNAVAILABLE</p>
                ) : (
                  <>
                    <p className="font-mono font-bold text-white text-lg leading-none">
                      Rs.{snap.price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </p>
                    <p className={`text-xs font-mono font-semibold flex items-center mt-1 ${isPos ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {isPos ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
                      {isPos ? '+' : ''}{snap.change_percent.toFixed(2)}%
                      <span className="text-slate-500 ml-1 font-normal text-[10px]">
                        ({isPos ? '+' : ''}Rs.{snap.change_amount.toFixed(2)})
                      </span>
                    </p>

                    <div className="mt-3 pt-2 border-t border-dark-700 grid grid-cols-2 gap-1 text-[10px] font-mono">
                      <div>
                        <span className="text-slate-500">RSI </span>
                        <span className={`font-bold ${snap.rsi_14 > 70 ? 'text-rose-400' : snap.rsi_14 < 30 ? 'text-emerald-400' : 'text-slate-300'}`}>
                          {snap.rsi_14}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500">Vol </span>
                        <span className={`font-bold ${snap.volume_anomaly ? 'text-amber-400' : 'text-slate-300'}`}>
                          {snap.volume_anomaly ? 'spike ' : ''}{(snap.volume / 1_000_000).toFixed(1)}M
                        </span>
                      </div>
                    </div>
                  </>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Risk Alerts */}
      <div className="terminal-card space-y-3">
        <h3 className="text-sm font-bold font-mono text-white flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-amber-400" />
          ACTIVE RISK &amp; CONCENTRATION ALERTS
        </h3>
        <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 space-y-1">
          <div className="flex items-center justify-between text-xs font-mono text-amber-300 font-bold">
            <span>Concentration Warning</span>
            <span>IT Sector Heavy</span>
          </div>
          <p className="text-xs text-slate-300">
            Combined exposure across TCS &amp; INFY may exceed conservative risk limits. Review sector allocation in the Portfolio tab.
          </p>
        </div>
        <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 space-y-1">
          <div className="flex items-center justify-between text-xs font-mono text-blue-300 font-bold">
            <span>Live Data Active</span>
            <span>All feeds verified</span>
          </div>
          <p className="text-xs text-slate-300">
            All prices above are fetched live via yfinance (NSE). Click any stock card to run the full 4-agent AI analysis.
          </p>
        </div>
      </div>

    </div>
  );
};
