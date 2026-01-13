/**
 * Correlation Matrix
 * Heatmap visualization for asset correlations
 */

import React from 'react';

interface CorrelationData {
    assets: string[];
    matrix: number[][];
}

interface CorrelationMatrixProps {
    data: CorrelationData;
}

const CorrelationMatrix: React.FC<CorrelationMatrixProps> = ({ data }) => {
    const getColor = (value: number) => {
        // Blue scale: darker = higher correlation
        const intensity = Math.abs(value);
        if (value >= 0.8) return 'bg-blue-600 text-white';
        if (value >= 0.5) return 'bg-blue-500 text-white';
        if (value >= 0.2) return 'bg-blue-400 text-white';
        if (value >= 0) return 'bg-blue-200 text-slate-700';
        if (value >= -0.2) return 'bg-slate-200 text-slate-700';
        if (value >= -0.5) return 'bg-red-200 text-slate-700';
        return 'bg-red-400 text-white';
    };

    return (
        <div className="overflow-x-auto">
            <table className="min-w-full">
                <thead>
                    <tr>
                        <th className="p-2"></th>
                        {data.assets.map((asset) => (
                            <th
                                key={asset}
                                className="p-2 text-xs font-medium text-slate-500 uppercase tracking-wider text-center"
                            >
                                {asset}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {data.assets.map((rowAsset, i) => (
                        <tr key={rowAsset}>
                            <td className="p-2 text-xs font-medium text-slate-500 uppercase tracking-wider">
                                {rowAsset}
                            </td>
                            {data.matrix[i].map((value, j) => (
                                <td key={j} className="p-1">
                                    <div
                                        className={`w-12 h-10 flex items-center justify-center rounded text-xs font-semibold ${getColor(value)}`}
                                        title={`${rowAsset} ↔ ${data.assets[j]}: ${value.toFixed(2)}`}
                                    >
                                        {value.toFixed(2)}
                                    </div>
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default CorrelationMatrix;
