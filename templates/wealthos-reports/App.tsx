
import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import { ReportView } from './types';
import PortfolioOverview from './pages/PortfolioOverview';
import AllocationRisk from './pages/AllocationRisk';
import GainsAnalysis from './pages/GainsAnalysis';
import CashFlow from './pages/CashFlow';
import Compass from './pages/Compass';
import Simulation from './pages/Simulation';
import { BrainCircuit } from 'lucide-react';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<ReportView>(ReportView.PORTFOLIO_OVERVIEW);

  const renderContent = () => {
    switch (currentView) {
      case ReportView.PORTFOLIO_OVERVIEW:
        return <PortfolioOverview />;
      case ReportView.ALLOCATION_RISK:
        return <AllocationRisk />;
      case ReportView.GAINS_ANALYSIS:
        return <GainsAnalysis />;
      case ReportView.CASH_FLOW:
        return <CashFlow />;
      case ReportView.COMPASS:
        return <Compass />;
      case ReportView.SIMULATION:
        return <Simulation />;
      default:
        return (
          <div className="flex flex-col items-center justify-center h-[70vh] text-slate-400 space-y-4">
            <div className="bg-slate-100 p-6 rounded-full">
              <BrainCircuit size={48} />
            </div>
            <div className="text-center">
              <h2 className="text-xl font-bold text-slate-900">Module Under Development</h2>
              <p className="text-sm font-medium">The {currentView} module is being prepared for your account.</p>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="flex h-screen bg-[#f8fafc] overflow-hidden">
      <Sidebar currentView={currentView} onViewChange={setCurrentView} />
      
      <main className="flex-1 flex flex-col min-w-0">
        <Header title={currentView} />
        
        <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
          <div className="max-w-[1440px] mx-auto">
            {renderContent()}
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;
