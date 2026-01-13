import React, { useState, useEffect } from 'react';
import { ClassificationRule } from '../../api/types/logic_studio';
import { ENDPOINTS } from '../../api/endpoints';
import apiClient from '../../api/client';

const ClassificationRules: React.FC = () => {
    const [rules, setRules] = useState<ClassificationRule[]>([]);
    const [loading, setLoading] = useState(true);

    const [showModal, setShowModal] = useState(false);
    const [newRule, setNewRule] = useState({
        name: '',
        pattern: '',
        match_field: 'asset_name',
        match_type: 'contains',
        tag_id: 0,
        priority: 0,
        taxonomy_id: 1 // Default to Asset Class
    });

    useEffect(() => {
        fetchRules();
    }, []);

    const fetchRules = async () => {
        try {
            const res = await apiClient.get<ClassificationRule[]>(ENDPOINTS.LOGIC_RULES);
            if (res.data) setRules(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async () => {
        try {
            const payload = { ...newRule, description: 'Created via Logic Studio' };
            await apiClient.post(ENDPOINTS.LOGIC_RULES, payload);
            setShowModal(false);
            fetchRules();
            setNewRule({ name: '', pattern: '', match_field: 'asset_name', match_type: 'contains', tag_id: 0, priority: 0, taxonomy_id: 1 });
        } catch (err) {
            alert('Failed to create rule');
        }
    };

    const handleDelete = async (id: number) => {
        if (!confirm('Are you sure you want to delete this rule?')) return;
        try {
            await apiClient.delete(`${ENDPOINTS.LOGIC_RULES}/${id}`); // Append ID manually as endpoint is base url
            setRules(prev => prev.filter(r => r.id !== id));
        } catch (err) {
            alert('Failed to delete rule');
        }
    };

    if (loading) return <div>Loading rules...</div>;

    return (
        <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden relative">
            <div className="p-4 border-b border-gray-200 flex justify-between items-center">
                <h3 className="font-bold text-gray-700">Automation Rules</h3>
                <button className="btn btn-primary text-sm px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700" onClick={() => setShowModal(true)}>
                    + New Rule
                </button>
            </div>

            {showModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-96 shadow-xl">
                        <h3 className="text-lg font-bold mb-4">Add Classification Rule</h3>
                        <div className="space-y-3">
                            <div>
                                <label className="block text-xs font-bold text-gray-500 mb-1">Rule Name</label>
                                <input
                                    className="w-full border rounded p-2 text-sm"
                                    placeholder="e.g. Uber Rides"
                                    value={newRule.name}
                                    onChange={e => setNewRule({ ...newRule, name: e.target.value })}
                                />
                            </div>
                            <div className="flex gap-2">
                                <div className="flex-1">
                                    <label className="block text-xs font-bold text-gray-500 mb-1">Field</label>
                                    <select
                                        className="w-full border rounded p-2 text-sm"
                                        value={newRule.match_field}
                                        onChange={e => setNewRule({ ...newRule, match_field: e.target.value })}
                                    >
                                        <option value="asset_name">Asset Name</option>
                                        <option value="description">Description</option>
                                    </select>
                                </div>
                                <div className="flex-1">
                                    <label className="block text-xs font-bold text-gray-500 mb-1">Type</label>
                                    <select
                                        className="w-full border rounded p-2 text-sm"
                                        value={newRule.match_type}
                                        onChange={e => setNewRule({ ...newRule, match_type: e.target.value })}
                                    >
                                        <option value="contains">Contains</option>
                                        <option value="equals">Equals</option>
                                        <option value="starts_with">Starts With</option>
                                    </select>
                                </div>
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-gray-500 mb-1">Pattern</label>
                                <input
                                    className="w-full border rounded p-2 text-sm"
                                    placeholder="Text to match..."
                                    value={newRule.pattern}
                                    onChange={e => setNewRule({ ...newRule, pattern: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-gray-500 mb-1">Assign Tag ID (Temp)</label>
                                <input
                                    type="number"
                                    className="w-full border rounded p-2 text-sm"
                                    placeholder="Tag ID"
                                    value={newRule.tag_id}
                                    onChange={e => setNewRule({ ...newRule, tag_id: parseInt(e.target.value) })}
                                />
                            </div>
                        </div>
                        <div className="mt-6 flex justify-end gap-2">
                            <button className="px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded" onClick={() => setShowModal(false)}>Cancel</button>
                            <button className="px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700" onClick={handleCreate}>Save Rule</button>
                        </div>
                    </div>
                </div>
            )}
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Priority</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Condition</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Assigns Tag</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {rules.map(rule => (
                            <tr key={rule.id} className="hover:bg-gray-50">
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {rule.priority}
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-900">
                                    <code className="bg-gray-100 px-2 py-1 rounded text-xs text-blue-700">
                                        {rule.match_field} {rule.match_type} "{rule.pattern}"
                                    </code>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                                        {rule.tag_name || `Tag #${rule.tag_id}`}
                                    </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                    <button onClick={() => handleDelete(rule.id)} className="text-red-600 hover:text-red-900">
                                        <span className="material-symbols-outlined text-lg">delete</span>
                                    </button>
                                </td>
                            </tr>
                        ))}
                        {rules.length === 0 && (
                            <tr>
                                <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                                    No rules defined yet.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default ClassificationRules;
