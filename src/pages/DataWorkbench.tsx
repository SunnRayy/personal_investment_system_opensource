import React, { useState } from 'react';
import {
    History,
    TrendingUp,
    Briefcase,
    Landmark,
    HelpCircle,
    CloudUpload,
    FileText,
    ArrowRight,
    Check,
    Wand2,
    Calendar,
    File,
    Tag,
    BarChart3,
    Search,
    Filter,
    Info,
    CheckCircle,
    AlertCircle,
    Loader2
} from 'lucide-react';
import { WorkflowStep, Transaction } from '../types';
import { getMagicMapping, getSmartFix } from '../lib/gemini';
import clsx from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: (string | undefined | null | false)[]) {
    return twMerge(clsx(inputs));
}

// --- Icons Helper ---
// Since we used Material Symbols in templates, we map them to Lucide here for consistency
// Or just use Lucide directly in the components.

// --- Main Component ---
const DataWorkbench: React.FC = () => {
    const [currentStep, setCurrentStep] = useState<WorkflowStep>(WorkflowStep.DASHBOARD);

    const renderContent = () => {
        switch (currentStep) {
            case WorkflowStep.DASHBOARD:
                return <WorkbenchDashboard onNext={() => setCurrentStep(WorkflowStep.UPLOAD)} />;
            case WorkflowStep.UPLOAD:
                return <UploadStep onNext={() => setCurrentStep(WorkflowStep.MAP)} onBack={() => setCurrentStep(WorkflowStep.DASHBOARD)} />;
            case WorkflowStep.MAP:
                return <MapStep onNext={() => setCurrentStep(WorkflowStep.REVIEW)} onBack={() => setCurrentStep(WorkflowStep.UPLOAD)} />;
            case WorkflowStep.REVIEW:
                return <ReviewStep onNext={() => setCurrentStep(WorkflowStep.COMPLETE)} onBack={() => setCurrentStep(WorkflowStep.MAP)} />;
            case WorkflowStep.COMPLETE:
                return <CompleteStep onFinish={() => setCurrentStep(WorkflowStep.DASHBOARD)} />;
            default:
                return <WorkbenchDashboard onNext={() => setCurrentStep(WorkflowStep.UPLOAD)} />;
        }
    };

    return (
        <div className="p-6 md:p-8 min-h-screen">
            {renderContent()}
        </div>
    );
};

// --- Sub Components ---

const WorkbenchDashboard: React.FC<{ onNext: () => void }> = ({ onNext }) => {
    return (
        <div className="max-w-5xl mx-auto py-12">
            <div className="text-center mb-12">
                <h1 className="text-4xl font-extrabold text-gray-900 mb-2 tracking-tight">Data Workbench</h1>
                <p className="text-lg text-gray-500">Choose data to import into your portfolio</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <WorkbenchCard
                    icon={History}
                    title="Resume pending import"
                    description="Continue your last import session exactly where you left off."
                    pending
                    onClick={onNext}
                />
                <WorkbenchCard
                    icon={TrendingUp}
                    title="Import Transactions"
                    description="Upload trade logs via CSV or connect directly to broker APIs."
                    onClick={onNext}
                />
                <WorkbenchCard
                    icon={Briefcase}
                    title="Import Holdings"
                    description="Update current portfolio positions, real estate, and private equity."
                    onClick={onNext}
                />
                <WorkbenchCard
                    icon={Landmark}
                    title="Import Accounts"
                    description="Bulk configure multiple banking and custodial accounts."
                    onClick={onNext}
                />
            </div>

            <div className="mt-16 text-center">
                <button className="inline-flex items-center gap-2 text-sm font-medium text-gray-400 hover:text-blue-600 transition-colors">
                    <HelpCircle size={18} />
                    Need help with data formats? View Documentation
                </button>
            </div>
        </div>
    );
};

