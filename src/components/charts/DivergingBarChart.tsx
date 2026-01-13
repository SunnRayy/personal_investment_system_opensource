/**
 * Diverging Bar Chart
 * Used for drift analysis with positive/negative values from zero
 */

import React from 'react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ReferenceLine,
    ResponsiveContainer,
    Cell,
} from 'recharts';

interface DriftData {
    name: string;
    drift: number;
    isCritical?: boolean;
}

interface DivergingBarChartProps {
    data: DriftData[];
    height?: number;
    criticalThreshold?: number;
}

const DivergingBarChart: React.FC<DivergingBarChartProps> = ({
    data,
    height = 300,
    criticalThreshold = 5,
}) => {
    const getBarColor = (drift: number) => {
        if (Math.abs(drift) >= criticalThreshold) return '#ef4444'; // Red for critical
        if (drift > 0) return '#3b82f6'; // Blue for overweight
        return '#f59e0b'; // Amber for underweight
    };

    return (
        <ResponsiveContainer width="100%" height={height}>
            <BarChart
                data={data}
                layout="vertical"
                margin={{ top: 20, right: 60, left: 80, bottom: 5 }}
            >
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
                <XAxis
                    type="number"
                    tick={{ fill: '#64748b', fontSize: 12 }}
                    tickFormatter={(v) => `${v > 0 ? '+' : ''}${v}%`}
                    domain={['dataMin - 2', 'dataMax + 2']}
                />
                <YAxis
                    type="category"
                    dataKey="name"
                    tick={{ fill: '#64748b', fontSize: 12 }}
                    width={70}
                />
                <Tooltip
                    contentStyle={{
                        backgroundColor: '#1e293b',
                        border: 'none',
                        borderRadius: '8px',
                        color: '#f8fafc',
                    }}
                    formatter={(value: number) => [
                        `${value > 0 ? '+' : ''}${value.toFixed(1)}%`,
                        value > 0 ? 'Overweight' : 'Underweight',
                    ]}
                />
                <ReferenceLine x={0} stroke="#475569" strokeWidth={2} />
                <Bar dataKey="drift" radius={[0, 4, 4, 0]}>
                    {data.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={getBarColor(entry.drift)} />
                    ))}
                </Bar>
            </BarChart>
        </ResponsiveContainer>
    );
};

export default DivergingBarChart;
