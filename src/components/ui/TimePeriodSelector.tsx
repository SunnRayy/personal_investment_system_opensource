/**
 * TimePeriodSelector - Reusable time period filter component
 * 
 * Provides consistent period selection across all report pages.
 */

import React from 'react';
import { Calendar } from 'lucide-react';

export type TimePeriod = '1M' | '3M' | '6M' | 'YTD' | '1Y' | 'ALL';

interface TimePeriodSelectorProps {
    value: TimePeriod;
    onChange: (period: TimePeriod) => void;
    options?: TimePeriod[];
    className?: string;
}

const DEFAULT_OPTIONS: TimePeriod[] = ['1M', '3M', '6M', 'YTD', '1Y', 'ALL'];

export const TimePeriodSelector: React.FC<TimePeriodSelectorProps> = ({
    value,
    onChange,
    options = DEFAULT_OPTIONS,
    className = '',
}) => {
    return (
        <div className={`flex items-center gap-1 bg-gray-100 rounded-lg p-1 ${className}`}>
            {options.map((period) => (
                <button
                    key={period}
                    onClick={() => onChange(period)}
                    className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${value === period
                            ? 'bg-white text-blue-600 shadow-sm'
                            : 'text-gray-500 hover:text-gray-700'
                        }`}
                >
                    {period}
                </button>
            ))}
        </div>
    );
};

/**
 * TimePeriodDropdown - Dropdown variant of time period selector
 */
interface TimePeriodDropdownProps {
    value: TimePeriod;
    onChange: (period: TimePeriod) => void;
    options?: TimePeriod[];
    className?: string;
}

export const TimePeriodDropdown: React.FC<TimePeriodDropdownProps> = ({
    value,
    onChange,
    options = DEFAULT_OPTIONS,
    className = '',
}) => {
    const labels: Record<TimePeriod, string> = {
        '1M': '1 Month',
        '3M': '3 Months',
        '6M': '6 Months',
        'YTD': 'Year to Date',
        '1Y': '1 Year',
        'ALL': 'All Time',
    };

    return (
        <div className={`relative ${className}`}>
            <select
                value={value}
                onChange={(e) => onChange(e.target.value as TimePeriod)}
                className="appearance-none pl-9 pr-8 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 cursor-pointer"
            >
                {options.map((period) => (
                    <option key={period} value={period}>
                        {labels[period]}
                    </option>
                ))}
            </select>
            <Calendar
                size={16}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none"
            />
        </div>
    );
};

export default TimePeriodSelector;
