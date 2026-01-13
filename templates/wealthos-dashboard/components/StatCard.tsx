
import React from 'react';

interface StatCardProps {
  label: string;
  value: string | number;
  colorClass?: string;
  prefix?: string;
  suffix?: string;
}

const StatCard: React.FC<StatCardProps> = ({ label, value, colorClass = "text-gray-900", prefix, suffix }) => {
  return (
    <div className="bg-white rounded-xl shadow-[0_4px_12px_-2px_rgba(0,0,0,0.03)] p-6 border-l-[3px] border-[#D4AF37] flex flex-col justify-center h-28">
      <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.15em] mb-2">{label}</h3>
      <div className={`text-2xl font-bold tracking-tight ${colorClass}`}>
        {prefix}{value}{suffix}
      </div>
    </div>
  );
};

export default StatCard;
