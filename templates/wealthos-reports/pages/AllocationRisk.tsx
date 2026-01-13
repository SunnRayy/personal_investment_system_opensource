
import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, AreaChart, Area } from 'recharts';
import { MetricCard } from '../components/DashboardCards';
import { MoreHorizontal, Filter } from 'lucide-react';

const ASSET_ALLOCATION_DATA = [
  { name: 'Equities', value: 55, color: '#3b82f6' },
  { name: 'Fixed Income', value: 25, color: '#f59e0b' },
  { name: 'Real Estate', value: 10, color: '#10b981' },
  { name: 'Alternatives', value: 5, color: '#8b5cf6' },
  { name: 'Cash', value: 5, color: '#94a3b8' },
];

const DRAWDOWN_DATA = [
  { month: 'Jan', value: -2.0 },
  { month: 'Feb', value: -5.0 },
  { month: 'Mar', value: -3.0 },
  { month: 'Apr', value: -8.0 },
  { month: 'May', value: -4.0 },
  { month: 'Jun', value: -1.0 },
  { month: 'Jul', value: -6.0 },
  { month: 'Aug', value: -9.0 },
  { month: 'Sep', value: -5.0 },
  { month: 'Oct', value: -2.0 },
  { month: 'Nov', value: -1.0 },
  { month: 'Dec', value: -2.4 },
];

const AllocationRisk: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Asset Allocation Card */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">Asset Allocation</h3>
              <p className="text-2xl font-extrabold text-slate-900 mt-1">Top-Level View</p>
            </div>
            <button className="p-2 text-slate-400 hover:bg-slate-50 rounded-lg">
              <MoreHorizontal size={20} />
            </button>
          </div>
          
          <div className="flex flex-col sm:flex-row items-center gap-8 h-64">
            <div className="relative w-48 h-48">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={ASSET_ALLOCATION_DATA}
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                    stroke="none"
                  >
                    {ASSET_ALLOCATION_DATA.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span className="text-[10px] font-bold text-slate-400 uppercase">Total</span>
                <span className="text-lg font-bold">100%</span>
              </div>
            </div>
            <div className="flex-1 space-y-2">
              {ASSET_ALLOCATION_DATA.map(item => (
                <div key={item.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="text-sm font-medium text-slate-600">{item.name}</span>
                  </div>
                  <span className="text-sm font-bold text-slate-900">{item.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Detailed Breakdown Card */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">Detailed Breakdown</h3>
              <p className="text-2xl font-extrabold text-slate-900 mt-1">Sub-Class View</p>
            </div>
            <button className="p-2 text-slate-400 hover:bg-slate-50 rounded-lg">
              <Filter size={20} />
            </button>
          </div>
          
          <div className="flex flex-col sm:flex-row items-center gap-8 h-64">
            <div className="relative w-48 h-48">
               {/* Reusing pie chart for demonstration */}
               <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={ASSET_ALLOCATION_DATA.slice(0, 3)}
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                    stroke="none"
                  >
                    {ASSET_ALLOCATION_DATA.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span className="text-[10px] font-bold text-slate-400 uppercase">Equity</span>
                <span className="text-lg font-bold">55%</span>
              </div>
            </div>
            <div className="flex-1 space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-slate-500">US Large Cap</span> <span className="font-bold">35%</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Intl Developed</span> <span className="font-bold">20%</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Emerging Mkts</span> <span className="font-bold">15%</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Govt Bonds</span> <span className="font-bold">18%</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Corp Credit</span> <span className="font-bold">12%</span></div>
            </div>
          </div>
        </div>
      </div>

      {/* Max Drawdown Chart */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8">
        <div className="flex justify-between items-start mb-8">
          <div>
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">Risk Analysis</h3>
            <div className="flex items-center gap-3 mt-1">
              <p className="text-2xl font-extrabold text-slate-900">Max Drawdown History</p>
              <span className="px-2 py-0.5 bg-rose-50 text-rose-600 text-[10px] font-bold rounded-full border border-rose-100 uppercase">
                Current: -2.4%
              </span>
            </div>
          </div>
          <div className="flex gap-2">
            {['1Y', '3Y', '5Y'].map(t => (
              <button key={t} className={`px-4 py-1.5 text-xs font-bold rounded-lg transition-all ${t === '3Y' ? 'bg-amber-500 text-white shadow-lg shadow-amber-500/20' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'}`}>
                {t}
              </button>
            ))}
          </div>
        </div>
        
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={DRAWDOWN_DATA}>
              <defs>
                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.1}/>
                  <stop offset="95%" stopColor="#f43f5e" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fontSize: 11, fontWeight: 600, fill: '#94a3b8' }} dy={10} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fontWeight: 600, fill: '#94a3b8' }} tickFormatter={(val) => `${val}%`} />
              <Tooltip 
                contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}
                itemStyle={{ color: '#f43f5e', fontWeight: 700 }}
              />
              <Area type="monotone" dataKey="value" stroke="#f43f5e" strokeWidth={3} fillOpacity={1} fill="url(#colorValue)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <MetricCard label="Sharpe Ratio" value="1.84" trend={0.12} description="Risk-adjusted return vs Benchmark" accentColor="amber" />
        <MetricCard label="Volatility (Ann)" value="12.4%" trend={-1.5} description="Portfolio annualized standard deviation" accentColor="blue" />
        <MetricCard label="Sortino Ratio" value="2.15" trend={0.08} description="Downside risk-adjusted return" accentColor="indigo" />
      </div>
    </div>
  );
};

export default AllocationRisk;
