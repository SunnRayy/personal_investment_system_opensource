/**
 * GlassTooltip - Glassmorphism-styled chart tooltip component
 * 
 * Provides a consistent, modern tooltip style across all charts
 * with frosted glass effect, backdrop blur, and subtle shadow.
 */

import React from 'react';

interface GlassTooltipProps {
    active?: boolean;
    payload?: Array<{
        value: number;
        name: string;
        color?: string;
        dataKey?: string;
    }>;
    label?: string;
    currency?: string;
    formatter?: (value: number, name: string) => [string, string];
}

/**
 * Custom glassmorphism tooltip for Recharts
 */
export const GlassTooltip: React.FC<GlassTooltipProps> = ({
    active,
    payload,
    label,
    currency = 'CNY',
    formatter,
}) => {
    if (!active || !payload || payload.length === 0) return null;

    const formatValue = (value: number, name: string): [string, string] => {
        if (formatter) return formatter(value, name);

        const symbol = currency === 'CNY' ? '¥' : '$';
        return [`${symbol}${value.toLocaleString()}`, name];
    };

    return (
        <div className="rounded-xl border border-white/20 bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl shadow-xl px-4 py-3 min-w-[140px]">
            {label && (
                <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wider">
                    {label}
                </p>
            )}
            <div className="space-y-1.5">
                {payload.map((entry, index) => {
                    const [formattedValue, formattedName] = formatValue(entry.value, entry.name);
                    return (
                        <div key={index} className="flex items-center justify-between gap-4">
                            <div className="flex items-center gap-2">
                                {entry.color && (
                                    <span
                                        className="w-2.5 h-2.5 rounded-full"
                                        style={{ backgroundColor: entry.color }}
                                    />
                                )}
                                <span className="text-xs font-medium text-gray-600 dark:text-gray-300">
                                    {formattedName}
                                </span>
                            </div>
                            <span className="text-sm font-bold text-gray-900 dark:text-white">
                                {formattedValue}
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

/**
 * Tooltip style object for Recharts (use when GlassTooltip isn't needed)
 */
export const glassTooltipStyle = {
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
    backdropFilter: 'blur(12px)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '12px',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
    padding: '12px 16px',
};

/**
 * Dark mode tooltip style
 */
export const glassDarkTooltipStyle = {
    backgroundColor: 'rgba(30, 41, 59, 0.9)',
    backdropFilter: 'blur(12px)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '12px',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
    padding: '12px 16px',
    color: '#f8fafc',
};

export default GlassTooltip;
