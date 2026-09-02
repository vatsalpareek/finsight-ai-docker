import { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { Dashboard } from './components/Dashboard';
import { ResearchTerminal } from './components/ResearchTerminal';
import { PersonalizationComparison } from './components/PersonalizationComparison';
import { PortfolioView } from './components/PortfolioView';
import { SessionHistory } from './components/SessionHistory';
import { PerformanceLog } from './components/PerformanceLog';
import { ExplainabilityPanel } from './components/ExplainabilityPanel';
import type { UserProfile, AnalysisSession } from './types';
import { ApiService } from './services/api';

export function App() {
  const [activeTab, setActiveTab] = useState<string>('terminal');
  const [profileId, setProfileId] = useState<string>('conservative');
  const [currentProfile, setCurrentProfile] = useState<UserProfile | null>(null);
  const [selectedStock, setSelectedStock] = useState<string>('RELIANCE');
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(false);

  // Modals
  const [explainabilitySession, setExplainabilitySession] = useState<AnalysisSession | null>(null);

  // Load profile on start & change
  useEffect(() => {
    loadProfile(profileId);
    checkHealth();
  }, [profileId]);

  const checkHealth = async () => {
    const ok = await ApiService.checkHealth();
    setIsBackendConnected(ok);
  };

  const loadProfile = async (pid: string) => {
    try {
      const p = await ApiService.getProfile(pid);
      setCurrentProfile(p);
    } catch (err) {
      console.error("Failed to load profile:", err);
    }
  };

  const handleProfileChange = (newPid: string) => {
    setProfileId(newPid);
  };

  const handleSelectStock = (sym: string) => {
    setSelectedStock(sym);
    setActiveTab('terminal');
  };



  if (!currentProfile) {
    return (
      <div className="min-h-screen bg-dark-950 flex flex-col items-center justify-center text-slate-400 font-mono text-xs space-y-3">
        <div className="w-8 h-8 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin" />
        <p>Initializing FinSight AI Autonomous Intelligence Platform...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-950 text-slate-100 flex flex-col font-sans">
      
      <Header
        currentProfile={currentProfile}
        onProfileChange={handleProfileChange}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isBackendConnected={isBackendConnected}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 lg:p-8 space-y-6">
        
        {activeTab === 'terminal' && (
          <ResearchTerminal
            currentProfile={currentProfile}
            selectedStockSymbol={selectedStock}
            onSelectSymbol={setSelectedStock}
            onOpenExplainabilityModal={setExplainabilitySession}
          />
        )}

        {activeTab === 'dashboard' && (
          <Dashboard
            profile={currentProfile}
            onSelectStockForAnalysis={handleSelectStock}
            onNavigateToComparison={() => setActiveTab('comparison')}
          />
        )}

        {activeTab === 'comparison' && (
          <PersonalizationComparison
            onSelectStock={handleSelectStock}
          />
        )}

        {activeTab === 'portfolio' && (
          <PortfolioView
            profile={currentProfile}
          />
        )}

        {activeTab === 'history' && (
          <div className="space-y-8">
            <SessionHistory
              onReopenSession={(sess) => {
                setExplainabilitySession(sess);
              }}
            />
            <PerformanceLog />
          </div>
        )}

      </main>

      {/* Explainability Reasoning Chain Modal */}
      {explainabilitySession && (
        <ExplainabilityPanel
          session={explainabilitySession}
          onClose={() => setExplainabilitySession(null)}
        />
      )}

      {/* Footer */}
      <footer className="border-t border-dark-800 py-4 px-6 text-center text-xs font-mono text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>FinSight AI — Autonomous Financial Intelligence Platform for Indian Retail Investors</span>
          <span className="text-amber-400/90 font-semibold">⚠ AI-generated investment intelligence. Not financial advice.</span>
        </div>
      </footer>

    </div>
  );
}

export default App;
