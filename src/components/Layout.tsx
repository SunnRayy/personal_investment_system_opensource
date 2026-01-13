import React, { useState } from 'react';
import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom';
import {
    LayoutDashboard,
    Wallet,
    Database,
    Settings,
    LogOut,
    TrendingUp,
    User,
    Compass,
    DollarSign,
    BarChart3,
    Plug,
    Heart
} from 'lucide-react';
import clsx from 'clsx';
import { twMerge } from 'tailwind-merge';
import { useAuth } from '../contexts/AuthContext';

function cn(...inputs: (string | undefined | null | false)[]) {
    return twMerge(clsx(inputs));
}

const Layout: React.FC = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { user, logout, isLoading } = useAuth();
    const [isLoggingOut, setIsLoggingOut] = useState(false);

    const mainNavItems = [
        { label: 'Dashboard', icon: LayoutDashboard, path: '/' },
        { label: 'Data Workbench', icon: Database, path: '/workbench' },
        { label: 'Logic Studio', icon: Database, path: '/logic-studio' },
    ];

    const analysisNavItems = [
        { label: 'Portfolio', icon: Wallet, path: '/portfolio' },
        { label: 'Cash Flow', icon: DollarSign, path: '/cashflow' },
        { label: 'Compass', icon: Compass, path: '/compass' },
        { label: 'Performance', icon: TrendingUp, path: '/performance' },
        { label: 'Simulation', icon: BarChart3, path: '/simulation' },
    ];

    const handleLogout = async () => {
        setIsLoggingOut(true);
        await logout();
        navigate('/login');
    };

    const renderNavItem = (item: { label: string; icon: any; path: string }) => {
        const Icon = item.icon;
        const isActive = location.pathname === item.path;
        return (
            <li key={item.path}>
                <NavLink
                    to={item.path}
                    className={({ isActive }) => cn(
                        "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
                        isActive
                            ? "bg-blue-50 text-blue-600 shadow-sm ring-1 ring-blue-200"
                            : "text-gray-500 hover:bg-gray-50 hover:text-gray-900"
                    )}
                >
                    <Icon size={20} strokeWidth={isActive ? 2.5 : 2} />
                    {item.label}
                </NavLink>
            </li>
        );
    };

    return (
        <div className="flex h-screen bg-gray-50 font-sans text-gray-900">
            {/* Sidebar */}
            <aside className="fixed left-0 top-0 z-50 flex h-full w-64 flex-col border-r border-gray-200 bg-white shadow-sm transition-transform duration-300">
                <div className="flex items-center gap-3 p-6">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white shadow-md shadow-blue-200">
                        <TrendingUp size={24} strokeWidth={2.5} />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold tracking-tight text-gray-900">WealthOS</h1>
                        <p className="text-[10px] font-semibold uppercase tracking-wider text-gray-400">Personal Edition</p>
                    </div>
                </div>

                <nav className="flex-1 space-y-6 overflow-y-auto px-4 py-4">
                    {/* Main Section */}
                    <div>
                        <h3 className="mb-3 px-3 text-xs font-bold uppercase tracking-widest text-gray-400">
                            Main
                        </h3>
                        <ul className="space-y-1">
                            {mainNavItems.map(renderNavItem)}
                        </ul>
                    </div>

                    {/* Analysis Section */}
                    <div>
                        <h3 className="mb-3 px-3 text-xs font-bold uppercase tracking-widest text-gray-400">
                            Analysis
                        </h3>
                        <ul className="space-y-1">
                            {analysisNavItems.map(renderNavItem)}
                        </ul>
                    </div>

                    {/* System Section */}
                    <div>
                        <h3 className="mb-3 px-3 text-xs font-bold uppercase tracking-widest text-gray-400">
                            System
                        </h3>
                        <ul className="space-y-1">
                            <li>
                                <button className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-gray-500 transition-all duration-200 hover:bg-gray-50 hover:text-gray-900">
                                    <Plug size={20} />
                                    Integrations
                                </button>
                            </li>
                            <li>
                                <button className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-gray-500 transition-all duration-200 hover:bg-gray-50 hover:text-gray-900">
                                    <Heart size={20} />
                                    Health
                                </button>
                            </li>
                        </ul>
                    </div>
                </nav>

                {/* User Profile Section */}
                <div className="border-t border-gray-100 p-4">
                    <div className="flex items-center gap-3 rounded-xl bg-gray-50 p-3 border border-gray-100">
                        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-sm">
                            <User size={18} />
                        </div>
                        <div className="flex-1 overflow-hidden">
                            <p className="truncate text-xs font-bold text-gray-900">
                                {user?.username || 'User'}
                            </p>
                            <p className="truncate text-[10px] font-medium text-gray-500">Pro Plan</p>
                        </div>
                        <button
                            onClick={handleLogout}
                            disabled={isLoggingOut || isLoading}
                            className="text-gray-400 hover:text-red-500 transition-colors disabled:opacity-50"
                            title="Logout"
                        >
                            {isLoggingOut ? (
                                <div className="h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-gray-600"></div>
                            ) : (
                                <LogOut size={16} />
                            )}
                        </button>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="ml-64 min-h-screen w-full bg-gray-50">
                <Outlet />
            </main>
        </div>
    );
};

export default Layout;
