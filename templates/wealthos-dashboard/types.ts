
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
