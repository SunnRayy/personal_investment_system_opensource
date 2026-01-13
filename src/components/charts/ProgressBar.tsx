/**
 * Progress Bar Component
 * Used for goal probability visualization
 */

import React from 'react';

interface GoalProgress {
    name: string;
    description?: string;
    probability: number;
    target?: string;
}

interface ProgressBarProps {
    goal: GoalProgress;
}

const ProgressBar: React.FC<ProgressBarProps> = ({ goal }) => {
    const getStatusColor = (prob: number) => {
        if (prob >= 90) return { bg: 'bg-emerald-500', text: 'text-emerald-600', badge: 'ON TRACK' };
        if (prob >= 75) return { bg: 'bg-amber-500', text: 'text-amber-600', badge: 'MONITOR' };
        return { bg: 'bg-red-500', text: 'text-red-600', badge: 'AT RISK' };
    };

    const status = getStatusColor(goal.probability);

    return (
        <div className="rounded-xl border border-slate-200 bg-white p-5">
            <div className="flex items-start justify-between mb-3">
                <div>
                    <h4 className="font-semibold text-slate-900">{goal.name}</h4>
                    {goal.description && (
                        <p className="text-sm text-slate-500">{goal.description}</p>
                    )}
                </div>
                <span
                    className={`px-2 py-1 text-xs font-bold rounded ${status.badge === 'ON TRACK'
                            ? 'bg-emerald-100 text-emerald-700'
                            : status.badge === 'MONITOR'
                                ? 'bg-amber-100 text-amber-700'
                                : 'bg-red-100 text-red-700'
                        }`}
                >
                    {status.badge}
                </span>
            </div>

            <div className="flex items-center gap-4">
                <div className="flex-1">
                    <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
                        <div
                            className={`h-full ${status.bg} rounded-full transition-all duration-500`}
                            style={{ width: `${Math.min(goal.probability, 100)}%` }}
                        />
                    </div>
                </div>
                <span className={`text-2xl font-bold ${status.text}`}>
                    {goal.probability}%
                </span>
            </div>

            {goal.target && (
                <p className="mt-2 text-xs text-slate-400">Target: {goal.target}</p>
            )}
        </div>
    );
};

export default ProgressBar;
