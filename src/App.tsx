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
