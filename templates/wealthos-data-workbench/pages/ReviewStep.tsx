
import React, { useState } from 'react';
import { WorkflowStepper } from './UploadStep';
import { Transaction } from '../types';
import { getSmartFix } from '../lib/gemini';

interface ReviewStepProps {
  onNext: () => void;
  onBack: () => void;
}

const ReviewStep: React.FC<ReviewStepProps> = ({ onNext, onBack }) => {
  const [isFixing, setIsFixing] = useState(false);
  const [data, setData] = useState<Transaction[]>([
    { id: '1', date: '2023-10-24', description: 'Dividend Payment - AAPL', category: 'Dividend', amount: 145.00, ticker: 'AAPL', account: 'Brokerage ...8842', status: 'ready' },
    { id: '2', date: '2023-13-45', description: 'Transfer to Savings', category: 'Transfer', amount: 5000.00, account: 'Chase Chk ...1234', status: 'error', errorMsg: 'Invalid date format' },
    { id: '3', date: '2023-10-23', description: 'Netflix Subscription', category: 'Entertainment', amount: -19.99, ticker: 'NFLX', account: 'Chase CC ...5501', status: 'ready' },
    { id: '4', date: '2023-10-22', description: 'Unknown Purchase #9921', category: 'Uncategorized', amount: -125.50, account: 'Chase Chk ...1234', status: 'error', errorMsg: 'Please select a category' },
    { id: '5', date: '2023-10-22', description: 'Whole Foods Market', category: 'Groceries', amount: -86.42, account: 'Chase CC ...5501', status: 'ready' },
    { id: '6', date: '2023-10-21', description: 'Shell Station', category: 'Transport', amount: -45.00, account: 'Chase CC ...5501', status: 'ready' },
    { id: '7', date: '2023-10-20', description: 'Salary Deposit', category: 'Income', amount: -2400.00, account: 'Chase Chk ...1234', status: 'error', errorMsg: 'Income cannot be negative' },
  ]);

  const errorCount = data.filter(r => r.status === 'error').length;

  const handleMagicFix = async () => {
    setIsFixing(true);
    const newData = [...data];
    
    for (let i = 0; i < newData.length; i++) {
      if (newData[i].status === 'error') {
        try {
          const fix = await getSmartFix(newData[i]);
          newData[i] = {
            ...newData[i],
            ...fix,
            status: 'ready',
            errorMsg: undefined,
            id: newData[i].id + '_fixed' // Track it's been fixed
          };
        } catch (e) {
          console.error("Failed to fix row", newData[i].id);
        }
      }
    }

    setData(newData);
    setIsFixing(false);
  };

  return (
    <div className="max-w-[1600px] mx-auto space-y-8 h-full flex flex-col relative">
      <div className="flex items-end justify-between">
        <div className="space-y-1">
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-4">
            Review & Fix Errors
            <span className={`px-3 py-0.5 rounded-full text-xs font-bold border transition-colors ${errorCount > 0 ? 'bg-red-100 text-red-700 border-red-200' : 'bg-emerald-100 text-emerald-700 border-emerald-200'}`}>
              {errorCount > 0 ? `${errorCount} Errors Remaining` : 'All Errors Fixed!'}
            </span>
          </h1>
          <p className="text-slate-500">Please review the parsed data. AI has identified {errorCount} issues.</p>
        </div>
        <div className="flex gap-3">
           <button 
            onClick={handleMagicFix}
            disabled={isFixing || errorCount === 0}
            className="flex items-center gap-2 px-6 py-2.5 bg-indigo-600 text-white text-sm font-bold rounded-xl hover:bg-indigo-700 transition-all shadow-lg hover:shadow-indigo-200 disabled:opacity-50 disabled:shadow-none"
          >
            {isFixing ? (
              <span className="material-symbols-outlined !text-lg animate-spin">sync</span>
            ) : (
              <span className="material-symbols-outlined !text-lg">auto_fix_high</span>
            )}
            {isFixing ? 'AI Fixing...' : 'Magic Fix with AI'}
          </button>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-2xl shadow-xl flex-1 flex flex-col overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-white flex-shrink-0">
          <div className="flex items-center gap-4">
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 !text-lg">search</span>
              <input 
                type="text" 
                placeholder="Filter transactions..." 
                className="pl-10 pr-4 py-2 text-sm border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 w-72 h-10" 
              />
            </div>
            <div className="h-6 w-px bg-slate-200"></div>
            <button className="flex items-center gap-2 px-3 py-2 text-sm font-bold text-slate-500 hover:bg-slate-50 rounded-lg transition-colors">
              <span className="material-symbols-outlined !text-lg">filter_list</span> All Status
            </button>
          </div>
          <div className="flex items-center gap-2 text-[13px] text-slate-400">
            <span className="material-symbols-outlined text-blue-500 !text-lg">info</span>
            AI suggestions are marked with <span className="text-indigo-600 font-bold">Sparkles</span>
          </div>
        </div>

        <div className="flex-1 overflow-auto">
          <table className="w-full text-left border-collapse min-w-[1200px]">
            <thead className="sticky top-0 bg-slate-50 z-20 border-b border-slate-200 shadow-sm">
              <tr className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                <th className="py-4 px-6 w-12 border-r border-slate-200 text-center"><input type="checkbox" className="rounded border-slate-300" /></th>
                <th className="py-4 px-6 border-r border-slate-200">Date</th>
                <th className="py-4 px-6 border-r border-slate-200">Description</th>
                <th className="py-4 px-6 border-r border-slate-200">Category</th>
                <th className="py-4 px-6 border-r border-slate-200 text-right">Amount</th>
                <th className="py-4 px-6">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {data.map((row) => (
                <tr 
                  key={row.id} 
                  className={`hover:bg-slate-50/50 transition-colors ${row.status === 'error' ? 'bg-red-50/40 border-l-4 border-l-red-500' : row.id.includes('fixed') ? 'bg-indigo-50/20 border-l-4 border-l-indigo-400' : ''}`}
                >
                  <td className="py-3 px-6 text-center border-r border-slate-100">
                    <input type="checkbox" className="rounded border-slate-300" />
                  </td>
                  <td className={`py-3 px-6 font-mono border-r border-slate-100 ${row.status === 'error' && row.errorMsg?.includes('date') ? 'text-red-600 font-bold' : row.id.includes('fixed') ? 'text-indigo-600 font-bold' : 'text-slate-500'}`}>
                    {row.date}
                    {row.id.includes('fixed') && <span className="material-symbols-outlined !text-xs ml-1 align-top text-indigo-400">auto_awesome</span>}
                  </td>
                  <td className="py-3 px-6 font-bold text-slate-900 border-r border-slate-100">{row.description}</td>
                  <td className="py-3 px-6 border-r border-slate-100">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider ${
                      row.status === 'error' && row.errorMsg?.includes('category') 
                      ? 'bg-red-100 text-red-600 italic' 
                      : row.id.includes('fixed') ? 'bg-indigo-100 text-indigo-600' : 'bg-blue-50 text-blue-600'
                    }`}>
                      {row.category}
                      {row.id.includes('fixed') && <span className="material-symbols-outlined !text-xs ml-1">auto_awesome</span>}
                    </span>
                  </td>
                  <td className={`py-3 px-6 font-mono text-right border-r border-slate-100 ${
                    row.status === 'error' && row.amount < 0 && row.category === 'Income'
                    ? 'text-red-600 font-bold' 
                    : row.amount > 0 ? 'text-emerald-600 font-bold' : 'text-slate-900'
                  }`}>
                    {row.amount < 0 ? '-' : '+'}${Math.abs(row.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-3 px-6">
                    {row.status === 'ready' ? (
                      <span className="flex items-center gap-1.5 text-emerald-600 font-bold text-xs uppercase tracking-widest">
                        <span className="material-symbols-outlined filled !text-base">check_circle</span> Ready
                      </span>
                    ) : (
                      <div className="flex flex-col">
                        <span className="text-red-600 font-extrabold text-[10px] uppercase tracking-widest">Error</span>
                        <span className="text-[10px] text-red-400 italic">{row.errorMsg}</span>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="px-8 py-6 bg-slate-50 border-t border-slate-200 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-6">
             <div className="flex items-center gap-2.5">
              <span className={`w-2.5 h-2.5 rounded-full ${errorCount === 0 ? 'bg-emerald-500' : 'bg-red-500 animate-pulse'}`}></span>
              <span className="text-sm font-bold text-slate-600">{data.length - errorCount} rows ready</span>
            </div>
            {errorCount > 0 && <span className="text-sm font-bold text-red-500">{errorCount} need fixing</span>}
          </div>

          <div className="flex items-center gap-4">
            <button onClick={onBack} className="px-6 py-3 bg-white border border-slate-200 text-slate-600 font-bold rounded-xl">
              Back
            </button>
            <button 
              onClick={onNext}
              disabled={errorCount > 0}
              className="px-10 py-3 bg-blue-600 text-white font-bold rounded-xl shadow-xl shadow-blue-500/25 hover:bg-blue-700 disabled:opacity-50 transition-all flex items-center gap-3 group"
            >
              Finalize Import
              <span className="material-symbols-outlined !text-xl group-hover:translate-x-1 transition-transform">arrow_forward</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReviewStep;
