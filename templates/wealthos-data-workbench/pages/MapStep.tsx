
import React, { useState } from 'react';
import { WorkflowStepper } from './UploadStep';
import { getMagicMapping } from '../lib/gemini';

interface MapStepProps {
  onNext: () => void;
  onBack: () => void;
}

const MapStep: React.FC<MapStepProps> = ({ onNext, onBack }) => {
  const [isMapping, setIsMapping] = useState(false);
  const [mappings, setMappings] = useState<Record<string, string>>({
    'Date Field': 'Date (Column A)',
    'Description': 'Description (Column D)',
    'Amount': 'Amount (Column E)',
    'Ticker / Symbol': 'Symbol (Column C)',
    'Category': '-- Select Column --'
  });

  const handleMagicMap = async () => {
    setIsMapping(true);
    try {
      const headers = ['Date', 'Action', 'Symbol', 'Description', 'Amount'];
      const targets = ['Date Field', 'Description', 'Amount', 'Ticker / Symbol', 'Category'];
      const result = await getMagicMapping(headers, targets);
      
      // Simulate mapping delay for UX
      setTimeout(() => {
        setMappings(prev => ({ ...prev, ...result }));
        setIsMapping(false);
      }, 1500);
    } catch (error) {
      console.error(error);
      setIsMapping(false);
    }
  };

  return (
    <div className="max-w-[1400px] mx-auto space-y-8 relative">
      {isMapping && (
        <div className="fixed inset-0 bg-white/60 backdrop-blur-[2px] z-50 flex flex-col items-center justify-center">
          <div className="w-64 h-2 bg-slate-100 rounded-full overflow-hidden mb-4">
            <div className="h-full bg-blue-600 animate-[shimmer_1.5s_infinite] w-1/2"></div>
          </div>
          <p className="text-sm font-bold text-slate-600 animate-pulse">Gemini AI is scanning your data structure...</p>
        </div>
      )}

      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Map CSV Columns</h1>
          <p className="text-slate-500">Match your file columns to WealthOS's data structure.</p>
        </div>
        <div className="flex items-center gap-2 bg-green-50 border border-green-100 text-green-700 px-4 py-2 rounded-lg shadow-sm">
          <span className="material-symbols-outlined !text-lg">auto_fix_high</span>
          <span className="text-sm font-bold tracking-tight">AI-ready for auto-mapping</span>
        </div>
      </div>

      <WorkflowStepper step={3} />

      <div className="grid grid-cols-12 gap-8 items-start">
        <div className="col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
              <span className="material-symbols-outlined text-slate-400">table_view</span>
              CSV Preview
            </h2>
            <div className="px-3 py-1 bg-slate-100 border border-slate-200 rounded text-[11px] font-mono text-slate-500">
              fidelity_export_2023.csv
            </div>
          </div>
          <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead className="bg-slate-50 text-slate-400 font-bold uppercase text-[10px] tracking-widest border-b border-slate-100">
                  <tr>
                    {['Date', 'Action', 'Symbol', 'Description', 'Amount'].map(h => (
                      <th key={h} className="px-4 py-3">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-[13px] text-slate-600">
                  <tr className="hover:bg-slate-50/50">
                    <td className="px-4 py-3 font-mono">2023-10-24</td>
                    <td className="px-4 py-3">BUY</td>
                    <td className="px-4 py-3 font-bold text-blue-600">AAPL</td>
                    <td className="px-4 py-3 truncate max-w-[150px]">APPLE INC COM</td>
                    <td className="px-4 py-3">-173.50</td>
                  </tr>
                  <tr className="hover:bg-slate-50/50">
                    <td className="px-4 py-3 font-mono">2023-10-24</td>
                    <td className="px-4 py-3">DIVIDEND</td>
                    <td className="px-4 py-3 font-bold text-blue-600">VTI</td>
                    <td className="px-4 py-3 truncate max-w-[150px]">VANGUARD TOTAL STK</td>
                    <td className="px-4 py-3 text-emerald-600">+45.20</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div className="col-span-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
              <span className="material-symbols-outlined text-slate-400">tune</span>
              Configuration
            </h2>
            <button 
              onClick={handleMagicMap}
              disabled={isMapping}
              className="flex items-center gap-2 px-4 py-1.5 bg-indigo-600 text-white text-[11px] font-bold uppercase tracking-widest rounded-full hover:bg-indigo-700 transition-all shadow-md hover:shadow-indigo-200"
            >
              <span className="material-symbols-outlined !text-sm">auto_fix_high</span>
              Magic Map with AI
            </button>
          </div>

          <div className="bg-white border border-slate-200 rounded-2xl shadow-lg p-8 space-y-6">
            {Object.entries(mappings).map(([field, value]) => (
              <MappingField 
                key={field} 
                label={field} 
                icon={getIconForField(field)} 
                value={value} 
                onChange={(val) => setMappings(p => ({...p, [field]: val}))}
                required={['Date Field', 'Description', 'Amount'].includes(field)} 
              />
            ))}

            <div className="pt-6 border-t border-slate-100 flex items-center justify-between">
              <button onClick={onBack} className="px-6 py-2.5 text-sm font-bold text-slate-400 hover:text-slate-600">Back</button>
              <button 
                onClick={onNext}
                className="px-8 py-2.5 bg-blue-600 text-white font-bold rounded-xl shadow-lg hover:bg-blue-700 transition-all flex items-center gap-2 group"
              >
                Next Step
                <span className="material-symbols-outlined !text-xl group-hover:translate-x-1 transition-transform">arrow_forward</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const getIconForField = (field: string) => {
  if (field.includes('Date')) return 'calendar_today';
  if (field.includes('Description')) return 'description';
  if (field.includes('Amount')) return 'attach_money';
  if (field.includes('Ticker')) return 'show_chart';
  return 'label';
};

const MappingField: React.FC<{
  label: string;
  icon: string;
  value: string;
  onChange: (v: string) => void;
  required?: boolean;
}> = ({ label, icon, value, onChange, required }) => (
  <div className="p-4 border border-slate-100 rounded-2xl space-y-2 hover:border-blue-500/30 transition-colors">
    <div className="flex items-center justify-between">
      <label className="flex items-center gap-2 text-sm font-bold text-slate-800">
        <span className="material-symbols-outlined !text-lg text-slate-400">{icon}</span>
        {label} {required && <span className="text-red-500">*</span>}
      </label>
      {value !== '-- Select Column --' && (
        <span className="text-[9px] font-bold text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-100 uppercase tracking-widest">Matched</span>
      )}
    </div>
    <select 
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full h-10 bg-slate-50 border-slate-200 rounded-lg text-sm font-medium text-slate-700 focus:ring-blue-500"
    >
      <option>-- Select Column --</option>
      <option>Date (Column A)</option>
      <option>Action (Column B)</option>
      <option>Symbol (Column C)</option>
      <option>Description (Column D)</option>
      <option>Amount (Column E)</option>
    </select>
  </div>
);

export default MapStep;
