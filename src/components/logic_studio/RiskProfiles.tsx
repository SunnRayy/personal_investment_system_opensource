import React, { useState, useEffect } from 'react';
import { RiskProfile, TargetAllocation, Tag } from '../../api/types/logic_studio';
import { ENDPOINTS } from '../../api/endpoints';
import apiClient from '../../api/client';

// Assuming Taxonomy ID 1 is "Asset Class"
const ASSET_CLASS_TAXONOMY_ID = 1;

const RiskProfiles: React.FC = () => {
    const [profiles, setProfiles] = useState<RiskProfile[]>([]);
    const [activeProfileId, setActiveProfileId] = useState<number | null>(null);
    const [assetClasses, setAssetClasses] = useState<Tag[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        Promise.all([
            fetchProfiles(),
            fetchAssetClasses()
        ]).then(() => setLoading(false));
    }, []);

    const fetchProfiles = async () => {
        const res = await apiClient.get<RiskProfile[]>(ENDPOINTS.LOGIC_RISK_PROFILES);
        if (res.data) setProfiles(res.data);
    };

    const fetchAssetClasses = async () => {
        const res = await apiClient.get<Tag[]>(ENDPOINTS.LOGIC_TAGS(ASSET_CLASS_TAXONOMY_ID));
        if (res.data) setAssetClasses(res.data);
    };

    return (
        <div className="space-y-4">
            {profiles.map(profile => (
                <ProfileEditor
                    key={profile.id}
                    profile={profile}
                    assetClasses={assetClasses}
                    onUpdate={fetchProfiles}
                />
            ))}
            <div className="mt-6 flex justify-end">
                <button className="btn btn-secondary" onClick={() => alert('Create Profile UI to be implemented')}>
                    + New Profile
                </button>
            </div>
        </div>
    );
};

const ProfileEditor: React.FC<{
    profile: RiskProfile;
    assetClasses: Tag[];
    onUpdate: () => void;
}> = ({ profile, assetClasses, onUpdate }) => {
    const [expanded, setExpanded] = useState(false);
    const [allocations, setAllocations] = useState<Record<number, number>>({});
    const [loadingAlloc, setLoadingAlloc] = useState(false);

    useEffect(() => {
        if (expanded && Object.keys(allocations).length === 0) {
            fetchAllocations();
        }
    }, [expanded]);

    const fetchAllocations = async () => {
        setLoadingAlloc(true);
        try {
            const res = await apiClient.get<TargetAllocation[]>(ENDPOINTS.LOGIC_PROFILE_ALLOCATIONS(profile.id));
            if (res.data) {
                const allocMap: Record<number, number> = {};
                res.data.forEach(a => allocMap[a.tag_id] = a.target_weight);

                // Initialize 0 for missing classes
                assetClasses.forEach(ac => {
                    if (allocMap[ac.id] === undefined) allocMap[ac.id] = 0;
                });

                setAllocations(allocMap);
            }
        } finally {
            setLoadingAlloc(false);
        }
    };

    const handleSliderChange = (tagId: number, val: number) => {
        setAllocations(prev => ({ ...prev, [tagId]: val }));
    };

    const total = Object.values(allocations).reduce((a, b) => a + b, 0);
    const isValid = Math.abs(total - 100) < 0.1;

    const handleSave = async () => {
        const payload = {
            allocations: Object.entries(allocations).map(([tagId, weight]) => ({
                tag_id: parseInt(tagId),
                weight: weight
            }))
        };

        try {
            await apiClient.post(ENDPOINTS.LOGIC_PROFILE_ALLOCATIONS(profile.id), payload);
            alert('Saved successfully!');
        } catch (err) {
            alert('Failed to save');
            console.error(err);
        }
    };

    const handleActivate = async () => {
        try {
            await apiClient.post(ENDPOINTS.LOGIC_PROFILE_ACTIVATE(profile.id), {});
            onUpdate(); // Refresh list to show active checkmark
        } catch (err) {
            console.error(err);
        }
    }

    return (
        <div className={`border rounded-lg bg-white overflow-hidden transition-all ${profile.is_active ? 'border-brand-gold ring-1 ring-brand-gold' : 'border-gray-200'}`}>
            <div
                className="p-4 flex items-center justify-between cursor-pointer hover:bg-gray-50"
                onClick={() => setExpanded(!expanded)}
            >
                <div className="flex items-center gap-3">
                    {profile.is_active ? (
                        <span className="material-symbols-outlined text-brand-gold">check_circle</span>
                    ) : (
                        <span className="material-symbols-outlined text-gray-300">circle</span>
                    )}
                    <div>
                        <h3 className="font-medium text-gray-900">{profile.name}</h3>
                        <p className="text-sm text-gray-500">{profile.description}</p>
                    </div>
                </div>
                <span className="material-symbols-outlined text-gray-400">
                    {expanded ? 'expand_less' : 'expand_more'}
                </span>
            </div>

            {expanded && (
                <div className="p-4 border-t border-gray-100 bg-gray-50">
                    {loadingAlloc ? (
                        <div className="py-4 text-center text-gray-500">Loading allocations...</div>
                    ) : (
                        <div className="space-y-4">
                            <div className="flex justify-between items-center mb-4">
                                <div className={`text-sm font-bold ${isValid ? 'text-green-600' : 'text-red-600'}`}>
                                    Total Allocation: {total.toFixed(1)}%
                                </div>
                                {!profile.is_active && (
                                    <button onClick={handleActivate} className="text-xs text-blue-600 hover:underline">
                                        Set as Active Profile
                                    </button>
                                )}
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {assetClasses.length === 0 && (
                                    <div className="col-span-2 text-center text-gray-500 py-4 italic">
                                        No Asset Classes found (Taxonomy ID 1). Please configure your taxonomies first.
                                    </div>
                                )}
                                {assetClasses.map(ac => (
                                    <div key={ac.id} className="bg-white p-3 rounded border border-gray-200">
                                        <div className="flex justify-between text-sm mb-1">
                                            <span className="font-medium text-gray-700">{ac.name}</span>
                                            <span className="text-gray-900 font-mono">{allocations[ac.id] || 0}%</span>
                                        </div>
                                        <input
                                            type="range"
                                            min="0"
                                            max="100"
                                            step="5"
                                            value={allocations[ac.id] || 0}
                                            onChange={(e) => handleSliderChange(ac.id, parseInt(e.target.value))}
                                            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                                        />
                                    </div>
                                ))}
                            </div>

                            <div className="mt-4 flex justify-end">
                                <button
                                    onClick={handleSave}
                                    disabled={!isValid}
                                    className={`px-4 py-2 rounded text-sm font-medium ${isValid
                                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                                        : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                        }`}
                                >
                                    Save Changes
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default RiskProfiles;
