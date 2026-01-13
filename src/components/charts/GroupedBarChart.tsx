/**
 * Grouped Bar Chart
 * Used for Target vs Current allocation comparison
 */

import React from 'react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from 'recharts';

interface GroupedBarData {
    name: string;
    target: number;
    current: number;
}

interface GroupedBarChartProps {
    data: GroupedBarData[];
    height?: number;
}

const GroupedBarChart: React.FC<GroupedBarChartProps> = ({ data, height = 300 }) => {
    return (
        <ResponsiveContainer width="100%" height={height}>
            <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 12 }} />
                <YAxis tick={{ fill: '#64748b', fontSize: 12 }} tickFormatter={(v) => `${v}%`} />
                <Tooltip
                    contentStyle={{
                        backgroundColor: '#1e293b',
                        border: 'none',
                        borderRadius: '8px',
                        color: '#f8fafc',
                    }}
                    formatter={(value: number) => [`${value.toFixed(1)}%`, '']}
                />
                <Legend />
                <Bar dataKey="target" name="Target" fill="#94a3b8" radius={[4, 4, 0, 0]} />
                <Bar dataKey="current" name="Current" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
        </ResponsiveContainer>
    );
};

export default GroupedBarChart;
