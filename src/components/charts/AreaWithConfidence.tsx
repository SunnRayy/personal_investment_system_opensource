/**
 * Area Chart with Confidence Bands
 * Used for projections with P5/P50/P95 percentiles
 */

import React from 'react';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
} from 'recharts';

interface ProjectionData {
    year: number | string;
    p5: number;
    p50: number;
    p95: number;
}

interface AreaWithConfidenceProps {
    data: ProjectionData[];
    height?: number;
    formatValue?: (value: number) => string;
}

const AreaWithConfidence: React.FC<AreaWithConfidenceProps> = ({
    data,
    height = 350,
    formatValue = (v) => `$${(v / 1000000).toFixed(1)}M`,
}) => {
    return (
        <ResponsiveContainer width="100%" height={height}>
            <AreaChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <defs>
                    <linearGradient id="confidenceBand" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.05} />
                    </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="year" tick={{ fill: '#64748b', fontSize: 12 }} />
                <YAxis tick={{ fill: '#64748b', fontSize: 12 }} tickFormatter={formatValue} />
                <Tooltip
                    contentStyle={{
                        backgroundColor: '#1e293b',
                        border: 'none',
                        borderRadius: '8px',
                        color: '#f8fafc',
                    }}
                    formatter={(value: number, name: string) => [formatValue(value), name]}
                />
                <Legend />
                {/* Confidence band between P5 and P95 */}
                <Area
                    type="monotone"
                    dataKey="p95"
                    name="Optimistic (P95)"
                    stroke="#22c55e"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    fill="url(#confidenceBand)"
                />
                <Area
                    type="monotone"
                    dataKey="p5"
                    name="Conservative (P5)"
                    stroke="#94a3b8"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    fill="white"
                />
                {/* Median line on top */}
                <Area
                    type="monotone"
                    dataKey="p50"
                    name="Median (P50)"
                    stroke="#3b82f6"
                    strokeWidth={3}
                    fill="none"
                />
            </AreaChart>
        </ResponsiveContainer>
    );
};

export default AreaWithConfidence;
