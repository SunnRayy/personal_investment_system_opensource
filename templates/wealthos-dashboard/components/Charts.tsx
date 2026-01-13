
import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { NET_WORTH_HISTORY, ALLOCATION_DATA } from '../constants';

export const NetWorthChart: React.FC = () => {
  return (
    <div className="w-full h-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={NET_WORTH_HISTORY} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorGold" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#D4AF37" stopOpacity={0.2} />
              <stop offset="95%" stopColor="#D4AF37" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="date" hide />
          <YAxis hide domain={['dataMin - 100000', 'auto']} />
          <Tooltip 
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                return (
                  <div className="bg-white border border-gray-100 p-2 shadow-lg rounded-lg">
                    <p className="text-xs font-bold text-gray-900">
                      ${payload[0].value?.toLocaleString()}
                    </p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke="#D4AF37"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorGold)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export const AllocationChart: React.FC = () => {
  return (
    <div className="w-48 h-48">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={ALLOCATION_DATA}
            cx="50%"
            cy="50%"
            innerRadius={65}
            outerRadius={85}
            paddingAngle={0}
            dataKey="value"
          >
            {ALLOCATION_DATA.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip 
             content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  return (
                    <div className="bg-white border border-gray-100 p-2 shadow-lg rounded-lg text-xs font-bold">
                        {payload[0].name}: {payload[0].value}%
                    </div>
                  );
                }
                return null;
              }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};
