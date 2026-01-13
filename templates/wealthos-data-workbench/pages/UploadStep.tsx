
import React from 'react';

interface UploadStepProps {
  onNext: () => void;
  onBack: () => void;
}

const UploadStep: React.FC<UploadStepProps> = ({ onNext, onBack }) => {
  return (
    <div className="max-w-4xl mx-auto space-y-10">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Upload Workflow</h1>
        <p className="text-slate-500">Step 2 of 5: Import your CSV data</p>
      </div>

      <WorkflowStepper step={2} />

      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
        <div className="bg-slate-50/50 border-b border-slate-100 p-1 flex justify-center">
          <div className="flex bg-slate-200 rounded-lg p-1 w-full max-w-sm my-4">
            <button className="flex-1 px-4 py-2 bg-white text-blue-600 font-bold rounded shadow-sm text-sm">Upload CSV</button>
            <button className="flex-1 px-4 py-2 text-slate-500 font-medium text-sm">Copy & Paste</button>
          </div>
        </div>

        <div className="p-10 space-y-8">
          <div className="grid grid-cols-2 gap-8">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700">Column Separator</label>
              <select className="w-full h-11 bg-slate-50 border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm">
                <option>Comma (,)</option>
                <option>Semicolon (;)</option>
                <option>Tab</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700">Target Account</label>
              <select className="w-full h-11 bg-slate-50 border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm">
                <option>Multi-account import</option>
                <option>Savings ...1234</option>
                <option>Checking ...5678</option>
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700">Upload File</label>
            <div className="border-2 border-dashed border-blue-200 bg-blue-50/30 rounded-2xl p-16 flex flex-col items-center justify-center text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50/50 transition-all group">
              <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center text-blue-600 shadow-sm mb-4 transition-transform group-hover:scale-110">
                <span className="material-symbols-outlined !text-4xl">cloud_upload</span>
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-1">Click to upload or drag and drop</h3>
              <p className="text-sm text-slate-500 mb-4">SVG, PNG, JPG or GIF (max. 800x400px)</p>
              <div className="px-3 py-1 bg-white border border-slate-200 rounded text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                Supported formats: .csv, .xls, .xlsx
              </div>
            </div>
            <div className="flex justify-between items-center px-1 text-xs text-slate-400">
              <a href="#" className="flex items-center gap-1 hover:text-blue-600">
                <span className="material-symbols-outlined !text-sm">description</span> Download sample template
              </a>
              <span>Max size: 50MB</span>
            </div>
          </div>

          <div className="pt-6 border-t border-slate-100 flex items-center justify-end gap-4">
            <button onClick={onBack} className="px-6 py-2.5 text-sm font-semibold text-slate-400 hover:text-slate-600 transition-colors">Cancel</button>
            <button 
              onClick={onNext}
              className="px-10 py-2.5 bg-blue-600 text-white rounded-xl font-bold shadow-lg shadow-blue-500/25 hover:bg-blue-700 transition-all flex items-center gap-2 group"
            >
              Continue to Mapping
              <span className="material-symbols-outlined !text-xl transition-transform group-hover:translate-x-1">arrow_forward</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export const WorkflowStepper: React.FC<{ step: number }> = ({ step }) => (
  <div className="flex items-center justify-between px-10 relative">
    <div className="absolute top-1/2 left-0 w-full h-0.5 bg-slate-200 -translate-y-1/2 z-0"></div>
    {[1, 2, 3, 4, 5].map((s) => (
      <div key={s} className="relative z-10 flex flex-col items-center gap-2">
        <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all shadow-sm ${s < step ? 'bg-blue-600 text-white' : s === step ? 'bg-blue-600 text-white ring-8 ring-blue-50' : 'bg-white text-slate-400 border-2 border-slate-100'}`}>
          {s < step ? <span className="material-symbols-outlined !text-lg">check</span> : s}
        </div>
        <span className={`text-xs font-bold transition-colors ${s <= step ? 'text-blue-600' : 'text-slate-400'}`}>
          {s === 1 && 'Source'}
          {s === 2 && 'Upload'}
          {s === 3 && 'Map'}
          {s === 4 && 'Review'}
          {s === 5 && 'Done'}
        </span>
      </div>
    ))}
  </div>
);

export default UploadStep;
