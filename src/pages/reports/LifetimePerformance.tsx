/**
 * Lifetime Performance Report
 * The "Scorecard" - Total realized profits, tax efficiency, and individual asset track records
 * 
 * Two Views:
 * 1. Gains Analysis - KPIs and charts for realized vs unrealized gains
 * 2. Asset Performance - Table view with individual asset track records
 */

import React, { useState } from 'react';
import { Download, Filter, Search, TrendingUp, BarChart3, Table } from 'lucide-react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
    Cell,
} from 'recharts';

// Demo data for gains breakdown
const GAINS_BREAKDOWN = [
    { name: 'Realized Gains', value: 328698, color: '#22c55e' },
    { name: 'Unrealized Gains', value: 97089, color: '#3b82f6' },
];

// Demo data for sub-class breakdown
const SUBCLASS_DATA = [
    { name: 'CN Equity', realized: 280000, unrealized: 45000 },
    { name: 'US Equity', realized: 35000, unrealized: 28000 },
    { name: 'HK ETF', realized: 8000, unrealized: 12000 },
    { name: 'Unknown', realized: 2000, unrealized: 3000 },
    { name: 'Bond', realized: 1500, unrealized: 2500 },
    { name: 'Crypto', realized: 1200, unrealized: 4000 },
    { name: 'Gold', realized: 500, unrealized: 1500 },
    { name: 'Real Estate', realized: 498, unrealized: 1089 },
];

// Demo data for asset performance table
const ASSET_DATA = [
    { name: '易方达中证500ETF联接发起式A', class: '股票', period: '4y 7m', status: 'ACTIVE', invested: 198099, currentValue: 152567, profit: 87037, return: 43.94 },
    { name: '景顺长城沪深300指数增强A', class: '股票', period: '7y 9m', status: 'ACTIVE', invested: 277833, currentValue: 256418, profit: 83689, return: 30.12 },
    { name: 'Amazon RSU', class: '股票', period: '2y 3m', status: 'ACTIVE', invested: 459822, currentValue: 255679, profit: 83434, return: 18.14 },
    { name: '申万菱信沪深300价值指数A', class: '股票', period: '6y 3m', status: 'CLOSED', invested: 178877, currentValue: 0, profit: 49764, return: 27.82 },
    { name: 'ALPHABET INC CLASS A', class: '股票', period: '1m 22d', status: 'ACTIVE', invested: 27218, currentValue: 30061, profit: 2863, return: 10.52 },
    { name: 'INVESCO QQQ-U ETF', class: '股票', period: '3m 22d', status: 'CLOSED', invested: 28208, currentValue: 0, profit: 2239, return: 7.94 },
    { name: 'Paper Gold (纸黄金)', class: '商品', period: '10m 13d', status: 'ACTIVE', invested: 229888, currentValue: 189838, profit: -13452, return: -5.85 },
    { name: '博时标普500ETF联接A', class: '股票', period: '1y 11m', status: 'ACTIVE', invested: 19123, currentValue: 24011, profit: 4888, return: 25.56 },
];

type ViewType = 'gains' | 'table';