const WorkbenchCard: React.FC<{
    icon: React.ElementType;
    title: string;
    description: string;
    pending?: boolean;
    onClick: () => void;
}> = ({ icon: Icon, title, description, pending, onClick }) => (
    <button
        onClick={onClick}
        className={cn(
            "group relative flex items-start p-6 text-left bg-white border-2 rounded-2xl transition-all duration-300 hover:shadow-xl hover:shadow-gray-200/60 w-full",
            pending ? 'border-amber-400 bg-amber-50/20' : 'border-gray-100 hover:border-blue-500/50'
        )}
    >
        {pending && (
            <span className="absolute top-0 right-0 -mt-2 mr-6 px-3 py-0.5 bg-amber-600 text-[10px] font-bold text-white uppercase tracking-wider rounded-full shadow-sm ring-4 ring-white">
                Pending
            </span>
        )}
        <div className={cn(
            "flex-shrink-0 w-12 h-12 flex items-center justify-center rounded-xl mr-5 transition-transform group-hover:scale-110 group-hover:-rotate-3",
            pending ? 'bg-white text-amber-600 shadow-sm border border-amber-100' : 'bg-blue-50 text-blue-600 group-hover:bg-blue-600 group-hover:text-white'
        )}>
            <Icon size={24} />
        </div>
        <div>
            <h3 className={cn("text-lg font-bold mb-1 transition-colors", pending ? 'text-amber-900 group-hover:text-amber-700' : 'text-gray-900 group-hover:text-blue-600')}>{title}</h3>
            <p className="text-sm text-gray-500 leading-relaxed">{description}</p>
        </div>
    </button>
);

