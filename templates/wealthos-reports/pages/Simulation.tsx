
import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Play, Settings2 } from 'lucide-react';

const SIM_DATA = [
  { year: '2024', low: 2.1, mid: 2.1, high: 2.1 },
  { year: '2025', low: 2.0, mid: 2.2, high: 2.4 },
  { year: '2026', low: 1.9, mid: 2.4, high: 2.8 },
  { year: '2027', low: 1.8, mid: 2.7, high: 3.3 },
  { year: '2028', low: 1.9, mid: 3.0, high: 4.1 },
  { year: '2029', low: 2.0, mid: 3.4, high: 5.2 },
  { year: '2030', low: 2.2, mid: 4.0, high: 6.8 },
];

const Simulation: React.FC = () => {
  return (
    <div className="space-y-6 pb-12">
      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-8 flex flex-col lg:flex-row gap-8">
         <div className="flex-1">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Monte Carlo Projection</h3>
            <h2 className="text-3xl font-extrabold text-slate-900 mb-6">Scenario Modeling</h2>
            <div className="h-96 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={SIM_DATA}>
                  <defs>
                    <linearGradient id="colorHigh" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.1}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="year" axisLine={false} tickLine={false} tick={{ fontSize: 12, fontWeight: 600, fill: '#64748b' }} dy={10} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fontWeight: 600, fill: '#64748b' }} tickFormatter={(val) => `$${val}M`} />
                  <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }} />
                  <Area type="monotone" dataKey="high" stroke="#3b82f6" strokeWidth={0} fillOpacity={1} fill="url(#colorHigh)" />
                  <Area type="monotone" dataKey="mid" stroke="#3b82f6" strokeWidth={3} fill="transparent" strokeDasharray="5 5" />
                  <Area type="monotone" dataKey="low" stroke="#f43f5e" strokeWidth={2} fill="transparent" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="flex justify-center gap-8 mt-4">
              <div className="flex items-center gap-2"><div className="w-3 h-1 bg-blue-500" /> <span className="text-xs font-bold text-slate-500 uppercase">P95 Outcome</span></div>
              <div className="flex items-center gap-2"><div className="w-3 h-1 bg-blue-500 border-dashed border-t-2" /> <span className="text-xs font-bold text-slate-500 uppercase">Median Path</span></div>
              <div className="flex items-center gap-2"><div className="w-3 h-1 bg-rose-500" /> <span className="text-xs font-bold text-slate-500 uppercase">P5 Stress Case</span></div>
            </div>
         </div>

         <div className="w-full lg:w-80 bg-slate-50 rounded-2xl border border-slate-200 p-6">
            <div className="flex items-center justify-between mb-8">
               <span className="text-xs font-bold text-slate-900 uppercase">Simulation Parameters</span>
               <Settings2 size={18} className="text-slate-400" />
            </div>
            <div className="space-y-8">
               <div className="space-y-3">
                  <div className="flex justify-between text-[11px] font-bold text-slate-500"><span>TERM</span><span className="text-blue-600">10 YEARS</span></div>
                  <input type="range" className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600" />
               </div>
               <div className="space-y-3">
                  <div className="flex justify-between text-[11px] font-bold text-slate-500"><span>ANNUAL SAVING</span><span className="text-blue-600">$120k</span></div>
                  <input type="range" className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600" />
               </div>
               <div className="space-y-3">
                  <div className="flex justify-between text-[11px] font-bold text-slate-500"><span>RISK LEVEL</span><span className="text-blue-600">AGGRESSIVE</span></div>
                  <input type="range" className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600" />
               </div>
               <button className="w-full py-4 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold text-sm shadow-xl shadow-blue-200 flex items-center justify-center gap-2 transition-all">
                  <Play size={16} fill="white" /> Run Scenario
               </button>
            </div>
         </div>
      </div>
    </div>
  );
};

export default Simulation;
