/**
 * Simulation Report Page
 * Monte Carlo projection and goal probability analysis
 */

import React, { useState } from 'react';
import { Play, Download, Share2, Target, Home, Briefcase } from 'lucide-react';
import { useSimulationMutation } from '../../hooks/useReports';
import AreaWithConfidence from '../../components/charts/AreaWithConfidence';
import ProgressBar from '../../components/charts/ProgressBar';

interface SimulationParams {
    initial_value: number;
    annual_contribution: number;
    years: number;
    expected_return: number;
    volatility: number;
    inflation: number;
}

const Simulation: React.FC = () => {
    const [params, setParams] = useState<SimulationParams>({
        initial_value: 5000000,
        annual_contribution: 200000,
        years: 20,
        expected_return: 8.5,
        volatility: 15,
        inflation: 2.5,
    });

    const [lastRun, setLastRun] = useState<string | null>(null);

    const { mutate: runSimulation, data: simResults, isPending } = useSimulationMutation();

    // Generate demo projection data
    const projectionData = React.useMemo(() => {
        const data = [];
        let p5 = params.initial_value;
        let p50 = params.initial_value;
        let p95 = params.initial_value;

        const currentYear = new Date().getFullYear();

        for (let i = 0; i <= params.years; i++) {
            if (i > 0) {
                // Conservative (P5): lower growth
                p5 = p5 * (1 + (params.expected_return - params.volatility * 1.5) / 100) + params.annual_contribution;
                // Median (P50): expected growth
                p50 = p50 * (1 + params.expected_return / 100) + params.annual_contribution;
                // Optimistic (P95): higher growth
                p95 = p95 * (1 + (params.expected_return + params.volatility * 0.8) / 100) + params.annual_contribution;
            }
            data.push({
                year: currentYear + i,
                p5: Math.max(0, p5),
                p50: p50,
                p95: p95,
            });
        }
        return data;
    }, [params]);

    // Demo goals
    const goals = [
        {
            name: 'Retirement at 60',
            description: 'Age 60 • $150k/yr expense',
            probability: 98,
            target: '$4.5M by 2040',
            icon: Target,
        },
        {
            name: 'Lake House Purchase',
            description: 'Year 2030 • $1.2M cost',
            probability: 74,
            target: '$1.2M by 2030',
            icon: Home,
        },
    ];

    const handleRunSimulation = () => {
        setLastRun('Just now');
        runSimulation({
            initial_value: params.initial_value,
            annual_contribution: params.annual_contribution,
            years: params.years,
            target_return: params.expected_return,
            volatility: params.volatility,
            inflation_rate: params.inflation,
            iterations: 10000,
        });
    };

    return (
        <div className="flex h-[calc(100vh-64px)]">
            {/* Sidebar - Parameters */}
            <aside className="w-80 border-r border-gray-200 bg-white p-6 overflow-y-auto">
                <h2 className="text-lg font-bold text-gray-900 mb-6">Parameters</h2>

                <div className="space-y-5">
                    {/* Initial Value */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Initial Portfolio Value
                        </label>
                        <div className="relative">
                            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">$</span>
                            <input
                                type="text"
                                value={params.initial_value.toLocaleString()}
                                onChange={(e) => setParams({ ...params, initial_value: parseInt(e.target.value.replace(/,/g, '')) || 0 })}
                                className="w-full rounded-lg border border-gray-200 bg-gray-50 pl-8 pr-4 py-3 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                            />
                        </div>
                    </div>

                    {/* Annual Contribution */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Annual Contribution
                        </label>
                        <div className="relative">
                            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">$</span>
                            <input
                                type="text"
                                value={params.annual_contribution.toLocaleString()}
                                onChange={(e) => setParams({ ...params, annual_contribution: parseInt(e.target.value.replace(/,/g, '')) || 0 })}
                                className="w-full rounded-lg border border-gray-200 bg-gray-50 pl-8 pr-4 py-3 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                            />
                        </div>
                    </div>

                    {/* Time Horizon */}
                    <div>
                        <div className="flex justify-between mb-2">
                            <label className="text-sm font-medium text-gray-700">Time Horizon</label>
                            <span className="text-sm font-bold text-blue-600">{params.years} Years</span>
                        </div>
                        <input
                            type="range"
                            min="5"
                            max="50"
                            value={params.years}
                            onChange={(e) => setParams({ ...params, years: parseInt(e.target.value) })}
                            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                        />
                        <div className="flex justify-between text-xs text-gray-400 mt-1">
                            <span>5y</span>
                            <span>50y</span>
                        </div>
                    </div>

                    {/* Target Return Rate */}
                    <div>
                        <div className="flex justify-between mb-2">
                            <label className="text-sm font-medium text-gray-700">Target Return Rate</label>
                            <span className="text-sm font-bold text-blue-600">↗ {params.expected_return}%</span>
                        </div>
                        <input
                            type="range"
                            min="1"
                            max="15"
                            step="0.5"
                            value={params.expected_return}
                            onChange={(e) => setParams({ ...params, expected_return: parseFloat(e.target.value) })}
                            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                        />
                    </div>

                    {/* Inflation Rate */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Inflation Rate (%)
                        </label>
                        <input
                            type="number"
                            value={params.inflation}
                            onChange={(e) => setParams({ ...params, inflation: parseFloat(e.target.value) || 0 })}
                            step="0.1"
                            className="w-full rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                        />
                    </div>

                    {/* Run Button */}
                    <button
                        onClick={handleRunSimulation}
                        disabled={isPending}
                        className="w-full flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-4 text-sm font-semibold text-white shadow-lg shadow-blue-200 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                        {isPending ? (
                            <>
                                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"></div>
                                Running...
                            </>
                        ) : (
                            <>
                                <Play size={18} />
                                Run Simulation
                            </>
                        )}
                    </button>

                    {lastRun && (
                        <p className="text-center text-xs text-gray-400">Last run: {lastRun}</p>
                    )}
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto p-6 lg:p-8 bg-gray-50">
                {/* Header */}
                <div className="mb-6 flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">Wealth Projection</h1>
                        <p className="text-sm text-gray-500">Monte Carlo simulation based on 10,000 scenarios</p>
                    </div>
                    <div className="flex gap-3">
                        <button className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
                            <Download size={16} />
                            Export Report
                        </button>
                        <button className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
                            <Share2 size={16} />
                            Share
                        </button>
                    </div>
                </div>

                {/* Projection Chart */}
                <div className="mb-6 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                    <div className="mb-4 flex items-center justify-between">
                        <div>
                            <h3 className="font-semibold text-gray-900">Projected Net Worth</h3>
                            <span className="text-sm text-gray-500">(Inflation Adjusted)</span>
                        </div>
                        <div className="flex gap-4 text-sm">
                            <span className="flex items-center gap-2">
                                <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
                                Optimistic (P95)
                            </span>
                            <span className="flex items-center gap-2">
                                <span className="h-2 w-2 rounded-full bg-blue-500"></span>
                                Median (P50)
                            </span>
                            <span className="flex items-center gap-2">
                                <span className="h-2 w-2 rounded-full bg-gray-400"></span>
                                Conservative (P5)
                            </span>
                        </div>
                    </div>
                    <AreaWithConfidence data={projectionData} height={350} />
                </div>

                {/* Goal Probability */}
                <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                    <h3 className="mb-6 font-semibold text-gray-900">Goal Probability Analysis</h3>
                    <div className="grid gap-4 lg:grid-cols-2">
                        {goals.map((goal) => (
                            <ProgressBar key={goal.name} goal={goal} />
                        ))}
                    </div>
                </div>
            </main>
        </div>
    );
};

export default Simulation;
