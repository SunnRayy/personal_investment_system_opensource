
import React from 'react';
import { RefreshCcw, Languages, Moon, ChevronDown, Bell } from 'lucide-react';
import { ReportView } from '../types';

interface HeaderProps {
  title: string;
}

const Header: React.FC<HeaderProps> = ({ title }) => {
  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8 shrink-0">
      <div>
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
          {title}
        </h2>
      </div>

      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg">
          <span className="text-xs font-medium text-slate-500">Period:</span>
          <button className="flex items-center gap-1 text-xs font-bold text-slate-900">
            YTD <ChevronDown size={14} />
          </button>
        </div>

        <div className="flex items-center gap-1">
          <button className="p-2 text-slate-400 hover:text-slate-600 transition-colors">
            <RefreshCcw size={18} />
          </button>
          <button className="p-2 text-slate-400 hover:text-slate-600 transition-colors">
            <Bell size={18} />
          </button>
          <button className="p-2 text-slate-400 hover:text-slate-600 transition-colors">
            <Moon size={18} />
          </button>
        </div>

        <div className="h-6 w-[1px] bg-slate-200" />

        <button className="flex items-center gap-2 px-3 py-1.5 border border-slate-200 rounded-lg hover:bg-slate-50 transition-all">
          <span className="text-xs font-bold">EN</span>
          <Languages size={16} className="text-slate-400" />
        </button>
      </div>
    </header>
  );
};

export default Header;
