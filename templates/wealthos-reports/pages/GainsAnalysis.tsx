
import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { MoreHorizontal, Download, Filter } from 'lucide-react';

const SUB_CLASS_GAINS = [
  { name: 'CN Equity', realized: 180, unrealized: 60 },
  { name: 'US Equity', realized: 100, unrealized: 30 },
  { name: 'HK ETF', realized: 5, unrealized: 15 },
  { name: 'Unknown', realized: 4, unrealized: 0 },
  { name: 'Bond', realized: 2, unrealized: 0 },
  { name: 'Crypto', realized: 0, unrealized: 10 },
  { name: 'Gold', realized: 12, unrealized: 4 },
  { name: 'Real Estate', realized: 3, unrealized: 0 },
];

const GainsAnalysis: React.FC = () => {
  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Realized vs. Unrealized Gains Analysis</h1>
          <div className="h-1.5 w-full bg-blue-500 rounded-full mt-2 opacity-30" />
        </div>
        <div className="flex items-center gap-2">
           <button className="flex items-center gap-2 px-4 py-2 text-sm font-bold bg-white border border-slate-200 rounded-xl hover:shadow-sm transition-all"><Filter size={16} /> Filter</button>
           <button className="flex items-center gap-2 px-4 py-2 text-sm font-bold bg-blue-600 text-white rounded-xl shadow-lg shadow-blue-600/20 hover:bg-blue-700 transition-all"><Download size={16} /> Export CSV</button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { l: 'Total Realized Gains', v: '¥328,698' },
          { l: 'Total Unrealized Gains', v: '¥97,089' },
          { l: 'Total Gains', v: '¥425,787' },
        ].map((stat, i) => (
          <div key={stat.l} className="bg-white p-8 rounded-2xl border border-slate-100 shadow-sm text-center">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">{stat.l}</p>
            <p className="text-4xl font-extrabold text-slate-900 tracking-tight">{stat.v}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
           <h3 className="text-lg font-bold text-slate-900 mb-8">Gains Breakdown</h3>
           <div className="h-72 w-full flex items-end justify-around pb-4">
              <div className="flex flex-col items-center group">
                 <div className="w-20 bg-emerald-400 rounded-t-lg h-56 transition-all hover:brightness-110 relative">
                   <span className="absolute -top-7 left-1/2 -translate-x-1/2 text-xs font-bold text-slate-500">¥328k</span>
                 </div>
                 <span className="mt-4 text-[10px] font-bold text-slate-400 uppercase">Realized</span>
              </div>
              <div className="flex flex-col items-center group">
                 <div className="w-20 bg-blue-400 rounded-t-lg h-24 transition-all hover:brightness-110 relative">
                   <span className="absolute -top-7 left-1/2 -translate-x-1/2 text-xs font-bold text-slate-500">¥97k</span>
                 </div>
                 <span className="mt-4 text-[10px] font-bold text-slate-400 uppercase">Unrealized</span>
              </div>
           </div>
        </div>

        <div className="lg:col-span-3 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
           <div className="flex justify-between items-center mb-6">
             <h3 className="text-lg font-bold text-slate-900">Sub-Class Level Trends</h3>
             <div className="flex gap-4">
                <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded bg-emerald-400" /><span className="text-[10px] font-bold text-slate-500 uppercase">Realized</span></div>
                <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded bg-blue-400" /><span className="text-[10px] font-bold text-slate-500 uppercase">Unrealized</span></div>
             </div>
           </div>
           <div className="h-72 w-full">
             <ResponsiveContainer width="100%" height="100%">
               <BarChart data={SUB_CLASS_GAINS}>
                 <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 9, fontWeight: 700, fill: '#94a3b8' }} angle={-30} textAnchor="end" height={60} />
                 <YAxis hide />
                 <Tooltip cursor={{ fill: '#f8fafc' }} contentStyle={{ borderRadius: '12px', border: 'none' }} />
                 <Bar dataKey="realized" stackId="a" fill="#34d399" radius={[0, 0, 0, 0]} />
                 <Bar dataKey="unrealized" stackId="a" fill="#60a5fa" radius={[4, 4, 0, 0]} />
               </BarChart>
             </ResponsiveContainer>
           </div>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
          <h3 className="text-xl font-bold text-slate-900">Lifetime Asset Performance</h3>
          <button className="text-xs font-bold text-blue-600 uppercase hover:underline">View Full Report</button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse min-w-[1000px]">
            <thead>
              <tr className="text-[10px] font-bold text-slate-400 uppercase tracking-widest border-b border-slate-100">
                <th className="px-6 py-4">Asset Name</th>
                <th className="px-4 py-4">Asset Class</th>
                <th className="px-4 py-4">Holding Period</th>
                <th className="px-4 py-4">Status</th>
                <th className="px-4 py-4 text-right">Total Invested</th>
                <th className="px-4 py-4 text-right">Current Value</th>
                <th className="px-4 py-4 text-right">Profit/Loss</th>
                <th className="px-4 py-4 text-right">Return %</th>
                <th className="px-6 py-4">Performance</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {[
                { name: '易方达中证500ETF联接发起式A', class: '股票', h: '4y 7m', status: 'Active', inv: '¥198,099', val: '¥152,567', pl: '¥87,037', ret: '43.94%', perf: 'Good' },
                { name: 'Amazon RSU', class: '股票', h: '2y 3m', status: 'Active', inv: '¥459,822', val: '¥255,679', pl: '¥83,434', ret: '18.14%', perf: 'Excellent' },
                { name: '申万菱信沪深300价值指数A', class: '股票', h: '6y 3m', status: 'Closed', inv: '¥178,877', val: '¥0', pl: '¥49,764', ret: '27.82%', perf: 'Average' },
              ].map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4 font-bold text-slate-900">{row.name}</td>
                  <td className="px-4 py-4 text-slate-500">{row.class}</td>
                  <td className="px-4 py-4 text-slate-500">{row.h}</td>
                  <td className="px-4 py-4">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${row.status === 'Active' ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-100 text-slate-500'}`}>
                      {row.status}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-right font-medium">{row.inv}</td>
                  <td className="px-4 py-4 text-right font-medium">{row.val}</td>
                  <td className="px-4 py-4 text-right font-bold text-emerald-500">{row.pl}</td>
                  <td className="px-4 py-4 text-right font-bold text-emerald-500">{row.ret}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wide ${row.perf === 'Excellent' ? 'bg-emerald-100 text-emerald-700' : row.perf === 'Good' ? 'bg-sky-100 text-sky-700' : 'bg-amber-100 text-amber-700'}`}>
                      {row.perf}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default GainsAnalysis;