const UploadStep: React.FC<{ onNext: () => void; onBack: () => void }> = ({ onNext, onBack }) => {
    const [activeTab, setActiveTab] = useState<'upload' | 'paste'>('upload');
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [pasteContent, setPasteContent] = useState('');
    const [isDragOver, setIsDragOver] = useState(false);
    const fileInputRef = React.useRef<HTMLInputElement>(null);

    const handleFileSelect = (file: File) => {
        const validExtensions = ['.csv', '.xls', '.xlsx'];
        const ext = file.name.toLowerCase().slice(file.name.lastIndexOf('.'));
        if (validExtensions.includes(ext)) {
            setSelectedFile(file);
        } else {
            alert('Please upload a CSV, XLS, or XLSX file');
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragOver(false);
        const file = e.dataTransfer.files[0];
        if (file) handleFileSelect(file);
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragOver(true);
    };

    const handleDragLeave = () => setIsDragOver(false);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) handleFileSelect(file);
    };

    const canProceed = activeTab === 'upload' ? !!selectedFile : pasteContent.trim().length > 0;

    return (
        <div className="max-w-4xl mx-auto space-y-10">
            <div className="text-center">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload Workflow</h1>
                <p className="text-gray-500">Step 2 of 5: Import your CSV data</p>
            </div>

            <WorkflowStepper step={2} />

            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden">
                <div className="bg-gray-50/50 border-b border-gray-100 p-1 flex justify-center">
                    <div className="flex bg-gray-200 rounded-lg p-1 w-full max-w-sm my-4">
                        <button
                            onClick={() => setActiveTab('upload')}
                            className={`flex-1 px-4 py-2 font-bold rounded text-sm transition-all ${activeTab === 'upload' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                        >
                            Upload CSV
                        </button>
                        <button
                            onClick={() => setActiveTab('paste')}
                            className={`flex-1 px-4 py-2 font-medium text-sm transition-all ${activeTab === 'paste' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                        >
                            Copy & Paste
                        </button>
                    </div>
                </div>

                <div className="p-10 space-y-8">
                    <div className="grid grid-cols-2 gap-8">
                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-gray-700">Column Separator</label>
                            <select className="w-full h-11 bg-gray-50 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm px-3">
                                <option>Comma (,)</option>
                                <option>Semicolon (;)</option>
                                <option>Tab</option>
                            </select>
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-gray-700">Target Account</label>
                            <select className="w-full h-11 bg-gray-50 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm px-3">
                                <option>Multi-account import</option>
                                <option>Savings ...1234</option>
                                <option>Checking ...5678</option>
                            </select>
                        </div>
                    </div>

                    {activeTab === 'upload' ? (
                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-gray-700">Upload File</label>
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept=".csv,.xls,.xlsx"
                                onChange={handleInputChange}
                                className="hidden"
                            />
                            <div
                                onClick={() => fileInputRef.current?.click()}
                                onDrop={handleDrop}
                                onDragOver={handleDragOver}
                                onDragLeave={handleDragLeave}
                                className={`border-2 border-dashed rounded-2xl p-16 flex flex-col items-center justify-center text-center cursor-pointer transition-all group ${isDragOver
                                        ? 'border-blue-500 bg-blue-50'
                                        : selectedFile
                                            ? 'border-emerald-400 bg-emerald-50/30'
                                            : 'border-blue-200 bg-blue-50/30 hover:border-blue-400 hover:bg-blue-50/50'
                                    }`}
                            >
                                {selectedFile ? (
                                    <>
                                        <div className="w-16 h-16 bg-emerald-500 rounded-full flex items-center justify-center text-white shadow-lg mb-4">
                                            <CheckCircle size={32} />
                                        </div>
                                        <h3 className="text-lg font-bold text-gray-900 mb-1">{selectedFile.name}</h3>
                                        <p className="text-sm text-gray-500">{(selectedFile.size / 1024).toFixed(1)} KB • Click to change</p>
                                    </>
                                ) : (
                                    <>
                                        <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center text-blue-600 shadow-sm mb-4 transition-transform group-hover:scale-110">
                                            <CloudUpload size={32} />
                                        </div>
                                        <h3 className="text-lg font-bold text-gray-900 mb-1">Click to upload or drag and drop</h3>
                                        <p className="text-sm text-gray-500 mb-4">Drag your file here or click to browse</p>
                                        <div className="px-3 py-1 bg-white border border-gray-200 rounded text-[10px] font-bold text-gray-400 uppercase tracking-widest">
                                            Supported formats: .csv, .xls, .xlsx
                                        </div>
                                    </>
                                )}
                            </div>
                            <div className="flex justify-between items-center px-1 text-xs text-gray-400">
                                <button className="flex items-center gap-1 hover:text-blue-600">
                                    <FileText size={14} /> Download sample template
                                </button>
                                <span>Max size: 50MB</span>
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-gray-700">Paste CSV Data</label>
                            <textarea
                                value={pasteContent}
                                onChange={(e) => setPasteContent(e.target.value)}
                                placeholder="Paste your CSV data here...&#10;&#10;Date,Symbol,Description,Amount&#10;2023-10-24,AAPL,Buy 10 shares,-1735.00"
                                className="w-full h-64 bg-gray-50 border border-gray-200 rounded-xl p-4 text-sm font-mono focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                            />
                            <p className="text-xs text-gray-400">Tip: Copy rows from Excel or Google Sheets and paste them directly</p>
                        </div>
                    )}

                    <div className="pt-6 border-t border-gray-100 flex items-center justify-end gap-4">
                        <button onClick={onBack} className="px-6 py-2.5 text-sm font-semibold text-gray-400 hover:text-gray-600 transition-colors">Cancel</button>
                        <button
                            onClick={onNext}
                            disabled={!canProceed}
                            className="px-10 py-2.5 bg-blue-600 text-white rounded-xl font-bold shadow-lg shadow-blue-500/25 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2 group"
                        >
                            Continue to Mapping
                            <ArrowRight size={20} className="transition-transform group-hover:translate-x-1" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

const MapStep: React.FC<{ onNext: () => void; onBack: () => void }> = ({ onNext, onBack }) => {
    const [isMapping, setIsMapping] = useState(false);
    const [mappings, setMappings] = useState<Record<string, string>>({
        'Date Field': 'Date (Column A)',
        'Description': 'Description (Column D)',
        'Amount': 'Amount (Column E)',
        'Ticker / Symbol': 'Symbol (Column C)',
        'Category': '-- Select Column --'
    });

    const handleMagicMap = async () => {
        setIsMapping(true);
        try {
            const headers = ['Date', 'Action', 'Symbol', 'Description', 'Amount'];
            const targets = ['Date Field', 'Description', 'Amount', 'Ticker / Symbol', 'Category'];
            const result = await getMagicMapping(headers, targets);

            // Simulate mapping delay for UX if AI is too specific/fast or mocks
            setTimeout(() => {
                setMappings(prev => ({ ...prev, ...result }));
                setIsMapping(false);
            }, 1500);
        } catch (error) {
            console.error(error);
            setIsMapping(false);
        }
    };

    return (
        <div className="max-w-[1400px] mx-auto space-y-8 relative">
            {isMapping && (
                <div className="fixed inset-0 bg-white/60 backdrop-blur-[2px] z-50 flex flex-col items-center justify-center">
                    <div className="w-64 h-2 bg-gray-100 rounded-full overflow-hidden mb-4">
                        <div className="h-full bg-blue-600 animate-[shimmer_1.5s_infinite] w-1/2"></div>
                    </div>
                    <p className="text-sm font-bold text-gray-600 animate-pulse">Gemini AI is scanning your data structure...</p>
                </div>
            )}

            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div className="space-y-1">
                    <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Map CSV Columns</h1>
                    <p className="text-gray-500">Match your file columns to WealthOS's data structure.</p>
                </div>
                <div className="flex items-center gap-2 bg-green-50 border border-green-100 text-green-700 px-4 py-2 rounded-lg shadow-sm">
                    <Wand2 size={18} />
                    <span className="text-sm font-bold tracking-tight">AI-ready for auto-mapping</span>
                </div>
            </div>

            <WorkflowStepper step={3} />

            <div className="grid grid-cols-12 gap-8 items-start">
                <div className="col-span-7 space-y-4">
                    <div className="flex items-center justify-between">
                        <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                            <FileText className="text-gray-400" size={20} />
                            CSV Preview
                        </h2>
                        <div className="px-3 py-1 bg-gray-100 border border-gray-200 rounded text-[11px] font-mono text-gray-500">
                            fidelity_export_2023.csv
                        </div>
                    </div>
                    <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead className="bg-gray-50 text-gray-400 font-bold uppercase text-[10px] tracking-widest border-b border-gray-100">
                                    <tr>
                                        {['Date', 'Action', 'Symbol', 'Description', 'Amount'].map(h => (
                                            <th key={h} className="px-4 py-3">{h}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100 text-[13px] text-gray-600">
                                    <tr className="hover:bg-gray-50/50">
                                        <td className="px-4 py-3 font-mono">2023-10-24</td>
                                        <td className="px-4 py-3">BUY</td>
                                        <td className="px-4 py-3 font-bold text-blue-600">AAPL</td>
                                        <td className="px-4 py-3 truncate max-w-[150px]">APPLE INC COM</td>
                                        <td className="px-4 py-3">-173.50</td>
                                    </tr>
                                    <tr className="hover:bg-gray-50/50">
                                        <td className="px-4 py-3 font-mono">2023-10-24</td>
                                        <td className="px-4 py-3">DIVIDEND</td>
                                        <td className="px-4 py-3 font-bold text-blue-600">VTI</td>
                                        <td className="px-4 py-3 truncate max-w-[150px]">VANGUARD TOTAL STK</td>
                                        <td className="px-4 py-3 text-emerald-600">+45.20</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <div className="col-span-5 space-y-4">
                    <div className="flex items-center justify-between">
                        <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                            <Filter className="text-gray-400" size={20} />
                            Configuration
                        </h2>
                        <button
                            onClick={handleMagicMap}
                            disabled={isMapping}
                            className="flex items-center gap-2 px-4 py-1.5 bg-blue-600 text-white text-[11px] font-bold uppercase tracking-widest rounded-full hover:bg-blue-700 transition-all shadow-md hover:shadow-blue-200 disabled:opacity-50"
                        >
                            <Wand2 size={14} />
                            Magic Map with AI
                        </button>
                    </div>

                    <div className="bg-white border border-gray-200 rounded-2xl shadow-lg p-8 space-y-6">
                        {Object.entries(mappings).map(([field, value]) => (
                            <MappingField
                                key={field}
                                label={field}
                                icon={getIconForField(field)}
                                value={value}
                                onChange={(val) => setMappings(p => ({ ...p, [field]: val }))}
                                required={['Date Field', 'Description', 'Amount'].includes(field)}
                            />
                        ))}

                        <div className="pt-6 border-t border-gray-100 flex items-center justify-between">
                            <button onClick={onBack} className="px-6 py-2.5 text-sm font-bold text-gray-400 hover:text-gray-600">Back</button>
                            <button
                                onClick={onNext}
                                className="px-8 py-2.5 bg-blue-600 text-white font-bold rounded-xl shadow-lg hover:bg-blue-700 transition-all flex items-center gap-2 group"
                            >
                                Next Step
                                <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

const ReviewStep: React.FC<{ onNext: () => void; onBack: () => void }> = ({ onNext, onBack }) => {
    const [isFixing, setIsFixing] = useState(false);
    const [data, setData] = useState<Transaction[]>([
        { id: '1', date: '2023-10-24', description: 'Dividend Payment - AAPL', category: 'Dividend', amount: 145.00, ticker: 'AAPL', account: 'Brokerage ...8842', status: 'ready' },
        { id: '2', date: '2023-13-45', description: 'Transfer to Savings', category: 'Transfer', amount: 5000.00, account: 'Chase Chk ...1234', status: 'error', errorMsg: 'Invalid date format' },
        { id: '3', date: '2023-10-23', description: 'Netflix Subscription', category: 'Entertainment', amount: -19.99, ticker: 'NFLX', account: 'Chase CC ...5501', status: 'ready' },
        { id: '4', date: '2023-10-22', description: 'Unknown Purchase #9921', category: 'Uncategorized', amount: -125.50, account: 'Chase Chk ...1234', status: 'error', errorMsg: 'Please select a category' },
        { id: '5', date: '2023-10-22', description: 'Whole Foods Market', category: 'Groceries', amount: -86.42, account: 'Chase CC ...5501', status: 'ready' },
        { id: '6', date: '2023-10-21', description: 'Shell Station', category: 'Transport', amount: -45.00, account: 'Chase CC ...5501', status: 'ready' },
        { id: '7', date: '2023-10-20', description: 'Salary Deposit', category: 'Income', amount: -2400.00, account: 'Chase Chk ...1234', status: 'error', errorMsg: 'Income cannot be negative' },
    ]);

    const errorCount = data.filter(r => r.status === 'error').length;

    const handleMagicFix = async () => {
        setIsFixing(true);
        const newData = [...data];

        for (let i = 0; i < newData.length; i++) {
            if (newData[i].status === 'error') {
                try {
                    const fix = await getSmartFix(newData[i]);
                    newData[i] = {
                        ...newData[i],
                        ...fix,
                        status: 'ready',
                        errorMsg: undefined,
                        id: newData[i].id + '_fixed' // Track it's been fixed
                    };
                } catch (e) {
                    console.error("Failed to fix row", newData[i].id);
                }
            }
        }

        setData(newData);
        setIsFixing(false);
    };

    return (
        <div className="max-w-[1600px] mx-auto space-y-8 h-full flex flex-col relative">
            <div className="flex items-end justify-between">
                <div className="space-y-1">
                    <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight flex items-center gap-4">
                        Review & Fix Errors
                        <span className={`px-3 py-0.5 rounded-full text-xs font-bold border transition-colors ${errorCount > 0 ? 'bg-red-100 text-red-700 border-red-200' : 'bg-emerald-100 text-emerald-700 border-emerald-200'}`}>
                            {errorCount > 0 ? `${errorCount} Errors Remaining` : 'All Errors Fixed!'}
                        </span>
                    </h1>
                    <p className="text-gray-500">Please review the parsed data. AI has identified {errorCount} issues.</p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={handleMagicFix}
                        disabled={isFixing || errorCount === 0}
                        className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 text-white text-sm font-bold rounded-xl hover:bg-blue-700 transition-all shadow-lg hover:shadow-blue-200 disabled:opacity-50 disabled:shadow-none"
                    >
                        {isFixing ? (
                            <Loader2 className="animate-spin" size={18} />
                        ) : (
                            <Wand2 size={18} />
                        )}
                        {isFixing ? 'AI Fixing...' : 'Magic Fix with AI'}
                    </button>
                </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-2xl shadow-xl flex-1 flex flex-col overflow-hidden max-h-[600px]">
                <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-white flex-shrink-0">
                    <div className="flex items-center gap-4">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                            <input
                                type="text"
                                placeholder="Filter transactions..."
                                className="pl-10 pr-4 py-2 text-sm border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 w-72 h-10 border outline-none"
                            />
                        </div>
                        <div className="h-6 w-px bg-gray-200"></div>
                        <button className="flex items-center gap-2 px-3 py-2 text-sm font-bold text-gray-500 hover:bg-gray-50 rounded-lg transition-colors">
                            <Filter size={16} /> All Status
                        </button>
                    </div>
                    <div className="flex items-center gap-2 text-[13px] text-gray-400">
                        <Info className="text-blue-500" size={16} />
                        AI suggestions are marked with <span className="text-blue-600 font-bold">Sparkles</span>
                    </div>
                </div>

                <div className="flex-1 overflow-auto">
                    <table className="w-full text-left border-collapse min-w-[1200px]">
                        <thead className="sticky top-0 bg-gray-50 z-20 border-b border-gray-200 shadow-sm">
                            <tr className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">
                                <th className="py-4 px-6 w-12 border-r border-gray-200 text-center"><input type="checkbox" className="rounded border-gray-300" /></th>
                                <th className="py-4 px-6 border-r border-gray-200">Date</th>
                                <th className="py-4 px-6 border-r border-gray-200">Description</th>
                                <th className="py-4 px-6 border-r border-gray-200">Category</th>
                                <th className="py-4 px-6 border-r border-gray-200 text-right">Amount</th>
                                <th className="py-4 px-6">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100 text-sm">
                            {data.map((row) => (
                                <tr
                                    key={row.id}
                                    className={`hover:bg-gray-50/50 transition-colors ${row.status === 'error' ? 'bg-red-50/40 border-l-4 border-l-red-500' : row.id.includes('fixed') ? 'bg-blue-50/20 border-l-4 border-l-blue-400' : ''}`}
                                >
                                    <td className="py-3 px-6 text-center border-r border-gray-100">
                                        <input type="checkbox" className="rounded border-gray-300" />
                                    </td>
                                    <td className={`py-3 px-6 font-mono border-r border-gray-100 ${row.status === 'error' && row.errorMsg?.includes('date') ? 'text-red-600 font-bold' : row.id.includes('fixed') ? 'text-blue-600 font-bold' : 'text-gray-500'}`}>
                                        {row.date}
                                        {row.id.includes('fixed') && <Wand2 size={12} className="inline ml-1 text-blue-400" />}
                                    </td>
                                    <td className="py-3 px-6 font-bold text-gray-900 border-r border-gray-100">{row.description}</td>
                                    <td className="py-3 px-6 border-r border-gray-100">
                                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider ${row.status === 'error' && row.errorMsg?.includes('category')
                                            ? 'bg-red-100 text-red-600 italic'
                                            : row.id.includes('fixed') ? 'bg-blue-100 text-blue-600' : 'bg-blue-50 text-blue-600'
                                            }`}>
                                            {row.category}
                                            {row.id.includes('fixed') && <Wand2 size={12} className="ml-1" />}
                                        </span>
                                    </td>
                                    <td className={`py-3 px-6 font-mono text-right border-r border-gray-100 ${row.status === 'error' && row.amount < 0 && row.category === 'Income'
                                        ? 'text-red-600 font-bold'
                                        : row.amount > 0 ? 'text-emerald-600 font-bold' : 'text-gray-900'
                                        }`}>
                                        {row.amount < 0 ? '-' : '+'}${Math.abs(row.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                    </td>
                                    <td className="py-3 px-6">
                                        {row.status === 'ready' ? (
                                            <span className="flex items-center gap-1.5 text-emerald-600 font-bold text-xs uppercase tracking-widest">
                                                <CheckCircle size={16} fill="currentColor" className="text-emerald-600" /> Ready
                                            </span>
                                        ) : (
                                            <div className="flex flex-col">
                                                <span className="text-red-600 font-extrabold text-[10px] uppercase tracking-widest flex items-center gap-1">
                                                    <AlertCircle size={10} />
                                                    Error
                                                </span>
                                                <span className="text-[10px] text-red-400 italic">{row.errorMsg}</span>
                                            </div>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                <div className="px-8 py-6 bg-gray-50 border-t border-gray-200 flex items-center justify-between flex-shrink-0">
                    <div className="flex items-center gap-6">
                        <div className="flex items-center gap-2.5">
                            <span className={`w-2.5 h-2.5 rounded-full ${errorCount === 0 ? 'bg-emerald-500' : 'bg-red-500 animate-pulse'}`}></span>
                            <span className="text-sm font-bold text-gray-600">{data.length - errorCount} rows ready</span>
                        </div>
                        {errorCount > 0 && <span className="text-sm font-bold text-red-500">{errorCount} need fixing</span>}
                    </div>

                    <div className="flex items-center gap-4">
                        <button onClick={onBack} className="px-6 py-3 bg-white border border-gray-200 text-gray-600 font-bold rounded-xl">
                            Back
                        </button>
                        <button
                            onClick={onNext}
                            disabled={errorCount > 0}
                            className="px-10 py-3 bg-blue-600 text-white font-bold rounded-xl shadow-xl shadow-blue-500/25 hover:bg-blue-700 disabled:opacity-50 transition-all flex items-center gap-3 group"
                        >
                            Finalize Import
                            <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

const CompleteStep: React.FC<{ onFinish: () => void }> = ({ onFinish }) => {
    return (
        <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-20 h-20 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mb-6">
                <CheckCircle size={40} />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Import Successful!</h1>
            <p className="text-gray-500 mb-8 max-w-md">Your transactions have been successfully imported and categorized. Your portfolio is now up to date.</p>
            <button
                onClick={onFinish}
                className="px-8 py-3 bg-gray-900 text-white font-bold rounded-xl shadow-lg hover:bg-gray-800 transition-all"
            >
                Return to Dashboard
            </button>
        </div>
    );
};

// --- Helpers ---

const WorkflowStepper: React.FC<{ step: number }> = ({ step }) => (
    <div className="flex items-center justify-between px-10 relative mb-12">
        <div className="absolute top-1/2 left-0 w-full h-0.5 bg-gray-200 -translate-y-1/2 z-0"></div>
        {[1, 2, 3, 4, 5].map((s) => (
            <div key={s} className="relative z-10 flex flex-col items-center gap-2">
                <div className={cn(
                    "w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all shadow-sm",
                    s < step ? 'bg-blue-600 text-white' : s === step ? 'bg-blue-600 text-white ring-8 ring-blue-50' : 'bg-white text-gray-400 border-2 border-gray-100'
                )}>
                    {s < step ? <Check size={18} /> : s}
                </div>
                <span className={cn("text-xs font-bold transition-colors", s <= step ? 'text-blue-600' : 'text-gray-400')}>
                    {s === 1 && 'Source'}
                    {s === 2 && 'Upload'}
                    {s === 3 && 'Map'}
                    {s === 4 && 'Review'}
                    {s === 5 && 'Done'}
                </span>
            </div>
        ))}
    </div>
);

const getIconForField = (field: string) => {
    if (field.includes('Date')) return Calendar;
    if (field.includes('Description')) return FileText;
    if (field.includes('Amount')) return Tag; // or DollarSign
    if (field.includes('Ticker')) return BarChart3;
    return Tag;
};

const MappingField: React.FC<{
    label: string;
    icon: React.ElementType;
    value: string;
    onChange: (v: string) => void;
    required?: boolean;
}> = ({ label, icon: Icon, value, onChange, required }) => (
    <div className="p-4 border border-gray-100 rounded-2xl space-y-2 hover:border-blue-500/30 transition-colors">
        <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 text-sm font-bold text-gray-800">
                <Icon size={18} className="text-gray-400" />
                {label} {required && <span className="text-red-500">*</span>}
            </label>
            {value !== '-- Select Column --' && (
                <span className="text-[9px] font-bold text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded border border-blue-100 uppercase tracking-widest">Matched</span>
            )}
        </div>
        <select
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className="w-full h-10 bg-gray-50 border-gray-200 rounded-lg text-sm font-medium text-gray-700 focus:ring-blue-500 outline-none px-2"
        >
            <option>-- Select Column --</option>
            <option>Date (Column A)</option>
            <option>Action (Column B)</option>
            <option>Symbol (Column C)</option>
            <option>Description (Column D)</option>
            <option>Amount (Column E)</option>
        </select>
    </div>
);

export default DataWorkbench;
