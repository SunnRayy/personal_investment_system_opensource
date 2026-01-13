
import React from 'react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  ScatterChart, 
  Scatter, 
  Cell, 
  ZAxis,
  XAxis as RechartsXAxis,
  YAxis as RechartsYAxis
} from 'recharts';
import { Download, Play, Activity, AlertCircle, MoreVertical } from 'lucide-react';

const ALLOCATION_DATA = [
  { name: 'Equity', target: 50, current: 62 },
  { name: 'Fixed Inc', target: 35, current: 25 },
  { name: 'Alts', target: 10, current: 8 },
  { name: 'Cash', target: 5, current: 5 },
];

const DRIFT_DATA = [
  { class: '0%', drift: 6 },
  { class: '1%', drift: -5 },
  { class: '2%', drift: -0.5 },
  { class: '3%', drift: -1 },
];

const CORRELATION_MATRIX = [
  { label: 'US Eq', values: [1.0, 0.82, -0.12, 0.45, 0.05], classes: ['US EQ', 'INTL EQ', 'BONDS', 'REITS', 'GOLD'] },
  { label: 'Intl Eq', values: [0.82, 1.0, -0.08, 0.38, 0.12], classes: ['US EQ', 'INTL EQ', 'BONDS', 'REITS', 'GOLD'] },
  { label: 'Bonds', values: [-0.12, -0.08, 1.0, 0.15, 0.22], classes: ['US EQ', 'INTL EQ', 'BONDS', 'REITS', 'GOLD'] },
];

const RISK_RETURN_DATA = [
  { x: 5, y: 3, name: 'Total', color: '#6366f1' },
  { x: 18, y: 15, name: 'Tech', color: '#3b82f6', hollow: true },
];

