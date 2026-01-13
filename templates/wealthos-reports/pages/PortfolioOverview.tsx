
import React from 'react';
import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts';
import { MetricCard } from '../components/DashboardCards';

const HEALTH_CHART_DATA = [
  { month: 'Jan', value: 2800000 },
  { month: 'Feb', value: 2950000 },
  { month: 'Mar', value: 3100000 },
  { month: 'Apr', value: 3050000 },
  { month: 'May', value: 3400000 },
  { month: 'Jun', value: 3800000 },
  { month: 'Jul', value: 4100000 },
  { month: 'Aug', value: 4350000 },
  { month: 'Sep', value: 4600000 },
  { month: 'Oct', value: 4800000 },
  { month: 'Nov', value: 5050000 },
  { month: 'Dec', value: 5240000 },
];

const PortfolioOverview: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Hero: Net Worth History */}
      <div className="bg-white rounded-[32px] border border-slate-200 shadow-sm p-10 relative overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-1 bg-amber-400/50" />
        <div className="flex flex-col mb-10">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-1">Total Net Worth</span>
          <div className="flex items-baseline gap-4">
            <h2 className="text-5xl font-extrabold text-slate-900 tracking-tight">$5,240,000</h2>
            <div className="flex items-center text-emerald-500 font-bold text-sm px-2.5 py-1 bg-emerald-50 rounded-full border border-emerald-100">
              <span className="mr-0.5">↑</span> 2.1%
            </div>
            <span className="text-sm font-semibold text-slate-400">this month</span>
          </div>
        </div>
        
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={HEALTH_CHART_DATA}>
              <defs>
                <linearGradient id="healthGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#2563eb" stopOpacity={0.15}/>
                  <stop offset="100%" stopColor="#2563eb" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <XAxis dataKey="month" hide />
              <YAxis hide domain={['dataMin - 100000', 'dataMax + 100000']} />
              <Tooltip 
                contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}
                formatter={(val: number) => `$${(val / 1000000).toFixed(2)}M`}
              />
              <Area 
                type="monotone" 
                dataKey="value" 
                stroke="#2563eb" 
                strokeWidth={4} 
                fillOpacity={1} 
                fill="url(#healthGradient)" 
                strokeLinecap="round"
              />
            </AreaChart>
          </ResponsiveContainer>
          <div className="flex justify-between mt-4 px-2 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
            {HEALTH_CHART_DATA.map(d => <span key={d.month}>{d.month}</span>)}
          </div>
        </div>
      </div>

      {/* Middle: Four Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[
          { label: 'YTD Return', val: '+12.4%', color: 'emerald' },
          { label: 'Holdings', val: '13', color: 'slate' },
          { label: 'Cash Reserves', val: '$1,200,000', color: 'slate' },
          { label: 'Portfolio XIRR', val: '18.4%', color: 'slate' },
        ].map((stat) => (
          <div key={stat.label} className="bg-white p-6 rounded-2xl border border-slate-200 border-l-[6px] border-l-amber-400/40 shadow-sm hover:shadow-md transition-all">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-4">{stat.label}</p>
            <p className={`text-3xl font-extrabold tracking-tight ${stat.color === 'emerald' ? 'text-emerald-500' : 'text-slate-900'}`}>{stat.val}</p>
          </div>
        ))}
      </div>

      {/* Bottom Grid: Performance List and Allocation Circle */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7 bg-white p-8 rounded-[32px] border border-slate-200 shadow-sm">
           <div className="flex justify-between items-center mb-8">
              <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">Performance by Asset Class</h3>
              <span className="text-[10px] font-bold text-slate-500 bg-slate-100 px-2 py-1 rounded">Last 12 Months</span>
           </div>
           <div className="space-y-6">
              {[
                { label: 'Public Equity', val: '14.2%', color: 'bg-blue-600', w: '85%' },
                { label: 'Fixed Income', val: '4.8%', color: 'bg-blue-400', w: '35%' },
                { label: 'Alternatives', val: '9.1%', color: 'bg-amber-400', w: '55%' },
                { label: 'Real Estate', val: '6.5%', color: 'bg-indigo-500', w: '42%' },
                { label: 'Cash / Equiv', val: '3.2%', color: 'bg-emerald-500', w: '20%' },
              ].map((item) => (
                <div key={item.label} className="space-y-2">
                  <div className="flex justify-between text-[11px] font-bold">
                    <span className="text-slate-600 uppercase">{item.label}</span>
                    <span className="text-slate-900">{item.val}</span>
                  </div>
                  <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                    <div className={`${item.color} h-full rounded-full transition-all duration-1000`} style={{ width: item.w }}></div>
                  </div>
                </div>
              ))}
           </div>
        </div>

        <div className="lg:col-span-5 bg-white p-8 rounded-[32px] border border-slate-200 shadow-sm">
           <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-8">Allocation Breakdown</h3>
           <div className="flex flex-col items-center justify-center h-full pb-8">
              <div className="w-48 h-48 rounded-full border-[14px] border-slate-50 flex items-center justify-center relative mb-8">
                 <div className="absolute inset-0 rounded-full border-[14px] border-blue-600 border-r-transparent border-b-transparent rotate-[45deg]" />
                 <div className="absolute inset-0 rounded-full border-[14px] border-amber-400 border-l-transparent border-t-transparent -rotate-[15deg]" />
                 <div className="flex flex-col items-center">
                   <span className="text-3xl font-extrabold text-slate-900">100%</span>
                   <span className="text-[10px] font-bold text-slate-400 uppercase">Invested</span>
                 </div>
              </div>
              <div className="grid grid-cols-2 gap-x-8 gap-y-3 w-full px-4">
                 {[
                   { l: 'Stocks', p: '45%', c: 'bg-blue-600' },
                   { l: 'Bonds', p: '30%', c: 'bg-blue-300' },
                   { l: 'Alts', p: '15%', c: 'bg-amber-400' },
                   { l: 'Cash', p: '10%', c: 'bg-emerald-500' },
                 ].map(item => (
                   <div key={item.l} className="flex justify-between items-center">
                     <div className="flex items-center gap-2">
                       <div className={`w-2.5 h-2.5 rounded-full ${item.c}`} />
                       <span className="text-xs font-semibold text-slate-500">{item.l}</span>
                     </div>
                     <span className="text-xs font-bold text-slate-900">{item.p}</span>
                   </div>
                 ))}
              </div>
           </div>
        </div>
      </div>
    </div>
  );
};

export default PortfolioOverview;
