/**
 * Wealth Overview Page
 * Net Worth, Cash Flow, and Expense analysis dashboard
 */

import React, { useState } from 'react';
import {
  Download,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Wallet,
  PiggyBank,
  Receipt,
  AlertCircle,
  ChevronUp,
  ChevronDown,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  PieChart,
  Pie,
  Cell,
  ComposedChart,
} from 'recharts';
import clsx from 'clsx';
import { twMerge } from 'tailwind-merge';
import { useWealthDashboard } from '../hooks/useWealth';

function cn(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs));
}

// Color palette (SunnRayy design system)
const COLORS = {
  primary: '#3b82f6',    // Blue
  success: '#22c55e',    // Green
  warning: '#f59e0b',    // Amber
  danger: '#ef4444',     // Red
  purple: '#8b5cf6',
  cyan: '#06b6d4',
  navy: '#1e3a5f',
  gold: '#d4a853',
};

const PIE_COLORS = [COLORS.primary, COLORS.success, COLORS.warning, COLORS.purple, COLORS.cyan, COLORS.danger];

type TabType = 'networth' | 'cashflow' | 'expenses';

// KPI Card Component
interface KPICardProps {
  label: string;
  value: string;
  yoy?: string;
  icon: React.ElementType;
  iconBgColor: string;
  iconColor: string;
}

