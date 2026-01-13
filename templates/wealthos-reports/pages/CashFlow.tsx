
import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import { Calendar, Download, ChevronDown } from 'lucide-react';

const INCOME_EXPENSE_DATA = [
  { month: 'JAN', net: 20000 },
  { month: 'FEB', net: 28000 },
  { month: 'MAR', net: 25000 },
  { month: 'APR', net: 32000 },
  { month: 'MAY', net: 30000 },
  { month: 'JUN', net: 35000 },
  { month: 'JUL', net: 33000 },
  { month: 'AUG', net: 38000 },
  { month: 'SEP', net: 42000 },
  { month: 'OCT', net: 45000 },
  { month: 'NOV', net: 43000 },
  { month: 'DEC', net: 48000 },
];

const FORECAST_DATA = [
  { month: 'Q1', value: 1200000, label: 'Stable' },
  { month: 'Q2', value: 1400000, label: 'Bonus Inflow' },
  { month: 'Q3', value: 1600000, label: 'Tax Outflow' },
  { month: 'Q4', value: 2400000, label: 'Holiday' },
];

const CashFlow: React.FC = () => {
  return (
    <div className="space-y-6 pb-12">
      {/* Breadcrumb and Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <nav className="flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">
            <span className="hover:text-slate-600 cursor-pointer">Portfolio</span>
            <span className="text-slate-300">›</span>
            <span className="text-blue-600">Cash Flow Analysis</span>
          </nav>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Cash Flow Analysis</h1>
          <p className="text-sm font-medium text-slate-500 mt-1">Visualizing capital movement and forecasting liquidity.</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="flex items-center gap-2 px-4 py-2.5 text-xs font-bold bg-white border border-slate-200 rounded-xl shadow-sm hover:bg-slate-50 transition-all">
            <Calendar size={14} className="text-slate-400" />
            Last 12 Months
            <ChevronDown size={14} className="text-slate-400" />
          </button>
          <button className="flex items-center gap-2 px-5 py-2.5 text-xs font-bold bg-blue-600 text-white rounded-xl shadow-lg shadow-blue-200 hover:bg-blue-700 transition-all">
            <Download size={14} />
            Export Report
          </button>
        </div>
      </div>

      {/* Hero: Capital Flow Diagram (Sankey-style) */}
      <div className="bg-white rounded-[32px] border border-slate-200 shadow-sm p-10">
        <div className="flex justify-between items-center mb-10">
          <div>
            <h3 className="text-lg font-bold text-slate-900">Capital Flow Diagram</h3>
            <p className="text-xs font-medium text-slate-400">Inflow breakdown (Salary, RSU, Dividends) → Outflow allocation</p>
          </div>
          <div className="flex gap-6">
            <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-emerald-500" /><span className="text-[10px] font-bold text-slate-500 uppercase">Income</span></div>
            <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-rose-500" /><span className="text-[10px] font-bold text-slate-500 uppercase">Expenses</span></div>
            <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-blue-500" /><span className="text-[10px] font-bold text-slate-500 uppercase">Savings/Inv</span></div>
          </div>
        </div>

        <div className="relative h-64 w-full flex justify-between items-stretch">
          {/* SVG Paths for Flows */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none" preserveAspectRatio="none">
            {/* Salary to Living/Tax/Inv */}
            <path d="M 120 40 C 400 40, 500 30, 800 35" stroke="#10b981" strokeWidth="12" fill="none" opacity="0.15" />
            <path d="M 120 40 C 400 40, 500 110, 800 105" stroke="#10b981" strokeWidth="8" fill="none" opacity="0.1" />
            <path d="M 120 40 C 400 40, 500 190, 800 185" stroke="#10b981" strokeWidth="15" fill="none" opacity="0.1" />
            
            {/* RSU to Inv */}
            <path d="M 120 125 C 400 125, 500 190, 800 185" stroke="#10b981" strokeWidth="25" fill="none" opacity="0.15" />
            
            {/* Dividends to Inv */}
            <path d="M 120 210 C 400 210, 500 190, 800 185" stroke="#10b981" strokeWidth="10" fill="none" opacity="0.15" />
          </svg>

          {/* Left Column: Inflows */}
          <div className="flex flex-col justify-around z-10 w-40">
            <div className="flex items-center gap-3">
              <div className="w-1.5 h-16 bg-emerald-500 rounded-full" />
              <div className="bg-emerald-50/50 p-2 rounded-lg flex-1">
                <p className="text-[10px] font-bold text-emerald-600 uppercase">Salary (£220k)</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-1.5 h-20 bg-emerald-500 rounded-full" />
              <div className="bg-emerald-50/50 p-2 rounded-lg flex-1">
                <p className="text-[10px] font-bold text-emerald-600 uppercase">RSU (£129k)</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-1.5 h-10 bg-emerald-500 rounded-full" />
              <div className="bg-emerald-50/50 p-2 rounded-lg flex-1">
                <p className="text-[10px] font-bold text-emerald-600 uppercase">Dividends (£40k)</p>
              </div>
            </div>
          </div>

          {/* Right Column: Outflows */}
          <div className="flex flex-col justify-around z-10 w-40 text-right">
            <div className="flex items-center gap-3 justify-end">
              <div className="bg-rose-50/50 p-2 rounded-lg flex-1">
                <p className="text-[10px] font-bold text-rose-600 uppercase">Living (£60k)</p>
              </div>
              <div className="w-1.5 h-12 bg-rose-500 rounded-full" />
            </div>
            <div className="flex items-center gap-3 justify-end">
              <div className="bg-rose-50/50 p-2 rounded-lg flex-1">
                <p className="text-[10px] font-bold text-rose-600 uppercase">Tax (£89k)</p>
              </div>
              <div className="w-1.5 h-16 bg-rose-500 rounded-full" />
            </div>
            <div className="flex items-center gap-3 justify-end">
              <div className="bg-blue-50/50 p-2 rounded-lg flex-1">
                <p className="text-[10px] font-bold text-blue-600 uppercase">Investments (£205k)</p>
              </div>
              <div className="w-1.5 h-24 bg-blue-500 rounded-full" />
            </div>
          </div>
        </div>
      </div>

      {/* Row 2: Analysis Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-[32px] border border-slate-200 shadow-sm p-8">
           <div className="flex justify-between items-start mb-8">
              <div>
                <h3 className="text-lg font-bold text-slate-900">Income vs Expense History</h3>
                <p className="text-xs font-medium text-slate-400">Monthly Net Performance</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-bold text-emerald-500">Net +$1.2M</p>
                <p className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">YTD Accumulation</p>
              </div>
           </div>
           
           <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={INCOME_EXPENSE_DATA}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fontSize: 9, fontWeight: 700, fill: '#94a3b8' }} />
                  <YAxis hide />
                  <Tooltip 
                    contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}
                    itemStyle={{ fontSize: '11px', fontWeight: 700 }}
                  />
                  <Line type="monotone" dataKey="net" stroke="#3b82f6" strokeWidth={3} dot={false} />
                </LineChart>
              </ResponsiveContainer>
           </div>
           
           <div className="flex justify-center gap-8 mt-4">
              <div className="flex items-center gap-2"><div className="w-2.5 h-2.5 rounded bg-emerald-500" /><span className="text-[9px] font-bold text-slate-500 uppercase">Income</span></div>
              <div className="flex items-center gap-2"><div className="w-2.5 h-2.5 rounded bg-rose-500" /><span className="text-[9px] font-bold text-slate-500 uppercase">Expense</span></div>
              <div className="flex items-center gap-2"><div className="w-4 h-0.5 bg-blue-500" /><span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">Net Trend</span></div>
           </div>
        </div>

        <div className="bg-white rounded-[32px] border border-slate-200 shadow-sm p-8">
           <div className="flex justify-between items-start mb-8">
              <div>
                <h3 className="text-lg font-bold text-slate-900">12-Month Cash Forecast</h3>
                <p className="text-xs font-medium text-slate-400">Projected Liquidity</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-bold text-blue-600">Proj. +$2.4M</p>
                <p className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">~ +8% vs Prior Year</p>
              </div>
           </div>
           
           <div className="h-64 w-full relative">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={FORECAST_DATA}>
                  <defs>
                    <linearGradient id="forecastGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fontSize: 9, fontWeight: 700, fill: '#94a3b8' }} />
                  <YAxis hide />
                  <Tooltip 
                    contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}
                  />
                  <Area type="stepAfter" dataKey="value" stroke="#3b82f6" strokeWidth={4} fill="url(#forecastGradient)" />
                </AreaChart>
              </ResponsiveContainer>
              
              {/* Floating Highlight Tag */}
              <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2">
                <div className="bg-slate-900 text-white text-[10px] font-bold px-3 py-1.5 rounded-lg shadow-xl flex flex-col items-center">
                   <span>$1.8M (June)</span>
                   <div className="w-1 h-1 bg-blue-500 rounded-full mt-1 border border-white" />
                </div>
              </div>
           </div>
           
           <div className="grid grid-cols-4 gap-2 mt-4 text-center">
              {FORECAST_DATA.map(d => (
                <div key={d.month}>
                  <p className="text-[10px] font-bold text-slate-900">{d.month}</p>
                  <p className="text-[8px] font-bold text-slate-400 uppercase tracking-tighter">{d.label}</p>
                </div>
              ))}
           </div>
        </div>
      </div>

      {/* Row 3: Smaller Insight Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
         <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
            <div className="flex items-center gap-4">
               <div className="p-2.5 bg-emerald-50 rounded-xl text-emerald-600">
                  <div className="w-5 h-5 rounded-full border-2 border-emerald-500 border-r-transparent animate-spin-slow" />
               </div>
               <div>
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-0.5">Income Mix</p>
                  <p className="text-lg font-extrabold text-slate-900">Highly Diversified</p>
               </div>
            </div>
            <div className="w-10 h-10 rounded-full bg-emerald-50 flex items-center justify-center">
               <div className="w-6 h-6 rounded-full bg-emerald-500 opacity-20" />
            </div>
         </div>
         
         <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
            <div className="flex items-center gap-4">
               <div className="p-2.5 bg-rose-50 rounded-xl text-rose-600">
                  <div className="w-5 h-5 bg-rose-500 rounded-md opacity-80" />
               </div>
               <div>
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-0.5">Expense Efficiency</p>
                  <p className="text-lg font-extrabold text-slate-900">Optimized (Low)</p>
               </div>
            </div>
            <div className="w-10 h-10 rounded-full bg-rose-50 flex items-center justify-center">
               <div className="w-6 h-6 rounded-full bg-rose-500 opacity-20" />
            </div>
         </div>
         
         <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
            <div className="flex items-center gap-4">
               <div className="p-2.5 bg-blue-50 rounded-xl text-blue-600">
                  <div className="flex gap-0.5 items-end h-5">
                    <div className="w-1.5 h-2 bg-blue-500 rounded-sm" />
                    <div className="w-1.5 h-4 bg-blue-500 rounded-sm" />
                    <div className="w-1.5 h-3 bg-blue-500 rounded-sm" />
                  </div>
               </div>
               <div>
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-0.5">Top Categories</p>
                  <p className="text-lg font-extrabold text-slate-900">Lifestyle Focus</p>
               </div>
            </div>
            <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center">
               <div className="w-6 h-6 rounded-full bg-blue-500 opacity-20" />
            </div>
         </div>
      </div>
    </div>
  );
};

export default CashFlow;
