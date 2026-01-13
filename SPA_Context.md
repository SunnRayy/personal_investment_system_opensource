# WealthOS SPA Codebase Context
Generated on Tue Jan 13 11:31:26 CST 2026

## File: package.json
```json
{
    "name": "personal-investment-system-spa",
    "private": true,
    "version": "0.1.0",
    "type": "module",
    "scripts": {
        "dev": "vite",
        "build": "vite build",
        "preview": "vite preview"
    },
    "dependencies": {
        "@google/genai": "^1.35.0",
        "clsx": "^2.1.1",
        "lucide-react": "^0.395.0",
        "react": "^18.3.1",
        "react-dom": "^18.3.1",
        "react-router-dom": "^6.23.1",
        "recharts": "^3.6.0",
        "tailwind-merge": "^2.3.0"
    },
    "devDependencies": {
        "@types/node": "^20.14.2",
        "@types/react": "^18.3.3",
        "@types/react-dom": "^18.3.0",
        "@vitejs/plugin-react": "^4.3.1",
        "typescript": "^5.4.5",
        "vite": "^5.3.1"
    }
}
```

## File: vite.config.ts
```ts
import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, '.', '');
    return {
      server: {
        port: 3000,
        host: '0.0.0.0',
      },
      plugins: [react()],
      define: {
        'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY),
        'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY)
      },
      resolve: {
        alias: {
          '@': path.resolve(__dirname, './src'),
        }
      }
    };
});
```

## File: index.html
```html
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>WealthOS - Personal Investment System</title>
    <!-- Google Fonts: Inter -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"
        rel="stylesheet">
    <!-- Google Fonts: Material Symbols (for backwards compatibility if needed, though replaced by Lucide) -->
    <link rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
</head>

<body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
</body>

</html>```

## File: src/App.tsx
```tsx
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import DataWorkbench from './pages/DataWorkbench';
import Portfolio from './pages/Portfolio';

const App: React.FC = () => {
    return (
        <BrowserRouter>
            <Routes>
                <Route element={<Layout />}>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/workbench" element={<DataWorkbench />} />
                    <Route path="/portfolio" element={<Portfolio />} />
                    {/* Add more routes as needed */}
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Route>
            </Routes>
        </BrowserRouter>
    );
};

export default App;
```

## File: src/components/Layout.tsx
```tsx
import React from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { LayoutDashboard, Wallet, Database, Settings, LogOut, TrendingUp, Sun } from 'lucide-react';
import clsx from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: (string | undefined | null | false)[]) {
    return twMerge(clsx(inputs));
}

const Layout: React.FC = () => {
    const location = useLocation();

    const navItems = [
        { label: 'Dashboard', icon: LayoutDashboard, path: '/' },
        { label: 'Data Workbench', icon: Database, path: '/workbench' },
        { label: 'Portfolio', icon: Wallet, path: '/portfolio' },
    ];

    return (
        <div className="flex h-screen bg-slate-50 font-sans text-slate-900">
            {/* Sidebar */}
            <aside className="fixed left-0 top-0 z-50 flex h-full w-64 flex-col border-r border-slate-200 bg-white shadow-sm transition-transform duration-300">
                <div className="flex items-center gap-3 p-6">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-md shadow-indigo-200">
                        <TrendingUp size={24} strokeWidth={2.5} />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold tracking-tight text-slate-900">WealthOS</h1>
                        <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Personal Edition</p>
                    </div>
                </div>

                <nav className="flex-1 space-y-8 overflow-y-auto px-4 py-4">
                    <div>
                        <h3 className="mb-3 px-3 text-xs font-bold uppercase tracking-widest text-slate-400">
                            Main
                        </h3>
                        <ul className="space-y-1">
                            {navItems.map((item) => {
                                const Icon = item.icon;
                                const isActive = location.pathname === item.path;
                                return (
                                    <li key={item.path}>
                                        <NavLink
                                            to={item.path}
                                            className={({ isActive }) => cn(
                                                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
                                                isActive
                                                    ? "bg-indigo-50 text-indigo-600 shadow-sm ring-1 ring-indigo-200"
                                                    : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"
                                            )}
                                        >
                                            <Icon size={20} strokeWidth={isActive ? 2.5 : 2} />
                                            {item.label}
                                        </NavLink>
                                    </li>
                                );
                            })}
                        </ul>
                    </div>

                    <div>
                        <h3 className="mb-3 px-3 text-xs font-bold uppercase tracking-widest text-slate-400">
                            System
                        </h3>
                        <ul className="space-y-1">
                            <li>
                                <button className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-500 transition-all duration-200 hover:bg-slate-50 hover:text-slate-900">
                                    <Settings size={20} />
                                    Settings
                                </button>
                            </li>
                        </ul>
                    </div>
                </nav>

                <div className="border-t border-slate-100 p-4">
                    <div className="flex items-center gap-3 rounded-xl bg-slate-50 p-3 border border-slate-100">
                        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white text-yellow-500 shadow-sm ring-1 ring-slate-200">
                            <Sun size={18} fill="currentColor" className="text-yellow-500" />
                        </div>
                        <div className="flex-1 overflow-hidden">
                            <p className="truncate text-xs font-bold text-slate-900">Ray</p>
                            <p className="truncate text-[10px] font-medium text-slate-500">Pro Plan</p>
                        </div>
                        <button className="text-slate-400 hover:text-slate-600">
                            <LogOut size={16} />
                        </button>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="ml-64 min-h-screen w-full bg-slate-50">
                <Outlet />
            </main>
        </div>
    );
};

export default Layout;
```

## File: src/index.css
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
    body {
        @apply font-sans antialiased bg-slate-50 text-slate-900;
    }
}```

## File: src/lib/gemini.ts
```ts

import { GoogleGenAI, Type } from "@google/genai";

const ai = new GoogleGenAI({ apiKey: process.env.API_KEY || '' });

export async function getMagicMapping(headers: string[], targetFields: string[]) {
    const response = await ai.models.generateContent({
        model: "gemini-3-flash-preview",
        contents: `Map these CSV headers [${headers.join(', ')}] to these target fields: [${targetFields.join(', ')}]. Return a JSON object where keys are target fields and values are the exact matching CSV header.`,
        config: {
            responseMimeType: "application/json",
            responseSchema: {
                type: Type.OBJECT,
                properties: targetFields.reduce((acc: any, field) => {
                    acc[field] = { type: Type.STRING };
                    return acc;
                }, {}),
            }
        },
    });
    return JSON.parse(response.text || '{}');
}

export async function getSmartFix(errorRow: any) {
    const response = await ai.models.generateContent({
        model: "gemini-3-flash-preview",
        contents: `Fix this erroneous transaction data. Error: "${errorRow.errorMsg}". Data: ${JSON.stringify(errorRow)}. Return a JSON object with corrected 'date', 'category', and 'amount' fields. Ensure date is YYYY-MM-DD.`,
        config: {
            responseMimeType: "application/json",
            responseSchema: {
                type: Type.OBJECT,
                properties: {
                    date: { type: Type.STRING },
                    category: { type: Type.STRING },
                    amount: { type: Type.NUMBER },
                    description: { type: Type.STRING }
                }
            }
        },
    });
    return JSON.parse(response.text || '{}');
}
```

## File: src/main.tsx
```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <App />
    </React.StrictMode>,
);
```

## File: src/pages/Dashboard.tsx
```tsx
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
```

## File: src/pages/DataWorkbench.tsx
```tsx
import React, { useState } from 'react';
import {
    History,
    TrendingUp,
    Briefcase,
    Landmark,
    HelpCircle,
    CloudUpload,
    FileText,
    ArrowRight,
    Check,
    Wand2,
    Calendar,
    File,
    Tag,
    BarChart3,
    Search,
    Filter,
    Info,
    CheckCircle,
    AlertCircle,
    Loader2
} from 'lucide-react';
import { WorkflowStep, Transaction } from '../types';
import { getMagicMapping, getSmartFix } from '../lib/gemini';
import clsx from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: (string | undefined | null | false)[]) {
    return twMerge(clsx(inputs));
}

// --- Icons Helper ---
// Since we used Material Symbols in templates, we map them to Lucide here for consistency
// Or just use Lucide directly in the components.

// --- Main Component ---
const DataWorkbench: React.FC = () => {
    const [currentStep, setCurrentStep] = useState<WorkflowStep>(WorkflowStep.DASHBOARD);

    const renderContent = () => {
        switch (currentStep) {
            case WorkflowStep.DASHBOARD:
                return <WorkbenchDashboard onNext={() => setCurrentStep(WorkflowStep.UPLOAD)} />;
            case WorkflowStep.UPLOAD:
                return <UploadStep onNext={() => setCurrentStep(WorkflowStep.MAP)} onBack={() => setCurrentStep(WorkflowStep.DASHBOARD)} />;
            case WorkflowStep.MAP:
                return <MapStep onNext={() => setCurrentStep(WorkflowStep.REVIEW)} onBack={() => setCurrentStep(WorkflowStep.UPLOAD)} />;
            case WorkflowStep.REVIEW:
                return <ReviewStep onNext={() => setCurrentStep(WorkflowStep.COMPLETE)} onBack={() => setCurrentStep(WorkflowStep.MAP)} />;
            case WorkflowStep.COMPLETE:
                return <CompleteStep onFinish={() => setCurrentStep(WorkflowStep.DASHBOARD)} />;
            default:
                return <WorkbenchDashboard onNext={() => setCurrentStep(WorkflowStep.UPLOAD)} />;
        }
    };

    return (
        <div className="p-6 md:p-8 min-h-screen">
            {renderContent()}
        </div>
    );
};

// --- Sub Components ---

const WorkbenchDashboard: React.FC<{ onNext: () => void }> = ({ onNext }) => {
    return (
        <div className="max-w-5xl mx-auto py-12">
            <div className="text-center mb-12">
                <h1 className="text-4xl font-extrabold text-slate-900 mb-2 tracking-tight">Data Workbench</h1>
                <p className="text-lg text-slate-500">Choose data to import into your portfolio</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <WorkbenchCard
                    icon={History}
                    title="Resume pending import"
                    description="Continue your last import session exactly where you left off."
                    pending
                    onClick={onNext}
                />
                <WorkbenchCard
                    icon={TrendingUp}
                    title="Import Transactions"
                    description="Upload trade logs via CSV or connect directly to broker APIs."
                    onClick={onNext}
                />
                <WorkbenchCard
                    icon={Briefcase}
                    title="Import Holdings"
                    description="Update current portfolio positions, real estate, and private equity."
                    onClick={onNext}
                />
                <WorkbenchCard
                    icon={Landmark}
                    title="Import Accounts"
                    description="Bulk configure multiple banking and custodial accounts."
                    onClick={onNext}
                />
            </div>

            <div className="mt-16 text-center">
                <button className="inline-flex items-center gap-2 text-sm font-medium text-slate-400 hover:text-blue-600 transition-colors">
                    <HelpCircle size={18} />
                    Need help with data formats? View Documentation
                </button>
            </div>
        </div>
    );
};

const WorkbenchCard: React.FC<{
    icon: React.ElementType;
    title: string;
    description: string;
    pending?: boolean;
    onClick: () => void;
}> = ({ icon: Icon, title, description, pending, onClick }) => (
    <button
        onClick={onClick}
        className={cn(
            "group relative flex items-start p-6 text-left bg-white border-2 rounded-2xl transition-all duration-300 hover:shadow-xl hover:shadow-slate-200/60 w-full",
            pending ? 'border-amber-400 bg-amber-50/20' : 'border-slate-100 hover:border-blue-500/50'
        )}
    >
        {pending && (
            <span className="absolute top-0 right-0 -mt-2 mr-6 px-3 py-0.5 bg-amber-600 text-[10px] font-bold text-white uppercase tracking-wider rounded-full shadow-sm ring-4 ring-white">
                Pending
            </span>
        )}
        <div className={cn(
            "flex-shrink-0 w-12 h-12 flex items-center justify-center rounded-xl mr-5 transition-transform group-hover:scale-110 group-hover:-rotate-3",
            pending ? 'bg-white text-amber-600 shadow-sm border border-amber-100' : 'bg-blue-50 text-blue-600 group-hover:bg-blue-600 group-hover:text-white'
        )}>
            <Icon size={24} />
        </div>
        <div>
            <h3 className={cn("text-lg font-bold mb-1 transition-colors", pending ? 'text-amber-900 group-hover:text-amber-700' : 'text-slate-900 group-hover:text-blue-600')}>{title}</h3>
            <p className="text-sm text-slate-500 leading-relaxed">{description}</p>
        </div>
    </button>
);

