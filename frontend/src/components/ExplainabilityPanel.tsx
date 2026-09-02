import React from 'react';
import { X, HelpCircle, ArrowDown } from 'lucide-react';
import type { AnalysisSession } from '../types';

interface ExplainabilityPanelProps {
  session: AnalysisSession;
  onClose: () => void;
}

export const ExplainabilityPanel: React.FC<ExplainabilityPanelProps> = ({ session, onClose }) => {
  const chain = session.synthesis.reasoning_chain;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="glass-panel w-full max-w-4xl max-h-[90vh] rounded-2xl border-cyan-500/40 p-6 overflow-y-auto space-y-6 shadow-2xl">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-dark-700 pb-4">
          <div className="flex items-center gap-2">
            <HelpCircle className="w-6 h-6 text-terminal-cyan" />
            <div>
              <h3 className="text-xl font-extrabold text-white">
                TRANSPARENT REASONING CHAIN
              </h3>
              <p className="text-xs text-slate-400 font-mono">
                "Why did AI reach this conclusion for {session.symbol}?"
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-dark-800 text-slate-400 hover:text-white hover:bg-dark-700 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Chain Flow Visualization */}
        <div className="space-y-4">
          {chain.map((node, idx) => (
            <div key={idx} className="space-y-2">
              
              <div className="p-4 rounded-xl bg-dark-900 border border-dark-700 hover:border-cyan-500/40 transition-all space-y-2">
                <div className="flex flex-wrap items-center justify-between gap-2 text-xs font-mono">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-cyan-500/20 text-cyan-400 font-bold flex items-center justify-center text-xs border border-cyan-500/40">
                      {node.step_number}
                    </span>
                    <span className="font-bold text-white text-sm">{node.title}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-slate-400">Agent: <strong className="text-slate-200">{node.agent_name}</strong></span>
                    <span className="px-2 py-0.5 rounded bg-blue-500/10 text-cyan-400 border border-blue-500/20 font-bold">
                      Signal Strength: {node.confidence}%
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs pt-1">
                  <div className="p-2.5 rounded bg-dark-950 border border-dark-800">
                    <span className="text-[10px] font-mono text-slate-500 uppercase block">Input Evaluated</span>
                    <span className="text-slate-300 font-mono">{node.input_summary}</span>
                  </div>
                  <div className="p-2.5 rounded bg-dark-950 border border-dark-800">
                    <span className="text-[10px] font-mono text-slate-500 uppercase block">Finding / Conclusion</span>
                    <span className="text-slate-200 font-semibold">{node.finding}</span>
                  </div>
                </div>

                <div className="text-[11px] font-mono text-cyan-400/90 pt-1">
                  <strong className="text-slate-400">Evidence / Grounding:</strong> {node.evidence}
                </div>
              </div>

              {/* Arrow connector except last */}
              {idx < chain.length - 1 && (
                <div className="flex justify-center my-1">
                  <ArrowDown className="w-4 h-4 text-cyan-500/50" />
                </div>
              )}

            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="p-4 rounded-xl bg-dark-900 border border-dark-700 text-xs font-mono text-slate-400 flex items-center justify-between">
          <span>AI-generated investment intelligence. Grounded strictly on retrieved SEBI disclosures & market signals.</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-blue-600 text-white font-bold hover:bg-blue-500 transition-colors"
          >
            Close Reasoning Chain
          </button>
        </div>

      </div>
    </div>
  );
};
