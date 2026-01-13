
import React from 'react';
import { WorkflowStep } from '../types';

interface LayoutProps {
  children: React.ReactNode;
  currentStep: WorkflowStep;
}

const Layout: React.FC<LayoutProps> = ({ children, currentStep }) => {
  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-slate-200 flex flex-col z-30 flex-shrink-0">
        <div className="h-16 flex items-center px-6 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-indigo-600 text-3xl filled">ssid_chart</span>
            <span className="text-xl font-bold tracking-tight">WealthOS</span>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto py-6 px-4 space-y-8">
          <div>
            <h3 className="px-3 text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">Main</h3>
            <div className="space-y-1">
              <SidebarLink icon="dashboard" label="Dashboard" />
              <SidebarLink icon="table_view" label="Data Workbench" active />
              <SidebarLink icon="psychology" label="Logic Studio" />
            </div>
          </div>

          <div>
            <h3 className="px-3 text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">Analysis</h3>
            <div className="space-y-1">
              <SidebarLink icon="pie_chart" label="Portfolio" />
              <SidebarLink icon="payments" label="Cash Flow" />
              <SidebarLink icon="explore" label="Compass" />
              <SidebarLink icon="science" label="Simulation" />
            </div>
          </div>

          <div>
            <h3 className="px-3 text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">System</h3>
            <div className="space-y-1">
              <SidebarLink icon="hub" label="Integrations" />
              <SidebarLink icon="monitor_heart" label="Health" />
            </div>
          </div>
        </nav>

        <div className="p-4 border-t border-slate-100">
          <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-50 cursor-pointer transition-colors group">
            <div className="w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-xs shadow-sm">RD</div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-slate-900 truncate">Ray Dalio</p>
              <p className="text-xs text-slate-500 truncate">Bridgewater</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8 shrink-0 z-20">
          <nav className="flex items-center space-x-2 text-sm text-slate-500">
            <span>Main</span>
            <span className="material-symbols-outlined !text-base text-slate-300">chevron_right</span>
            <span className="text-blue-600 font-medium">Data Workbench</span>
          </nav>

          <div className="flex items-center gap-4">
            <button className="flex items-center gap-1 px-3 py-1.5 text-xs font-bold text-slate-600 bg-slate-100 rounded hover:bg-slate-200 transition-colors">
              EN <span className="material-symbols-outlined !text-xs">expand_more</span>
            </button>
            <div className="h-6 w-px bg-slate-200"></div>
            <button className="p-2 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-50 relative">
              <span className="material-symbols-outlined">notifications</span>
              <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-white"></span>
            </button>
            <button className="p-2 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-50">
              <span className="material-symbols-outlined">account_circle</span>
            </button>
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-8 relative">
          {children}
        </div>
      </main>
    </div>
  );
};

const SidebarLink: React.FC<{ icon: string; label: string; active?: boolean }> = ({ icon, label, active }) => (
  <a className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all ${active ? 'bg-blue-50 text-blue-600' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'}`} href="#">
    <span className={`material-symbols-outlined !text-[20px] ${active ? 'filled' : ''}`}>{icon}</span>
    {label}
  </a>
);

export default Layout;