const KPICard: React.FC<KPICardProps> = ({ label, value, yoy, icon: Icon, iconBgColor, iconColor }) => {
  const isPositive = yoy?.startsWith('+');
  const isNegative = yoy?.startsWith('-');

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition-all hover:shadow-md">
      <div className="flex items-center gap-3">
        <div className={cn('flex h-10 w-10 items-center justify-center rounded-lg', iconBgColor)}>
          <Icon className={cn('h-5 w-5', iconColor)} />
        </div>
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-gray-500">{label}</p>
          <p className="text-xl font-bold text-gray-900">{value}</p>
          {yoy && (
            <div className={cn(
              'flex items-center gap-1 text-xs font-medium',
              isPositive && 'text-emerald-600',
              isNegative && label.includes('Expense') ? 'text-emerald-600' : isNegative && 'text-red-600',
              !isPositive && !isNegative && 'text-gray-500'
            )}>
              {isPositive ? <ChevronUp size={14} /> : isNegative ? <ChevronDown size={14} /> : null}
              {yoy} YoY
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const Wealth: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('networth');
  const { data: wealthData, isLoading, error, refetch, isFetching } = useWealthDashboard();

  // Demo data for charts (fallback when API data unavailable)
  const netWorthTrendData = React.useMemo(() => {
    if (wealthData?.balance_sheet?.trend_chart?.labels) {
      const { labels, datasets } = wealthData.balance_sheet.trend_chart;
      return labels.map((label, i) => ({
        month: label,
        assets: datasets[0]?.data[i] || 0,
        liabilities: datasets[1]?.data[i] || 0,
        netWorth: datasets[2]?.data[i] || 0,
      }));
    }
    // Demo data
    return [
      { month: 'Jan', assets: 2800000, liabilities: 450000, netWorth: 2350000 },
      { month: 'Feb', assets: 2850000, liabilities: 445000, netWorth: 2405000 },
      { month: 'Mar', assets: 2920000, liabilities: 440000, netWorth: 2480000 },
      { month: 'Apr', assets: 2880000, liabilities: 435000, netWorth: 2445000 },
      { month: 'May', assets: 3000000, liabilities: 430000, netWorth: 2570000 },
      { month: 'Jun', assets: 3100000, liabilities: 425000, netWorth: 2675000 },
      { month: 'Jul', assets: 3050000, liabilities: 420000, netWorth: 2630000 },
      { month: 'Aug', assets: 3150000, liabilities: 415000, netWorth: 2735000 },
      { month: 'Sep', assets: 3250000, liabilities: 410000, netWorth: 2840000 },
      { month: 'Oct', assets: 3300000, liabilities: 405000, netWorth: 2895000 },
      { month: 'Nov', assets: 3400000, liabilities: 400000, netWorth: 3000000 },
      { month: 'Dec', assets: 3500000, liabilities: 395000, netWorth: 3105000 },
    ];
  }, [wealthData]);

  const assetAllocationData = React.useMemo(() => {
    if (wealthData?.balance_sheet?.asset_allocation?.labels) {
      const { labels, data } = wealthData.balance_sheet.asset_allocation;
      return labels.map((label, i) => ({
        name: label,
        value: data[i] || 0,
      }));
    }
    // Demo data
    return [
      { name: 'Investments', value: 1800000 },
      { name: 'Real Estate', value: 800000 },
      { name: 'Cash', value: 400000 },
      { name: 'Retirement', value: 350000 },
      { name: 'Other', value: 150000 },
    ];
  }, [wealthData]);

  const ratiosData = React.useMemo(() => {
    if (wealthData?.balance_sheet?.ratios_chart?.labels) {
      const { labels, datasets } = wealthData.balance_sheet.ratios_chart;
      return labels.map((label, i) => ({
        month: label,
        debtToAsset: datasets[0]?.data[i] || 0,
        liquidity: datasets[1]?.data[i] || 0,
      }));
    }
    // Demo data
    return [
      { month: 'Jan', debtToAsset: 0.16, liquidity: 2.8 },
      { month: 'Feb', debtToAsset: 0.156, liquidity: 2.9 },
      { month: 'Mar', debtToAsset: 0.151, liquidity: 3.0 },
      { month: 'Apr', debtToAsset: 0.151, liquidity: 2.9 },
      { month: 'May', debtToAsset: 0.143, liquidity: 3.1 },
      { month: 'Jun', debtToAsset: 0.137, liquidity: 3.2 },
    ];
  }, [wealthData]);

  const cashFlowData = React.useMemo(() => {
    if (wealthData?.cash_flow?.combined_chart?.labels) {
      const { labels, datasets } = wealthData.cash_flow.combined_chart;
      return labels.map((label, i) => ({
        month: label,
        income: datasets[0]?.data[i] || 0,
        expense: datasets[1]?.data[i] || 0,
        investment: datasets[2]?.data[i] || 0,
        net: (datasets[0]?.data[i] || 0) - (datasets[1]?.data[i] || 0) - (datasets[2]?.data[i] || 0),
      }));
    }
    // Demo data
    return [
      { month: 'Jan', income: 32000, expense: 18000, investment: 8000, net: 6000 },
      { month: 'Feb', income: 28000, expense: 19000, investment: 5000, net: 4000 },
      { month: 'Mar', income: 35000, expense: 17000, investment: 10000, net: 8000 },
      { month: 'Apr', income: 30000, expense: 20000, investment: 6000, net: 4000 },
      { month: 'May', income: 33000, expense: 18500, investment: 8500, net: 6000 },
      { month: 'Jun', income: 38000, expense: 21000, investment: 10000, net: 7000 },
      { month: 'Jul', income: 31000, expense: 19000, investment: 7000, net: 5000 },
      { month: 'Aug', income: 34000, expense: 20000, investment: 8000, net: 6000 },
      { month: 'Sep', income: 36000, expense: 18000, investment: 10000, net: 8000 },
      { month: 'Oct', income: 32000, expense: 19500, investment: 7500, net: 5000 },
      { month: 'Nov', income: 40000, expense: 22000, investment: 10000, net: 8000 },
      { month: 'Dec', income: 45000, expense: 25000, investment: 12000, net: 8000 },
    ];
  }, [wealthData]);

  const expenseBreakdownData = React.useMemo(() => {
    if (wealthData?.cash_flow?.expense_breakdown?.labels) {
      const { labels, data } = wealthData.cash_flow.expense_breakdown;
      return labels.map((label, i) => ({
        name: label,
        value: data[i] || 0,
      }));
    }
    // Demo data
    return [
      { name: 'Housing', value: 72000 },
      { name: 'Food & Dining', value: 36000 },
      { name: 'Transportation', value: 24000 },
      { name: 'Healthcare', value: 18000 },
      { name: 'Entertainment', value: 15000 },
      { name: 'Other', value: 35000 },
    ];
  }, [wealthData]);

  // Extract KPI values
  const summary = wealthData?.summary;
  const bsKpis = wealthData?.balance_sheet?.kpis;
  const cfKpis = wealthData?.cash_flow?.kpis;

  const tabs = [
    { id: 'networth' as TabType, label: 'Net Worth & Health', icon: Wallet },
    { id: 'cashflow' as TabType, label: 'Cash Flow', icon: TrendingUp },
    { id: 'expenses' as TabType, label: 'Expenses', icon: Receipt },
  ];

  if (isLoading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600"></div>
          <p className="text-sm font-medium text-gray-500">Loading wealth data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-[60vh] items-center justify-center p-8">
        <div className="max-w-md rounded-xl border border-red-200 bg-red-50 p-6 text-center">
          <AlertCircle className="mx-auto h-12 w-12 text-red-500" />
          <h3 className="mt-4 text-lg font-semibold text-red-800">Failed to load wealth data</h3>
          <p className="mt-2 text-sm text-red-600">{error.message}</p>
          <button
            onClick={() => refetch()}
            className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">Overview</p>
          <h1 className="text-3xl font-bold text-gray-900">Wealth Dashboard</h1>
          <p className="text-sm text-gray-500">Comprehensive view of your financial health</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw size={16} className={isFetching ? 'animate-spin' : ''} />
            Refresh
          </button>
          <button className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
            <Download size={16} />
            Export Report
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      {summary?.period_label && summary.period_label !== 'YTD' && (
        <div className="mb-2 flex items-center gap-2 text-sm text-amber-600">
          <AlertCircle size={14} />
          <span>Showing <strong>{summary.period_label}</strong> data (no current year data available)</span>
        </div>
      )}
      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard
          label={`${summary?.period_label || 'YTD'} Income`}
          value={summary?.ytd_income || '$384,000'}
          yoy={summary?.ytd_income_yoy || '+12.5%'}
          icon={TrendingUp}
          iconBgColor="bg-emerald-100"
          iconColor="text-emerald-600"
        />
        <KPICard
          label={`${summary?.period_label || 'YTD'} Expenses`}
          value={summary?.ytd_expense || '$218,500'}
          yoy={summary?.ytd_expense_yoy || '+8.2%'}
          icon={TrendingDown}
          iconBgColor="bg-red-100"
          iconColor="text-red-600"
        />
        <KPICard
          label={`${summary?.period_label || 'YTD'} Investments`}
          value={summary?.ytd_investment || '$92,000'}
          yoy={summary?.ytd_investment_yoy || '+15.3%'}
          icon={PiggyBank}
          iconBgColor="bg-blue-100"
          iconColor="text-blue-600"
        />
        <KPICard
          label={`${summary?.period_label || 'YTD'} Net Cash Flow`}
          value={summary?.ytd_net_cf || '$73,500'}
          yoy={summary?.ytd_net_cf_yoy || '+18.7%'}
          icon={Wallet}
          iconBgColor="bg-amber-100"
          iconColor="text-amber-600"
        />
      </div>

      {/* Tabs */}
      <div className="mb-6 border-b border-gray-200">
        <nav className="-mb-px flex gap-6">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  'flex items-center gap-2 border-b-2 px-1 py-3 text-sm font-medium transition-all',
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                )}
              >
                <Icon size={18} />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'networth' && (
        <div className="space-y-6">
          {/* Net Worth Trend */}
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Net Worth Trend</h3>
                <p className="text-sm text-gray-500">Assets, liabilities, and net worth over time</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-gray-900">{bsKpis?.total_assets || '$3.5M'}</p>
                <p className="text-xs text-gray-500">Total Assets</p>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={320}>
              <AreaChart data={netWorthTrendData}>
                <defs>
                  <linearGradient id="netWorthGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={COLORS.success} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={COLORS.success} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 12 }} />
                <YAxis tick={{ fill: '#64748b', fontSize: 12 }} tickFormatter={(v) => `$${(v / 1000000).toFixed(1)}M`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc' }}
                  formatter={(value: number) => [`$${value.toLocaleString()}`, '']}
                />
                <Legend />
                <Area type="monotone" dataKey="assets" name="Total Assets" stroke={COLORS.primary} fill={`${COLORS.primary}20`} strokeWidth={2} />
                <Area type="monotone" dataKey="liabilities" name="Liabilities" stroke={COLORS.danger} fill={`${COLORS.danger}20`} strokeWidth={2} />
                <Area type="monotone" dataKey="netWorth" name="Net Worth" stroke={COLORS.success} fill="url(#netWorthGradient)" strokeWidth={3} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            {/* Asset Allocation */}
            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
              <h3 className="mb-4 text-lg font-semibold text-gray-900">Asset Allocation</h3>
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={assetAllocationData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}
                  >
                    {assetAllocationData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => [`$${value.toLocaleString()}`, '']} />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Financial Health Ratios */}
            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Financial Health Ratios</h3>
                  <p className="text-sm text-gray-500">Debt-to-Asset and Liquidity trends</p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-emerald-600">{bsKpis?.liability_to_asset || '11.3%'}</p>
                  <p className="text-xs text-gray-500">Debt-to-Asset</p>
                </div>
              </div>
              <ResponsiveContainer width="100%" height={240}>
                <ComposedChart data={ratiosData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 12 }} />
                  <YAxis yAxisId="left" tick={{ fill: '#64748b', fontSize: 12 }} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
                  <YAxis yAxisId="right" orientation="right" tick={{ fill: '#64748b', fontSize: 12 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc' }}
                  />
                  <Legend />
                  <Bar yAxisId="left" dataKey="debtToAsset" name="Debt-to-Asset" fill={COLORS.primary} radius={[4, 4, 0, 0]} />
                  <Line yAxisId="right" type="monotone" dataKey="liquidity" name="Liquidity Ratio" stroke={COLORS.success} strokeWidth={2} dot />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'cashflow' && (
        <div className="space-y-6">
          {/* Income vs Expenses */}
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Income vs Expenses</h3>
                <p className="text-sm text-gray-500">Monthly income, expenses, and investments</p>
              </div>
              <div className="text-right">
                <p className="text-lg font-bold text-emerald-600">{cfKpis?.savings_rate || '45.2%'}</p>
                <p className="text-xs text-gray-500">Savings Rate</p>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={320}>
              <ComposedChart data={cashFlowData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 12 }} />
                <YAxis tick={{ fill: '#64748b', fontSize: 12 }} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc' }}
                  formatter={(value: number) => [`$${value.toLocaleString()}`, '']}
                />
                <Legend />
                <Bar dataKey="expense" name="Expenses" stackId="a" fill={COLORS.danger} radius={[0, 0, 0, 0]} />
                <Bar dataKey="investment" name="Investments" stackId="a" fill={COLORS.primary} radius={[0, 0, 0, 0]} />
                <Bar dataKey="net" name="Net Savings" stackId="a" fill={COLORS.success} radius={[4, 4, 0, 0]} />
                <Line type="monotone" dataKey="income" name="Income" stroke={COLORS.gold} strokeWidth={3} dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* Net Cash Flow Trend */}
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <h3 className="mb-4 text-lg font-semibold text-gray-900">Net Cash Flow Trend</h3>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={cashFlowData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 12 }} />
                <YAxis tick={{ fill: '#64748b', fontSize: 12 }} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc' }}
                  formatter={(value: number) => [`$${value.toLocaleString()}`, '']}
                />
                <Bar
                  dataKey="net"
                  name="Net Cash Flow"
                  fill={COLORS.success}
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {activeTab === 'expenses' && (
        <div className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Expense Breakdown Pie */}
            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
              <h3 className="mb-4 text-lg font-semibold text-gray-900">Expense Breakdown</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={expenseBreakdownData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}
                  >
                    {expenseBreakdownData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => [`$${value.toLocaleString()}`, '']} />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Expense Efficiency */}
            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
              <h3 className="mb-4 text-lg font-semibold text-gray-900">Expense Efficiency</h3>
              <div className="space-y-6 pt-4">
                <div>
                  <div className="mb-2 flex justify-between text-sm">
                    <span className="font-medium text-gray-700">Essential Expenses</span>
                    <span className="font-bold text-blue-600">62%</span>
                  </div>
                  <div className="h-4 overflow-hidden rounded-full bg-gray-100">
                    <div className="h-full rounded-full bg-blue-500" style={{ width: '62%' }}></div>
                  </div>
                  <p className="mt-1 text-xs text-gray-500">Housing, utilities, healthcare, groceries</p>
                </div>
                <div>
                  <div className="mb-2 flex justify-between text-sm">
                    <span className="font-medium text-gray-700">Lifestyle Expenses</span>
                    <span className="font-bold text-amber-600">23%</span>
                  </div>
                  <div className="h-4 overflow-hidden rounded-full bg-gray-100">
                    <div className="h-full rounded-full bg-amber-500" style={{ width: '23%' }}></div>
                  </div>
                  <p className="mt-1 text-xs text-gray-500">Dining out, subscriptions, shopping</p>
                </div>
                <div>
                  <div className="mb-2 flex justify-between text-sm">
                    <span className="font-medium text-gray-700">Discretionary</span>
                    <span className="font-bold text-purple-600">15%</span>
                  </div>
                  <div className="h-4 overflow-hidden rounded-full bg-gray-100">
                    <div className="h-full rounded-full bg-purple-500" style={{ width: '15%' }}></div>
                  </div>
                  <p className="mt-1 text-xs text-gray-500">Entertainment, travel, hobbies</p>
                </div>
              </div>
            </div>
          </div>

          {/* Monthly Expense Trend */}
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <h3 className="mb-4 text-lg font-semibold text-gray-900">Monthly Expense Trend</h3>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={cashFlowData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 12 }} />
                <YAxis tick={{ fill: '#64748b', fontSize: 12 }} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc' }}
                  formatter={(value: number) => [`$${value.toLocaleString()}`, '']}
                />
                <Legend />
                <Line type="monotone" dataKey="expense" name="Total Expenses" stroke={COLORS.danger} strokeWidth={2} dot />
                <Line type="monotone" dataKey="investment" name="Investments" stroke={COLORS.primary} strokeWidth={2} dot />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
};

export default Wealth;
