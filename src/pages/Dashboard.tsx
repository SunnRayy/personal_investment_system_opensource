import React from 'react';
import {
    ArrowUp,
    ArrowUpRight,
    Wallet,
    TrendingUp,
    PieChart,
    Clock,
    DollarSign
} from 'lucide-react';
import { AllocationData, Activity, NetWorthPoint } from '../types';
import { AreaChart, Area, PieChart as RechartsPie, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

// Constants (Inlined for simplicity as requested to be a page component)
const ALLOCATION_DATA: AllocationData[] = [
    { name: 'Stocks', value: 60, color: '#3B82F6' },
    { name: 'Bonds', value: 30, color: '#D4AF37' },
    { name: 'Alternatives', value: 10, color: '#14B8A6' },
    { name: 'Cash', value: 0, color: '#10B981' },
];

const RECENT_ACTIVITY: Activity[] = [
    { id: '1', type: 'buy', asset: 'Apple Inc. (AAPL)', amount: -1200.00, date: 'May 15, 2024', icon: 'arrow_upward' },
    { id: '2', type: 'deposit', asset: 'Deposit from Bank', amount: 5000.00, date: 'May 14, 2024', icon: 'vertical_align_bottom' },
    { id: '3', type: 'dividend', asset: 'Microsoft Corp. (MSFT)', amount: 85.50, date: 'May 12, 2024', icon: 'database' },
];

const NET_WORTH_HISTORY: NetWorthPoint[] = [
    { date: 'Jan', value: 1350000 },
    { date: 'Feb', value: 1420000 },
    { date: 'Mar', value: 1480000 },
    { date: 'Apr', value: 1450000 },
    { date: 'May', value: 1410000 },
    { date: 'Jun', value: 1380000 },
    { date: 'Jul', value: 1420000 },
    { date: 'Aug', value: 1480000 },
    { date: 'Sep', value: 1520000 },
    { date: 'Oct', value: 1550000 },
    { date: 'Nov', value: 1540000 },
    { date: 'Dec', value: 1561662.82 },
];

const Dashboard: React.FC = () => {
    return (
        <div className="p-6 md:p-8 space-y-8">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900">Welcome back, Ray</h1>
                    <p className="text-sm text-slate-500">Here's your financial overview for today.</p>
                </div>
                <div className="flex items-center gap-3">
                    <button className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 shadow-sm transition-colors">
                        Last Month
                    </button>
                    <button className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 shadow-sm transition-colors flex items-center gap-2">
                        <ArrowUpRight size={16} />
                        Generate Report
                    </button>
                </div>
            </div>

            {/* Main Net Worth Section */}
            <div className="bg-white rounded-2xl shadow-sm border-[2px] border-[#EAD588] overflow-hidden relative">
                <div className="p-8 pb-4 relative z-10">
                    <h2 className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em] mb-3">Net Worth</h2>
                    <div className="text-5xl font-bold text-gray-900 tracking-tighter mb-4">$1,561,662.82</div>
                    <div className="flex items-center gap-2 text-sm font-semibold">
                        <div className="flex items-center text-[#10B981] bg-emerald-50 px-2 py-1 rounded-full">
                            <ArrowUp size={16} strokeWidth={3} />
                            <span className="ml-1">+ $23,456 (+2.1%)</span>
                        </div>
                        <span className="text-gray-400 font-medium">this month</span>
                    </div>
                </div>

                <div className="h-64 md:h-72 w-full mt-4 -mb-1">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={NET_WORTH_HISTORY}>
                            <defs>
                                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#EAD588" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#EAD588" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <Tooltip
                                contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
                                formatter={(value: number) => [`$${value.toLocaleString()}`, 'Net Worth']}
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
                </div>
            </div>

            {/* Stats Grid */}
            <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard label="YTD Return" value="+15.3%" colorClass="text-[#10B981]" icon={TrendingUp} />
                <StatCard label="Holdings" value="13" icon={PieChart} />
                <StatCard label="Cash" value="$45,000.00" icon={Wallet} />
                <StatCard label="XIRR" value="12.4%" colorClass="text-[#3B82F6]" icon={Clock} />
            </section>

            {/* Secondary Grid */}
            <section className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Allocation Breakdown */}
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 flex flex-col overflow-hidden">
                    <div className="px-6 py-5 border-b border-gray-50 flex justify-between items-center">
                        <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Allocation Breakdown</h3>
                        <button className="text-slate-400 hover:text-slate-600 transition-colors">
                            <PieChart size={16} />
                        </button>
                    </div>
                    <div className="flex-grow flex flex-col sm:flex-row items-center p-8 gap-8">
                        <div className="w-[180px] h-[180px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <RechartsPie width={180} height={180}>
                                    <Pie
                                        data={ALLOCATION_DATA}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={80}
                                        paddingAngle={5}
                                        dataKey="value"
                                    >
                                        {ALLOCATION_DATA.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.color} stroke="none" />
                                        ))}
                                    </Pie>
                                </RechartsPie>
                            </ResponsiveContainer>
                        </div>
                        <div className="flex flex-col justify-center gap-5 flex-1 w-full">
                            {ALLOCATION_DATA.filter(d => d.value > 0).map((item) => (
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
                        <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Recent Activity</h3>
                    </div>
                    <div className="flex-grow overflow-y-auto">
                        {RECENT_ACTIVITY.map((activity) => (
                            <div key={activity.id} className="flex items-center justify-between p-5 border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors cursor-pointer group">
                                <div className="flex items-center gap-4">
                                    <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-transform group-hover:scale-105 ${activity.type === 'buy' ? 'bg-blue-50 text-blue-600' :
                                            activity.type === 'deposit' ? 'bg-green-50 text-green-600' : 'bg-yellow-50 text-yellow-600'
                                        }`}>
                                        {activity.type === 'buy' && <TrendingUp size={20} />}
                                        {activity.type === 'deposit' && <DollarSign size={20} />}
                                        {activity.type === 'dividend' && <PieChart size={20} />}
                                    </div>
                                    <div>
                                        <div className="text-sm font-bold text-gray-900">{activity.asset}</div>
                                        <div className="text-[11px] font-bold text-gray-400 uppercase mt-0.5 tracking-tight">{activity.type}</div>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className={`text-sm font-bold ${activity.amount > 0 ? 'text-[#10B981]' : 'text-gray-900'}`}>
                                        {activity.amount > 0 ? '+' : ''} {activity.amount.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
                                    </div>
                                    <div className="text-[11px] font-medium text-gray-400 mt-0.5">{activity.date}</div>
                                </div>
                            </div>
                        ))}
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
            <h3 className="text-[11px] font-bold text-gray-400 uppercase tracking-widest group-hover:text-indigo-500 transition-colors">{label}</h3>
            {Icon && <Icon size={18} className="text-gray-300 group-hover:text-indigo-400 transition-colors" />}
        </div>
        <div className={`text-3xl font-bold tracking-tight ${colorClass}`}>{value}</div>
    </div>
);

export default Dashboard;
