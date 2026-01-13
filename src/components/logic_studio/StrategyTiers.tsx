import React, { useState, useEffect } from 'react';
import { Tag } from '../../api/types/logic_studio';
import { ENDPOINTS } from '../../api/endpoints';
import apiClient from '../../api/client';

const StrategyTiers: React.FC = () => {
    const [tiers, setTiers] = useState<Tag[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Assuming Taxonomy ID 2 is "Asset Tier" based on the spec
    const TIER_TAXONOMY_ID = 2;

    useEffect(() => {
        fetchTiers();
    }, []);

    const fetchTiers = async () => {
        try {
            const response = await apiClient.get<Tag[]>(ENDPOINTS.LOGIC_TAGS(TIER_TAXONOMY_ID));
            if (response.data) {
                setTiers(response.data);
            }
        } catch (err) {
            setError('Failed to fetch strategy tiers');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const updateDescription = async (tagId: number, description: string) => {
        try {
            await apiClient.put(ENDPOINTS.LOGIC_TAG_DETAILS(tagId), { description });
            // Update local state to reflect change without re-fetching
            setTiers(prev => prev.map(t => t.id === tagId ? { ...t, description } : t));
        } catch (err) {
            console.error('Failed to update description', err);
            alert('Failed to save description');
        }
    };

    const getTierColor = (name: string) => {
        const n = name.toLowerCase();
        if (n.includes('tier 1') || n.includes('core')) return 'bg-blue-500';
        if (n.includes('tier 2') || n.includes('diversify')) return 'bg-green-500';
        if (n.includes('tier 3') || n.includes('trading')) return 'bg-orange-500';
        return 'bg-gray-500';
    };

    if (loading) return <div>Loading tiers...</div>;
    if (error) return <div className="text-red-600">{error}</div>;

    if (tiers.length === 0) {
        return (
            <div className="text-center py-12 bg-gray-50 rounded-lg border border-dashed border-gray-300">
                <span className="material-symbols-outlined text-4xl text-gray-300 mb-2">layers_clear</span>
                <p className="text-gray-500">No Strategy Tiers found.</p>
                <p className="text-sm text-gray-400">Ensure 'Asset Tier' taxonomy (ID: 2) exists and has tags.</p>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {tiers.map(tier => (
                <div key={tier.id} className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-bold text-gray-900 flex items-center">
                            <span className={`w-3 h-3 rounded-full mr-2 ${getTierColor(tier.name)}`}></span>
                            {tier.name}
                        </h3>
                        <span className="material-symbols-outlined text-gray-400">layers</span>
                    </div>

                    <div className="mb-4">
                        <label className="block text-xs font-medium text-gray-500 mb-1">Strategy Description</label>
                        <textarea
                            className="w-full text-sm border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 p-2 border"
                            rows={3}
                            defaultValue={tier.description || ''}
                            onBlur={(e) => updateDescription(tier.id, e.target.value)}
                        />
                    </div>

                    <div>
                        <label className="block text-xs font-medium text-gray-500 mb-1">Included Assets</label>
                        <div className="text-xs text-gray-400 italic">
                            (Asset mapping is managed in Classification Rules)
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
};

export default StrategyTiers;
