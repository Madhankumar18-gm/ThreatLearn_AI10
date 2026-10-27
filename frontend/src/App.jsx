import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Overview from './pages/Overview';
import ScenarioLab from './pages/ScenarioLab';
import IncidentAnalysis from './pages/IncidentAnalysis';
import ImpactAnalysis from './pages/ImpactAnalysis';
import IncidentHistory from './pages/IncidentHistory';
import AboutLimitations from './pages/AboutLimitations';
import ScenarioBuilder from './pages/ScenarioBuilder';
import OCPPGateway from './pages/OCPPGateway';
import ImportWizard from './pages/ImportWizard';
import EvaluationScorecard from './pages/EvaluationScorecard';
import FleetGrid from './pages/FleetGrid';
import IncidentComparison from './pages/IncidentComparison';
import IncidentReports from './pages/IncidentReports';
import { api } from './services/api';
import { AlertCircle, Shield } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [currentRun, setCurrentRun] = useState(null);
  const [scenarios, setScenarios] = useState([]);
  const [targetEventId, setTargetEventId] = useState(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [errorBanner, setErrorBanner] = useState(null);

  // Fetch scenarios on initial mount
  useEffect(() => {
    api.getScenarios()
      .then((data) => setScenarios(data))
      .catch((err) => console.error('Failed to load scenarios', err));
  }, []);

  // Redirect obsolete tabs cleanly to active features
  useEffect(() => {
    if (activeTab === 'counterfactual' || activeTab === 'defense-lab' || activeTab === 'ablation-studio') {
      setActiveTab('impact-analysis');
    }
  }, [activeTab]);

  // Handler to run a simulation
  const handleRunSimulation = async (scenarioId, seed = null) => {
    setIsSimulating(true);
    setErrorBanner(null);
    try {
      const run = await api.runSimulation(scenarioId, seed);
      setCurrentRun(run);
      // Default target event for counterfactual
      const attackEv = run.events.find(
        (e) => e.auth_status === 'unauthorized' || e.auth_status === 'spoofed'
      );
      if (attackEv) {
        setTargetEventId(attackEv.event_id);
      } else if (run.events.length > 0) {
        setTargetEventId(run.events[0].event_id);
      }
      setActiveTab('incident-analysis');
    } catch (err) {
      console.error('Simulation execution failed', err);
      setErrorBanner(err.message || 'Simulation execution failed');
    } finally {
      setIsSimulating(false);
    }
  };

  const handleSelectAndRun = (scenarioId, seed = null) => {
    handleRunSimulation(scenarioId, seed);
  };

  const handleSelectEventForReplay = (eventId) => {
    setTargetEventId(eventId);
    setActiveTab('impact-analysis');
  };

  const handleLoadRun = async (runId) => {
    setErrorBanner(null);
    try {
      const run = await api.getRun(runId);
      setCurrentRun(run);
      if (run.events && run.events.length > 0) {
        setTargetEventId(run.events[0].event_id);
      }
      setActiveTab('incident-analysis');
    } catch (err) {
      console.error('Failed to load incident run', err);
      setErrorBanner(err.message || 'Failed to load incident run');
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#F3F6FB] text-[#172033] flex flex-col font-sans selection:bg-cyan-100 selection:text-cyan-900 overflow-x-hidden">
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        currentRun={currentRun}
      />

      {/* Global Error Banner */}
      {errorBanner && (
        <div className="w-full px-4 sm:px-6 lg:px-8 mt-4 animate-page-enter">
          <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-900 text-sm font-mono flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-2.5">
              <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />
              <span>{errorBanner}</span>
            </div>
            <button
              onClick={() => setErrorBanner(null)}
              className="text-red-500 hover:text-red-800 font-bold ml-4 text-base cursor-pointer"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 w-full px-4 sm:px-6 lg:px-8 pt-8 pb-12">
        {activeTab === 'overview' && (
          <Overview
            setActiveTab={setActiveTab}
            onSelectAndRun={handleSelectAndRun}
            currentRun={currentRun}
          />
        )}

        {activeTab === 'fleet-grid' && (
          <FleetGrid />
        )}

        {activeTab === 'scenario-lab' && (
          <ScenarioLab
            onRunSimulation={handleRunSimulation}
            isSimulating={isSimulating}
          />
        )}

        {activeTab === 'scenario-builder' && (
          <ScenarioBuilder
            onRunGenerated={(run) => {
              setCurrentRun(run);
              if (run.events && run.events.length > 0) {
                setTargetEventId(run.events[0].event_id);
              }
            }}
            setActiveTab={setActiveTab}
          />
        )}

        {activeTab === 'incident-analysis' && (
          <IncidentAnalysis
            currentRun={currentRun}
            setActiveTab={setActiveTab}
            onSelectEventForReplay={handleSelectEventForReplay}
          />
        )}

        {activeTab === 'impact-analysis' && (
          <ImpactAnalysis
            currentRun={currentRun}
            setCurrentRun={setCurrentRun}
            setActiveTab={setActiveTab}
            targetEventId={targetEventId}
          />
        )}

        {activeTab === 'ocpp-gateway' && (
          <OCPPGateway />
        )}

        {activeTab === 'incident-comparison' && (
          <IncidentComparison />
        )}

        {activeTab === 'incident-reports' && (
          <IncidentReports />
        )}

        {activeTab === 'import-wizard' && (
          <ImportWizard setActiveTab={setActiveTab} />
        )}

        {activeTab === 'evaluation-scorecard' && (
          <EvaluationScorecard />
        )}

        {activeTab === 'history' && (
          <IncidentHistory
            onLoadRun={handleLoadRun}
            setActiveTab={setActiveTab}
          />
        )}

        {activeTab === 'about' && <AboutLimitations />}
      </main>

      {/* Full-Width Footer */}
      <footer className="w-full border-t border-[#D7E1ED] bg-white py-8 text-center text-sm text-[#52647A] font-mono shadow-2xs mt-auto">
        <div className="w-full px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <Shield className="w-4 h-4 text-[#0891B2]" />
            <span className="font-bold text-[#172033] text-base">ThreatLens</span>
            <span className="hidden sm:inline text-[#52647A]">|</span>
            <span className="text-xs sm:text-sm text-[#52647A]">Cybersecurity and Cyber-Physical Impact Analysis Platform</span>
          </div>
          <div className="text-xs sm:text-sm text-[#52647A]">
            See the Threat. Trace the Impact. Prove the Difference.
          </div>
        </div>
      </footer>
    </div>
  );
}
