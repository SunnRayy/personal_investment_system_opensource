import React, { useState } from 'react';
import ClassificationRules from '../components/logic_studio/ClassificationRules';
import StrategyTiers from '../components/logic_studio/StrategyTiers';
import RiskProfiles from '../components/logic_studio/RiskProfiles';

const LogicStudio: React.FC = () => {
    const [activeTab, setActiveTab] = useState<'rules' | 'tiers' | 'profiles'>('rules');

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="mb-8">
                <h1 className="text-2xl font-bold text-gray-900">Logic Studio</h1>
                <p className="text-gray-600">Configure asset classification rules, strategic tiers, and risk profiles.</p>
            </div>

            <div className="border-b border-gray-200 mb-6">
                <nav className="-mb-px flex space-x-8" aria-label="Tabs">
                    <button
                        onClick={() => setActiveTab('rules')}
                        className={`
              whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center
              ${activeTab === 'rules' ? 'border-brand-gold text-brand-gold' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
            `}
                    >
                        <span className="material-symbols-outlined text-lg mr-2">category</span>
                        Classification Rules
                    </button>

                    <button
                        onClick={() => setActiveTab('tiers')}
                        className={`
              whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center
              ${activeTab === 'tiers' ? 'border-brand-gold text-brand-gold' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
            `}
                    >
                        <span className="material-symbols-outlined text-lg mr-2">layers</span>
                        Strategy Tiers
                    </button>

                    <button
                        onClick={() => setActiveTab('profiles')}
                        className={`
              whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center
              ${activeTab === 'profiles' ? 'border-brand-gold text-brand-gold' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
            `}
                    >
                        <span className="material-symbols-outlined text-lg mr-2">tune</span>
                        Risk Profiles
                    </button>
                </nav>
            </div>

            <div>
                {activeTab === 'rules' && <ClassificationRules />}
                {activeTab === 'tiers' && <StrategyTiers />}
                {activeTab === 'profiles' && <RiskProfiles />}
            </div>
        </div>
    );
};

export default LogicStudio;
