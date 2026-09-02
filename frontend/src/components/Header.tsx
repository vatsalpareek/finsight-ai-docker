import React from 'react';
import { UserCheck, Layers } from 'lucide-react';
import type { UserProfile } from '../types';

interface HeaderProps {
  currentProfile: UserProfile;
  onProfileChange: (profileId: string) => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  isBackendConnected: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  currentProfile,
  onProfileChange,
  activeTab,
  setActiveTab,
  isBackendConnected
}) => {
  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-dark-700/80 px-4 lg:px-8 py-3">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        
        {/* Brand & System Status */}
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-tr from-blue-600 via-cyan-500 to-emerald-400 rounded-xl shadow-lg shadow-blue-500/20">
            <Layers className="w-6 h-6 text-black font-bold" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold text-xl tracking-tight text-white flex items-center gap-1.5">
                FINSIGHT <span className="text-terminal-cyan">AI</span>
              </h1>
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-semibold">
                Autonomous Hedge Fund Intelligence
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono flex items-center gap-2">
              <span>Multi-Agent Research Terminal</span>
              <span className="text-slate-600">•</span>
              <span className={`inline-flex items-center gap-1 text-[11px] ${isBackendConnected ? 'text-emerald-400' : 'text-rose-400'}`}>
                <span className={`w-2 h-2 rounded-full ${isBackendConnected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'}`} />
                {isBackendConnected ? 'Engine Online' : 'Connecting Engine...'}
              </span>
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 bg-dark-900/90 p-1 rounded-xl border border-dark-700 text-xs font-medium">
          <button
            onClick={() => setActiveTab('terminal')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'terminal' ? 'bg-blue-600 text-white shadow-md' : 'text-slate-400 hover:text-white'
            }`}
          >
            AI Research Terminal
          </button>
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'dashboard' ? 'bg-blue-600 text-white shadow-md' : 'text-slate-400 hover:text-white'
            }`}
          >
            Dashboard
          </button>

          <button
            onClick={() => setActiveTab('comparison')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'comparison' ? 'bg-blue-600 text-white shadow-md' : 'text-slate-400 hover:text-white'
            }`}
          >
            Profile Compare
          </button>
          <button
            onClick={() => setActiveTab('portfolio')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'portfolio' ? 'bg-blue-600 text-white shadow-md' : 'text-slate-400 hover:text-white'
            }`}
          >
            Portfolio & Risk
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'history' ? 'bg-blue-600 text-white shadow-md' : 'text-slate-400 hover:text-white'
            }`}
          >
            History & Logs
          </button>
        </nav>

        {/* Controls: Profile Switcher */}
        <div className="flex items-center gap-3">
          
          {/* Profile Switcher */}
          <div className="flex items-center gap-2 bg-dark-900 border border-dark-700 rounded-lg p-1">
            <UserCheck className="w-4 h-4 text-cyan-400 ml-1" />
            <select
              value={currentProfile.user_id}
              onChange={(e) => onProfileChange(e.target.value)}
              className="bg-transparent text-xs text-white font-medium focus:outline-none cursor-pointer pr-1"
            >
              <option value="conservative" className="bg-dark-900 text-white">Arjun Sharma (Conservative)</option>
              <option value="aggressive" className="bg-dark-900 text-white">Priya Patel (Aggressive)</option>
            </select>
          </div>

        </div>

      </div>
    </header>
  );
};
