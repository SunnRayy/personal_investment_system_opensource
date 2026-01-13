
import React from 'react';
import { NAVIGATION_ITEMS } from '../constants';
import { ReportView } from '../types';
import { TrendingUp } from 'lucide-react';

interface SidebarProps {
  currentView: ReportView;
  onViewChange: (view: ReportView) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ currentView, onViewChange }) => {
  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col h-full shrink-0">
      <div className="p-6 flex items-center gap-3">
        <div className="bg-amber-500 p-1.5 rounded-lg text-white">
          <TrendingUp size={24} />
        </div>
        <h1 className="text-xl font-bold tracking-tight text-slate-900">WealthOS</h1>
      </div>

      <nav className="flex-1 px-4 py-2 space-y-8 overflow-y-auto">
        {NAVIGATION_ITEMS.map((group) => (
          <div key={group.group}>
            <h3 className="px-3 mb-2 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
              {group.group}
            </h3>
            <ul className="space-y-1">
              {group.items.map((item) => (
                <li key={item.name}>
                  <button
                    onClick={() => onViewChange(item.name)}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                      currentView === item.name
                        ? 'bg-blue-50 text-blue-600 shadow-sm'
                        : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                    }`}
                  >
                    <span className={currentView === item.name ? 'text-blue-600' : 'text-slate-400'}>
                      {item.icon}
                    </span>
                    {item.name}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      <div className="p-4 border-t border-slate-100">
        <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-xl">
          <img
            src="https://picsum.photos/seed/wealthos-user/40/40"
            alt="Profile"
            className="w-10 h-10 rounded-full border border-slate-200"
          />
          <div className="overflow-hidden">
            <p className="text-sm font-bold text-slate-900 truncate">Ray Dalio</p>
            <p className="text-[10px] font-medium text-slate-500 uppercase">Pro Plan</p>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
