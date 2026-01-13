
import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface MetricCardProps {
  label: string;
  value: string;
  trend?: number;
  description?: string;
  accentColor?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({ label, value, trend, description, accentColor = 'blue' }) => {
  const isPositive = trend && trend > 0;
  
  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm relative overflow-hidden group hover:shadow-md transition-shadow">
      <div className={`absolute right-0 top-0 h-full w-1.5 bg-${accentColor}-500/30 rounded-l transition-opacity group-hover:opacity-100 opacity-50`} />
      <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">
        {label}
      </h3>
      <div className="flex items-baseline gap-2">
        <p className="text-3xl font-extrabold text-slate-900 tracking-tight">
          {value}
        </p>
        {trend !== undefined && (
          <span className={`flex items-center text-xs font-bold ${isPositive ? 'text-emerald-500' : 'text-rose-500'}`}>
            {isPositive ? <TrendingUp size={14} className="mr-0.5" /> : <TrendingDown size={14} className="mr-0.5" />}
            {Math.abs(trend)}%
          </span>
        )}
      </div>
      {description && <p className="text-[10px] text-slate-400 mt-2 font-medium">{description}</p>}
    </div>
  );
};
