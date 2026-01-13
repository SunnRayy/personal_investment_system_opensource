import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import DataWorkbench from './pages/DataWorkbench';
import Portfolio from './pages/Portfolio';
import Login from './pages/Login';
import { Compass, CashFlow, Simulation, LifetimePerformance } from './pages/reports';
import LogicStudio from './pages/LogicStudio';

// Create a client with default options
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 5 * 60 * 1000, // 5 minutes
            gcTime: 30 * 60 * 1000,   // 30 minutes
            retry: 2,
            refetchOnWindowFocus: false,
        },
    },
});

const App: React.FC = () => {
    return (
        <AuthProvider>
            <QueryClientProvider client={queryClient}>
                <BrowserRouter>
                    <Routes>
                        {/* Public route - Login */}
                        <Route path="/login" element={<Login />} />

                        {/* Protected routes - require authentication */}
                        <Route element={
                            <ProtectedRoute>
                                <Layout />
                            </ProtectedRoute>
                        }>
                            <Route path="/" element={<Dashboard />} />
                            <Route path="/workbench" element={<DataWorkbench />} />
                            <Route path="/portfolio" element={<Portfolio />} />

                            {/* Report Pages */}
                            <Route path="/compass" element={<Compass />} />
                            <Route path="/cashflow" element={<CashFlow />} />
                            <Route path="/simulation" element={<Simulation />} />
                            <Route path="/performance" element={<LifetimePerformance />} />

                            {/* Logic Studio */}
                            <Route path="/logic-studio" element={<LogicStudio />} />

                            {/* Catch-all */}
                            <Route path="*" element={<Navigate to="/" replace />} />
                        </Route>
                    </Routes>
                </BrowserRouter>
            </QueryClientProvider>
        </AuthProvider>
    );
};

export default App;
