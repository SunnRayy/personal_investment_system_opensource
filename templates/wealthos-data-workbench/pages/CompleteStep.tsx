
import React, { useEffect, useState } from 'react';
import { WorkflowStepper } from './UploadStep';

interface CompleteStepProps {
  onFinish: () => void;
}

const CompleteStep: React.FC<CompleteStepProps> = ({ onFinish }) => {
  const [isProcessing, setIsProcessing] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setIsProcessing(false), 2000);
    return () => clearTimeout(timer);
  }, []);

  if (isProcessing) {
    return (
      <div className="flex flex-col items-center justify-center h-full space-y-8 py-20">
        <div className="relative">
          <div className="w-24 h-24 border-4 border-slate-100 border-t-blue-600 rounded-full animate-spin"></div>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="material-symbols-outlined text-blue-600 animate-pulse">cloud_sync</span>
          </div>
        </div>
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-bold text-slate-900">Finalizing Import...</h2>
          <p className="text-slate-500">Committing 84 transactions to your portfolio database.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-10 py-10 animate-[fadeIn_0.5s_ease-out]">
      <WorkflowStepper step={5} />

      <div className="bg-white border border-slate-200 rounded-3xl shadow-2xl shadow-slate-200/50 overflow-hidden">
        <div className="bg-emerald-500 p-10 flex flex-col items-center text-white relative overflow-hidden">
          {/* Decorative background shapes */}
          <div className="absolute -top-10 -right-10 w-40 h-40 bg-white/10 rounded-full blur-3xl"></div>
          <div className="absolute -bottom-10 -left-10 w-40 h-40 bg-black/10 rounded-full blur-2xl"></div>
          
          <div className="w-20 h-20 bg-white rounded-full flex items-center justify-center text-emerald-500 mb-6 shadow-xl animate-[bounce_1s_infinite_alternate]">
            <span className="material-symbols-outlined !text-4xl filled">check_circle</span>
          </div>
          <h1 className="text-3xl font-extrabold mb-2">Import Successful!</h1>
          <p className="text-emerald-50 text-center opacity-90 max-w-sm">
            Your data has been processed and is now available across the WealthOS platform.
          </p>
        </div>

        <div className="p-10 space-y-8">
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100">
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Total Imported</p>
              <p className="text-2xl font-black text-slate-900">84 <span className="text-sm font-medium text-slate-500">Rows</span></p>
            </div>
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100">
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Batch Amount</p>
              <p className="text-2xl font-black text-slate-900">$12,450.22</p>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-sm font-bold text-slate-900 px-1">Import Details</h3>
            <div className="divide-y divide-slate-100 border border-slate-100 rounded-2xl overflow-hidden">
              <DetailRow label="Import ID" value="#WOS-992184" copyable />
              <DetailRow label="Destination" value="Chase Checking ...1234" />
              <DetailRow label="Status" value="Success" status="success" />
              <DetailRow label="Completion Time" value={new Date().toLocaleString()} />
            </div>
          </div>

          <div className="flex flex-col gap-3 pt-4">
            <button 
              onClick={onFinish}
              className="w-full py-4 bg-slate-900 text-white font-bold rounded-2xl hover:bg-slate-800 transition-all shadow-xl shadow-slate-200 flex items-center justify-center gap-2 group"
            >
              Go to Data Workbench
              <span className="material-symbols-outlined !text-xl group-hover:translate-x-1 transition-transform">arrow_forward</span>
            </button>
            <button 
              className="w-full py-4 bg-white border border-slate-200 text-slate-600 font-bold rounded-2xl hover:bg-slate-50 transition-all flex items-center justify-center gap-2"
            >
              <span className="material-symbols-outlined !text-xl">pie_chart</span>
              View in Portfolio
            </button>
          </div>
        </div>
      </div>

      <p className="text-center text-xs text-slate-400">
        A copy of this import receipt has been sent to your registered email.
      </p>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
};

const DetailRow: React.FC<{ label: string; value: string; copyable?: boolean; status?: 'success' }> = ({ label, value, copyable, status }) => (
  <div className="flex items-center justify-between p-4 bg-white">
    <span className="text-xs font-semibold text-slate-500">{label}</span>
    <div className="flex items-center gap-2">
      {status === 'success' && <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>}
      <span className={`text-xs font-bold ${status === 'success' ? 'text-emerald-600' : 'text-slate-900'} font-mono`}>{value}</span>
      {copyable && <span className="material-symbols-outlined !text-sm text-slate-300 cursor-pointer hover:text-blue-500">content_copy</span>}
    </div>
  </div>
);

export default CompleteStep;
