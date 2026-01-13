
export interface Activity {
    id: string;
    type: 'buy' | 'deposit' | 'dividend' | 'sell';
    asset: string;
    amount: number;
    date: string;
    icon: string;
}

export interface NavItem {
    label: string;
    icon: string;
    section: 'Main' | 'Analysis' | 'System';
    isActive?: boolean;
}

export interface AllocationData {
    name: string;
    value: number;
    color: string;
}

export interface NetWorthPoint {
    date: string;
    value: number;
}

export enum WorkflowStep {
    DASHBOARD = 'DASHBOARD',
    UPLOAD = 'UPLOAD',
    MAP = 'MAP',
    REVIEW = 'REVIEW',
    COMPLETE = 'COMPLETE'
}

export interface Transaction {
    id: string;
    date: string;
    description: string;
    category: string;
    amount: number;
    ticker?: string;
    account: string;
    status: 'ready' | 'error';
    errorMsg?: string;
}

export enum ReportView {
    PORTFOLIO_OVERVIEW = 'Portfolio Overview',
    ALLOCATION_RISK = 'Allocation & Risk',
    GAINS_ANALYSIS = 'Gains Analysis',
    CASH_FLOW = 'Cash Flow',
    COMPASS = 'Compass',
    SIMULATION = 'Simulation',
    DASHBOARD = 'Dashboard',
    DATA_WORKBENCH = 'Data Workbench',
    LOGIC_STUDIO = 'Logic Studio',
    INTEGRATIONS = 'Integrations',
    HEALTH = 'Health'
}

export interface AssetPerformance {
    name: string;
    class: string;
    period: string;
    status: 'Active' | 'Closed';
    invested: number;
    value: number;
    profitLoss: number;
    returnPct: number;
    performance: 'Excellent' | 'Good' | 'Average' | 'Poor';
}
