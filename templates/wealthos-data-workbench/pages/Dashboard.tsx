
import React from 'react';

interface DashboardProps {
  onNext: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({ onNext }) => {
  return (
    <div className="max-w-5xl mx-auto py-12">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-extrabold text-slate-900 mb-2 tracking-tight">Data Workbench</h1>
        <p className="text-lg text-slate-500">Choose data to import into your portfolio</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <WorkbenchCard 
          icon="history"
          title="Resume pending import"
          description="Continue your last import session exactly where you left off."
          pending
          onClick={onNext}
        />
        <WorkbenchCard 
          icon="show_chart"
          title="Import Transactions"
          description="Upload trade logs via CSV or connect directly to broker APIs."
          onClick={onNext}
        />
        <WorkbenchCard 
          icon="business_center"
          title="Import Holdings"
          description="Update current portfolio positions, real estate, and private equity."
          onClick={onNext}
        />
        <WorkbenchCard 
          icon="account_balance"
          title="Import Accounts"
          description="Bulk configure multiple banking and custodial accounts."
          onClick={onNext}
        />
      </div>

      <div className="mt-16 text-center">
        <a href="#" className="inline-flex items-center gap-2 text-sm font-medium text-slate-400 hover:text-blue-600 transition-colors">
          <span className="material-symbols-outlined !text-lg">help</span>
          Need help with data formats? View Documentation
        </a>
      </div>
    </div>
  );
};

const WorkbenchCard: React.FC<{
  icon: string;
  title: string;
  description: string;
  pending?: boolean;
  onClick: () => void;
}> = ({ icon, title, description, pending, onClick }) => (
  <button 
    onClick={onClick}
    className={`group relative flex items-start p-6 text-left bg-white border-2 rounded-2xl transition-all duration-300 hover:shadow-xl hover:shadow-slate-200/60 ${pending ? 'border-amber-400 bg-amber-50/20' : 'border-slate-100 hover:border-blue-500/50'}`}
  >
    {pending && (
      <span className="absolute top-0 right-0 -mt-2 mr-6 px-3 py-0.5 bg-amber-600 text-[10px] font-bold text-white uppercase tracking-wider rounded-full shadow-sm ring-4 ring-white">
        Pending
      </span>
    )}
    <div className={`flex-shrink-0 w-12 h-12 flex items-center justify-center rounded-xl mr-5 transition-transform group-hover:scale-110 group-hover:-rotate-3 ${pending ? 'bg-white text-amber-600 shadow-sm border border-amber-100' : 'bg-blue-50 text-blue-600 group-hover:bg-blue-600 group-hover:text-white'}`}>
      <span className="material-symbols-outlined !text-2xl">{icon}</span>
    </div>
    <div>
      <h3 className={`text-lg font-bold mb-1 transition-colors ${pending ? 'text-amber-900 group-hover:text-amber-700' : 'text-slate-900 group-hover:text-blue-600'}`}>{title}</h3>
      <p className="text-sm text-slate-500 leading-relaxed">{description}</p>
    </div>
  </button>
);

export default Dashboard;
