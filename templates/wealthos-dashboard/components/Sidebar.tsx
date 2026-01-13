
import React from 'react';
import { NAV_ITEMS } from '../constants';

const Sidebar: React.FC = () => {
  const sections = ['Main', 'Analysis', 'System'] as const;

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col h-screen fixed left-0 top-0 z-50 transition-transform duration-300 md:translate-x-0 -translate-x-full">
      <div className="p-6 flex items-center gap-3">
        <span className="material-symbols-outlined text-[#D4AF37] text-3xl font-bold">trending_up</span>
        <h1 className="text-xl font-bold text-gray-900 tracking-tight">WealthOS</h1>
      </div>

      <nav className="flex-1 px-4 space-y-8 overflow-y-auto pb-6">
        {sections.map((section) => (
          <div key={section}>
            <h3 className="px-3 text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-3">
              {section}
            </h3>
            <ul className="space-y-1">
              {NAV_ITEMS.filter((item) => item.section === section).map((item) => (
                <li key={item.label}>
                  <a
                    href="#"
                    className={`flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg transition-all duration-200 ${
                      item.isActive
                        ? 'bg-blue-50 text-blue-600'
                        : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                  >
                    <span className={`material-symbols-outlined text-[20px] ${item.isActive ? 'filled' : ''}`}>
                      {item.icon}
                    </span>
                    {item.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;
