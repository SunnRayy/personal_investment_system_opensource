
import React from 'react';

const Header: React.FC = () => {
  return (
    <header className="bg-white border-b border-gray-100 h-16 px-6 md:px-8 flex items-center justify-between sticky top-0 z-40">
      <div className="flex items-center gap-4">
        <button className="md:hidden text-gray-500 hover:text-gray-700">
          <span className="material-symbols-outlined">menu</span>
        </button>
        <button className="hidden md:flex items-center justify-center p-2 rounded-lg text-gray-400 hover:bg-gray-50 transition-colors">
          <span className="material-symbols-outlined text-[22px]">subject</span>
        </button>
      </div>

      <div className="flex flex-col items-center text-center">
        <h2 className="text-sm font-bold text-gray-900 leading-tight">Welcome back, Ray</h2>
        <p className="text-[11px] text-gray-400 font-medium">Here's your financial overview for today.</p>
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden lg:flex items-center gap-2">
            <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">Period</span>
            <button className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-gray-200 rounded text-xs font-bold text-gray-700 hover:border-gray-300 transition-colors">
                1M
                <span className="material-symbols-outlined text-[16px]">expand_more</span>
            </button>
        </div>
        
        <div className="h-6 w-px bg-gray-200 mx-2 hidden sm:block"></div>

        <div className="flex items-center bg-gray-50 rounded-full p-1 border border-gray-100">
          <button className="flex items-center justify-center h-6 w-6 rounded-full bg-white shadow-sm ring-1 ring-gray-200">
            <div className="w-1.5 h-1.5 rounded-full bg-yellow-400"></div>
          </button>
          <button className="p-1 text-gray-400 hover:text-gray-600">
            <span className="material-symbols-outlined text-[14px]">refresh</span>
          </button>
        </div>

        <button className="flex items-center gap-1 px-2.5 py-1.5 border border-gray-200 rounded text-[10px] font-bold text-gray-500 hover:bg-gray-50">
          EN <span className="material-symbols-outlined text-[14px]">language</span>
        </button>
      </div>
    </header>
  );
};

export default Header;