const Compass: React.FC = () => {
  return (
    <div className="space-y-6 pb-12">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Action Compass Strategy</h1>
          <p className="text-sm font-medium text-slate-500 mt-1">Tactical rebalancing and regime analysis for Portfolio #1024</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="flex items-center gap-2 px-5 py-2 text-xs font-bold bg-white border border-slate-200 rounded-xl shadow-sm hover:bg-slate-50 transition-all">
            <Download size={14} className="text-slate-400" />
            Export
          </button>
          <button className="flex items-center gap-2 px-5 py-2 text-xs font-bold bg-blue-600 text-white rounded-xl shadow-lg shadow-blue-200 hover:bg-blue-700 transition-all">
            <Play size={14} fill="white" />
            Run Simulation
          </button>
        </div>
      </div>

      {/* Hero: Current Regime Card */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-[28px] p-8 text-white shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 p-12 opacity-10 pointer-events-none">
          <Activity size={200} />
        </div>
        
        <div className="flex flex-col lg:flex-row items-center gap-8 relative z-10">
          <div className="flex items-start gap-5 flex-1">
            <div className="p-4 bg-white/20 rounded-2xl backdrop-blur-md">
              <Activity size={32} />
            </div>
            <div>
              <div className="flex items-center gap-3 mb-2">
                <h3 className="text-2xl font-bold tracking-tight">Current Regime: Cautious Rotation</h3>
                <span className="px-2.5 py-0.5 bg-white/20 text-[10px] font-bold rounded-full border border-white/30 uppercase tracking-wide">Updated 2h ago</span>
              </div>
              <p className="text-blue-50 text-sm leading-relaxed max-w-2xl opacity-90 font-medium">
                Market signals suggest reducing beta exposure in tech sectors while increasing quality duration in fixed income. Volatility remains elevated.
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-12 px-10 border-l border-white/20">
            <div>
              <p className="text-[10px] font-bold text-blue-200 uppercase tracking-widest mb-1">VIX INDEX</p>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-extrabold">18.42</span>
                <span className="text-xs font-bold text-rose-300 flex items-center">↑ 2.1%</span>
              </div>
            </div>
            <div>
              <p className="text-[10px] font-bold text-blue-200 uppercase tracking-widest mb-1">10Y TREASURY</p>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-extrabold">4.21%</span>
                <span className="text-xs font-bold text-emerald-300 flex items-center">↓ 0.05</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Row 2: Analysis Grids */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Target vs Current Allocation */}
        <div className="bg-white rounded-[28px] border border-slate-200 shadow-sm p-8">
          <div className="flex justify-between items-start mb-8">
            <div>
              <h3 className="text-lg font-bold text-slate-900">Target vs Current Allocation</h3>
              <p className="text-xs font-medium text-slate-400">Total Portfolio Value: $12.5M</p>
            </div>
            <button className="text-slate-400 hover:text-slate-600"><MoreVertical size={20} /></button>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={ALLOCATION_DATA} barGap={12}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 11, fontWeight: 600, fill: '#94a3b8' }} />
                <YAxis hide domain={[0, 80]} />
                <Tooltip cursor={{fill: '#f8fafc'}} contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }} />
                <Bar dataKey="target" fill="#cbd5e1" radius={[4, 4, 0, 0]} barSize={28} />
                <Bar dataKey="current" fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={28} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-6 mt-6">
            <div className="flex items-center gap-2"><div className="w-3 h-3 rounded bg-slate-300" /><span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Target</span></div>
            <div className="flex items-center gap-2"><div className="w-3 h-3 rounded bg-blue-500" /><span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Current</span></div>
          </div>
        </div>

        {/* Drift Analysis */}
        <div className="bg-white rounded-[28px] border border-slate-200 shadow-sm p-8">
          <div className="flex justify-between items-start mb-8">
            <div>
              <h3 className="text-lg font-bold text-slate-900">Drift Analysis</h3>
              <p className="text-xs font-medium text-slate-400">Red indicates >5% drift requiring action</p>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-rose-50 border border-rose-100 rounded-full text-rose-600">
              <AlertCircle size={14} />
              <span className="text-[10px] font-bold uppercase tracking-wide">2 Critical</span>
            </div>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={DRIFT_DATA}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="class" hide />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fontWeight: 600, fill: '#94a3b8' }} hide />
                <Tooltip cursor={{ fill: '#f8fafc' }} contentStyle={{ borderRadius: '12px', border: 'none' }} />
                <Bar dataKey="drift" radius={[4, 4, 4, 4]} barSize={36}>
                  {DRIFT_DATA.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={Math.abs(entry.drift) > 4 ? '#f43f5e' : '#94a3b8'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-between px-10 mt-2">
            {['0%', '1%', '2%', '3%'].map(l => (
              <span key={l} className="text-[10px] font-bold text-slate-400 uppercase">{l}</span>
            ))}
          </div>
          <div className="flex justify-between px-10 mt-4 text-[11px] font-bold">
            <span className="text-emerald-500">+1%</span>
            <span className="text-emerald-500">-1%</span>
            <span className="text-rose-500">-6%</span>
            <span className="text-emerald-500">+7%</span>
          </div>
        </div>
      </div>

      {/* Row 3: Matrix & Profile */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Asset Correlation Matrix */}
        <div className="lg:col-span-7 bg-white p-8 rounded-[28px] border border-slate-200 shadow-sm overflow-hidden">
          <h3 className="text-lg font-bold text-slate-900 mb-8">Asset Correlation Matrix</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-center border-separate border-spacing-2">
              <thead>
                <tr className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                  <th className="w-20"></th>
                  {['US EQ', 'INTL EQ', 'BONDS', 'REITS', 'GOLD'].map(h => (
                    <th key={h} className="pb-4">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {CORRELATION_MATRIX.map((row, i) => (
                  <tr key={i}>
                    <td className="text-left text-[11px] font-bold text-slate-500 uppercase py-2 pr-4">{row.label}</td>
                    {row.values.map((v, j) => {
                      const isHigh = v >= 0.8;
                      const isNeutral = v > 0 && v < 0.8;
                      const isNegative = v < 0;
                      const bgColor = v === 1 ? 'bg-blue-600 text-white' : 
                                      isHigh ? 'bg-blue-500 text-white' : 
                                      isNeutral ? 'bg-blue-100 text-blue-700' : 
                                      'bg-slate-50 text-slate-500';
                      return (
                        <td key={j} className={`p-4 rounded-xl text-xs font-bold ${bgColor}`}>
                          {v.toFixed(2)}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Risk / Return Profile */}
        <div className="lg:col-span-5 bg-white p-8 rounded-[28px] border border-slate-200 shadow-sm relative">
          <div className="flex justify-between items-center mb-8">
            <h3 className="text-lg font-bold text-slate-900">Risk / Return Profile</h3>
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-blue-500" />
              <span className="text-[10px] font-bold text-slate-500 uppercase">Current</span>
            </div>
          </div>
          
          <div className="h-64 w-full relative">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <RechartsXAxis type="number" dataKey="x" name="Risk" hide domain={[0, 25]} />
                <RechartsYAxis type="number" dataKey="y" name="Return" hide domain={[0, 20]} />
                <ZAxis range={[500, 1000]} />
                <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                <Scatter name="Assets" data={RISK_RETURN_DATA}>
                  {RISK_RETURN_DATA.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
            
            {/* Custom Labels on Chart Area */}
            <div className="absolute top-[80%] left-[15%]">
              <div className="px-3 py-1.5 bg-indigo-600 text-white text-[10px] font-bold rounded-full shadow-lg">Total</div>
            </div>
            <div className="absolute top-[25%] left-[82%]">
              <div className="px-3 py-1.5 border-2 border-blue-500 text-blue-600 text-[10px] font-bold rounded-full shadow-lg bg-white">Tech</div>
            </div>

            {/* Axis Titles Overlay */}
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 text-[9px] font-bold text-slate-400 uppercase tracking-widest">Risk (Vol)</div>
            <div className="absolute left-0 top-1/2 -translate-y-1/2 -rotate-90 text-[9px] font-bold text-slate-400 uppercase tracking-widest">Return (%)</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Compass;
