import React, { useState, useEffect } from 'react';
import { History, Eye, Clock } from 'lucide-react';
import type { AnalysisSession } from '../types';
import { ApiService } from '../services/api';

interface SessionHistoryProps {
  onReopenSession: (session: AnalysisSession) => void;
}

export const SessionHistory: React.FC<SessionHistoryProps> = ({ onReopenSession }) => {
  const [sessions, setSessions] = useState<AnalysisSession[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    setIsLoading(true);
    try {
      const res = await ApiService.getHistory();
      setSessions(res.sessions);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-mono font-bold text-white uppercase flex items-center gap-2">
          <History className="w-4 h-4 text-terminal-cyan" />
          SESSION HISTORY & AI RESEARCH AUDIT LOG
        </h3>
        <button
          onClick={fetchHistory}
          className="text-xs font-mono text-cyan-400 hover:underline"
        >
          Refresh History
        </button>
      </div>

      {isLoading ? (
        <div className="h-32 flex items-center justify-center text-slate-500 font-mono text-xs">
          Loading history records...
        </div>
      ) : sessions.length === 0 ? (
        <div className="terminal-card p-8 text-center text-slate-400 font-mono text-xs space-y-2">
          <Clock className="w-8 h-8 text-slate-600 mx-auto" />
          <p>No previous session records logged yet.</p>
          <p className="text-slate-500">Run an analysis in the AI Research Terminal to populate session logs.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {sessions.map((sess) => (
            <div
              key={sess.session_id}
              onClick={() => onReopenSession(sess)}
              className="glass-panel-interactive rounded-xl p-4 cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-4 text-xs font-mono"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-white text-sm">{sess.symbol}</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    sess.synthesis.overall_signal === 'BULLISH' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                  }`}>
                    Signal Strength: <span className="text-slate-200 ml-1">{sess.synthesis.overall_confidence}%</span>
                  </span>
                  {sess.is_degraded && (
                    <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 text-[10px] border border-amber-500/30">
                      DEGRADED MODE
                    </span>
                  )}
                </div>
                <p className="text-slate-400">{sess.user_profile.name} • {sess.timestamp}</p>
              </div>

              <div className="flex items-center gap-4">
                <span className="text-slate-300 max-w-xs truncate hidden lg:block">
                  {sess.synthesis.executive_summary}
                </span>
                <button className="px-3 py-1.5 rounded-lg bg-blue-600/20 border border-blue-500/40 text-blue-300 hover:bg-blue-600 hover:text-white transition-all flex items-center gap-1.5">
                  <Eye className="w-3.5 h-3.5" />
                  <span>Reopen Analysis</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
