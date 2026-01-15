/**
 * Cash Flow Report Page
 * Capital flow visualization and forecasting
 */

import React, { useState } from 'react';
import { Download, Calendar, TrendingUp, TrendingDown, DollarSign, PiggyBank, RefreshCw } from 'lucide-react';
import {
    AreaChart,
    Area,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
    Line,
    ComposedChart,
    PieChart,
    Pie,
    Cell,
} from 'recharts';
import { useCashFlow } from '../../hooks/useReports';
import { TimePeriodSelector, type TimePeriod } from '../../components/ui/TimePeriodSelector';

const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

const CashFlow: React.FC = () => {
    const [period, setPeriod] = useState<TimePeriod>('1Y');
    const { data: cashFlowData, isLoading, error, refetch, isFetching } = useCashFlow();

    // Demo data for visualization
    const monthlyData = React.useMemo(() => {
        if (cashFlowData?.monthly) {
            return cashFlowData.monthly.map((m: any) => ({
                month: m.month,
                income: m.income || 0,
                expense: m.expense || 0,
                net: (m.income || 0) - (m.expense || 0),
            }));
        }
        // Demo data
        return [
            { month: 'Jan', income: 32000, expense: 18000, net: 14000 },
            { month: 'Feb', income: 28000, expense: 19000, net: 9000 },
            { month: 'Mar', income: 35000, expense: 17000, net: 18000 },
            { month: 'Apr', income: 30000, expense: 20000, net: 10000 },
            { month: 'May', income: 33000, expense: 18500, net: 14500 },
            { month: 'Jun', income: 38000, expense: 21000, net: 17000 },
            { month: 'Jul', income: 31000, expense: 19000, net: 12000 },
            { month: 'Aug', income: 34000, expense: 20000, net: 14000 },
            { month: 'Sep', income: 36000, expense: 18000, net: 18000 },
            { month: 'Oct', income: 32000, expense: 19500, net: 12500 },
            { month: 'Nov', income: 40000, expense: 22000, net: 18000 },
            { month: 'Dec', income: 45000, expense: 25000, net: 20000 },
        ];
    }, [cashFlowData]);

    const forecastData = [
        { quarter: 'Q1', projected: 1200000, lower: 1100000, upper: 1350000 },
        { quarter: 'Q2', projected: 1450000, lower: 1300000, upper: 1650000 },
        { quarter: 'Q3', projected: 1750000, lower: 1550000, upper: 2000000 },
        { quarter: 'Q4', projected: 2100000, lower: 1850000, upper: 2400000 },
    ];

    const incomeBreakdown = [
        { name: 'Salary', value: 220000 },
        { name: 'RSU', value: 129000 },
        { name: 'Dividends', value: 40000 },
    ];

    const expenseBreakdown = [
        { name: 'Living', value: 60000 },
        { name: 'Tax', value: 89000 },
        { name: 'Investments', value: 205000 },
    ];

    const expenseCategories = [
        { name: 'Housing', value: 35 },
        { name: 'Food', value: 15 },
        { name: 'Transport', value: 10 },
        { name: 'Entertainment', value: 8 },
        { name: 'Utilities', value: 7 },
        { name: 'Other', value: 25 },
    ];

    const totalIncome = monthlyData.reduce((sum, m) => sum + m.income, 0);
    const totalExpense = monthlyData.reduce((sum, m) => sum + m.expense, 0);
    const netFlow = totalIncome - totalExpense;

    if (isLoading) {
        return (
            <div className="flex h-[60vh] items-center justify-center">
                <div className="flex flex-col items-center gap-4">
                    <div className="h-10 w-10 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600"></div>
                    <p className="text-sm font-medium text-gray-500">Loading cash flow data...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="p-6 lg:p-8">
            {/* Header */}
            <div className="mb-6 flex items-center justify-between">
                <div>
                    <p className="text-sm text-gray-500">Portfolio › Cash Flow Analysis</p>
                    <h1 className="text-3xl font-bold text-gray-900">Cash Flow Analysis</h1>
                    <p className="text-sm text-gray-500">Visualizing capital movement and forecasting liquidity</p>
                </div>
                <div className="flex items-center gap-3">
                    <TimePeriodSelector
                        value={period}
                        onChange={setPeriod}
                        options={['3M', '6M', '1Y', 'ALL']}
                    />
                    <button
                        onClick={() => refetch()}
                        disabled={isFetching}
                        className="p-2 text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                    >
                        <RefreshCw size={16} className={isFetching ? 'animate-spin' : ''} />
                    </button>
                    <button
                        onClick={() => {
                            const csvContent = [
                                ['Month', 'Income', 'Expense', 'Net'],
                                ...monthlyData.map(row => [row.month, row.income, row.expense, row.net])
                            ].map(row => row.join(',')).join('\n');
                            const blob = new Blob([csvContent], { type: 'text/csv' });
                            const link = document.createElement('a');
                            link.href = URL.createObjectURL(blob);
                            link.download = `cashflow_${new Date().toISOString().split('T')[0]}.csv`;
                            link.click();
                        }}
                        className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                    >
                        <Download size={16} />
                        Export
                    </button>
                </div>
            </div>

            {/* Row 1: Sankey-style Flow Diagram (improved styling) */}
            <div className="mb-6 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                <div className="mb-4 flex items-center justify-between">
                    <div>
                        <h3 className="font-semibold text-gray-900">Capital Flow Diagram</h3>
                        <p className="text-sm text-gray-500">Inflow breakdown → Outflow allocation</p>
                    </div>
                    <div className="flex gap-4 text-sm">
                        <span className="flex items-center gap-2">
                            <span className="h-3 w-3 rounded-full bg-gradient-to-br from-emerald-400 to-emerald-600"></span>
                            Income
                        </span>
                        <span className="flex items-center gap-2">
                            <span className="h-3 w-3 rounded-full bg-gradient-to-br from-red-400 to-red-600"></span>
                            Expenses
                        </span>
                        <span className="flex items-center gap-2">
                            <span className="h-3 w-3 rounded-full bg-gradient-to-br from-blue-400 to-blue-600"></span>
                            Savings/Inv
                        </span>
                    </div>
                </div>

                {/* Improved Sankey visualization */}
                <div className="flex items-center justify-center gap-8 py-8">
                    {/* Income sources */}
                    <div className="flex flex-col gap-3 min-w-[160px]">
                        {incomeBreakdown.map((item, i) => {
                            const height = Math.max(40, (item.value / 4000) + 30);
                            return (
                                <div
                                    key={item.name}
                                    className="group relative flex items-center gap-3 rounded-xl bg-gradient-to-r from-emerald-50 to-emerald-100 border border-emerald-200/60 px-4 transition-all hover:shadow-md hover:scale-[1.02]"
                                    style={{ height: `${height}px` }}
                                >
                                    <div className="w-1 h-3/4 rounded-full bg-gradient-to-b from-emerald-400 to-emerald-600" />
                                    <div className="flex-1">
                                        <span className="text-sm font-semibold text-emerald-800">{item.name}</span>
                                        <p className="text-xs text-emerald-600 font-mono">¥{(item.value / 1000).toFixed(0)}k</p>
                                    </div>
                                </div>
                            );
                        })}
                    </div>

                    {/* Flow connectors */}
                    <div className="flex flex-col items-center justify-center relative w-32">
                        <svg className="w-full h-40" viewBox="0 0 100 120">
                            <defs>
                                <linearGradient id="flowGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                                    <stop offset="0%" stopColor="#10b981" stopOpacity="0.4" />
                                    <stop offset="50%" stopColor="#94a3b8" stopOpacity="0.2" />
                                    <stop offset="100%" stopColor="#ef4444" stopOpacity="0.4" />
                                </linearGradient>
                            </defs>
                            {/* Flow paths */}
                            <path d="M 0 20 Q 50 20, 100 30" fill="none" stroke="url(#flowGrad)" strokeWidth="8" strokeLinecap="round" opacity="0.6" />
                            <path d="M 0 60 Q 50 60, 100 60" fill="none" stroke="url(#flowGrad)" strokeWidth="12" strokeLinecap="round" opacity="0.8" />
                            <path d="M 0 100 Q 50 100, 100 90" fill="none" stroke="url(#flowGrad)" strokeWidth="6" strokeLinecap="round" opacity="0.5" />
                        </svg>
                        <div className="absolute bottom-0 text-center">
                            <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400">Total Flow</span>
                            <p className="text-xs font-mono text-gray-600">¥389k</p>
                        </div>
                    </div>

                    {/* Outflow */}
                    <div className="flex flex-col gap-3 min-w-[160px]">
                        {expenseBreakdown.map((item, i) => {
                            const height = Math.max(40, (item.value / 4000) + 30);
                            const isInvestment = item.name === 'Investments';
                            return (
                                <div
                                    key={item.name}
                                    className={`group relative flex items-center gap-3 rounded-xl border px-4 transition-all hover:shadow-md hover:scale-[1.02] ${isInvestment
                                        ? 'bg-gradient-to-r from-blue-50 to-blue-100 border-blue-200/60'
                                        : 'bg-gradient-to-r from-red-50 to-red-100 border-red-200/60'
                                        }`}
                                    style={{ height: `${height}px` }}
                                >
                                    <div className={`w-1 h-3/4 rounded-full ${isInvestment
                                        ? 'bg-gradient-to-b from-blue-400 to-blue-600'
                                        : 'bg-gradient-to-b from-red-400 to-red-600'
                                        }`} />
                                    <div className="flex-1">
                                        <span className={`text-sm font-semibold ${isInvestment ? 'text-blue-800' : 'text-red-800'}`}>
                                            {item.name}
                                        </span>
                                        <p className={`text-xs font-mono ${isInvestment ? 'text-blue-600' : 'text-red-600'}`}>
                                            ¥{(item.value / 1000).toFixed(0)}k
                                        </p>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>

            {/* Row 2: Trends */}
            <div className="mb-6 grid gap-6 lg:grid-cols-2">
                {/* Income vs Expense History */}
                <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                    <div className="mb-4 flex items-center justify-between">
                        <div>
                            <h3 className="font-semibold text-gray-900">Income vs Expense History</h3>
                            <p className="text-sm text-gray-500">Monthly Net Performance</p>
                        </div>
                        <div className="text-right">
                            <p className="text-lg font-bold text-emerald-600">Net +¥{(netFlow / 1000000).toFixed(1)}M</p>
                            <p className="text-xs text-gray-500">YTD Accumulation</p>
                        </div>
                    </div>
                    <ResponsiveContainer width="100%" height={280}>
                        <ComposedChart data={monthlyData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                            <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 12 }} />
                            <YAxis tick={{ fill: '#64748b', fontSize: 12 }} tickFormatter={(v) => `¥${v / 1000}k`} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc' }}
                                formatter={(value: number) => [`¥${value.toLocaleString()}`, '']}
                            />
                            <Legend />
                            <Bar dataKey="expense" name="Expense" stackId="a" fill="#ef4444" radius={[0, 0, 0, 0]} />
                            <Bar dataKey="net" name="Savings" stackId="a" fill="#22c55e" radius={[4, 4, 0, 0]} />
                            <Line type="monotone" dataKey="income" name="Income" stroke="#3b82f6" strokeWidth={2} dot={false} />
                        </ComposedChart>
                    </ResponsiveContainer>
                </div>

                {/* 12-Month Forecast */}
                <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                    <div className="mb-4 flex items-center justify-between">
                        <div>
                            <h3 className="font-semibold text-gray-900">12-Month Cash Forecast</h3>
                            <p className="text-sm text-gray-500">Projected Liquidity</p>
                        </div>
                        <div className="text-right">
                            <p className="text-lg font-bold text-blue-600">Proj. +¥2.4M</p>
                            <p className="text-xs text-gray-500">↗ +8% vs Prior Year</p>
                        </div>
                    </div>
                    <ResponsiveContainer width="100%" height={280}>
                        <AreaChart data={forecastData}>
                            <defs>
                                <linearGradient id="forecast" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                            <XAxis dataKey="quarter" tick={{ fill: '#64748b', fontSize: 12 }} />
                            <YAxis tick={{ fill: '#64748b', fontSize: 12 }} tickFormatter={(v) => `¥${(v / 1000000).toFixed(1)}M`} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc' }}
                                formatter={(value: number) => [`¥${(value / 1000000).toFixed(2)}M`, '']}
                            />
                            <Area type="monotone" dataKey="upper" stroke="transparent" fill="#e0f2fe" />
                            <Area type="monotone" dataKey="lower" stroke="transparent" fill="white" />
                            <Line type="monotone" dataKey="projected" stroke="#3b82f6" strokeWidth={3} dot />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Row 3: Deep Dives (3 cards) */}
            <div className="grid gap-6 lg:grid-cols-3">
                {/* Income Mix */}
                <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                    <div className="mb-4 flex items-center gap-2">
                        <div className="rounded-lg bg-emerald-100 p-2">
                            <TrendingUp className="h-4 w-4 text-emerald-600" />
                        </div>
                        <h3 className="font-semibold text-gray-900">Income Mix</h3>
                    </div>
                    <ResponsiveContainer width="100%" height={180}>
                        <PieChart>
                            <Pie
                                data={incomeBreakdown}
                                cx="50%"
                                cy="50%"
                                innerRadius={40}
                                outerRadius={70}
                                dataKey="value"
                                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                labelLine={false}
                            >
                                {incomeBreakdown.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip formatter={(value: number) => [`¥${value.toLocaleString()}`, '']} />
                        </PieChart>
                    </ResponsiveContainer>
                </div>

                {/* Expense Efficiency */}
                <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                    <div className="mb-4 flex items-center gap-2">
                        <div className="rounded-lg bg-red-100 p-2">
                            <TrendingDown className="h-4 w-4 text-red-600" />
                        </div>
                        <h3 className="font-semibold text-gray-900">Expense Efficiency</h3>
                    </div>
                    <div className="space-y-4">
                        <div>
                            <div className="flex justify-between text-sm mb-1">
                                <span className="text-gray-600">Essential</span>
                                <span className="font-medium">62%</span>
                            </div>
                            <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                                <div className="h-full bg-blue-500 rounded-full" style={{ width: '62%' }}></div>
                            </div>
                        </div>
                        <div>
                            <div className="flex justify-between text-sm mb-1">
                                <span className="text-gray-600">Lifestyle</span>
                                <span className="font-medium">23%</span>
                            </div>
                            <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                                <div className="h-full bg-amber-500 rounded-full" style={{ width: '23%' }}></div>
                            </div>
                        </div>
                        <div>
                            <div className="flex justify-between text-sm mb-1">
                                <span className="text-gray-600">Discretionary</span>
                                <span className="font-medium">15%</span>
                            </div>
                            <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                                <div className="h-full bg-purple-500 rounded-full" style={{ width: '15%' }}></div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Top Categories */}
                <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                    <div className="mb-4 flex items-center gap-2">
                        <div className="rounded-lg bg-blue-100 p-2">
                            <PiggyBank className="h-4 w-4 text-blue-600" />
                        </div>
                        <h3 className="font-semibold text-gray-900">Top Categories</h3>
                    </div>
                    <ResponsiveContainer width="100%" height={180}>
                        <PieChart>
                            <Pie
                                data={expenseCategories}
                                cx="50%"
                                cy="50%"
                                innerRadius={40}
                                outerRadius={70}
                                dataKey="value"
                                label={({ name, value }) => `${name}`}
                                labelLine={false}
                            >
                                {expenseCategories.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip formatter={(value: number) => [`${value}%`, '']} />
                        </PieChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
};

export default CashFlow;
