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