const LifetimePerformance: React.FC = () => {
    const [view, setView] = useState<ViewType>('gains');
    const [searchQuery, setSearchQuery] = useState('');

    const totalRealized = 328698;
    const totalUnrealized = 97089;
    const totalGains = totalRealized + totalUnrealized;

    const filteredAssets = ASSET_DATA.filter(asset =>
        asset.name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const activeAssets = ASSET_DATA.filter(a => a.status === 'ACTIVE').length;
    const totalAssets = ASSET_DATA.length;

    return (
        <div className="p-6 lg:p-8">
            {/* Header with Tab Navigation */}
            <div className="mb-6">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">
                            {view === 'gains' ? 'Realized vs. Unrealized Gains Analysis' : 'Lifetime Asset Performance'}
                        </h1>
                    </div>
                    <div className="flex items-center gap-3">
                        {/* View Toggle */}
                        <div className="flex rounded-lg border border-gray-200 bg-white p-1">
                            <button
                                onClick={() => setView('gains')}
                                className={`flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${view === 'gains' ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:text-gray-900'
                                    }`}
                            >
                                <BarChart3 size={16} />
                                Gains Analysis
                            </button>
                            <button
                                onClick={() => setView('table')}
                                className={`flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${view === 'table' ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:text-gray-900'
                                    }`}
                            >
                                <Table size={16} />
                                Performance Table
                            </button>
                        </div>
                    </div>
                </div>
                <div className="h-1 w-full bg-gradient-to-r from-blue-500 to-blue-300 rounded-full"></div>
            </div>

            {view === 'gains' ? (
                /* VIEW 1: Gains Analysis */
                <>
                    {/* Row 1: KPI Cards */}
                    <div className="mb-6 grid gap-6 lg:grid-cols-3">
                        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm text-center">
                            <p className="text-3xl font-bold text-emerald-600">¥{totalRealized.toLocaleString()}</p>
                            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mt-2">Total Realized Gains</p>
                        </div>
                        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm text-center">
                            <p className="text-3xl font-bold text-blue-600">¥{totalUnrealized.toLocaleString()}</p>
                            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mt-2">Total Unrealized Gains</p>
                        </div>
                        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm text-center">
                            <p className="text-3xl font-bold text-gray-900">¥{totalGains.toLocaleString()}</p>
                            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mt-2">Total Gains</p>
                        </div>
                    </div>

                    {/* Row 2: Charts */}
                    <div className="grid gap-6 lg:grid-cols-2">
                        {/* Gains Breakdown */}
                        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                            <h3 className="font-semibold text-gray-900 mb-4">Gains Breakdown</h3>
                            <ResponsiveContainer width="100%" height={300}>
                                <BarChart data={GAINS_BREAKDOWN} layout="horizontal">
                                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                                    <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} />
                                    <YAxis tick={{ fill: '#64748b', fontSize: 12 }} tickFormatter={(v) => `¥${(v / 1000).toFixed(0)}k`} axisLine={false} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc' }}
                                        formatter={(value: number) => [`¥${value.toLocaleString()}`, '']}
                                    />
                                    <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                                        {GAINS_BREAKDOWN.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.color} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Sub-Class Level Breakdown */}
                        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="font-semibold text-gray-900">Sub-Class Level Realized vs Unrealized</h3>
                                <div className="flex gap-4 text-sm">
                                    <span className="flex items-center gap-2">
                                        <span className="h-3 w-3 rounded-sm bg-[#22c55e]"></span>
                                        Realized Gains
                                    </span>
                                    <span className="flex items-center gap-2">
                                        <span className="h-3 w-3 rounded-sm bg-blue-500"></span>
                                        Unrealized Gains
                                    </span>
                                </div>
                            </div>
                            <ResponsiveContainer width="100%" height={300}>
                                <BarChart data={SUBCLASS_DATA}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                                    <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} angle={-45} textAnchor="end" height={80} />
                                    <YAxis tick={{ fill: '#64748b', fontSize: 12 }} tickFormatter={(v) => `¥${(v / 1000).toFixed(0)}k`} axisLine={false} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc' }}
                                        formatter={(value: number) => [`¥${value.toLocaleString()}`, '']}
                                    />
                                    <Bar dataKey="realized" name="Realized" stackId="a" fill="#22c55e" />
                                    <Bar dataKey="unrealized" name="Unrealized" stackId="a" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </>
            ) : (
                /* VIEW 2: Asset Performance Table */
                <>
                    {/* Header Controls */}
                    <div className="mb-4 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => setView('gains')}
                                className="px-3 py-1.5 text-sm font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50"
                            >
                                Hide Table
                            </button>
                        </div>
                        <div className="flex items-center gap-3">
                            <div className="relative">
                                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                                <input
                                    type="text"
                                    placeholder="Search assets..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="pl-9 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-200"
                                />
                            </div>
                            <button className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">
                                <Filter size={16} />
                                Filter
                            </button>
                            <button className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700">
                                <Download size={16} />
                                Export CSV
                            </button>
                        </div>
                    </div>

                    {/* Data Table */}
                    <div className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="min-w-full">
                                <thead>
                                    <tr className="border-b border-gray-100 bg-gray-50">
                                        <th className="py-3 px-4 text-left text-xs font-semibold uppercase text-gray-500">Asset Name</th>
                                        <th className="py-3 px-4 text-left text-xs font-semibold uppercase text-gray-500">Asset Class</th>
                                        <th className="py-3 px-4 text-left text-xs font-semibold uppercase text-gray-500">Holding Period</th>
                                        <th className="py-3 px-4 text-center text-xs font-semibold uppercase text-gray-500">Status</th>
                                        <th className="py-3 px-4 text-right text-xs font-semibold uppercase text-gray-500">Total Invested</th>
                                        <th className="py-3 px-4 text-right text-xs font-semibold uppercase text-gray-500">Current Value</th>
                                        <th className="py-3 px-4 text-right text-xs font-semibold uppercase text-gray-500">Profit/Loss</th>
                                        <th className="py-3 px-4 text-right text-xs font-semibold uppercase text-gray-500">Return %</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100 text-xs">
                                    {filteredAssets.map((asset, i) => (
                                        <tr key={i} className="hover:bg-gray-50 transition-colors">
                                            <td className="py-3 px-4 font-medium text-gray-900">{asset.name}</td>
                                            <td className="py-3 px-4 text-gray-600">{asset.class}</td>
                                            <td className="py-3 px-4 text-gray-600">{asset.period}</td>
                                            <td className="py-3 px-4 text-center">
                                                <span className={`px-2 py-1 text-xs font-semibold rounded-full ${asset.status === 'ACTIVE'
                                                    ? 'bg-emerald-100 text-emerald-700'
                                                    : 'bg-gray-100 text-gray-600'
                                                    }`}>
                                                    {asset.status}
                                                </span>
                                            </td>
                                            <td className="py-3 px-4 text-right font-mono text-gray-700">¥{asset.invested.toLocaleString()}</td>
                                            <td className="py-3 px-4 text-right font-mono text-gray-700">
                                                {asset.currentValue > 0 ? `¥${asset.currentValue.toLocaleString()}` : '—'}
                                            </td>
                                            <td className={`py-3 px-4 text-right font-mono font-semibold ${asset.profit >= 0 ? 'text-emerald-600' : 'text-red-600'
                                                }`}>
                                                ¥{asset.profit.toLocaleString()}
                                            </td>
                                            <td className={`py-3 px-4 text-right font-semibold ${asset.return >= 0 ? 'text-emerald-600' : 'text-red-600'
                                                }`}>
                                                {asset.return >= 0 ? '+' : ''}{asset.return.toFixed(2)}%
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                        <div className="px-4 py-3 border-t border-gray-100 flex items-center justify-between">
                            <p className="text-sm text-gray-500">Showing 1 to {filteredAssets.length} of {totalAssets} assets</p>
                            <div className="flex items-center gap-1">
                                <button className="px-3 py-1 text-sm text-gray-400 hover:text-gray-600">&lt;</button>
                                <button className="px-3 py-1 text-sm font-medium text-white bg-blue-600 rounded">1</button>
                                <button className="px-3 py-1 text-sm text-gray-600 hover:bg-gray-100 rounded">2</button>
                                <button className="px-3 py-1 text-sm text-gray-600 hover:bg-gray-100 rounded">3</button>
                                <button className="px-3 py-1 text-sm text-gray-400 hover:text-gray-600">&gt;</button>
                            </div>
                        </div>
                    </div>

                    {/* Footer Summary Cards */}
                    <div className="mt-6 grid gap-6 lg:grid-cols-3">
                        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Total Lifetime Gain</p>
                            <p className="text-3xl font-bold text-emerald-600">+¥{totalGains.toLocaleString()}</p>
                            <p className="text-xs text-gray-500 mt-1">Combined realized & unrealized</p>
                        </div>
                        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Weighted XIRR</p>
                            <p className="text-3xl font-bold text-blue-600">18.42%</p>
                            <p className="text-xs text-gray-500 mt-1">Overall portfolio performance</p>
                        </div>
                        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Active Assets</p>
                            <p className="text-3xl font-bold text-gray-900">{activeAssets} / {totalAssets}</p>
                            <p className="text-xs text-gray-500 mt-1">Current holding distribution</p>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};

export default LifetimePerformance;
