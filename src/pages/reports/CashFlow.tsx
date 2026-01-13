/**
 * Cash Flow Report Page
 * Capital flow visualization and forecasting
 */

import React from 'react';
import { Download, Calendar, TrendingUp, TrendingDown, DollarSign, PiggyBank } from 'lucide-react';
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

const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

const CashFlow: React.FC = () => {
    const { data: cashFlowData, isLoading, error, refetch } = useCashFlow();

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
                <div className="flex gap-3">
                    <button className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
                        <Calendar size={16} />
                        Last 12 Months
                    </button>
                    <button className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
                        <Download size={16} />
                        Export Report
                    </button>
                </div>
            </div>

            {/* Row 1: Sankey-style Flow Diagram (simplified as stacked visual) */}
            <div className="mb-6 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                <div className="mb-4 flex items-center justify-between">
                    <div>
                        <h3 className="font-semibold text-gray-900">Capital Flow Diagram</h3>
                        <p className="text-sm text-gray-500">Inflow breakdown (Salary, RSU, Dividends) → Outflow allocation</p>
                    </div>
                    <div className="flex gap-4 text-sm">
                        <span className="flex items-center gap-2">
                            <span className="h-3 w-3 rounded-full bg-emerald-500"></span>
                            Income
                        </span>
                        <span className="flex items-center gap-2">
                            <span className="h-3 w-3 rounded-full bg-red-500"></span>
                            Expenses
                        </span>
                        <span className="flex items-center gap-2">
                            <span className="h-3 w-3 rounded-full bg-blue-500"></span>
                            Savings/Inv
                        </span>
                    </div>
                </div>

                {/* Simplified Sankey visualization */}
                <div className="flex items-center justify-center gap-4 py-8">
                    {/* Income sources */}
                    <div className="flex flex-col gap-2">
                        {incomeBreakdown.map((item, i) => (
                            <div
                                key={item.name}
                                className="flex items-center gap-2 rounded-lg bg-emerald-100 px-4 py-3"
                                style={{ height: `${30 + (item.value / 5000)}px` }}
                            >
                                <span className="text-sm font-medium text-emerald-700">{item.name}</span>
                                <span className="text-xs text-emerald-600">¥{(item.value / 1000).toFixed(0)}k</span>
                            </div>
                        ))}
                    </div>

                    {/* Flow arrows */}
                    <div className="flex flex-col items-center justify-center">
                        <div className="h-32 w-24 rounded-lg bg-gradient-to-r from-emerald-200 via-gray-100 to-red-200"></div>
                        <p className="mt-2 text-xs text-gray-500">Total Flow</p>
                    </div>

                    {/* Outflow */}
                    <div className="flex flex-col gap-2">
                        {expenseBreakdown.map((item, i) => (
                            <div
                                key={item.name}
                                className={`flex items-center gap-2 rounded-lg px-4 py-3 ${item.name === 'Investments' ? 'bg-blue-100' : 'bg-red-100'
                                    }`}
                                style={{ height: `${30 + (item.value / 5000)}px` }}
                            >
                                <span className={`text-sm font-medium ${item.name === 'Investments' ? 'text-blue-700' : 'text-red-700'
                                    }`}>{item.name}</span>
                                <span className={`text-xs ${item.name === 'Investments' ? 'text-blue-600' : 'text-red-600'
                                    }`}>¥{(item.value / 1000).toFixed(0)}k</span>
                            </div>
                        ))}
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