const UploadStep: React.FC<{ onNext: () => void; onBack: () => void }> = ({ onNext, onBack }) => {
    return (
        <div className="max-w-4xl mx-auto space-y-10">
            <div className="text-center">
                <h1 className="text-3xl font-bold text-slate-900 mb-2">Upload Workflow</h1>
                <p className="text-slate-500">Step 2 of 5: Import your CSV data</p>
            </div>

            <WorkflowStepper step={2} />

            <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
                <div className="bg-slate-50/50 border-b border-slate-100 p-1 flex justify-center">
                    <div className="flex bg-slate-200 rounded-lg p-1 w-full max-w-sm my-4">
                        <button className="flex-1 px-4 py-2 bg-white text-blue-600 font-bold rounded shadow-sm text-sm">Upload CSV</button>
                        <button className="flex-1 px-4 py-2 text-slate-500 font-medium text-sm">Copy & Paste</button>
                    </div>
                </div>

                <div className="p-10 space-y-8">
                    <div className="grid grid-cols-2 gap-8">
                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-slate-700">Column Separator</label>
                            <select className="w-full h-11 bg-slate-50 border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm px-3">
                                <option>Comma (,)</option>
                                <option>Semicolon (;)</option>
                                <option>Tab</option>
                            </select>
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-slate-700">Target Account</label>
                            <select className="w-full h-11 bg-slate-50 border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm px-3">
                                <option>Multi-account import</option>
                                <option>Savings ...1234</option>
                                <option>Checking ...5678</option>
                            </select>
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-slate-700">Upload File</label>
                        <div className="border-2 border-dashed border-blue-200 bg-blue-50/30 rounded-2xl p-16 flex flex-col items-center justify-center text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50/50 transition-all group">
                            <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center text-blue-600 shadow-sm mb-4 transition-transform group-hover:scale-110">
                                <CloudUpload size={32} />
                            </div>
                            <h3 className="text-lg font-bold text-slate-900 mb-1">Click to upload or drag and drop</h3>
                            <p className="text-sm text-slate-500 mb-4">SVG, PNG, JPG or GIF (max. 800x400px)</p>
                            <div className="px-3 py-1 bg-white border border-slate-200 rounded text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                                Supported formats: .csv, .xls, .xlsx
                            </div>
                        </div>
                        <div className="flex justify-between items-center px-1 text-xs text-slate-400">
                            <button className="flex items-center gap-1 hover:text-blue-600">
                                <FileText size={14} /> Download sample template
                            </button>
                            <span>Max size: 50MB</span>
                        </div>
                    </div>

                    <div className="pt-6 border-t border-slate-100 flex items-center justify-end gap-4">
                        <button onClick={onBack} className="px-6 py-2.5 text-sm font-semibold text-slate-400 hover:text-slate-600 transition-colors">Cancel</button>
                        <button
                            onClick={onNext}
                            className="px-10 py-2.5 bg-blue-600 text-white rounded-xl font-bold shadow-lg shadow-blue-500/25 hover:bg-blue-700 transition-all flex items-center gap-2 group"
                        >
                            Continue to Mapping
                            <ArrowRight size={20} className="transition-transform group-hover:translate-x-1" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

const MapStep: React.FC<{ onNext: () => void; onBack: () => void }> = ({ onNext, onBack }) => {
    const [isMapping, setIsMapping] = useState(false);
    const [mappings, setMappings] = useState<Record<string, string>>({
        'Date Field': 'Date (Column A)',
        'Description': 'Description (Column D)',
        'Amount': 'Amount (Column E)',
        'Ticker / Symbol': 'Symbol (Column C)',
        'Category': '-- Select Column --'
    });

    const handleMagicMap = async () => {
        setIsMapping(true);
        try {
            const headers = ['Date', 'Action', 'Symbol', 'Description', 'Amount'];
            const targets = ['Date Field', 'Description', 'Amount', 'Ticker / Symbol', 'Category'];
            const result = await getMagicMapping(headers, targets);

            // Simulate mapping delay for UX if AI is too specific/fast or mocks
            setTimeout(() => {
                setMappings(prev => ({ ...prev, ...result }));
                setIsMapping(false);
            }, 1500);
        } catch (error) {
            console.error(error);
            setIsMapping(false);
        }
    };

    return (
        <div className="max-w-[1400px] mx-auto space-y-8 relative">
            {isMapping && (
                <div className="fixed inset-0 bg-white/60 backdrop-blur-[2px] z-50 flex flex-col items-center justify-center">
                    <div className="w-64 h-2 bg-slate-100 rounded-full overflow-hidden mb-4">
                        <div className="h-full bg-blue-600 animate-[shimmer_1.5s_infinite] w-1/2"></div>
                    </div>
                    <p className="text-sm font-bold text-slate-600 animate-pulse">Gemini AI is scanning your data structure...</p>
                </div>
            )}

            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div className="space-y-1">
                    <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Map CSV Columns</h1>
                    <p className="text-slate-500">Match your file columns to WealthOS's data structure.</p>
                </div>
                <div className="flex items-center gap-2 bg-green-50 border border-green-100 text-green-700 px-4 py-2 rounded-lg shadow-sm">
                    <Wand2 size={18} />
                    <span className="text-sm font-bold tracking-tight">AI-ready for auto-mapping</span>
                </div>
            </div>

            <WorkflowStepper step={3} />

            <div className="grid grid-cols-12 gap-8 items-start">
                <div className="col-span-7 space-y-4">
                    <div className="flex items-center justify-between">
                        <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                            <FileText className="text-slate-400" size={20} />
                            CSV Preview
                        </h2>
                        <div className="px-3 py-1 bg-slate-100 border border-slate-200 rounded text-[11px] font-mono text-slate-500">
                            fidelity_export_2023.csv
                        </div>
                    </div>
                    <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead className="bg-slate-50 text-slate-400 font-bold uppercase text-[10px] tracking-widest border-b border-slate-100">
                                    <tr>
                                        {['Date', 'Action', 'Symbol', 'Description', 'Amount'].map(h => (
                                            <th key={h} className="px-4 py-3">{h}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100 text-[13px] text-slate-600">
                                    <tr className="hover:bg-slate-50/50">
                                        <td className="px-4 py-3 font-mono">2023-10-24</td>
                                        <td className="px-4 py-3">BUY</td>
                                        <td className="px-4 py-3 font-bold text-blue-600">AAPL</td>
                                        <td className="px-4 py-3 truncate max-w-[150px]">APPLE INC COM</td>
                                        <td className="px-4 py-3">-173.50</td>
                                    </tr>
                                    <tr className="hover:bg-slate-50/50">
                                        <td className="px-4 py-3 font-mono">2023-10-24</td>
                                        <td className="px-4 py-3">DIVIDEND</td>
                                        <td className="px-4 py-3 font-bold text-blue-600">VTI</td>
                                        <td className="px-4 py-3 truncate max-w-[150px]">VANGUARD TOTAL STK</td>
                                        <td className="px-4 py-3 text-emerald-600">+45.20</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <div className="col-span-5 space-y-4">
                    <div className="flex items-center justify-between">
                        <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                            <Filter className="text-slate-400" size={20} />
                            Configuration
                        </h2>
                        <button
                            onClick={handleMagicMap}
                            disabled={isMapping}
                            className="flex items-center gap-2 px-4 py-1.5 bg-indigo-600 text-white text-[11px] font-bold uppercase tracking-widest rounded-full hover:bg-indigo-700 transition-all shadow-md hover:shadow-indigo-200 disabled:opacity-50"
                        >
                            <Wand2 size={14} />
                            Magic Map with AI
                        </button>
                    </div>

                    <div className="bg-white border border-slate-200 rounded-2xl shadow-lg p-8 space-y-6">
                        {Object.entries(mappings).map(([field, value]) => (
                            <MappingField
                                key={field}
                                label={field}
                                icon={getIconForField(field)}
                                value={value}
                                onChange={(val) => setMappings(p => ({ ...p, [field]: val }))}
                                required={['Date Field', 'Description', 'Amount'].includes(field)}
                            />
                        ))}

                        <div className="pt-6 border-t border-slate-100 flex items-center justify-between">
                            <button onClick={onBack} className="px-6 py-2.5 text-sm font-bold text-slate-400 hover:text-slate-600">Back</button>
                            <button
                                onClick={onNext}
                                className="px-8 py-2.5 bg-blue-600 text-white font-bold rounded-xl shadow-lg hover:bg-blue-700 transition-all flex items-center gap-2 group"
                            >
                                Next Step
                                <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

const ReviewStep: React.FC<{ onNext: () => void; onBack: () => void }> = ({ onNext, onBack }) => {
    const [isFixing, setIsFixing] = useState(false);
    const [data, setData] = useState<Transaction[]>([
        { id: '1', date: '2023-10-24', description: 'Dividend Payment - AAPL', category: 'Dividend', amount: 145.00, ticker: 'AAPL', account: 'Brokerage ...8842', status: 'ready' },
        { id: '2', date: '2023-13-45', description: 'Transfer to Savings', category: 'Transfer', amount: 5000.00, account: 'Chase Chk ...1234', status: 'error', errorMsg: 'Invalid date format' },
        { id: '3', date: '2023-10-23', description: 'Netflix Subscription', category: 'Entertainment', amount: -19.99, ticker: 'NFLX', account: 'Chase CC ...5501', status: 'ready' },
        { id: '4', date: '2023-10-22', description: 'Unknown Purchase #9921', category: 'Uncategorized', amount: -125.50, account: 'Chase Chk ...1234', status: 'error', errorMsg: 'Please select a category' },
        { id: '5', date: '2023-10-22', description: 'Whole Foods Market', category: 'Groceries', amount: -86.42, account: 'Chase CC ...5501', status: 'ready' },
        { id: '6', date: '2023-10-21', description: 'Shell Station', category: 'Transport', amount: -45.00, account: 'Chase CC ...5501', status: 'ready' },
        { id: '7', date: '2023-10-20', description: 'Salary Deposit', category: 'Income', amount: -2400.00, account: 'Chase Chk ...1234', status: 'error', errorMsg: 'Income cannot be negative' },
    ]);

    const errorCount = data.filter(r => r.status === 'error').length;

    const handleMagicFix = async () => {
        setIsFixing(true);
        const newData = [...data];

        for (let i = 0; i < newData.length; i++) {
            if (newData[i].status === 'error') {
                try {
                    const fix = await getSmartFix(newData[i]);
                    newData[i] = {
                        ...newData[i],
                        ...fix,
                        status: 'ready',
                        errorMsg: undefined,
                        id: newData[i].id + '_fixed' // Track it's been fixed
                    };
                } catch (e) {
                    console.error("Failed to fix row", newData[i].id);
                }
            }
        }

        setData(newData);
        setIsFixing(false);
    };

    return (
        <div className="max-w-[1600px] mx-auto space-y-8 h-full flex flex-col relative">
            <div className="flex items-end justify-between">
                <div className="space-y-1">
                    <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-4">
                        Review & Fix Errors
                        <span className={`px-3 py-0.5 rounded-full text-xs font-bold border transition-colors ${errorCount > 0 ? 'bg-red-100 text-red-700 border-red-200' : 'bg-emerald-100 text-emerald-700 border-emerald-200'}`}>
                            {errorCount > 0 ? `${errorCount} Errors Remaining` : 'All Errors Fixed!'}
                        </span>
                    </h1>
                    <p className="text-slate-500">Please review the parsed data. AI has identified {errorCount} issues.</p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={handleMagicFix}
                        disabled={isFixing || errorCount === 0}
                        className="flex items-center gap-2 px-6 py-2.5 bg-indigo-600 text-white text-sm font-bold rounded-xl hover:bg-indigo-700 transition-all shadow-lg hover:shadow-indigo-200 disabled:opacity-50 disabled:shadow-none"
                    >
                        {isFixing ? (
                            <Loader2 className="animate-spin" size={18} />
                        ) : (
                            <Wand2 size={18} />
                        )}
                        {isFixing ? 'AI Fixing...' : 'Magic Fix with AI'}
                    </button>
                </div>
            </div>

            <div className="bg-white border border-slate-200 rounded-2xl shadow-xl flex-1 flex flex-col overflow-hidden max-h-[600px]">
                <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-white flex-shrink-0">
                    <div className="flex items-center gap-4">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                            <input
                                type="text"
                                placeholder="Filter transactions..."
                                className="pl-10 pr-4 py-2 text-sm border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 w-72 h-10 border outline-none"
                            />
                        </div>
                        <div className="h-6 w-px bg-slate-200"></div>
                        <button className="flex items-center gap-2 px-3 py-2 text-sm font-bold text-slate-500 hover:bg-slate-50 rounded-lg transition-colors">
                            <Filter size={16} /> All Status
                        </button>
                    </div>
                    <div className="flex items-center gap-2 text-[13px] text-slate-400">
                        <Info className="text-blue-500" size={16} />
                        AI suggestions are marked with <span className="text-indigo-600 font-bold">Sparkles</span>
                    </div>
                </div>

                <div className="flex-1 overflow-auto">
                    <table className="w-full text-left border-collapse min-w-[1200px]">
                        <thead className="sticky top-0 bg-slate-50 z-20 border-b border-slate-200 shadow-sm">
                            <tr className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                                <th className="py-4 px-6 w-12 border-r border-slate-200 text-center"><input type="checkbox" className="rounded border-slate-300" /></th>
                                <th className="py-4 px-6 border-r border-slate-200">Date</th>
                                <th className="py-4 px-6 border-r border-slate-200">Description</th>
                                <th className="py-4 px-6 border-r border-slate-200">Category</th>
                                <th className="py-4 px-6 border-r border-slate-200 text-right">Amount</th>
                                <th className="py-4 px-6">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 text-sm">
                            {data.map((row) => (
                                <tr
                                    key={row.id}
                                    className={`hover:bg-slate-50/50 transition-colors ${row.status === 'error' ? 'bg-red-50/40 border-l-4 border-l-red-500' : row.id.includes('fixed') ? 'bg-indigo-50/20 border-l-4 border-l-indigo-400' : ''}`}
                                >
                                    <td className="py-3 px-6 text-center border-r border-slate-100">
                                        <input type="checkbox" className="rounded border-slate-300" />
                                    </td>
                                    <td className={`py-3 px-6 font-mono border-r border-slate-100 ${row.status === 'error' && row.errorMsg?.includes('date') ? 'text-red-600 font-bold' : row.id.includes('fixed') ? 'text-indigo-600 font-bold' : 'text-slate-500'}`}>
                                        {row.date}
                                        {row.id.includes('fixed') && <Wand2 size={12} className="inline ml-1 text-indigo-400" />}
                                    </td>
                                    <td className="py-3 px-6 font-bold text-slate-900 border-r border-slate-100">{row.description}</td>
                                    <td className="py-3 px-6 border-r border-slate-100">
                                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider ${row.status === 'error' && row.errorMsg?.includes('category')
                                                ? 'bg-red-100 text-red-600 italic'
                                                : row.id.includes('fixed') ? 'bg-indigo-100 text-indigo-600' : 'bg-blue-50 text-blue-600'
                                            }`}>
                                            {row.category}
                                            {row.id.includes('fixed') && <Wand2 size={12} className="ml-1" />}
                                        </span>
                                    </td>
                                    <td className={`py-3 px-6 font-mono text-right border-r border-slate-100 ${row.status === 'error' && row.amount < 0 && row.category === 'Income'
                                            ? 'text-red-600 font-bold'
                                            : row.amount > 0 ? 'text-emerald-600 font-bold' : 'text-slate-900'
                                        }`}>
                                        {row.amount < 0 ? '-' : '+'}${Math.abs(row.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                    </td>
                                    <td className="py-3 px-6">
                                        {row.status === 'ready' ? (
                                            <span className="flex items-center gap-1.5 text-emerald-600 font-bold text-xs uppercase tracking-widest">
                                                <CheckCircle size={16} fill="currentColor" className="text-emerald-600" /> Ready
                                            </span>
                                        ) : (
                                            <div className="flex flex-col">
                                                <span className="text-red-600 font-extrabold text-[10px] uppercase tracking-widest flex items-center gap-1">
                                                    <AlertCircle size={10} />
                                                    Error
                                                </span>
                                                <span className="text-[10px] text-red-400 italic">{row.errorMsg}</span>
                                            </div>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                <div className="px-8 py-6 bg-slate-50 border-t border-slate-200 flex items-center justify-between flex-shrink-0">
                    <div className="flex items-center gap-6">
                        <div className="flex items-center gap-2.5">
                            <span className={`w-2.5 h-2.5 rounded-full ${errorCount === 0 ? 'bg-emerald-500' : 'bg-red-500 animate-pulse'}`}></span>
                            <span className="text-sm font-bold text-slate-600">{data.length - errorCount} rows ready</span>
                        </div>
                        {errorCount > 0 && <span className="text-sm font-bold text-red-500">{errorCount} need fixing</span>}
                    </div>

                    <div className="flex items-center gap-4">
                        <button onClick={onBack} className="px-6 py-3 bg-white border border-slate-200 text-slate-600 font-bold rounded-xl">
                            Back
                        </button>
                        <button
                            onClick={onNext}
                            disabled={errorCount > 0}
                            className="px-10 py-3 bg-blue-600 text-white font-bold rounded-xl shadow-xl shadow-blue-500/25 hover:bg-blue-700 disabled:opacity-50 transition-all flex items-center gap-3 group"
                        >
                            Finalize Import
                            <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

const CompleteStep: React.FC<{ onFinish: () => void }> = ({ onFinish }) => {
    return (
        <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-20 h-20 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mb-6">
                <CheckCircle size={40} />
            </div>
            <h1 className="text-3xl font-bold text-slate-900 mb-2">Import Successful!</h1>
            <p className="text-slate-500 mb-8 max-w-md">Your transactions have been successfully imported and categorized. Your portfolio is now up to date.</p>
            <button
                onClick={onFinish}
                className="px-8 py-3 bg-slate-900 text-white font-bold rounded-xl shadow-lg hover:bg-slate-800 transition-all"
            >
                Return to Dashboard
            </button>
        </div>
    );
};

// --- Helpers ---

const WorkflowStepper: React.FC<{ step: number }> = ({ step }) => (
    <div className="flex items-center justify-between px-10 relative mb-12">
        <div className="absolute top-1/2 left-0 w-full h-0.5 bg-slate-200 -translate-y-1/2 z-0"></div>
        {[1, 2, 3, 4, 5].map((s) => (
            <div key={s} className="relative z-10 flex flex-col items-center gap-2">
                <div className={cn(
                    "w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all shadow-sm",
                    s < step ? 'bg-blue-600 text-white' : s === step ? 'bg-blue-600 text-white ring-8 ring-blue-50' : 'bg-white text-slate-400 border-2 border-slate-100'
                )}>
                    {s < step ? <Check size={18} /> : s}
                </div>
                <span className={cn("text-xs font-bold transition-colors", s <= step ? 'text-blue-600' : 'text-slate-400')}>
                    {s === 1 && 'Source'}
                    {s === 2 && 'Upload'}
                    {s === 3 && 'Map'}
                    {s === 4 && 'Review'}
                    {s === 5 && 'Done'}
                </span>
            </div>
        ))}
    </div>
);

const getIconForField = (field: string) => {
    if (field.includes('Date')) return Calendar;
    if (field.includes('Description')) return FileText;
    if (field.includes('Amount')) return Tag; // or DollarSign
    if (field.includes('Ticker')) return BarChart3;
    return Tag;
};

const MappingField: React.FC<{
    label: string;
    icon: React.ElementType;
    value: string;
    onChange: (v: string) => void;
    required?: boolean;
}> = ({ label, icon: Icon, value, onChange, required }) => (
    <div className="p-4 border border-slate-100 rounded-2xl space-y-2 hover:border-blue-500/30 transition-colors">
        <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 text-sm font-bold text-slate-800">
                <Icon size={18} className="text-slate-400" />
                {label} {required && <span className="text-red-500">*</span>}
            </label>
            {value !== '-- Select Column --' && (
                <span className="text-[9px] font-bold text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-100 uppercase tracking-widest">Matched</span>
            )}
        </div>
        <select
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className="w-full h-10 bg-slate-50 border-slate-200 rounded-lg text-sm font-medium text-slate-700 focus:ring-blue-500 outline-none px-2"
        >
            <option>-- Select Column --</option>
            <option>Date (Column A)</option>
            <option>Action (Column B)</option>
            <option>Symbol (Column C)</option>
            <option>Description (Column D)</option>
            <option>Amount (Column E)</option>
        </select>
    </div>
);

export default DataWorkbench;
```

## File: src/pages/Portfolio.tsx
```tsx
import React from 'react';
import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts';

const HEALTH_CHART_DATA = [
    { month: 'Jan', value: 2800000 },
    { month: 'Feb', value: 2950000 },
    { month: 'Mar', value: 3100000 },
    { month: 'Apr', value: 3050000 },
    { month: 'May', value: 3400000 },
    { month: 'Jun', value: 3800000 },
    { month: 'Jul', value: 4100000 },
    { month: 'Aug', value: 4350000 },
    { month: 'Sep', value: 4600000 },
    { month: 'Oct', value: 4800000 },
    { month: 'Nov', value: 5050000 },
    { month: 'Dec', value: 5240000 },
];

const Portfolio: React.FC = () => {
    return (
        <div className="p-6 md:p-8 space-y-8">
            <div className="mb-6">
                <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Portfolio Overview</h1>
                <p className="text-slate-500 mt-1">Detailed breakdown of asset allocation and performance.</p>
            </div>

            {/* Hero: Net Worth History */}
            <div className="bg-white rounded-[32px] border border-slate-200 shadow-sm p-10 relative overflow-hidden">
                <div className="absolute top-0 left-0 right-0 h-1 bg-amber-400/50" />
                <div className="flex flex-col mb-10">
                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-1">Total Net Worth</span>
                    <div className="flex items-baseline gap-4">
                        <h2 className="text-5xl font-extrabold text-slate-900 tracking-tight">$5,240,000</h2>
                        <div className="flex items-center text-emerald-500 font-bold text-sm px-2.5 py-1 bg-emerald-50 rounded-full border border-emerald-100">
                            <span className="mr-0.5">↑</span> 2.1%
                        </div>
                        <span className="text-sm font-semibold text-slate-400">this month</span>
                    </div>
                </div>

                <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={HEALTH_CHART_DATA}>
                            <defs>
                                <linearGradient id="healthGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="#2563eb" stopOpacity={0.15} />
                                    <stop offset="100%" stopColor="#2563eb" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <XAxis dataKey="month" hide />
                            <YAxis hide domain={['dataMin - 100000', 'dataMax + 100000']} />
                            <Tooltip
                                contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}
                                formatter={(val: number) => `$${(val / 1000000).toFixed(2)}M`}
                            />
                            <Area
                                type="monotone"
                                dataKey="value"
                                stroke="#2563eb"
                                strokeWidth={4}
                                fillOpacity={1}
                                fill="url(#healthGradient)"
                                strokeLinecap="round"
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                    <div className="flex justify-between mt-4 px-2 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                        {HEALTH_CHART_DATA.map(d => <span key={d.month}>{d.month}</span>)}
                    </div>
                </div>
            </div>

            {/* Middle: Four Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {[
                    { label: 'YTD Return', val: '+12.4%', color: 'emerald' },
                    { label: 'Holdings', val: '13', color: 'slate' },
                    { label: 'Cash Reserves', val: '$1,200,000', color: 'slate' },
                    { label: 'Portfolio XIRR', val: '18.4%', color: 'slate' },
                ].map((stat) => (
                    <div key={stat.label} className="bg-white p-6 rounded-2xl border border-slate-200 border-l-[6px] border-l-amber-400/40 shadow-sm hover:shadow-md transition-all">
                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-4">{stat.label}</p>
                        <p className={`text-3xl font-extrabold tracking-tight ${stat.color === 'emerald' ? 'text-emerald-500' : 'text-slate-900'}`}>{stat.val}</p>
                    </div>
                ))}
            </div>

            {/* Bottom Grid: Performance List and Allocation Circle */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                <div className="lg:col-span-7 bg-white p-8 rounded-[32px] border border-slate-200 shadow-sm">
                    <div className="flex justify-between items-center mb-8">
                        <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">Performance by Asset Class</h3>
                        <span className="text-[10px] font-bold text-slate-500 bg-slate-100 px-2 py-1 rounded">Last 12 Months</span>
                    </div>
                    <div className="space-y-6">
                        {[
                            { label: 'Public Equity', val: '14.2%', color: 'bg-blue-600', w: '85%' },
                            { label: 'Fixed Income', val: '4.8%', color: 'bg-blue-400', w: '35%' },
                            { label: 'Alternatives', val: '9.1%', color: 'bg-amber-400', w: '55%' },
                            { label: 'Real Estate', val: '6.5%', color: 'bg-indigo-500', w: '42%' },
                            { label: 'Cash / Equiv', val: '3.2%', color: 'bg-emerald-500', w: '20%' },
                        ].map((item) => (
                            <div key={item.label} className="space-y-2">
                                <div className="flex justify-between text-[11px] font-bold">
                                    <span className="text-slate-600 uppercase">{item.label}</span>
                                    <span className="text-slate-900">{item.val}</span>
                                </div>
                                <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                                    <div className={`${item.color} h-full rounded-full transition-all duration-1000`} style={{ width: item.w }}></div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="lg:col-span-5 bg-white p-8 rounded-[32px] border border-slate-200 shadow-sm">
                    <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-8">Allocation Breakdown</h3>
                    <div className="flex flex-col items-center justify-center h-full pb-8">
                        <div className="w-48 h-48 rounded-full border-[14px] border-slate-50 flex items-center justify-center relative mb-8">
                            <div className="absolute inset-0 rounded-full border-[14px] border-blue-600 border-r-transparent border-b-transparent rotate-[45deg]" />
                            <div className="absolute inset-0 rounded-full border-[14px] border-amber-400 border-l-transparent border-t-transparent -rotate-[15deg]" />
                            <div className="flex flex-col items-center">
                                <span className="text-3xl font-extrabold text-slate-900">100%</span>
                                <span className="text-[10px] font-bold text-slate-400 uppercase">Invested</span>
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-x-8 gap-y-3 w-full px-4">
                            {[
                                { l: 'Stocks', p: '45%', c: 'bg-blue-600' },
                                { l: 'Bonds', p: '30%', c: 'bg-blue-300' },
                                { l: 'Alts', p: '15%', c: 'bg-amber-400' },
                                { l: 'Cash', p: '10%', c: 'bg-emerald-500' },
                            ].map(item => (
                                <div key={item.l} className="flex justify-between items-center">
                                    <div className="flex items-center gap-2">
                                        <div className={`w-2.5 h-2.5 rounded-full ${item.c}`} />
                                        <span className="text-xs font-semibold text-slate-500">{item.l}</span>
                                    </div>
                                    <span className="text-xs font-bold text-slate-900">{item.p}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Portfolio;
```

## File: src/types/index.ts
```ts

export interface Activity {
    id: string;
    type: 'buy' | 'deposit' | 'dividend' | 'sell';
    asset: string;
    amount: number;
    date: string;
    icon: string;
}

export interface NavItem {
    label: string;
    icon: string;
    section: 'Main' | 'Analysis' | 'System';
    isActive?: boolean;
}

export interface AllocationData {
    name: string;
    value: number;
    color: string;
}

export interface NetWorthPoint {
    date: string;
    value: number;
}

export enum WorkflowStep {
    DASHBOARD = 'DASHBOARD',
    UPLOAD = 'UPLOAD',
    MAP = 'MAP',
    REVIEW = 'REVIEW',
    COMPLETE = 'COMPLETE'
}

export interface Transaction {
    id: string;
    date: string;
    description: string;
    category: string;
    amount: number;
    ticker?: string;
    account: string;
    status: 'ready' | 'error';
    errorMsg?: string;
}

export enum ReportView {
    PORTFOLIO_OVERVIEW = 'Portfolio Overview',
    ALLOCATION_RISK = 'Allocation & Risk',
    GAINS_ANALYSIS = 'Gains Analysis',
    CASH_FLOW = 'Cash Flow',
    COMPASS = 'Compass',
    SIMULATION = 'Simulation',
    DASHBOARD = 'Dashboard',
    DATA_WORKBENCH = 'Data Workbench',
    LOGIC_STUDIO = 'Logic Studio',
    INTEGRATIONS = 'Integrations',
    HEALTH = 'Health'
}

export interface AssetPerformance {
    name: string;
    class: string;
    period: string;
    status: 'Active' | 'Closed';
    invested: number;
    value: number;
    profitLoss: number;
    returnPct: number;
    performance: 'Excellent' | 'Good' | 'Average' | 'Poor';
}
```

## File: src/web_app/compass_dashboard/style.css
```css
/* Investment Compass Dashboard Styles */

/* Reset and base styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    min-height: 100vh;
}

/* Main container */
.main-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

/* Header styles */
.dashboard-header {
    background: white;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    margin-bottom: 2rem;
    text-align: center;
}

.dashboard-header h1 {
    color: #2c3e50;
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
    font-weight: 300;
}

.last-updated {
    color: #7f8c8d;
    font-size: 0.9rem;
}

/* Header controls container */
.header-controls {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
}

/* Refresh button styles */
.refresh-btn {
    background: linear-gradient(135deg, #3498db, #2980b9);
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    font-size: 0.9rem;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.refresh-btn:hover {
    background: linear-gradient(135deg, #2980b9, #1abc9c);
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.refresh-btn:active {
    transform: translateY(0);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.refresh-btn:disabled {
    background: #bdc3c7;
    cursor: not-allowed;
    transform: none;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Refresh message styles */
.refresh-message {
    background: #e8f4fd;
    border: 1px solid #3498db;
    color: #2c3e50;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
    text-align: center;
    display: none;
}

.refresh-message.error {
    background: #fdf2f2;
    border-color: #e74c3c;
    color: #c0392b;
}

.refresh-message.success {
    background: #f0f9f0;
    border-color: #27ae60;
    color: #1e8449;
}

/* Main content */
.dashboard-content {
    flex: 1;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
    gap: 2rem;
}

/* Dashboard sections */
.dashboard-section {
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    overflow: hidden;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.dashboard-section:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.dashboard-section h2 {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1.5rem;
    margin: 0;
    font-size: 1.3rem;
    font-weight: 500;
}

/* Component containers */
.component-container {
    padding: 2rem;
    min-height: 200px;
}

/* Loading states */
.loading {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 150px;
    color: #7f8c8d;
    font-style: italic;
}

/* Error states */
.error {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 150px;
    color: #e74c3c;
    background: #fdf2f2;
    border: 1px solid #fecaca;
    border-radius: 8px;
    margin: 1rem;
}

/* Data display styles */
.data-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin: 1rem 0;
}

.data-item {
    text-align: center;
    padding: 1rem;
    background: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #e9ecef;
}

/* Portfolio Snapshot Component Styling */
.portfolio-metrics {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.metric-card {
    background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
    border: 1px solid #e1e5e9;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

.metric-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #007bff, #28a745);
    opacity: 0;
    transition: opacity 0.3s ease;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.metric-card:hover::before {
    opacity: 1;
}

.metric-card.primary {
    background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
    color: white;
    border: none;
}

.metric-card.primary::before {
    background: linear-gradient(90deg, #ffffff, #f8f9fa);
}

.metric-label {
    font-size: 14px;
    font-weight: 500;
    margin-bottom: 8px;
    opacity: 0.8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.metric-card.primary .metric-label {
    color: rgba(255, 255, 255, 0.9);
}

.metric-value {
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 4px;
    color: #2c3e50;
}

.metric-card.primary .metric-value {
    color: white;
    font-size: 32px;
}

.metric-subtitle {
    font-size: 12px;
    opacity: 0.6;
    font-style: italic;
}

.metric-card.primary .metric-subtitle {
    color: rgba(255, 255, 255, 0.7);
}

/* Liquid Portfolio Highlight */
.metric-card.liquid-highlight {
    background: linear-gradient(135deg, #e8f4fd 0%, #f0f9ff 100%);
    border: 2px solid #3498db;
}

.metric-card.liquid-highlight .metric-label {
    color: #2980b9;
    font-weight: 600;
}

.metric-card.liquid-highlight .metric-value {
    color: #1f4e79;
    font-weight: 700;
}

/* Info Tooltips */
.info-tooltip {
    cursor: help;
    color: #7f8c8d;
    font-size: 0.8em;
    margin-left: 5px;
}

.info-tooltip:hover {
    color: #3498db;
}

/* Rebalancing Note */
.rebalancing-note {
    background: linear-gradient(135deg, #f0f9f0 0%, #ffffff 100%);
    border: 1px solid #27ae60;
    border-radius: 8px;
    padding: 15px;
    margin: 20px 0;
    display: flex;
    align-items: flex-start;
    gap: 10px;
}

.note-icon {
    font-size: 1.2em;
    flex-shrink: 0;
}

.note-text {
    color: #1e8449;
    font-size: 0.9em;
    line-height: 1.4;
}

.note-text strong {
    color: #155724;
}

/* Single Asset Risk Section */
.single-asset-risk-section {
    background: linear-gradient(135deg, #fff8f0 0%, #ffffff 100%);
    border: 1px solid #ffd699;
    border-radius: 12px;
    padding: 25px;
    margin-top: 20px;
}

.risk-section-title {
    margin: 0 0 20px 0;
    font-size: 18px;
    font-weight: 600;
    color: #d69e2e;
    display: flex;
    align-items: center;
}

.risk-section-title::before {
    content: '⚠️';
    margin-right: 8px;
}

.risk-details {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.risk-asset {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 15px;
}

.risk-asset-name {
    display: flex;
    align-items: center;
    gap: 10px;
}

.asset-label {
    font-size: 14px;
    color: #666;
    font-weight: 500;
}

.asset-ticker {
    font-size: 16px;
    font-weight: 700;
    color: #2c3e50;
    background: #f1f3f4;
    padding: 4px 8px;
    border-radius: 6px;
}

.risk-concentration {
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 200px;
}

.concentration-bar {
    flex-grow: 1;
    height: 12px;
    background: #e9ecef;
    border-radius: 6px;
    overflow: hidden;
    position: relative;
}

.concentration-fill {
    height: 100%;
    background: linear-gradient(90deg, #ffc107 0%, #ff6b35 50%, #dc3545 100%);
    border-radius: 6px;
    transition: width 0.8s ease-in-out;
    position: relative;
}

.concentration-fill::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.3) 50%, transparent 100%);
    animation: shimmer 2s infinite;
}

@keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}

.concentration-percentage {
    font-size: 16px;
    font-weight: 700;
    color: #d69e2e;
    min-width: 50px;
    text-align: right;
}

.risk-assessment {
    display: flex;
    align-items: flex-start;
    gap: 15px;
    flex-wrap: wrap;
}

.risk-level-badge {
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    white-space: nowrap;
}

.risk-level-badge.risk-low {
    background: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.risk-level-badge.risk-medium {
    background: #fff3cd;
    color: #856404;
    border: 1px solid #ffeaa7;
}

.risk-level-badge.risk-high {
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

.risk-description {
    flex-grow: 1;
    margin: 0;
    font-size: 14px;
    line-height: 1.5;
    color: #555;
    background: rgba(255, 255, 255, 0.7);
    padding: 12px;
    border-radius: 8px;
    border-left: 4px solid #ffc107;
}

/* Responsive Design for Portfolio Snapshot */
@media (max-width: 768px) {
    .portfolio-metrics {
        grid-template-columns: 1fr;
        gap: 15px;
    }
    
    .metric-card {
        padding: 15px;
    }
    
    .metric-value {
        font-size: 24px;
    }
    
    .metric-card.primary .metric-value {
        font-size: 28px;
    }
    
    .risk-asset {
        flex-direction: column;
        align-items: flex-start;
    }
    
    .risk-concentration {
        width: 100%;
        min-width: unset;
    }
    
    .risk-assessment {
        flex-direction: column;
        gap: 10px;
    }
    
    .single-asset-risk-section {
        padding: 20px;
    }
}

/* Asset Allocation Component Styling */
.chart-container {
    height: 400px;
    margin-bottom: 30px;
    background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.allocation-summary {
    background: linear-gradient(135deg, #e3f2fd 0%, #ffffff 100%);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 25px;
    border-left: 4px solid #2196f3;
}

.allocation-summary h3 {
    margin: 0 0 15px 0;
    color: #1976d2;
    font-size: 18px;
    font-weight: 600;
}

.allocation-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
}

.stat-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 15px;
    background: rgba(255, 255, 255, 0.7);
    border-radius: 8px;
    border: 1px solid #e3f2fd;
}

.stat-label {
    font-size: 14px;
    color: #666;
    font-weight: 500;
}

.stat-value {
    font-size: 16px;
    font-weight: 700;
    color: #1976d2;
}

.allocation-table-container {
    background: white;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.allocation-table-container h3 {
    margin: 0;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-size: 18px;
    font-weight: 600;
}

.allocation-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
}

.allocation-table thead th {
    background: #f8f9fa;
    padding: 15px 12px;
    text-align: left;
    font-weight: 600;
    color: #495057;
    border-bottom: 2px solid #dee2e6;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.allocation-row {
    transition: all 0.3s ease;
    border-bottom: 1px solid #f1f3f4;
}

.allocation-row:hover {
    background: linear-gradient(135deg, #f8f9ff 0%, #ffffff 100%);
    transform: scale(1.01);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.allocation-row.high-allocation {
    background: linear-gradient(135deg, #fff3e0 0%, #ffffff 100%);
}

.allocation-table td {
    padding: 15px 12px;
    vertical-align: middle;
}

.category-cell {
    font-weight: 600;
}

.category-info {
    display: flex;
    align-items: center;
    gap: 10px;
}

.category-indicator {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    display: inline-block;
}

.category-name {
    font-size: 15px;
    color: #2c3e50;
}

.percentage-cell {
    text-align: center;
    font-weight: 600;
}

.percentage-cell.actual {
    position: relative;
}

.percentage-bar {
    display: block;
    height: 6px;
    background: #e9ecef;
    border-radius: 3px;
    margin-bottom: 6px;
    position: relative;
    overflow: hidden;
}

.percentage-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.8s ease-in-out;
    position: relative;
}

.percentage-fill::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.4) 50%, transparent 100%);
    animation: shimmer 2s infinite;
}

.deviation-cell {
    text-align: center;
    font-weight: 700;
    font-size: 13px;
}

.deviation-positive {
    color: #28a745;
    background: rgba(40, 167, 69, 0.1);
    padding: 4px 8px;
    border-radius: 4px;
}

.deviation-negative {
    color: #dc3545;
    background: rgba(220, 53, 69, 0.1);
    padding: 4px 8px;
    border-radius: 4px;
}

.deviation-high-positive {
    color: #ff6b35;
    background: rgba(255, 107, 53, 0.15);
    padding: 4px 8px;
    border-radius: 4px;
    border: 1px solid rgba(255, 107, 53, 0.3);
}

.deviation-high-negative {
    color: #c62828;
    background: rgba(198, 40, 40, 0.15);
    padding: 4px 8px;
    border-radius: 4px;
    border: 1px solid rgba(198, 40, 40, 0.3);
}

.deviation-neutral {
    color: #6c757d;
    background: rgba(108, 117, 125, 0.1);
    padding: 4px 8px;
    border-radius: 4px;
}

.value-cell {
    text-align: right;
    font-weight: 600;
    color: #2c3e50;
}

.status-cell {
    text-align: center;
    font-size: 16px;
}

.status-icon {
    display: inline-block;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.7; transform: scale(1.1); }
    100% { opacity: 1; transform: scale(1); }
}

/* Two-Level Allocation Hierarchy Styles */
.allocation-hierarchy {
    margin-top: 20px;
}

.allocation-category {
    border: 1px solid #e1e8ed;
    border-radius: 12px;
    margin-bottom: 15px;
    background: white;
    overflow: hidden;
    transition: all 0.3s ease;
}

.allocation-category:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.allocation-category.non-rebalanceable {
    background: #f8f9fa;
    border-color: #ced4da;
    opacity: 0.8;
}

.category-header {
    padding: 20px;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
    border-bottom: 1px solid #e9ecef;
}

.category-header:hover {
    background: linear-gradient(135deg, #e9ecef 0%, #f8f9fa 100%);
}

.category-main {
    display: flex;
    align-items: center;
    gap: 15px;
    flex: 1;
}

.category-name {
    margin: 0;
    font-size: 1.1em;
    font-weight: 600;
    color: #2c3e50;
    display: flex;
    align-items: center;
    gap: 8px;
}

.lock-icon {
    font-size: 0.9em;
    opacity: 0.7;
}

.expand-icon {
    font-size: 0.8em;
    color: #7f8c8d;
    margin-left: 10px;
}

.category-metrics {
    display: flex;
    gap: 15px;
    align-items: center;
}

.current-value {
    font-weight: 700;
    color: #2c3e50;
    font-size: 1.1em;
}

.current-pct {
    background: #3498db;
    color: white;
    padding: 4px 8px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.9em;
}

.category-targets {
    display: flex;
    gap: 20px;
    align-items: center;
}

.target-info, .deviation-info {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
}

.target-label, .deviation-label {
    font-size: 0.8em;
    color: #7f8c8d;
    font-weight: 500;
}

.target-pct {
    font-weight: 600;
    color: #27ae60;
}

.deviation-pct {
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.9em;
}

.deviation-high-positive {
    color: #c0392b;
    background: rgba(192, 57, 43, 0.1);
}

.deviation-positive {
    color: #e67e22;
    background: rgba(230, 126, 34, 0.1);
}

.deviation-neutral {
    color: #27ae60;
    background: rgba(39, 174, 96, 0.1);
}

.deviation-negative {
    color: #f39c12;
    background: rgba(243, 156, 18, 0.1);
}

.deviation-high-negative {
    color: #8e44ad;
    background: rgba(142, 68, 173, 0.1);
}

.non-rebalanceable-note {
    background: #ced4da;
    color: #6c757d;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 0.9em;
    font-weight: 500;
}

.allocation-bar {
    padding: 0 20px 15px;
}

.bar-background {
    position: relative;
    height: 8px;
    background: #e9ecef;
    border-radius: 4px;
    margin-bottom: 8px;
}

.bar-current {
    height: 100%;
    background: linear-gradient(90deg, #3498db, #2980b9);
    border-radius: 4px;
    transition: width 0.3s ease;
}

.bar-target {
    position: absolute;
    top: -2px;
    width: 3px;
    height: 12px;
    background: #27ae60;
    border-radius: 2px;
}

.bar-labels {
    display: flex;
    justify-content: space-between;
    font-size: 0.8em;
    color: #7f8c8d;
}

.sub-categories {
    background: #f8f9fa;
    border-top: 1px solid #e9ecef;
}

.sub-category {
    padding: 15px 20px;
    border-bottom: 1px solid #e9ecef;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.sub-category:last-child {
    border-bottom: none;
}

.sub-category-main {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.sub-category-name {
    font-weight: 500;
    color: #495057;
    padding-left: 20px;
    position: relative;
}

.sub-category-name::before {
    content: '└';
    position: absolute;
    left: 0;
    color: #ced4da;
    font-weight: 400;
}

.sub-category-metrics {
    display: flex;
    gap: 12px;
    align-items: center;
    font-size: 0.9em;
}

.sub-value {
    font-weight: 600;
    color: #2c3e50;
}

.sub-current {
    background: rgba(52, 152, 219, 0.1);
    color: #2980b9;
    padding: 2px 6px;
    border-radius: 4px;
    font-weight: 500;
}

.sub-target {
    color: #27ae60;
    font-weight: 500;
}

.sub-deviation {
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.85em;
}

.sub-allocation-bar {
    margin-left: 20px;
    height: 4px;
    background: #e9ecef;
    border-radius: 2px;
    overflow: hidden;
}

.sub-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, #74b9ff, #0984e3);
    transition: width 0.3s ease;
}

.no-sub-categories {
    padding: 15px 20px;
    color: #6c757d;
    font-style: italic;
    text-align: center;
}

/* Enhanced Rebalancing Recommendations Styles */
.rebalancing-header {
    border-bottom: 2px solid #e9ecef;
    padding-bottom: 15px;
    margin-bottom: 20px;
}

.rebalancing-header h3 {
    margin: 0 0 10px 0;
    color: #2c3e50;
    font-size: 1.3em;
    display: flex;
    align-items: center;
    gap: 10px;
}

.liquid-assets-note {
    background: linear-gradient(135deg, #e3f2fd 0%, #f8f9fa 100%);
    color: #1565c0;
    padding: 10px 15px;
    border-radius: 8px;
    font-size: 0.9em;
    display: flex;
    align-items: center;
    gap: 8px;
    border-left: 4px solid #2196f3;
}

.portfolio-status {
    padding: 20px;
    border-radius: 12px;
    border: 2px solid;
    margin-bottom: 20px;
}

.portfolio-status.balanced {
    background: linear-gradient(135deg, #e8f5e8 0%, #f1f8e9 100%);
    border-color: #4caf50;
    color: #2e7d32;
}

.portfolio-status.needs-attention {
    background: linear-gradient(135deg, #fff3e0 0%, #fafafa 100%);
    border-color: #ff9800;
    color: #e65100;
}

.status-indicator {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
}

.status-indicator i {
    font-size: 1.2em;
}

.status-text {
    font-size: 1.1em;
    font-weight: 700;
}

.status-message {
    font-size: 0.95em;
    opacity: 0.9;
    margin-left: 32px;
}

.trigger-section, .categories-section, .actions-section {
    background: white;
    border: 1px solid #e9ecef;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
}

.trigger-section h4, .categories-section h4, .actions-section h4 {
    margin: 0 0 15px 0;
    color: #2c3e50;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 1.1em;
}

.trigger-reason {
    background: #f8f9fa;
    padding: 15px;
    border-left: 4px solid #6c757d;
    border-radius: 6px;
    font-style: italic;
}

.categories-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.category-deviation {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 15px;
    transition: all 0.3s ease;
}

.category-deviation:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.category-deviation.over-allocated {
    border-left: 4px solid #dc3545;
    background: linear-gradient(135deg, #fff5f5 0%, #fafafa 100%);
}

.category-deviation.under-allocated {
    border-left: 4px solid #ffc107;
    background: linear-gradient(135deg, #fffbf0 0%, #fafafa 100%);
}

.category-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 5px;
}

.category-name {
    font-weight: 600;
    color: #2c3e50;
}

.deviation-badge {
    background: #495057;
    color: white;
    padding: 4px 8px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.85em;
    display: flex;
    align-items: center;
    gap: 4px;
}

.over-allocated .deviation-badge {
    background: #dc3545;
}

.under-allocated .deviation-badge {
    background: #ffc107;
    color: #212529;
}

.category-note {
    font-size: 0.85em;
    color: #6c757d;
    margin-left: 5px;
}

.actions-list {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.action-item {
    display: flex;
    align-items: flex-start;
    gap: 15px;
    background: #f8f9fa;
    padding: 15px;
    border-radius: 8px;
    border-left: 4px solid #007bff;
}

.action-number {
    background: #007bff;
    color: white;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.85em;
    flex-shrink: 0;
}

.action-content {
    flex: 1;
}

.action-text {
    font-weight: 500;
    color: #2c3e50;
    margin-bottom: 5px;
}

.action-context {
    font-size: 0.85em;
    color: #6c757d;
    font-style: italic;
}

.implementation-guidance {
    background: linear-gradient(135deg, #e8f4fd 0%, #f8f9fa 100%);
    border: 1px solid #bee5eb;
    border-radius: 10px;
    padding: 20px;
}

.implementation-guidance h4 {
    margin: 0 0 15px 0;
    color: #0c5460;
    display: flex;
    align-items: center;
    gap: 8px;
}

.guidance-list {
    margin: 0;
    padding-left: 20px;
}

.guidance-list li {
    margin-bottom: 8px;
    color: #0c5460;
}

.no-actions {
    background: linear-gradient(135deg, #e8f5e8 0%, #f1f8e9 100%);
    border: 2px solid #4caf50;
    border-radius: 12px;
    padding: 30px;
    text-align: center;
}

.no-actions-content i {
    font-size: 3em;
    color: #4caf50;
    margin-bottom: 15px;
}

.no-actions-content h4 {
    margin: 0 0 10px 0;
    color: #2e7d32;
    font-size: 1.2em;
}

.no-actions-content p {
    margin: 0 0 15px 0;
    color: #388e3c;
}

.next-review {
    background: rgba(76, 175, 80, 0.1);
    padding: 10px 15px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    color: #2e7d32;
    font-weight: 500;
    margin-top: 10px;
}

/* Responsive Design for Asset Allocation */
@media (max-width: 768px) {
    .chart-container {
        height: 300px;
        padding: 15px;
    }
    
    .allocation-stats {
        grid-template-columns: 1fr;
        gap: 10px;
    }
    
    .allocation-table {
        font-size: 12px;
    }
    
    .allocation-table td,
    .allocation-table th {
        padding: 10px 8px;
    }
    
    .category-info {
        gap: 6px;
    }
    
    .category-name {
        font-size: 13px;
    }
    
    .percentage-bar {
        height: 4px;
        margin-bottom: 4px;
    }
}

@media (max-width: 600px) {
    .allocation-table thead th:nth-child(2),
    .allocation-table tbody td:nth-child(2) {
        display: none;
    }
    
    .allocation-table thead th:nth-child(6),
    .allocation-table tbody td:nth-child(6) {
        display: none;
    }
}

.data-item {
    background: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #e9ecef;
}

.data-item .label {
    font-size: 0.9rem;
    color: #7f8c8d;
    margin-bottom: 0.5rem;
}

.data-item .value {
    font-size: 1.8rem;
    font-weight: 600;
    color: #2c3e50;
}

/* Tables */
.data-table {
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0;
}

.data-table th,
.data-table td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid #dee2e6;
}

.data-table th {
    background: #f8f9fa;
    font-weight: 600;
    color: #495057;
}

.data-table tr:hover {
    background: #f8f9fa;
}

/* Risk indicators */
.risk-indicator {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
}

.risk-low { background: #d4edda; color: #155724; }
.risk-medium { background: #fff3cd; color: #856404; }
.risk-high { background: #f8d7da; color: #721c24; }

/* Percentage indicators */
.percentage {
    font-weight: 600;
}

.percentage.positive { color: #28a745; }
.percentage.negative { color: #dc3545; }

/* Footer */
.dashboard-footer {
    margin-top: 2rem;
    text-align: center;
    color: #7f8c8d;
    font-size: 0.9rem;
    padding: 1rem;
}

/* Responsive design */
@media (max-width: 768px) {
    .main-container {
        padding: 10px;
    }
    
    .dashboard-content {
        grid-template-columns: 1fr;
        gap: 1rem;
    }
    
    .dashboard-header h1 {
        font-size: 2rem;
    }
    
    .component-container {
        padding: 1rem;
    }
}

/* Utility classes */
.text-center { text-align: center; }
.text-right { text-align: right; }
.mb-1 { margin-bottom: 1rem; }
.mb-2 { margin-bottom: 2rem; }
.hidden { display: none; }
```

## File: src/web_app/static/css/design-tokens.css
```css
/* 
 * Personal Investment System - Design Tokens
 * Implementation of docs/design-framework.md
 * Theme: SunnRayy (Champagne Gold + Tech Blue)
 */

:root {
  /* --- Brand Colors --- */
  /* SunnRayy Identity */
  --brand-gold: #D4AF37;         /* Champagne Gold - Wealth/Prestige */
  --brand-gold-light: #E5C158;   /* Light Gold - Hover */
  --brand-gold-dark: #C9A227;    /* Deep Gold - Emphasis */
  --brand-blue: #3B82F6;         /* Tech Blue - Trust/Action */
  --brand-blue-light: #60A5FA;   /* Light Blue - Hover */
  --brand-blue-dark: #2563EB;    /* Deep Blue - Active */
  
  /* Brand Gradient (Accents only) */
  --brand-gradient: linear-gradient(135deg, #D4AF37 0%, #3B82F6 100%);

  /* --- Semantic Colors --- */
  /* Backgrounds */
  --bg-surface: #FAFAFA;         /* Page background */
  --bg-container: #FFFFFF;       /* Cards, modals */
  --bg-container-inset: #F5F5F5; /* Nested containers */
  --bg-container-hover: #F0F0F0;

  /* Text */
  --text-primary: #171717;       /* Gray-900 */
  --text-secondary: #525252;     /* Gray-600 */
  --text-tertiary: #A3A3A3;      /* Gray-400 */
  --text-inverse: #FFFFFF;

  /* Borders */
  --border-primary: rgba(0, 0, 0, 0.15);
  --border-secondary: rgba(0, 0, 0, 0.10);
  --border-tertiary: rgba(0, 0, 0, 0.05);

  /* Functional Colors */
  --color-success: #10B981;      /* Emerald-500 */
  --color-success-bg: #D1FAE5;
  --color-warning: #F59E0B;      /* Amber-500 */
  --color-warning-bg: #FEF3C7;
  --color-error: #EF4444;        /* Red-500 */
  --color-error-bg: #FEE2E2;
  --color-info: #3B82F6;         /* Blue-500 */
  --color-info-bg: #DBEAFE;

  /* Financial Semantics */
  --color-gain: #10B981;
  --color-loss: #EF4444;
  --color-neutral: #6B7280;

  /* --- Chart Colors --- */
  --chart-equity: #D4AF37;       /* Gold */
  --chart-fixed-income: #3B82F6; /* Tech Blue */
  --chart-cash: #6B7280;         /* Gray */
  --chart-alternatives: #0EA5E9; /* Sky Blue */
  --chart-real-estate: #C9A227;  /* Deep Gold */
  --chart-crypto: #14B8A6;       /* Teal */
  --chart-commodities: #60A5FA;  /* Light Blue */
  --chart-other: #78716C;        /* Stone */

  /* --- Typography --- */
  --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;

  /* --- Spacing System (8px Grid) --- */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;

  /* --- Effects --- */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-full: 9999px;
  
  --transition-base: all 0.2s ease-in-out;
}

/* Dark Mode Support (Future Proofing) */
@media (prefers-color-scheme: dark) {
  /* Add dark mode overrides here in Phase 4 */
}
```

## File: src/web_app/static/css/fix_scrolling.css
```css
```

## File: src/web_app/static/css/style.css
```css
@import 'design-tokens.css';

/* Dashboard CSS - Personal Investment System */
/* Basic styling for the financial dashboard */

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: inherit;
}

body {
    font-family: var(--font-sans);
    background-color: var(--bg-surface);
    color: var(--text-primary);
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
}

h1,
h2,
h3,
h4,
h5,
h6 {
    color: var(--text-primary);
    font-weight: 600;
}

a {
    color: var(--brand-blue);
    text-decoration: none;
    transition: var(--transition-base);
}

a:hover {
    color: var(--brand-blue-dark);
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: var(--space-5);
}

/* Header Replaced in new layout, keeping for backward compat */
header {
    text-align: center;
    margin-bottom: var(--space-8);
    padding: var(--space-5) 0;
    background: var(--bg-container);
    color: var(--text-primary);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border-tertiary);
}

header h1 {
    font-size: 2.5em;
    margin-bottom: var(--space-3);
    color: var(--text-primary);
}

header p {
    font-size: 1.1em;
    color: var(--text-secondary);
}

.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
    gap: var(--space-5);
    margin-top: var(--space-5);
}

/* Special layout for chart sections */
.dashboard-section.chart-section {
    min-height: 400px;
}

.dashboard-section {
    background: var(--bg-container);
    padding: var(--space-5);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border-tertiary);
    transition: var(--transition-base);
}

.dashboard-section:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
    border-color: var(--border-secondary);
}

.dashboard-section h2 {
    margin-bottom: var(--space-4);
    color: var(--text-primary);
    border-bottom: 2px solid var(--brand-blue);
    padding-bottom: var(--space-2);
    font-size: 1.25rem;
}

#networth-chart-container,
#portfolio-chart-container,
#performance-chart-container,
#allocation-chart-container {
    height: 300px;
    position: relative;
}

/* Special styling for donut charts */
#portfolio-chart-container {
    height: 350px;
    /* Slightly taller for legend space */
}

/* Asset allocation chart needs more height for horizontal bar chart with many categories */
#allocation-chart-container {
    height: 500px;
    /* Taller for horizontal bar chart with 10+ categories */
    padding: var(--space-2);
}

#cashflow-chart-container {
    height: 400px;
    /* Increased height for better bar visibility */
    position: relative;
    padding: var(--space-2);
}

#recommendations-container {
    min-height: 200px;
    padding: var(--space-4);
    background-color: var(--bg-container-inset);
    border-radius: var(--radius-md);
    border-left: 4px solid var(--color-success);
}

/* Error message styling */
.error-message {
    background-color: var(--color-error-bg);
    color: var(--color-error);
    padding: var(--space-4);
    margin: var(--space-3) 0;
    border: 1px solid var(--color-error);
    border-radius: var(--radius-md);
    text-align: center;
    font-weight: 500;
}

/* Chart loading/message styling */
.chart-message {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 300px;
    color: var(--text-tertiary);
    font-style: italic;
    text-align: center;
    font-size: 14px;
}

/* Priority badge styles */
.priority-badge {
    display: inline-block;
    padding: 4px 8px;
    border-radius: var(--radius-full);
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.priority-high {
    background-color: var(--color-error);
    color: white;
}

.priority-medium {
    background-color: var(--color-warning);
    color: var(--text-primary);
}

.priority-low {
    background-color: var(--color-success);
    color: white;
}

/* Recommendations table styling */
#recommendations-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: var(--space-3);
}

#recommendations-table th {
    background-color: var(--bg-container-hover);
    padding: var(--space-3) var(--space-2);
    text-align: left;
    font-weight: 600;
    font-size: 13px;
    color: var(--text-secondary);
    border-bottom: 2px solid var(--border-secondary);
}

#recommendations-table td {
    padding: var(--space-3) var(--space-2);
    border-bottom: 1px solid var(--border-tertiary);
    vertical-align: top;
    color: var(--text-primary);
}

#recommendations-table tr:hover {
    background-color: var(--bg-container-hover);
}

/* Button styling for recommendations */
.btn-details {
    background-color: var(--brand-blue);
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: var(--radius-sm);
    cursor: pointer;
    font-size: 12px;
    font-weight: 500;
    transition: var(--transition-base);
}

.btn-details:hover {
    background-color: var(--brand-blue-dark);
}

/* Responsive design */
@media (max-width: 768px) {
    .dashboard-grid {
        grid-template-columns: 1fr;
    }

    header h1 {
        font-size: 2em;
    }

    .container {
        padding: var(--space-3);
    }

    /* Make recommendations table mobile-friendly */
    #recommendations-table {
        font-size: 12px;
    }

    #recommendations-table th,
    #recommendations-table td {
        padding: 8px 4px;
    }

    .priority-badge {
        font-size: 10px;
        padding: 3px 6px;
    }
}

/* ===== COMPREHENSIVE ANALYSIS STYLES ===== */

/* Enhanced metric cards for comprehensive analysis */
.analysis-section .metric-card {
    background: var(--bg-container);
    border: 1px solid var(--border-secondary);
    border-radius: var(--radius-lg);
    padding: var(--space-5);
    margin-bottom: var(--space-5);
    box-shadow: var(--shadow-sm);
    transition: var(--transition-base);
}

.analysis-section .metric-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
    border-color: var(--brand-gold);
}

.analysis-section .metric-card h3 {
    margin: 0 0 15px 0;
    color: var(--text-secondary);
    font-size: 1.2em;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 8px;
}

.analysis-section .metric-value {
    font-size: 2em;
    font-weight: bold;
    color: var(--brand-gold-dark);
    /* Using Gold to signify wealth */
    margin: 10px 0;
}

.analysis-section .metric-label {
    color: var(--text-tertiary);
    font-size: 0.9em;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Goal probability styling */
.goal-probability-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid var(--border-tertiary);
}

.goal-probability-item:last-child {
    border-bottom: none;
}

.goal-name {
    font-weight: 500;
    color: var(--text-primary);
}

.goal-probability {
    font-weight: bold;
    padding: 4px 8px;
    border-radius: var(--radius-sm);
}

.goal-probability-item.high .goal-probability {
    background-color: var(--color-success-bg);
    color: var(--color-success);
}

.goal-probability-item.medium .goal-probability {
    background-color: var(--color-warning-bg);
    color: var(--color-warning);
}

.goal-probability-item.low .goal-probability {
    background-color: var(--color-error-bg);
    color: var(--color-error);
}

/* Cash flow forecast chart container */
.forecast-chart-container {
    background: var(--bg-container);
    border-radius: var(--radius-md);
    padding: var(--space-5);
    margin-top: var(--space-5);
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border-tertiary);
}

/* Analysis section icons */
.analysis-section h2 {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 25px;
    color: var(--text-primary);
    font-size: 1.5em;
    font-weight: 600;
    padding-bottom: 10px;
    border-bottom: 2px solid var(--brand-blue);
}

/* Metric grid layout */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: var(--space-5);
    margin-bottom: 30px;
}

/* Attribution specific styling */
.attribution-metrics .metric-card {
    text-align: center;
}

.attribution-metrics .metric-value.positive {
    color: var(--color-success);
}

.attribution-metrics .metric-value.negative {
    color: var(--color-error);
}

/* Recommendations grid */
.recommendations-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: var(--space-4);
}

.recommendation-card {
    background: var(--bg-container);
    border: 1px solid var(--border-tertiary);
    border-radius: var(--radius-md);
    padding: var(--space-4);
    text-align: center;
    transition: var(--transition-base);
}

.recommendation-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
    border-color: var(--brand-blue-light);
}

.recommendation-count {
    font-size: 2em;
    font-weight: bold;
    color: var(--brand-blue);
    margin-bottom: 5px;
}

.recommendation-label {
    color: var(--text-secondary);
    font-size: 0.9em;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Loading states */
.loading-placeholder {
    background: linear-gradient(90deg, var(--bg-container-hover) 25%, var(--bg-container-inset) 50%, var(--bg-container-hover) 75%);
    background-size: 200% 100%;
    animation: loading-shimmer 1.5s infinite;
    border-radius: var(--radius-sm);
    height: 1.2em;
    margin: 5px 0;
}

@keyframes loading-shimmer {
    0% {
        background-position: -200% 0;
    }

    100% {
        background-position: 200% 0;
    }
}

/* Error states */
.error-state {
    color: var(--color-error);
    font-style: italic;
    opacity: 0.8;
}

/* Responsive adjustments for comprehensive analysis */
@media (max-width: 768px) {
    .analysis-section .metric-card {
        padding: var(--space-4);
        margin-bottom: var(--space-4);
    }

    .metrics-grid {
        grid-template-columns: 1fr;
        gap: var(--space-4);
    }

    .recommendations-grid {
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: var(--space-3);
    }

    .analysis-section .metric-value {
        font-size: 1.5em;
    }
}

/* ===== LAYOUT & NAVIGATION (New for Redesign) ===== */

.app-wrapper {
    display: flex;
    min-height: 100vh;
    background-color: var(--bg-container-inset);
    /* Lightest gray background for whole app */
}

/* Sidebar Styling */
.sidebar {
    width: 260px;
    background-color: var(--bg-container);
    border-right: 1px solid var(--border-secondary);
    display: flex;
    flex-direction: column;
    position: fixed;
    top: 0;
    bottom: 0;
    left: 0;
    z-index: 50;
    padding: var(--space-5) 0;
    transition: transform 0.3s ease;
}

.sidebar-header {
    padding: 0 var(--space-5) var(--space-6);
    display: flex;
    align-items: center;
    gap: var(--space-3);
}

.brand-logo {
    color: var(--text-primary);
    font-size: 1.25rem;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: var(--space-2);
    text-decoration: none;
}

.brand-logo i {
    color: var(--brand-gold);
    /* SunnRayy Brand Accent */
}

.sidebar-nav {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 0 var(--space-3);
    gap: var(--space-1);
}

.nav-item {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-3) var(--space-4);
    color: var(--text-secondary);
    border-radius: var(--radius-md);
    font-weight: 500;
    text-decoration: none;
    transition: var(--transition-base);
}

.nav-item:hover {
    background-color: var(--bg-container-hover);
    color: var(--text-primary);
}

.nav-item.active {
    background-color: var(--color-info-bg);
    /* Use brand light mix */
    color: var(--brand-blue);
    font-weight: 600;
}

.nav-item i {
    width: 20px;
    text-align: center;
}

/* Main Content Area */
.main-content {
    flex: 1;
    margin-left: 260px;
    /* Width of sidebar */
    display: flex;
    flex-direction: column;
    min-width: 0;
    /* Prevent overflow issues */
}

.top-bar {
    height: 64px;
    background-color: var(--bg-container);
    border-bottom: 1px solid var(--border-secondary);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 var(--space-6);
    position: sticky;
    top: 0;
    z-index: 40;
}

padding: var(--space-6);
margin: 0 auto;
width: 100%;
max-width: 1400px;
/* Cap width for large screens */
font-size: 0.925rem;
}

/* Mobile Toggle */
.mobile-menu-toggle {
    display: none;
    font-size: 1.5rem;
    background: none;
    border: none;
    cursor: pointer;
    color: var(--text-primary);
}

/* Responsive Layout */
@media (max-width: 1024px) {
    .sidebar {
        transform: translateX(-100%);
        box-shadow: var(--shadow-lg);
    }

    .sidebar.open {
        transform: translateX(0);
    }

    .main-content {
        margin-left: 0;
    }

    .mobile-menu-toggle {
        display: block;
    }

    .overlay {
        display: none;
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.5);
        z-index: 40;
    }

    .overlay.active {
        display: block;
    }
}

/* Layout Utility for Internal Sidebars (e.g. Logic Studio) */
.layout-sidebar-content {
    display: grid;
    grid-template-columns: 280px 1fr;
    gap: var(--space-6);
    align-items: start;
}

@media (max-width: 768px) {
    .layout-sidebar-content {
        grid-template-columns: 1fr;
    }
}

/* Tab Navigation Component */
.tabs-container {
    border-bottom: 1px solid var(--border-secondary);
    margin-bottom: var(--space-6);
}

.tabs-header {
    display: flex;
    gap: var(--space-4);
    overflow-x: auto;
    white-space: nowrap;
    scrollbar-width: none;
}

.tabs-header::-webkit-scrollbar {
    display: none;
}

.tab-btn {
    background: none;
    border: none;
    padding: var(--space-3) var(--space-4);
    font-weight: 500;
    color: var(--text-secondary);
    cursor: pointer;
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
    font-family: var(--font-sans);
    display: flex;
    align-items: center;
}

.tab-btn:hover {
    color: var(--text-primary);
    background-color: var(--bg-container-hover);
    border-radius: var(--radius-sm) var(--radius-sm) 0 0;
}

.tab-btn.active {
    color: var(--brand-blue);
    border-bottom-color: var(--brand-blue);
    font-weight: 600;
}

.tab-pane {
    animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(5px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* ===== COMPONENT LIBRARY ===== */

/* --- Cards --- */
.card {
    background: var(--bg-container);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border-tertiary);
    overflow: hidden;
    font-size: 0.875rem;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--space-4) var(--space-5);
    border-bottom: 1px solid var(--border-tertiary);
    background: var(--bg-container);
}

.card-header h3 {
    font-size: 1rem;
    font-weight: 600;
    margin: 0;
}

.card-body {
    padding: var(--space-5);
}

/* --- Metric Card (from macro) --- */
.metric-card {
    background: var(--bg-container);
    border-radius: var(--radius-lg);
    padding: var(--space-5);
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border-tertiary);
    transition: var(--transition-base);
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
    border-color: var(--brand-gold);
}

.metric-card h3 {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-secondary);
    margin-bottom: var(--space-2);
    display: flex;
    align-items: center;
    gap: var(--space-2);
}

.metric-card .metric-value {
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.2;
}

.metric-card .metric-trend {
    font-size: 0.875rem;
    margin-top: var(--space-2);
    display: flex;
    align-items: center;
    gap: var(--space-1);
}

.metric-card .metric-trend.positive {
    color: var(--color-success);
}

.metric-card .metric-trend.negative {
    color: var(--color-error);
}

.metric-card .metric-trend.neutral {
    color: var(--text-tertiary);
}

/* --- Buttons --- */
.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-2);
    padding: var(--space-2) var(--space-4);
    font-size: 0.875rem;
    font-weight: 500;
    font-family: var(--font-sans);
    border-radius: var(--radius-md);
    border: 1px solid transparent;
    cursor: pointer;
    transition: var(--transition-base);
    text-decoration: none;
    white-space: nowrap;
}

.btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.btn-sm {
    padding: var(--space-1) var(--space-3);
    font-size: 0.8125rem;
}

.btn-lg {
    padding: var(--space-3) var(--space-6);
    font-size: 1rem;
}

/* Primary Button */
.btn-primary {
    background: var(--brand-blue);
    color: var(--text-inverse);
    border-color: var(--brand-blue);
}

.btn-primary:hover {
    background: var(--brand-blue-dark);
    border-color: var(--brand-blue-dark);
}

/* Secondary Button */
.btn-secondary {
    background: var(--bg-container-inset);
    color: var(--text-primary);
    border-color: var(--border-primary);
}

.btn-secondary:hover {
    background: var(--bg-container-hover);
}

/* Success Button */
.btn-success {
    background: var(--color-success);
    color: var(--text-inverse);
    border-color: var(--color-success);
}

.btn-success:hover {
    filter: brightness(0.9);
}

/* Danger Button */
.btn-danger {
    background: var(--color-error);
    color: var(--text-inverse);
    border-color: var(--color-error);
}

.btn-danger:hover {
    filter: brightness(0.9);
}

/* Outline Button */
.btn-outline {
    background: transparent;
    color: var(--brand-blue);
    border-color: var(--brand-blue);
}

.btn-outline:hover {
    background: var(--color-info-bg);
}

/* Icon Button */
.btn-icon {
    background: none;
    border: none;
    color: var(--text-secondary);
    padding: var(--space-2);
    cursor: pointer;
    border-radius: var(--radius-md);
}

.btn-icon:hover {
    background: var(--bg-container-hover);
    color: var(--text-primary);
}

/* --- Badges --- */
.badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    font-size: 0.75rem;
    font-weight: 500;
    border-radius: var(--radius-full);
}

.badge-primary {
    background: var(--color-info-bg);
    color: var(--brand-blue);
}

.badge-success {
    background: var(--color-success-bg);
    color: var(--color-success);
}

.badge-warning {
    background: var(--color-warning-bg);
    color: #92400E;
    /* Amber-800 for contrast */
}

.badge-danger,
.badge-error {
    background: var(--color-error-bg);
    color: var(--color-error);
}

.badge-neutral {
    background: var(--bg-container-inset);
    color: var(--text-secondary);
}

/* --- Forms --- */
.form-label {
    display: block;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-secondary);
    margin-bottom: var(--space-1);
}

.form-input,
.form-select {
    display: block;
    width: 100%;
    padding: var(--space-2) var(--space-3);
    font-size: 0.9rem;
    font-family: var(--font-sans);
    color: var(--text-primary);
    background-color: var(--bg-container);
    border: 1px solid var(--border-secondary);
    border-radius: var(--radius-md);
    transition: border-color 0.2s, box-shadow 0.2s;
}

.form-input:focus,
.form-select:focus {
    outline: none;
    border-color: var(--brand-blue);
    box-shadow: 0 0 0 3px var(--color-info-bg);
}

.form-input::placeholder {
    color: var(--text-tertiary);
}

textarea.form-input {
    resize: vertical;
    min-height: 80px;
}

/* --- Tables --- */
width: 100%;
border-collapse: collapse;
font-size: 0.85rem;
}

.table th {
    text-align: left;
    padding: var(--space-3) var(--space-4);
    font-weight: 600;
    color: var(--text-secondary);
    background: var(--bg-container-inset);
    border-bottom: 1px solid var(--border-secondary);
    text-transform: uppercase;
    font-size: 0.75rem;
    letter-spacing: 0.05em;
}

.table td {
    padding: var(--space-3) var(--space-4);
    border-bottom: 1px solid var(--border-tertiary);
    color: var(--text-primary);
    vertical-align: middle;
}

.table tbody tr:hover {
    background: var(--bg-container-hover);
}

.table-responsive {
    overflow-x: auto;
}

/* --- Page Header (from macro) --- */
.page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: var(--space-6);
    padding-bottom: var(--space-4);
    border-bottom: 1px solid var(--border-tertiary);
}

.page-header h1 {
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
}

.page-header .subtitle {
    font-size: 0.95rem;
    color: var(--text-secondary);
    margin-top: var(--space-1);
}

.header-actions {
    display: flex;
    gap: var(--space-3);
}

/* --- Alerts --- */
.alert {
    padding: var(--space-4);
    border-radius: var(--radius-md);
    margin-bottom: var(--space-4);
}

.alert-info {
    background: var(--color-info-bg);
    border-left: 4px solid var(--color-info);
    color: var(--brand-blue-dark);
}

.alert-success {
    background: var(--color-success-bg);
    border-left: 4px solid var(--color-success);
    color: #065F46;
    /* Emerald-800 */
}

.alert-warning {
    background: var(--color-warning-bg);
    border-left: 4px solid var(--color-warning);
    color: #92400E;
    /* Amber-800 */
}

.alert-error {
    background: var(--color-error-bg);
    border-left: 4px solid var(--color-error);
    color: #991B1B;
    /* Red-800 */
}

/* --- Utility Classes --- */
.hidden {
    display: none !important;
}

.text-center {
    text-align: center;
}

.text-right {
    text-align: right;
}

.text-muted {
    color: var(--text-tertiary);
}

.text-primary {
    color: var(--brand-blue) !important;
}

.text-success {
    color: var(--color-success) !important;
}

.text-danger,
.text-red-500 {
    color: var(--color-error) !important;
}

.text-green-500 {
    color: var(--color-success) !important;
}

.text-blue-500 {
    color: var(--brand-blue) !important;
}

.font-bold {
    font-weight: 700;
}

.font-medium {
    font-weight: 500;
}

.mb-0 {
    margin-bottom: 0;
}

.mb-2 {
    margin-bottom: var(--space-2);
}

.mb-4 {
    margin-bottom: var(--space-4);
}

.mb-6 {
    margin-bottom: var(--space-6);
}

.mb-8 {
    margin-bottom: var(--space-8);
}

.mt-2 {
    margin-top: var(--space-2);
}

.mt-4 {
    margin-top: var(--space-4);
}

.mt-6 {
    margin-top: var(--space-6);
}

.mr-2 {
    margin-right: var(--space-2);
}

.ml-2 {
    margin-left: var(--space-2);
}

.p-0 {
    padding: 0;
}

.p-3 {
    padding: var(--space-3);
}

.p-4 {
    padding: var(--space-4);
}

.py-1 {
    padding-top: var(--space-1);
    padding-bottom: var(--space-1);
}

.py-4 {
    padding-top: var(--space-4);
    padding-bottom: var(--space-4);
}

.py-5 {
    padding-top: var(--space-5);
    padding-bottom: var(--space-5);
}

.flex {
    display: flex;
}

.items-center {
    align-items: center;
}

.justify-between {
    justify-content: space-between;
}

.justify-end {
    justify-content: flex-end;
}

.gap-2 {
    gap: var(--space-2);
}

.gap-3 {
    gap: var(--space-3);
}

.gap-4 {
    gap: var(--space-4);
}

.gap-6 {
    gap: var(--space-6);
}

.space-y-3>*+* {
    margin-top: var(--space-3);
}

.space-y-4>*+* {
    margin-top: var(--space-4);
}

.grid {
    display: grid;
}

.grid-cols-1 {
    grid-template-columns: repeat(1, 1fr);
}

.grid-cols-2 {
    grid-template-columns: repeat(2, 1fr);
}

.grid-cols-3 {
    grid-template-columns: repeat(3, 1fr);
}

@media (min-width: 768px) {
    .md\:grid-cols-2 {
        grid-template-columns: repeat(2, 1fr);
    }

    .md\:grid-cols-3 {
        grid-template-columns: repeat(3, 1fr);
    }

    .md\:col-span-2 {
        grid-column: span 2;
    }
}

.w-full {
    width: 100%;
}

.w-24 {
    width: 6rem;
}

.w-20 {
    width: 5rem;
}

.bg-primary-subtle {
    background: var(--color-info-bg);
}

.border-t {
    border-top: 1px solid var(--border-tertiary);
}

.border-l-4 {
    border-left: 4px solid;
}

.rounded {
    border-radius: var(--radius-md);
}

.shadow-sm {
    box-shadow: var(--shadow-sm);
}

.shadow-lg {
    box-shadow: var(--shadow-lg);
}

.divider {
    height: 1px;
    background: var(--border-tertiary);
    margin: var(--space-6) 0;
}

/* ===== EXTENDED UTILITY CLASSES FOR REPORTS ===== */

/* Padding Utilities */
.p-5 {
    padding: var(--space-5);
}

.p-6 {
    padding: var(--space-6);
}

.py-3 {
    padding-top: var(--space-3);
    padding-bottom: var(--space-3);
}

.px-4 {
    padding-left: var(--space-4);
    padding-right: var(--space-4);
}

/* Spacing Utilities */
.space-y-6>*+* {
    margin-top: var(--space-6);
}

/* Typography Colors */
.text-secondary {
    color: var(--text-secondary);
}

.text-gray-900 {
    color: var(--text-primary);
}

.text-gray-700 {
    color: var(--text-secondary);
}

.text-gray-500 {
    color: var(--text-tertiary);
}

/* Semantic Colors */
.text-emerald-600 {
    color: var(--color-success);
}

.text-rose-600 {
    color: var(--color-error);
}

.text-blue-600 {
    color: var(--brand-blue);
}

.text-purple-600 {
    color: #9333EA;
}

.text-sky-600 {
    color: #0284C7;
}

.text-indigo-600 {
    color: #4F46E5;
}

/* Background Colors */
.bg-gray-50 {
    background-color: var(--bg-container-hover);
}

.bg-gray-100 {
    background-color: var(--bg-container-inset);
}

.bg-yellow-50 {
    background-color: var(--color-warning-bg);
}

.bg-rose-50 {
    background-color: var(--color-error-bg);
}

/* Border Utilities */
.border-t-4 {
    border-top-width: 4px;
    border-top-style: solid;
}

.border-b {
    border-bottom: 1px solid var(--border-tertiary);
}

.border {
    border: 1px solid var(--border-tertiary);
}

.border-gray-100 {
    border-color: var(--border-tertiary);
}

.border-gray-200 {
    border-color: var(--border-secondary);
}

/* Semantic Border Colors */
.border-sky-500 {
    border-color: #0EA5E9;
}

.border-emerald-500 {
    border-color: #10B981;
}

.border-rose-500 {
    border-color: #F43F5E;
}

.border-purple-500 {
    border-color: #A855F7;
}

.border-indigo-500 {
    border-color: #6366F1;
}

.border-amber-500 {
    border-color: #F59E0B;
}

/* Divide Utilities */
.divide-y>*:not(:first-child) {
    border-top: 1px solid var(--border-tertiary);
}

.divide-gray-100>*:not(:first-child) {
    border-color: var(--border-tertiary);
}

/* Text Alignment */
.text-left {
    text-align: left;
}

.text-center {
    text-align: center;
}

.text-right {
    text-align: right;
}

/* Font Sizes */
.text-xs {
    font-size: 0.75rem;
    line-height: 1rem;
}

.text-sm {
    font-size: 0.875rem;
    line-height: 1.25rem;
}

.text-lg {
    font-size: 1.125rem;
    line-height: 1.75rem;
}

.text-2xl {
    font-size: 1.5rem;
    line-height: 2rem;
}

.text-3xl {
    font-size: 1.875rem;
    line-height: 2.25rem;
}

/* Font Weight */
.font-semibold {
    font-weight: 600;
}

/* Text Transform */
.uppercase {
    text-transform: uppercase;
}

.tracking-wider {
    letter-spacing: 0.05em;
}

/* Responsive Grid */
@media (min-width: 1024px) {
    .lg\:grid-cols-2 {
        grid-template-columns: repeat(2, 1fr);
    }

    .lg\:grid-cols-3 {
        grid-template-columns: repeat(3, 1fr);
    }

    .lg\:col-span-1 {
        grid-column: span 1;
    }

    .lg\:col-span-2 {
        grid-column: span 2;
    }
}

/* Table Enhancements */
.table-responsive {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}

/* Transitions */
.transition-colors {
    transition: color 0.15s ease, background-color 0.15s ease, border-color 0.15s ease;
}

.transition-transform {
    transition: transform 0.15s ease;
}

/* Hover States */
.hover\:bg-gray-50:hover {
    background-color: var(--bg-container-hover);
}

.hover\:text-gray-900:hover {
    color: var(--text-primary);
}

/* Height Utilities */
.h-full {
    height: 100%;
}

.h-96 {
    height: 24rem;
}

.relative {
    position: relative;
}

/* Badge Component */
.badge {
    display: inline-flex;
    align-items: center;
    padding: 0.25rem 0.75rem;
    font-size: 0.75rem;
    font-weight: 500;
    border-radius: var(--radius-full);
}

.badge-success {
    background-color: var(--color-success-bg);
    color: var(--color-success);
}

.badge-warning {
    background-color: var(--color-warning-bg);
    color: #92400E;
}

.badge-danger {
    background-color: var(--color-error-bg);
    color: var(--color-error);
}

.badge-secondary {
    background-color: var(--bg-container-inset);
    color: var(--text-secondary);
}

.badge-primary {
    background-color: var(--color-info-bg);
    color: var(--brand-blue);
}

/* Card Accent Borders */
.card.border-t-4 {
    border-top-width: 4px;
    border-top-style: solid;
}

/* Whitespace */
.whitespace-nowrap {
    white-space: nowrap;
}

/* ===== DASHBOARD COMPONENTS (SunnRayy Design) ===== */

/* --- Dashboard Header --- */
.dashboard-title {
    font-size: 1.25rem;
    font-weight: 400;
    color: var(--text-primary);
    margin: 0;
    line-height: 1.4;
}

.dashboard-title strong {
    font-weight: 600;
}

.dashboard-subtitle {
    font-size: 0.875rem;
    color: var(--text-tertiary);
    margin: 0;
    margin-top: 2px;
}

/* --- Hero Card: Net Worth Display --- */
.hero-card {
    background: linear-gradient(135deg, #FFFBF5 0%, #FFF8ED 50%, #FEFCE8 100%);
    border: 1px solid rgba(212, 175, 55, 0.15);
    border-radius: var(--radius-xl, 16px);
    padding: var(--space-6) var(--space-8);
    margin-bottom: var(--space-6);
    position: relative;
    overflow: hidden;
}

.hero-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--brand-gold) 0%, var(--brand-gold-light, #E8D48A) 100%);
}

.hero-card__label {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-tertiary);
    margin-bottom: var(--space-2);
}

.hero-card__value {
    font-size: 3rem;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.1;
    margin-bottom: var(--space-2);
}

.hero-card__change {
    font-size: 0.95rem;
    display: flex;
    align-items: center;
    gap: var(--space-2);
}

.hero-card__change.positive {
    color: var(--color-success);
}

.hero-card__change.negative {
    color: var(--color-error);
}

.hero-card__change i {
    font-size: 0.875rem;
}

/* --- Metric Card with Gold Accent --- */
.metric-card--accent {
    background: var(--bg-container);
    border-radius: var(--radius-lg);
    padding: var(--space-4) var(--space-5);
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border-tertiary);
    border-left: 4px solid var(--brand-gold);
    transition: var(--transition-base);
}

.metric-card--accent:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}

.metric-card--accent h3 {
    font-size: 0.8125rem;
    font-weight: 500;
    color: var(--text-tertiary);
    margin-bottom: var(--space-2);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.metric-card--accent .metric-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.2;
}

/* --- Activity List --- */
.activity-list {
    list-style: none;
    padding: 0;
    margin: 0;
}

.activity-item {
    display: flex;
    align-items: center;
    gap: var(--space-4);
    padding: var(--space-4) 0;
    border-bottom: 1px solid var(--border-tertiary);
}

.activity-item:last-child {
    border-bottom: none;
}

.activity-icon {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    font-size: 1rem;
}

.activity-icon.buy {
    background: #DBEAFE;
    color: #2563EB;
}

.activity-icon.sell {
    background: #FEE2E2;
    color: #DC2626;
}

.activity-icon.deposit {
    background: #D1FAE5;
    color: #059669;
}

.activity-icon.withdrawal {
    background: #FEE2E2;
    color: #DC2626;
}

.activity-icon.dividend {
    background: #FEF3C7;
    color: #D97706;
}

.activity-icon.transfer {
    background: #E0E7FF;
    color: #4F46E5;
}

.activity-details {
    flex: 1;
    min-width: 0;
}

.activity-title {
    font-weight: 600;
    color: var(--text-primary);
    font-size: 0.9375rem;
    margin-bottom: 2px;
}

.activity-subtitle {
    font-size: 0.8125rem;
    color: var(--text-tertiary);
}

.activity-amount {
    font-weight: 600;
    font-size: 0.9375rem;
    text-align: right;
}

.activity-amount.positive {
    color: var(--color-success);
}

.activity-amount.negative {
    color: var(--text-primary);
}

.activity-date {
    font-size: 0.75rem;
    color: var(--text-tertiary);
    display: block;
    text-align: right;
    margin-top: 2px;
}

/* --- Dashboard Grid Layout --- */
.dashboard-metrics-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: var(--space-4);
    margin-bottom: var(--space-6);
}

@media (max-width: 1024px) {
    .dashboard-metrics-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 640px) {
    .dashboard-metrics-grid {
        grid-template-columns: 1fr;
    }

    .hero-card__value {
        font-size: 2rem;
    }
}

/* --- Card Header Uppercase Style --- */
.card-header h3.uppercase {
    text-transform: uppercase;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    color: var(--text-tertiary);
}

/* --- Utility Classes --- */
.letter-spacing-1 {
    letter-spacing: 0.05em;
}

.letter-spacing-2 {
    letter-spacing: 0.1em;
}

.glass-card {
    background: var(--bg-container);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border-tertiary);
    overflow: hidden;
    padding: var(--space-5);
    transition: var(--transition-base);
}

.glass-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
    border-color: var(--brand-blue-light);
}```

## File: src/web_app/static/css/wizard.css
```css
:root {
    /* Wizard Specific Variables mapping to SunnRayy System */
    --wizard-bg: var(--bg-surface);
    --wizard-surface: var(--bg-container);
    --wizard-border: var(--border-secondary);
    --wizard-primary: var(--brand-blue);
    --wizard-primary-hover: var(--brand-blue-dark);
    --wizard-primary-light: #EFF6FF;
    /* Blue-50 equivalent */
    --wizard-success: var(--color-success);
    --wizard-success-bg: var(--color-success-bg);
    --wizard-error: var(--color-error);
    --wizard-error-bg: var(--color-error-bg);
    --wizard-warning: var(--color-warning);
    --wizard-text-main: var(--text-primary);
    --wizard-text-sub: var(--text-secondary);
    --wizard-gold: var(--brand-gold);
    --wizard-gold-light: #FEFCE8;
    /* Yellow-50 */
    --wizard-gold-border: #FDE047;
    /* Yellow-300 */
}

/* --- Container & Layout --- */
.wizard-container {
    max-width: 1200px;
    margin: 40px auto;
    padding: 0 var(--space-4);
    font-family: var(--font-sans);
    color: var(--wizard-text-main);
}

.wizard-panel {
    background: var(--wizard-surface);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--wizard-border);
    padding: 40px;
    margin-bottom: var(--space-8);
}

/* --- Step 1: Selection Grid --- */
.wizard-header {
    text-align: center;
    margin-bottom: var(--space-10);
}

.wizard-title-lg {
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: var(--space-2);
    letter-spacing: -0.02em;
}

.wizard-subtitle {
    color: var(--wizard-text-sub);
    font-size: 1.125rem;
}

.option-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-6);
}

@media (max-width: 768px) {
    .option-grid {
        grid-template-columns: 1fr;
    }
}

.option-card {
    display: flex;
    align-items: flex-start;
    padding: var(--space-6);
    border-radius: var(--radius-lg);
    border: 1px solid var(--wizard-border);
    background: var(--wizard-surface);
    cursor: pointer;
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
}

.option-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-md);
    border-color: var(--wizard-primary);
}

.option-card.pending {
    background: var(--wizard-gold-light);
    border-color: var(--wizard-gold-border);
}

.option-card.pending:hover {
    box-shadow: 0 10px 15px -3px rgba(234, 179, 8, 0.1);
    /* Gold shadow */
}

.card-icon-wrapper {
    width: 48px;
    height: 48px;
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: var(--space-5);
    font-size: 1.5rem;
    flex-shrink: 0;
}

.option-card.standard .card-icon-wrapper {
    background: var(--wizard-primary-light);
    color: var(--wizard-primary);
}

.option-card.pending .card-icon-wrapper {
    background: #FEF9C3;
    /* Yellow-100 */
    color: #D97706;
    /* Yellow-600 */
}

.card-content h3 {
    font-size: 1.125rem;
    font-weight: 700;
    margin-bottom: 4px;
}

.card-content p {
    font-size: 0.875rem;
    color: var(--wizard-text-sub);
    line-height: 1.5;
}

.pending-badge {
    position: absolute;
    top: 12px;
    right: 12px;
    background: var(--wizard-gold);
    color: white;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 999px;
    text-transform: uppercase;
}

/* --- Progress Line (Timeline) --- */
.progress-container {
    position: relative;
    margin: 0 auto 50px auto;
    max-width: 800px;
    padding: 0 var(--space-4);
}

.progress-line-bg {
    position: absolute;
    top: 20px;
    /* Center of a 40px circle */
    left: 0;
    width: 100%;
    height: 2px;
    background: var(--wizard-border);
    z-index: 0;
}

.progress-line-active {
    position: absolute;
    top: 20px;
    left: 0;
    height: 2px;
    background: var(--wizard-primary);
    z-index: 0;
    transition: width 0.3s ease;
}

.progress-steps {
    display: flex;
    justify-content: space-between;
    position: relative;
    z-index: 1;
}

.progress-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    cursor: default;
}

.step-circle {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: var(--wizard-surface);
    border: 2px solid var(--wizard-border);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    color: var(--wizard-text-sub);
    margin-bottom: 8px;
    transition: all 0.3s;
}

.progress-step.active .step-circle {
    background: var(--wizard-primary);
    border-color: var(--wizard-primary);
    color: white;
    box-shadow: 0 0 0 4px var(--wizard-primary-light);
}

.progress-step.completed .step-circle {
    background: var(--wizard-primary);
    border-color: var(--wizard-primary);
    color: white;
}

.step-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--wizard-text-sub);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.progress-step.active .step-label {
    color: var(--wizard-primary);
}

/* --- Toggle Switch --- */
.mode-toggle {
    display: inline-flex;
    background: var(--bg-container-inset);
    padding: 4px;
    border-radius: var(--radius-md);
    margin-bottom: var(--space-6);
}

.toggle-btn {
    padding: 8px 24px;
    border-radius: 6px;
    border: none;
    background: transparent;
    color: var(--wizard-text-sub);
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
}

.toggle-btn.active {
    background: var(--wizard-surface);
    color: var(--wizard-primary);
    box-shadow: var(--shadow-sm);
    font-weight: 600;
}

/* --- Dropzone --- */
.upload-zone {
    border: 2px dashed var(--brand-blue-light);
    border-radius: var(--radius-lg);
    background: linear-gradient(180deg, var(--wizard-primary-light) 0%, rgba(255, 255, 255, 0) 100%);
    padding: 60px 20px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
}

.upload-zone:hover {
    border-color: var(--wizard-primary);
    background: aliceblue;
    /* slight tint */
}

/* --- Custom Table for Validation --- */
.table-validation {
    width: 100%;
    border-collapse: collapse;
}

.table-validation th {
    background: var(--bg-container-inset);
    padding: 12px 16px;
    text-align: left;
    font-weight: 600;
    font-size: 0.75rem;
    text-transform: uppercase;
    color: var(--wizard-text-sub);
    border-bottom: 1px solid var(--wizard-border);
}

.table-validation td {
    padding: 12px 16px;
    border-bottom: 1px solid var(--wizard-border);
    font-size: 0.875rem;
}

.table-validation tr.row-error {
    background-color: var(--wizard-error-bg);
}

.table-validation tr.row-error td {
    border-color: #FECACA;
    /* Red-200 */
}

.error-cell {
    position: relative;
    font-family: var(--font-mono);
    color: var(--wizard-error);
    font-weight: 600;
    text-decoration: underline;
    text-decoration-style: wavy;
}

.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px;
    border-radius: 99px;
    font-size: 0.75rem;
    font-weight: 600;
}

.status-valid {
    background: var(--wizard-success-bg);
    color: var(--wizard-success);
}

.status-error {
    background: var(--wizard-error-bg);
    color: var(--wizard-error);
}

/* --- Buttons --- */
.btn-wizard-next {
    background: var(--wizard-primary);
    color: white;
    padding: 10px 24px;
    border-radius: var(--radius-md);
    font-weight: 600;
    border: none;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    transition: all 0.2s;
}

.btn-wizard-next:hover {
    background: var(--wizard-primary-hover);
    transform: translateY(-1px);
    box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.4);
}

.btn-wizard-next:disabled {
    background: var(--text-tertiary);
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
}

.btn-wizard-back {
    background: transparent;
    color: var(--wizard-text-sub);
    border: 1px solid var(--wizard-border);
    padding: 10px 20px;
    border-radius: var(--radius-md);
    font-weight: 500;
    cursor: pointer;
}

.btn-wizard-back:hover {
    background: var(--bg-container-inset);
    color: var(--wizard-text-main);
}

/* --- Magic Map Button --- */
.btn-magic-map {
    background: #FEF3C7;
    color: #92400E;
    border: 1px solid #FDE68A;
    padding: 6px 12px;
    border-radius: 99px;
    font-size: 0.75rem;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    cursor: pointer;
    transition: all 0.2s;
}

.btn-magic-map:hover {
    background: #FDE68A;
}

/* --- Animations (Tailwind-like utilities) --- */
@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

.animate-spin {
    animation: spin 1s linear infinite;
}

@keyframes pulse {
    50% {
        opacity: .5;
    }
}

.animate-pulse {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes bounce {

    0%,
    100% {
        transform: translateY(-25%);
        animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
    }

    50% {
        transform: none;
        animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
    }
}

.animate-bounce {
    animation: bounce 1s infinite;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.animate-fade-in {
    animation: fadeIn 0.5s ease-out forwards;
}

/* Utilities used in Step 5 not present elsewhere */
.bg-slate-50 {
    background-color: #f8fafc;
}

.bg-slate-900 {
    background-color: #0f172a;
}

.text-slate-900 {
    color: #0f172a;
}

.text-slate-500 {
    color: #64748b;
}

.text-slate-400 {
    color: #94a3b8;
}

.border-slate-100 {
    border-color: #f1f5f9;
}

.border-slate-200 {
    border-color: #e2e8f0;
}

.text-emerald-500 {
    color: #10b981;
}

.bg-emerald-500 {
    background-color: #10b981;
}

.text-emerald-50 {
    color: #ecfdf5;
}

.rounded-3xl {
    border-radius: 1.5rem;
}

.rounded-2xl {
    border-radius: 1rem;
}

.rounded-xl {
    border-radius: 0.75rem;
}

.rounded-full {
    border-radius: 9999px;
}

.shadow-2xl {
    box-shadow: 0 25px 50px -12px rgb(0 0 0 / 0.25);
}

.shadow-xl {
    box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
}

.relative {
    position: relative;
}

.absolute {
    position: absolute;
}

.inset-0 {
    top: 0;
    right: 0;
    bottom: 0;
    left: 0;
}

.flex-col {
    flex-direction: column;
}

.items-center {
    align-items: center;
}

.justify-center {
    justify-content: center;
}

.space-y-8> :not([hidden])~ :not([hidden]) {
    --tw-space-y-reverse: 0;
    margin-top: calc(2rem * calc(1 - var(--tw-space-y-reverse)));
    margin-bottom: calc(2rem * var(--tw-space-y-reverse));
}

.space-y-2> :not([hidden])~ :not([hidden]) {
    --tw-space-y-reverse: 0;
    margin-top: calc(0.5rem * calc(1 - var(--tw-space-y-reverse)));
    margin-bottom: calc(0.5rem * var(--tw-space-y-reverse));
}

.space-y-10> :not([hidden])~ :not([hidden]) {
    --tw-space-y-reverse: 0;
    margin-top: calc(2.5rem * calc(1 - var(--tw-space-y-reverse)));
    margin-bottom: calc(2.5rem * var(--tw-space-y-reverse));
}

.gap-4 {
    gap: 1rem;
}

.gap-3 {
    gap: 0.75rem;
}

.grid {
    display: grid;
}

.grid-cols-2 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
}

.w-full {
    width: 100%;
}

.h-24 {
    height: 6rem;
}

.w-24 {
    width: 6rem;
}

.py-20 {
    padding-top: 5rem;
    padding-bottom: 5rem;
}

.p-10 {
    padding: 2.5rem;
}

.p-4 {
    padding: 1rem;
}

.blur-3xl {
    filter: blur(64px);
}

.blur-2xl {
    filter: blur(40px);
}

.overflow-hidden {
    overflow: hidden;
}

.font-black {
    font-weight: 900;
}

.font-bold {
    font-weight: 700;
}

.font-mono {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

.uppercase {
    text-transform: uppercase;
}

.tracking-widest {
    letter-spacing: 0.1em;
}

.opacity-90 {
    opacity: 0.9;
}

.text-2xl {
    font-size: 1.5rem;
    line-height: 2rem;
}

.text-3xl {
    font-size: 1.875rem;
    line-height: 2.25rem;
}

.text-xl {
    font-size: 1.25rem;
    line-height: 1.75rem;
}

.text-4xl {
    font-size: 2.25rem;
    line-height: 2.5rem;
}

.text-sm {
    font-size: 0.875rem;
    line-height: 1.25rem;
}

.text-xs {
    font-size: 0.75rem;
    line-height: 1rem;
}

.border-t-blue-600 {
    border-top-color: #2563eb;
}

.text-blue-600 {
    color: #2563eb;
}

.border-4 {
    border-width: 4px;
}

.-top-10 {
    top: -2.5rem;
}

.-right-10 {
    right: -2.5rem;
}

.-bottom-10 {
    bottom: -2.5rem;
}

.-left-10 {
    left: -2.5rem;
}

.w-40 {
    width: 10rem;
}

.h-40 {
    height: 10rem;
}

.bg-white\/10 {
    background-color: rgba(255, 255, 255, 0.1);
}

.bg-black\/10 {
    background-color: rgba(0, 0, 0, 0.1);
}```

