import React, { useState, useEffect, useCallback } from 'react';
import { PieChart, PlusCircle, ArrowUpRight, ArrowDownRight, RefreshCw, Search } from 'lucide-react';
import type { UserProfile, PortfolioHolding } from '../types';
import { ApiService } from '../services/api';

interface PortfolioViewProps {
  profile: UserProfile;
}

interface LiveHolding extends PortfolioHolding {
  livePrice: number | null;
  liveValue: number | null;
  livePnL: number | null;
  livePnLPct: number | null;
  priceLoading: boolean;
}

export const PortfolioView: React.FC<PortfolioViewProps> = ({ profile }) => {
  const [liveHoldings, setLiveHoldings] = useState<LiveHolding[]>([]);
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());
  const [isRefreshing, setIsRefreshing] = useState(false);

  // What-If Simulator state
  const [simTicker, setSimTicker] = useState('');
  const [simShares, setSimShares] = useState<number>(50);
  const [simFetchedPrice, setSimFetchedPrice] = useState<number | null>(null);
  const [simManualPrice, setSimManualPrice] = useState<number>(0);
  const [simFetching, setSimFetching] = useState(false);
  const [simFetchError, setSimFetchError] = useState<string | null>(null);

  const fetchLivePrices = useCallback(async () => {
    if (!profile.portfolio_holdings.length) {
      setLiveHoldings([]);
      return;
    }
    setIsRefreshing(true);

    const initial: LiveHolding[] = profile.portfolio_holdings.map(h => ({
      ...h,
      livePrice: null,
      liveValue: null,
      livePnL: null,
      livePnLPct: null,
      priceLoading: true,
    }));
    setLiveHoldings(initial);

    const updated = await Promise.all(
      profile.portfolio_holdings.map(async (h) => {
        try {
          const data = await ApiService.getMarketData(h.symbol, false);
          const livePrice = data.snapshot.price;
          const liveValue = livePrice * h.shares;
          const livePnL = (livePrice - h.avg_cost) * h.shares;
          const livePnLPct = ((livePrice - h.avg_cost) / h.avg_cost) * 100;
          return { ...h, livePrice, liveValue, livePnL, livePnLPct, priceLoading: false };
        } catch {
          return { ...h, livePrice: null, liveValue: null, livePnL: null, livePnLPct: null, priceLoading: false };
        }
      })
    );
    setLiveHoldings(updated);
    setLastRefreshed(new Date());
    setIsRefreshing(false);
  }, [profile.portfolio_holdings]);

  useEffect(() => {
    fetchLivePrices();
  }, [fetchLivePrices]);

  // Fetch live price for What-If simulator when user finishes typing a ticker
  const fetchSimPrice = async (ticker: string) => {
    if (!ticker || ticker.length < 2) return;
    setSimFetching(true);
    setSimFetchError(null);
    setSimFetchedPrice(null);
    try {
      const data = await ApiService.getMarketData(ticker, false);
      setSimFetchedPrice(data.snapshot.price);
      setSimManualPrice(data.snapshot.price);
    } catch {
      setSimFetchError('Could not fetch price. Enter manually below.');
    } finally {
      setSimFetching(false);
    }
  };

  // Computed from live holdings
  const liveTotalValue = liveHoldings.reduce((acc, h) => acc + (h.liveValue ?? h.value), 0);
  const liveTotalPnL = liveHoldings.reduce((acc, h) => acc + (h.livePnL ?? h.profit_loss), 0);
  const liveTotalInvested = profile.portfolio_holdings.reduce((acc, h) => acc + h.avg_cost * h.shares, 0);
  const liveTotalPnLPct = liveTotalInvested > 0 ? (liveTotalPnL / liveTotalInvested) * 100 : 0;

  // Sector totals from live values
  const sectorTotals: Record<string, number> = {};
  liveHoldings.forEach(h => {
    const val = h.liveValue ?? h.value;
    sectorTotals[h.sector] = (sectorTotals[h.sector] || 0) + val;
  });

  // What-If calculations
  const activeSimPrice = simManualPrice || simFetchedPrice || 0;
  const simAddCost = activeSimPrice * simShares;
  const simNewTotal = liveTotalValue + simAddCost;
  const simNewSectorPct = simNewTotal > 0 ? (simAddCost / simNewTotal) * 100 : 0;

  return (
    <div className="space-y-6">
      
      {/* Top Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

        <div className="terminal-card">
          <p className="text-xs font-mono text-slate-400 uppercase">Live Portfolio Value</p>
          <h2 className="text-2xl font-extrabold text-white font-mono mt-1">
            {isRefreshing ? (
              <span className="text-slate-400 animate-pulse">Updating...</span>
            ) : (
              <span>Rs.{(liveTotalValue / 100000).toFixed(2)} Lakhs</span>
            )}
          </h2>
          <p className={`text-xs font-mono mt-1 flex items-center ${liveTotalPnL >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            {liveTotalPnL >= 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
            Total P&L: {liveTotalPnL >= 0 ? '+' : ''}Rs.{Math.abs(liveTotalPnL).toLocaleString('en-IN', { maximumFractionDigits: 0 })} ({liveTotalPnLPct.toFixed(2)}%)
          </p>
        </div>

        <div className="terminal-card">
          <p className="text-xs font-mono text-slate-400 uppercase">Sector Concentration Score</p>
          <h2 className="text-2xl font-extrabold text-amber-400 font-mono mt-1">
            {profile.risk_score}/100
          </h2>
          <p className="text-xs text-slate-400 font-mono mt-1">
            {profile.risk_score > 60 ? 'Elevated — review diversification' : 'Well diversified portfolio'}
          </p>
        </div>

        <div className="terminal-card">
          <p className="text-xs font-mono text-slate-400 uppercase">Investor Profile</p>
          <h2 className="text-xl font-extrabold text-terminal-cyan font-mono mt-1">
            {profile.name}
          </h2>
          <p className="text-xs text-slate-400 font-mono mt-1">
            {profile.risk_tolerance} • {profile.investment_horizon}
          </p>
        </div>

      </div>

      {/* Holdings Table + Sector Sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Holdings Table */}
        <div className="lg:col-span-2 terminal-card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-mono font-bold text-white uppercase flex items-center gap-2">
              <PieChart className="w-4 h-4 text-blue-400" />
              CURRENT PORTFOLIO HOLDINGS (LIVE PRICES)
            </h3>
            <div className="flex items-center gap-3">
              <span className="text-[10px] text-slate-500 font-mono">Updated: {lastRefreshed.toLocaleTimeString()}</span>
              <button
                onClick={fetchLivePrices}
                className="flex items-center gap-1 text-xs font-mono text-slate-400 hover:text-white transition-colors"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
          </div>

          {liveHoldings.length === 0 ? (
            <div className="py-12 text-center text-slate-500 font-mono text-xs space-y-2">
              <PieChart className="w-8 h-8 mx-auto text-slate-600" />
              <p>No holdings found for this profile.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs font-mono text-left">
                <thead>
                  <tr className="border-b border-dark-700 text-slate-400">
                    <th className="py-2.5 px-3">Ticker</th>
                    <th className="py-2.5 px-3">Shares</th>
                    <th className="py-2.5 px-3">Avg Cost</th>
                    <th className="py-2.5 px-3">Live Price</th>
                    <th className="py-2.5 px-3">Live Value</th>
                    <th className="py-2.5 px-3">Alloc %</th>
                    <th className="py-2.5 px-3 text-right">P&L</th>
                  </tr>
                </thead>
                <tbody>
                  {liveHoldings.map((h) => {
                    const pnlPos = (h.livePnL ?? h.profit_loss) >= 0;
                    const liveAlloc = liveTotalValue > 0 ? ((h.liveValue ?? h.value) / liveTotalValue) * 100 : 0;
                    return (
                      <tr key={h.symbol} className="border-b border-dark-800 hover:bg-dark-900/50">
                        <td className="py-3 px-3">
                          <span className="font-bold text-white block">{h.symbol}</span>
                          <span className="text-[10px] text-slate-500">{h.sector}</span>
                        </td>
                        <td className="py-3 px-3 text-slate-300">{h.shares}</td>
                        <td className="py-3 px-3 text-slate-400">Rs.{h.avg_cost.toFixed(2)}</td>
                        <td className="py-3 px-3 font-bold text-slate-200">
                          {h.priceLoading ? (
                            <div className="h-3 w-16 rounded bg-dark-700 animate-pulse" />
                          ) : h.livePrice != null ? (
                            <span className={h.livePrice >= h.avg_cost ? 'text-emerald-400' : 'text-rose-400'}>
                              Rs.{h.livePrice.toFixed(2)}
                            </span>
                          ) : (
                            <span className="text-rose-400">N/A</span>
                          )}
                        </td>
                        <td className="py-3 px-3 font-bold text-white">
                          {h.priceLoading ? (
                            <div className="h-3 w-14 rounded bg-dark-700 animate-pulse" />
                          ) : h.liveValue != null ? (
                            `Rs.${(h.liveValue / 1000).toFixed(1)}k`
                          ) : '—'}
                        </td>
                        <td className="py-3 px-3">
                          <span className="px-2 py-0.5 rounded bg-blue-500/10 text-cyan-400 font-bold border border-blue-500/20">
                            {liveAlloc.toFixed(1)}%
                          </span>
                        </td>
                        <td className="py-3 px-3 text-right font-bold">
                          {h.priceLoading ? (
                            <div className="h-3 w-12 rounded bg-dark-700 animate-pulse ml-auto" />
                          ) : (
                            <div>
                              <span className={pnlPos ? 'text-emerald-400' : 'text-rose-400'}>
                                {pnlPos ? '+' : ''}Rs.{Math.abs(h.livePnL ?? h.profit_loss).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                              </span>
                              <br />
                              <span className={`text-[10px] ${pnlPos ? 'text-emerald-400' : 'text-rose-400'}`}>
                                {pnlPos ? '+' : ''}{(h.livePnLPct ?? h.profit_loss_pct).toFixed(2)}%
                              </span>
                            </div>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Sidebar: Sector Breakdown + What-If */}
        <div className="space-y-4">

          {/* Sector Breakdown */}
          <div className="terminal-card space-y-3">
            <h4 className="text-xs font-mono font-bold text-slate-400 uppercase">Sector Concentration (Live)</h4>
            {Object.keys(sectorTotals).length === 0 ? (
              <p className="text-xs text-slate-500 font-mono">No holdings loaded.</p>
            ) : (
              <div className="space-y-2 text-xs font-mono">
                {Object.entries(sectorTotals)
                  .sort((a, b) => b[1] - a[1])
                  .map(([sec, val]) => {
                    const pct = liveTotalValue > 0 ? ((val / liveTotalValue) * 100) : 0;
                    const isHigh = pct > 30;
                    return (
                      <div key={sec} className="space-y-1">
                        <div className="flex justify-between text-slate-300">
                          <span className="truncate max-w-[120px]">{sec}</span>
                          <span className={`font-bold ${isHigh ? 'text-amber-400' : 'text-cyan-400'}`}>{pct.toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-dark-950 rounded-full h-1.5 overflow-hidden border border-dark-800">
                          <div
                            className={`h-1.5 rounded-full ${isHigh ? 'bg-amber-500' : 'bg-blue-500'}`}
                            style={{ width: `${Math.min(pct, 100)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
              </div>
            )}
          </div>

          {/* What-If Position Simulator */}
          <div className="terminal-card space-y-3 border-blue-500/30">
            <h4 className="text-xs font-mono font-bold text-white uppercase flex items-center gap-1.5">
              <PlusCircle className="w-4 h-4 text-cyan-400" />
              WHAT-IF POSITION SIMULATOR
            </h4>

            <div className="space-y-3 text-xs font-mono">

              {/* Ticker input with fetch button */}
              <div>
                <label className="text-slate-400 block mb-1">Stock Ticker</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={simTicker}
                    onChange={(e) => setSimTicker(e.target.value.toUpperCase())}
                    onKeyDown={(e) => e.key === 'Enter' && fetchSimPrice(simTicker)}
                    placeholder="e.g. AAPL, TCS"
                    className="flex-1 bg-dark-950 border border-dark-700 rounded px-2 py-1.5 text-white font-mono focus:outline-none focus:border-blue-500"
                  />
                  <button
                    onClick={() => fetchSimPrice(simTicker)}
                    disabled={simFetching || !simTicker}
                    className="px-2 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white transition-colors disabled:opacity-40 flex items-center gap-1"
                  >
                    {simFetching ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
                  </button>
                </div>
                {simFetchedPrice && (
                  <p className="text-emerald-400 mt-1 text-[10px]">
                    Live price fetched: Rs.{simFetchedPrice.toFixed(2)}
                  </p>
                )}
                {simFetchError && (
                  <p className="text-amber-400 mt-1 text-[10px]">{simFetchError}</p>
                )}
              </div>

              {/* Manual price override */}
              <div>
                <label className="text-slate-400 block mb-1">
                  Price (Rs.) {simFetchedPrice ? '— auto-filled, editable' : '— enter manually'}
                </label>
                <input
                  type="number"
                  value={simManualPrice || ''}
                  onChange={(e) => setSimManualPrice(Number(e.target.value))}
                  placeholder="Enter price"
                  className="w-full bg-dark-950 border border-dark-700 rounded px-2 py-1.5 text-white font-mono focus:outline-none focus:border-blue-500"
                />
              </div>

              {/* Shares */}
              <div>
                <label className="text-slate-400 block mb-1">Number of Shares</label>
                <input
                  type="number"
                  value={simShares}
                  onChange={(e) => setSimShares(Number(e.target.value))}
                  min={1}
                  className="w-full bg-dark-950 border border-dark-700 rounded px-2 py-1.5 text-white font-mono focus:outline-none focus:border-blue-500"
                />
              </div>

              {/* Results */}
              {activeSimPrice > 0 && simShares > 0 ? (
                <div className="p-3 rounded bg-dark-950 border border-blue-500/30 space-y-2 mt-1">
                  <p className="text-slate-400 uppercase text-[10px] font-bold tracking-wider">Projected Impact</p>
                  <div className="space-y-1.5">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Investment Cost</span>
                      <span className="font-bold text-white">Rs.{simAddCost.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">New Portfolio Value</span>
                      <span className="font-bold text-cyan-400">Rs.{(simNewTotal / 100000).toFixed(2)}L</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">{simTicker || 'New'} Weight</span>
                      <span className={`font-bold ${simNewSectorPct > 20 ? 'text-amber-400' : 'text-emerald-400'}`}>
                        {simNewSectorPct.toFixed(1)}%
                        {simNewSectorPct > 20 && ' ⚠ Concentrated'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Risk Suitability</span>
                      <span className={`font-bold ${profile.risk_tolerance === 'Conservative' && simNewSectorPct > 15 ? 'text-rose-400' : 'text-emerald-400'}`}>
                        {profile.risk_tolerance === 'Conservative' && simNewSectorPct > 15
                          ? 'Exceeds conservative limit'
                          : 'Within risk profile'}
                      </span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-3 rounded bg-dark-950 border border-dark-800 text-slate-500 text-[11px] text-center">
                  Enter a ticker and price to see projected impact
                </div>
              )}
            </div>
          </div>

        </div>
      </div>

    </div>
  );
};
