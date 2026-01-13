/**
 * Portfolio Report Page
 * Performance & Growth Metrics - The "Health Check"
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
    Line,
    ComposedChart,
    BarChart,
    Bar,
    PieChart,
    Pie,
    Cell,
    Legend,
} from 'recharts';
import { TrendingUp, TrendingDown, Award, Droplets, DollarSign, BarChart3 } from 'lucide-react';
import { useUnifiedAnalysis } from '../hooks/useReports';

// Demo data for portfolio growth
const GROWTH_DATA = [
    { month: 'Jan', portfolio: 1980000, invested: 1900000, equity: 1100000, fixedIncome: 600000, alts: 280000 },
    { month: 'Feb', portfolio: 2020000, invested: 1920000, equity: 1150000, fixedIncome: 590000, alts: 280000 },
    { month: 'Mar', portfolio: 1950000, invested: 1940000, equity: 1050000, fixedIncome: 620000, alts: 280000 },
    { month: 'Apr', portfolio: 2050000, invested: 1960000, equity: 1180000, fixedIncome: 590000, alts: 280000 },
    { month: 'May', portfolio: 2080000, invested: 1980000, equity: 1200000, fixedIncome: 600000, alts: 280000 },
    { month: 'Jun', portfolio: 2100000, invested: 2000000, equity: 1210000, fixedIncome: 610000, alts: 280000 },
    { month: 'Jul', portfolio: 2050000, invested: 2020000, equity: 1150000, fixedIncome: 620000, alts: 280000 },
    { month: 'Aug', portfolio: 2090000, invested: 2040000, equity: 1190000, fixedIncome: 620000, alts: 280000 },
    { month: 'Sep', portfolio: 2100000, invested: 2060000, equity: 1200000, fixedIncome: 620000, alts: 280000 },
    { month: 'Oct', portfolio: 2110000, invested: 2080000, equity: 1210000, fixedIncome: 620000, alts: 280000 },
    { month: 'Nov', portfolio: 2130000, invested: 2100000, equity: 1230000, fixedIncome: 620000, alts: 280000 },
    { month: 'Dec', portfolio: 2140580, invested: 2012130, equity: 1250000, fixedIncome: 610000, alts: 280580 },
];

// YoY Net Worth data
const YOY_DATA = [
    { year: '2020', growth: 180000, baseline: 1400000 },
    { year: '2021', growth: 220000, baseline: 1580000 },
    { year: '2022', growth: 150000, baseline: 1800000 },
    { year: '2023', growth: 280000, baseline: 1950000 },
    { year: '2024', growth: 190000, baseline: 2230000 },
];

// Performance by asset class
const PERFORMANCE_DATA = [
    { name: 'Public Equity', xirr: 14.2, color: '#3b82f6' },
    { name: 'Fixed Income', xirr: 4.8, color: '#f59e0b' },
    { name: 'Alternatives', xirr: 9.1, color: '#22c55e' },
    { name: 'Real Estate', xirr: 6.5, color: '#3b82f6' },
    { name: 'Cash / Equiv', xirr: 3.2, color: '#64748b' },
];

// Allocation data for donut
const ALLOCATION_DATA = [
    { name: 'Equity', value: 55, color: '#3b82f6' },
    { name: 'Fixed Income', value: 25, color: '#f59e0b' },
    { name: 'Alternatives', value: 12, color: '#22c55e' },
    { name: 'Cash', value: 8, color: '#94a3b8' },
];

const Portfolio: React.FC = () => {
    const { data: analysisData, isLoading } = useUnifiedAnalysis();

    // Extract portfolio snapshot data
    const netWorth = analysisData?.portfolio_snapshot?.total_value || 2140580;
    const ytdGrowth = analysisData?.performance?.ytd_return || 6.4;
    const ytdAmount = 128450;
    const liquidAssets = analysisData?.portfolio_snapshot?.liquid_assets || 420000;
    const sharpeRatio = 1.85;

    if (isLoading) {
        return (
            <div className="flex h-[60vh] items-center justify-center">
                <div className="flex flex-col items-center gap-4">
                    <div className="h-10 w-10 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600"></div>
                    <p className="text-sm font-medium text-gray-500">Loading portfolio...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="p-6 lg:p-8 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-2">
                <h1 className="text-3xl font-bold text-gray-900">Performance & Growth Metrics</h1>
                <div className="flex items-center gap-4">
                    <button className="px-3 py-1.5 text-sm font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">
                        Period: YTD ▾
                    </button>
                </div>
            </div>

            {/* Row 1: Hero - Asset Category Growth */}
            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Asset Category Growth</h3>
                        <div className="flex items-baseline gap-3">
                            <span className="text-4xl font-bold text-gray-900">
                                ${netWorth.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                            </span>
                            <span className="flex items-center text-emerald-500 font-semibold text-sm">
                                <TrendingUp size={16} className="mr-1" />
                                +${ytdAmount.toLocaleString()} (+{ytdGrowth}%) YTD
                            </span>
                        </div>
                    </div>
                    <div className="flex gap-4 text-sm">
                        <span className="flex items-center gap-2">
                            <span className="h-3 w-3 rounded-full bg-blue-500"></span>
                            Equity
                        </span>
                        <span className="flex items-center gap-2">
                            <span className="h-3 w-3 rounded-full bg-amber-400"></span>
                            Fixed Income
                        </span>
                        <span className="flex items-center gap-2">
                            <span className="h-3 w-3 rounded-full bg-emerald-400"></span>
                            Alts
                        </span>
                    </div>
                </div>

                <ResponsiveContainer width="100%" height={280}>
                    <AreaChart data={GROWTH_DATA} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                        <defs>
                            <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.05} />
                            </linearGradient>
                            <linearGradient id="fixedGrad" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.4} />
                                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.05} />
                            </linearGradient>
                            <linearGradient id="altsGrad" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#22c55e" stopOpacity={0.4} />
                                <stop offset="95%" stopColor="#22c55e" stopOpacity={0.05} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                        <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                        <YAxis
                            tick={{ fill: '#64748b', fontSize: 12 }}
                            tickFormatter={(v) => `$${(v / 1000000).toFixed(1)}M`}
                            axisLine={false}
                            tickLine={false}
                        />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc' }}
                            formatter={(value: number) => [`$${value.toLocaleString()}`, '']}
                        />
                        <Area type="monotone" dataKey="equity" stackId="1" stroke="#3b82f6" fill="url(#equityGrad)" />
                        <Area type="monotone" dataKey="fixedIncome" stackId="1" stroke="#f59e0b" fill="url(#fixedGrad)" />
                        <Area type="monotone" dataKey="alts" stackId="1" stroke="#22c55e" fill="url(#altsGrad)" />
                    </AreaChart>
                </ResponsiveContainer>
            </div>

            {/* Row 2: Performance by Class + YoY Growth */}
            <div className="grid gap-6 lg:grid-cols-2">
                {/* Performance by Class */}
                <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Performance by Class (XIRR)</h3>
                        <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded">Last 12 Months</span>
                    </div>
                    <div className="space-y-4">
                        {PERFORMANCE_DATA.map((item) => (
                            <div key={item.name}>
                                <div className="flex justify-between text-sm mb-1.5">
                                    <span className="font-medium text-gray-700">{item.name}</span>
                                    <span className="font-bold text-gray-900">{item.xirr}%</span>
                                </div>
                                <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                                    <div
                                        className="h-full rounded-full transition-all duration-700"
                                        style={{
                                            width: `${Math.min(item.xirr * 6, 100)}%`,
                                            backgroundColor: item.color
                                        }}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* YoY Net Worth Growth */}
                <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider">YoY Net Worth Growth</h3>
                    </div>
                    <ResponsiveContainer width="100%" height={220}>
                        <BarChart data={YOY_DATA}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                            <XAxis dataKey="year" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} />
                            <YAxis tick={{ fill: '#64748b', fontSize: 12 }} tickFormatter={(v) => `$${(v / 1000000).toFixed(1)}M`} axisLine={false} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc' }}
                                formatter={(value: number) => [`$${value.toLocaleString()}`, '']}
                            />
                            <Bar dataKey="baseline" stackId="a" fill="#3b82f6" radius={[0, 0, 0, 0]} />
                            <Bar dataKey="growth" stackId="a" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Row 3: Top Performers */}
            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Top Performers (This Period)</h3>
                    <button className="text-sm font-medium text-blue-600 hover:text-blue-700">View Full Report</button>
                </div>
                <div className="overflow-x-auto">
                    <table className="min-w-full">
                        <thead>
                            <tr className="border-b border-gray-100">
                                <th className="py-3 text-left text-xs font-semibold uppercase text-gray-400">Asset</th>
                                <th className="py-3 text-left text-xs font-semibold uppercase text-gray-400">Class</th>
                                <th className="py-3 text-right text-xs font-semibold uppercase text-gray-400">Value</th>
                                <th className="py-3 text-right text-xs font-semibold uppercase text-gray-400">Return</th>
                                <th className="py-3 text-right text-xs font-semibold uppercase text-gray-400">Allocation</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50">
                            {[
                                { name: 'NVDA', class: 'US Equity', value: 285000, return: 142.5, alloc: 13.3 },
                                { name: 'AAPL', class: 'US Equity', value: 195000, return: 48.2, alloc: 9.1 },
                                { name: 'MSFT', class: 'US Equity', value: 178000, return: 56.8, alloc: 8.3 },
                                { name: 'VTI', class: 'US ETF', value: 320000, return: 24.1, alloc: 14.9 },
                                { name: 'BND', class: 'Bond ETF', value: 210000, return: 4.2, alloc: 9.8 },
                            ].map((asset, i) => (
                                <tr key={i} className="hover:bg-gray-50">
                                    <td className="py-3 font-semibold text-gray-900">{asset.name}</td>
                                    <td className="py-3 text-sm text-gray-500">{asset.class}</td>
                                    <td className="py-3 text-right font-mono text-gray-700">${asset.value.toLocaleString()}</td>
                                    <td className="py-3 text-right">
                                        <span className={`font-semibold ${asset.return > 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                                            {asset.return > 0 ? '+' : ''}{asset.return}%
                                        </span>
                                    </td>
                                    <td className="py-3 text-right text-gray-600">{asset.alloc}%</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default Portfolio;
