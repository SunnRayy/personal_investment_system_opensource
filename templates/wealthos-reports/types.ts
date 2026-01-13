
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
