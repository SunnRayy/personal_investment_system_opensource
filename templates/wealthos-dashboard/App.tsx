
import React from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import StatCard from './components/StatCard';
import { NetWorthChart, AllocationChart } from './components/Charts';
import { RECENT_ACTIVITY, ALLOCATION_DATA } from './constants';

const App: React.FC = () => {
  return (
    <div className="flex min-h-screen bg-[#F9FAFB]">
      <Sidebar />
      
      <div className="flex-1 flex flex-col md:ml-64 transition-all duration-300">
        <Header />
        
        <main className="flex-1 p-6 md:p-8">
          {/* Main Net Worth Section */}
          <section className="mb-8">
            <div className="bg-white rounded-2xl shadow-sm border-[2px] border-[#EAD588] overflow-hidden relative">
              <div className="p-8 pb-4 relative z-10">
                <h2 className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em] mb-3">Net Worth</h2>
                <div className="text-5xl font-bold text-gray-900 tracking-tighter mb-4">$1,561,662.82</div>
                <div className="flex items-center gap-2 text-sm font-semibold">
                  <span className="material-symbols-outlined text-[#10B981] text-[20px] font-bold">arrow_upward</span>
                  <span className="text-[#10B981]">+ $23,456 (+2.1%)</span>
                  <span className="text-gray-400 font-medium">this month</span>
                </div>
              </div>
              
              <div className="h-64 md:h-72 w-full mt-4 -mb-1">
                <NetWorthChart />
              </div>
            </div>
          </section>

          {/* Stats Grid */}
          <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <StatCard label="YTD Return" value="+15.3%" colorClass="text-[#10B981]" />
            <StatCard label="Holdings" value="13" />
            <StatCard label="Cash" value="$45,000.00" />
            <StatCard label="XIRR" value="12.4%" colorClass="text-[#3B82F6]" />
          </section>

          {/* Secondary Grid */}
          <section className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Allocation Breakdown */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 flex flex-col overflow-hidden">
              <div className="px-6 py-5 border-b border-gray-50">
                <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Allocation Breakdown</h3>
              </div>
              <div className="flex-grow flex flex-col sm:flex-row items-center p-8 gap-8">
                <AllocationChart />
                <div className="flex flex-col justify-center gap-5 flex-1 w-full">
                  {ALLOCATION_DATA.map((item) => (
                    <div key={item.name} className="flex items-center justify-between group">
                      <div className="flex items-center gap-3">
                        <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }}></div>
                        <span className="text-sm font-medium text-gray-600 group-hover:text-gray-900 transition-colors">{item.name}</span>
                      </div>
                      <span className="text-sm font-bold text-gray-900">{item.value}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 flex flex-col overflow-hidden">
              <div className="px-6 py-5 border-b border-gray-50">
                <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Recent Activity</h3>
              </div>
              <div className="flex-grow overflow-y-auto">
                {RECENT_ACTIVITY.map((activity) => (
                  <div key={activity.id} className="flex items-center justify-between p-5 border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors cursor-pointer group">
                    <div className="flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-transform group-hover:scale-105 ${
                        activity.type === 'buy' ? 'bg-blue-50 text-blue-600' : 
                        activity.type === 'deposit' ? 'bg-green-50 text-green-600' : 'bg-yellow-50 text-yellow-600'
                      }`}>
                        <span className="material-symbols-outlined text-[20px]">{activity.icon}</span>
                      </div>
                      <div>
                        <div className="text-sm font-bold text-gray-900">{activity.asset}</div>
                        <div className="text-[11px] font-bold text-gray-400 uppercase mt-0.5 tracking-tight">{activity.type}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`text-sm font-bold ${activity.amount > 0 ? 'text-[#10B981]' : 'text-gray-900'}`}>
                        {activity.amount > 0 ? '+' : ''} {activity.amount.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
                      </div>
                      <div className="text-[11px] font-medium text-gray-400 mt-0.5">{activity.date}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
};

export default App;
