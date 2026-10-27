import React, { useState } from 'react';
import {
  Activity,
  Layers,
  Cpu,
  GitCompare,
  History,
  HelpCircle,
  Zap,
  Shield,
  Menu,
  X,
  Sliders,
  ShieldCheck,
  Upload,
  Award,
  Radio,
  FileText,
  BarChart2
} from 'lucide-react';
import SimulationBadge from './SimulationBadge';

export default function Header({ activeTab, setActiveTab, currentRun }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { id: 'overview', label: 'Overview', icon: Zap },
    { id: 'fleet-grid', label: 'Fleet & Grid', icon: Radio },
    { id: 'scenario-lab', label: 'Scenario Lab', icon: Layers },
    { id: 'scenario-builder', label: 'Scenario Builder', icon: Sliders },
    { id: 'incident-analysis', label: 'Incident Analysis', icon: Activity },
    { id: 'counterfactual', label: 'Counterfactual Replay', icon: GitCompare },
    { id: 'defense-lab', label: 'Defense Lab', icon: ShieldCheck },
    { id: 'ocpp-gateway', label: 'OCPP Gateway', icon: Shield },
    { id: 'incident-comparison', label: 'Compare', icon: GitCompare },
    { id: 'incident-reports', label: 'Reports', icon: FileText },
    { id: 'ablation-studio', label: 'Ablation & Data', icon: BarChart2 },
    { id: 'evaluation-scorecard', label: 'Scorecard', icon: Award },
    { id: 'import-wizard', label: 'Ingestion', icon: Upload },
    { id: 'history', label: 'History', icon: History },
    { id: 'about', label: 'About', icon: HelpCircle },
  ];

  const handleNavClick = (id) => {
    setActiveTab(id);
    setMobileMenuOpen(false);
  };

  return (
    <header className="sticky top-0 z-50 w-full bg-white/95 backdrop-blur-md border-b border-[#D7E1ED] shadow-xs text-[#172033]">
      <div className="w-full px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-18">
          {/* Logo & Product Identity */}
          <div className="flex items-center gap-4">
            <div
              className="flex items-center gap-3 cursor-pointer group select-none"
              onClick={() => handleNavClick('overview')}
            >
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-600 to-blue-600 flex items-center justify-center shadow-md shadow-cyan-600/25 group-hover:scale-105 transition-transform">
                <Shield className="w-5 h-5 text-white stroke-[2.4]" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-extrabold tracking-tight text-xl text-[#172033] font-mono">
                    THREAT<span className="text-[#0891B2]">LENS</span>
                  </span>
                  <span className="text-[11px] font-mono uppercase px-2 py-0.5 rounded-md bg-[#E6FAFF] text-[#0891B2] font-bold border border-[#0891B2]/30">
                    Tier 3 Advanced
                  </span>
                </div>
                <p className="text-xs text-[#52647A] font-medium hidden md:block">
                  See the Threat. Trace the Impact. Prove the Difference.
                </p>
              </div>
            </div>
          </div>

          {/* Right Header Status Controls & Simulation Badge */}
          <div className="flex items-center gap-3.5">
            {currentRun && (
              <div
                className="hidden xl:flex items-center gap-2.5 px-3.5 py-1.5 rounded-lg bg-slate-50 border border-[#D7E1ED] text-xs font-mono text-[#172033] cursor-pointer hover:border-cyan-500 hover:bg-[#E6FAFF]/40 transition-colors"
                onClick={() => handleNavClick('incident-analysis')}
                title="Active simulation in memory"
              >
                <span className="w-2.5 h-2.5 rounded-full bg-[#0891B2] animate-pulse"></span>
                <span className="text-[#52647A]">Active:</span>
                <span className="text-[#0891B2] font-bold">{currentRun.run_id}</span>
              </div>
            )}
            <SimulationBadge />

            {/* Mobile menu button */}
            <div className="flex xl:hidden">
              <button
                type="button"
                className="p-2.5 rounded-xl text-[#52647A] hover:text-[#172033] hover:bg-slate-100 focus:outline-none cursor-pointer"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                aria-label="Toggle navigation menu"
              >
                {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>
            </div>
          </div>
        </div>

        {/* Desktop Navigation Row (Full Width scrollable tabs) */}
        <div className="hidden xl:flex items-center gap-1 overflow-x-auto py-2 border-t border-[#F1F5F9] scrollbar-none">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                className={`flex items-center gap-2 px-3 py-2 text-xs font-semibold rounded-xl whitespace-nowrap transition-all cursor-pointer ${
                  isActive
                    ? 'bg-cyan-50 text-[#0891B2] font-bold border border-cyan-200/80 shadow-xs'
                    : 'text-[#52647A] hover:text-[#172033] hover:bg-slate-100/80'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-[#0891B2]' : 'text-[#64748B]'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Mobile menu dropdown */}
      {mobileMenuOpen && (
        <div className="xl:hidden border-t border-[#D7E1ED] bg-white px-4 pt-3 pb-5 space-y-1 shadow-lg">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 text-xs font-semibold rounded-xl transition-all cursor-pointer ${
                  isActive
                    ? 'bg-cyan-50 text-[#0891B2] font-bold border border-cyan-200'
                    : 'text-[#52647A] hover:bg-slate-100'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-[#0891B2]' : 'text-[#64748B]'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      )}
    </header>
  );
}
