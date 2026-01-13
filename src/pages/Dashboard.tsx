import React from 'react';
import {
    ArrowUp,
    ArrowDown,
    ArrowUpRight,
    Wallet,
    TrendingUp,
    PieChart,
    Clock,
    DollarSign,
    RefreshCw,
    AlertCircle,
    Loader2
} from 'lucide-react';
import { AllocationData, Activity, NetWorthPoint } from '../types';
import { AreaChart, Area, PieChart as RechartsPie, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { usePortfolioOverview } from '../hooks/usePortfolio';

// Chart colors using SunnRayy design system
const CHART_COLORS = {
    equity: '#D4AF37',       // Gold - Stocks
    fixed_income: '#3B82F6', // Tech Blue - Bonds
    cash: '#6B7280',         // Gray - Cash
    alternatives: '#8B5CF6', // Violet - Alternatives
    real_estate: '#F59E0B',  // Amber - Real estate
    crypto: '#EC4899',       // Pink - Cryptocurrency
    default: '#14B8A6',      // Teal - Other
};

// Map allocation categories to colors
function getAllocationColor(category: string): string {
    const key = category.toLowerCase().replace(/[\s-]/g, '_');
    if (key.includes('stock') || key.includes('equity')) return CHART_COLORS.equity;
    if (key.includes('bond') || key.includes('fixed')) return CHART_COLORS.fixed_income;
    if (key.includes('cash') || key.includes('money')) return CHART_COLORS.cash;
    if (key.includes('alternative')) return CHART_COLORS.alternatives;
    if (key.includes('real') || key.includes('estate')) return CHART_COLORS.real_estate;
    if (key.includes('crypto')) return CHART_COLORS.crypto;
    return CHART_COLORS.default;
}

// Format currency
function formatCurrency(value: number, currency: string = 'CNY'): string {
    const symbol = currency === 'CNY' ? '¥' : '$';
    return `${symbol}${value.toLocaleString('en-US', { maximumFractionDigits: 0 })}`;
}

// Format percentage
function formatPercent(value: number): string {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(1)}%`;
}

// Format date string to short month
function formatDateToMonth(dateStr: string): string {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short' });
}

// Fallback data for when API is unavailable
const FALLBACK_ALLOCATION: AllocationData[] = [
    { name: 'Stocks', value: 60, color: CHART_COLORS.equity },
    { name: 'Bonds', value: 30, color: CHART_COLORS.fixed_income },
    { name: 'Alternatives', value: 10, color: CHART_COLORS.alternatives },
];

const FALLBACK_ACTIVITY: Activity[] = [
    { id: '1', type: 'dividend', asset: 'Connect Flask backend...', amount: 0, date: 'Now', icon: 'info' },
];

const Dashboard: React.FC = () => {
    const { data, isLoading, isError, error, refetch } = usePortfolioOverview();

    // Transform API data to chart format
    const allocationData: AllocationData[] = React.useMemo(() => {
        if (!data?.allocation) return FALLBACK_ALLOCATION;

        const total = Object.values(data.allocation).reduce((sum, val) => sum + val, 0);
        if (total === 0) return FALLBACK_ALLOCATION;

        return Object.entries(data.allocation)
            .filter(([_, value]) => value > 0)
            .map(([name, value]) => ({
                name,
                value: Math.round((value / total) * 100),
                color: getAllocationColor(name),
            }));
    }, [data?.allocation]);

    const netWorthHistory: NetWorthPoint[] = React.useMemo(() => {
        if (!data?.trend?.dates || !data?.trend?.values) return [];

        return data.trend.dates.map((date, i) => ({
            date: formatDateToMonth(date),
            value: data.trend.values[i],
        }));
    }, [data?.trend]);

    // Calculate month-over-month change
    const monthChange = React.useMemo(() => {
        if (netWorthHistory.length < 2) return { amount: 0, percent: 0 };

        const current = netWorthHistory[netWorthHistory.length - 1]?.value || 0;
        const previous = netWorthHistory[netWorthHistory.length - 2]?.value || current;
        const change = current - previous;
        const percent = previous > 0 ? (change / previous) * 100 : 0;

        return { amount: change, percent };
    }, [netWorthHistory]);

    const isPositiveChange = monthChange.amount >= 0;
    const currency = data?.currency || 'CNY';

    // Loading state
    if (isLoading) {
        return (
            <div className="p-6 md:p-8 flex items-center justify-center min-h-[400px]">
                <div className="text-center">
                    <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
                    <p className="text-gray-500">Loading portfolio data...</p>
                </div>
            </div>
        );
    }

    // Error state
    if (isError) {
        return (
            <div className="p-6 md:p-8">
                <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
                    <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-3" />
                    <h3 className="text-lg font-semibold text-red-800 mb-2">Failed to load data</h3>
                    <p className="text-red-600 text-sm mb-4">
                        {error instanceof Error ? error.message : 'Unable to connect to backend'}
                    </p>
                    <p className="text-red-500 text-xs mb-4">
                        Make sure Flask backend is running on port 5001
                    </p>
                    <button
                        onClick={() => refetch()}
                        className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 transition-colors inline-flex items-center gap-2"
                    >
                        <RefreshCw size={16} />
                        Try Again
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="p-6 md:p-8 space-y-8">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Welcome back, Ray</h1>
                    <p className="text-sm text-gray-500">Here's your financial overview for today.</p>
                </div>
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => refetch()}
                        className="px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 shadow-sm transition-colors inline-flex items-center gap-2"
                    >
                        <RefreshCw size={16} />
                        Refresh
                    </button>
                    <button className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 shadow-sm transition-colors flex items-center gap-2">
                        <ArrowUpRight size={16} />
                        Generate Report
                    </button>
                </div>
            </div>

            {/* Main Net Worth Section */}
            <div className="bg-white rounded-2xl shadow-sm border-[2px] border-[#EAD588] overflow-hidden relative">
                <div className="p-8 pb-4 relative z-10">
                    <h2 className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em] mb-3">Net Worth</h2>
                    <div className="text-5xl font-bold text-gray-900 tracking-tighter mb-4">
                        {formatCurrency(data?.total_portfolio_value || 0, currency)}
                    </div>
                    <div className="flex items-center gap-2 text-sm font-semibold">
                        <div className={`flex items-center ${isPositiveChange ? 'text-[#10B981] bg-emerald-50' : 'text-[#EF4444] bg-red-50'} px-2 py-1 rounded-full`}>
                            {isPositiveChange ? <ArrowUp size={16} strokeWidth={3} /> : <ArrowDown size={16} strokeWidth={3} />}
                            <span className="ml-1">
                                {isPositiveChange ? '+' : ''}{formatCurrency(monthChange.amount, currency)} ({formatPercent(monthChange.percent)})
                            </span>
                        </div>
                        <span className="text-gray-400 font-medium">this month</span>
                    </div>
                </div>

                <div className="h-64 md:h-72 w-full mt-4 -mb-1">
                    {netWorthHistory.length > 0 ? (
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={netWorthHistory}>
                                <defs>
                                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#EAD588" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#EAD588" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <Tooltip
                                    contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
                                    formatter={(value: number) => [formatCurrency(value, currency), 'Net Worth']}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="value"
                                    stroke="#D4AF37"
                                    strokeWidth={3}
                                    fillOpacity={1}
                                    fill="url(#colorValue)"
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="flex items-center justify-center h-full text-gray-400">
                            <p>No historical data available</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Stats Grid */}
            <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    label="Holdings"
                    value={String(data?.current_holdings_count || 0)}
                    icon={PieChart}
                />
                <StatCard
                    label="History Points"
                    value={String(data?.historical_records || 0)}
                    icon={Clock}
                />
                <StatCard
                    label="Currency"
                    value={currency}
                    icon={Wallet}
                />
                <StatCard
                    label="Data Status"
                    value={data?.holdings_available ? 'Live' : 'Demo'}
                    colorClass={data?.holdings_available ? 'text-[#10B981]' : 'text-[#F59E0B]'}
                    icon={TrendingUp}
                />
            </section>

            {/* Secondary Grid */}
            <section className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Allocation Breakdown */}
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 flex flex-col overflow-hidden">
                    <div className="px-6 py-5 border-b border-gray-50 flex justify-between items-center">
                        <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Allocation Breakdown</h3>
                        <button className="text-gray-400 hover:text-gray-600 transition-colors">
                            <PieChart size={16} />
                        </button>
                    </div>
                    <div className="flex-grow flex flex-col sm:flex-row items-center p-8 gap-8">
                        <div className="w-[180px] h-[180px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <RechartsPie width={180} height={180}>
                                    <Pie
                                        data={allocationData}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={80}
                                        paddingAngle={5}
                                        dataKey="value"
                                    >
                                        {allocationData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.color} stroke="none" />
                                        ))}
                                    </Pie>
                                </RechartsPie>
                            </ResponsiveContainer>
                        </div>
                        <div className="flex flex-col justify-center gap-5 flex-1 w-full">
                            {allocationData.filter(d => d.value > 0).map((item) => (
                                <div key={item.name} className="flex items-center justify-between group">
                                    <div className="flex items-center gap-3">
                                        <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }}></div>
                                        <span className="text-sm font-medium text-gray-600 group-hover:text-gray-900 transition-colors">{item.name}</span>
                                    </div>
                                    <span className="text-sm font-bold text-gray-900">{item.value}%</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Recent Activity */}
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 flex flex-col overflow-hidden">
                    <div className="px-6 py-5 border-b border-gray-50">
                        <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">System Status</h3>
                    </div>
                    <div className="flex-grow overflow-y-auto p-6">
                        <div className="space-y-4">
                            <StatusItem
                                label="Backend Connection"
                                status="connected"
                                detail="Flask API responding"
                            />
                            <StatusItem
                                label="Holdings Data"
                                status={data?.holdings_available ? 'available' : 'unavailable'}
                                detail={data?.holdings_available ? `${data.current_holdings_count} assets loaded` : 'No holdings found'}
                            />
                            <StatusItem
                                label="Balance Sheet"
                                status={data?.balance_sheet_available ? 'available' : 'unavailable'}
                                detail={data?.balance_sheet_available ? 'Historical data ready' : 'Not configured'}
                            />
                            <StatusItem
                                label="Last Updated"
                                status="info"
                                detail={data?.generated_at ? new Date(data.generated_at).toLocaleTimeString() : 'Unknown'}
                            />
                        </div>
                    </div>
                </div>
            </section>
        </div>
    );
};

interface StatCardProps {
    label: string;
    value: string;
    colorClass?: string;
    icon?: React.ElementType;
}

const StatCard: React.FC<StatCardProps> = ({ label, value, colorClass = "text-gray-900", icon: Icon }) => (
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col transition-all duration-300 hover:shadow-md hover:border-gray-200 group">
        <div className="flex items-center justify-between mb-4">
            <h3 className="text-[11px] font-bold text-gray-400 uppercase tracking-widest group-hover:text-blue-500 transition-colors">{label}</h3>
            {Icon && <Icon size={18} className="text-gray-300 group-hover:text-blue-400 transition-colors" />}
        </div>
        <div className={`text-3xl font-bold tracking-tight ${colorClass}`}>{value}</div>
    </div>
);

interface StatusItemProps {
    label: string;
    status: 'connected' | 'available' | 'unavailable' | 'info';
    detail: string;
}

const StatusItem: React.FC<StatusItemProps> = ({ label, status, detail }) => {
    const statusColors = {
        connected: 'bg-green-100 text-green-700',
        available: 'bg-green-100 text-green-700',
        unavailable: 'bg-yellow-100 text-yellow-700',
        info: 'bg-blue-100 text-blue-700',
    };

    const statusDots = {
        connected: 'bg-green-500',
        available: 'bg-green-500',
        unavailable: 'bg-yellow-500',
        info: 'bg-blue-500',
    };

    return (
        <div className="flex items-center justify-between py-3 border-b border-gray-50 last:border-0">
            <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${statusDots[status]}`} />
                <span className="text-sm font-medium text-gray-700">{label}</span>
            </div>
            <span className={`text-xs font-medium px-2 py-1 rounded-full ${statusColors[status]}`}>
                {detail}
            </span>
        </div>
    );
};

export default Dashboard;
