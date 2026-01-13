
import { NavItem, AllocationData, NetWorthPoint, Activity } from './types';

export const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', icon: 'home', section: 'Main', isActive: true },
  { label: 'Data Workbench', icon: 'database', section: 'Main' },
  { label: 'Logic Studio', icon: 'psychology', section: 'Main' },
  { label: 'Portfolio', icon: 'pie_chart', section: 'Analysis' },
  { label: 'Cash Flow', icon: 'payments', section: 'Analysis' },
  { label: 'Compass', icon: 'explore', section: 'Analysis' },
  { label: 'Simulation', icon: 'science', section: 'Analysis' },
  { label: 'Integrations', icon: 'cable', section: 'System' },
  { label: 'Health', icon: 'monitor_heart', section: 'System' },
];

export const ALLOCATION_DATA: AllocationData[] = [
  { name: 'Stocks', value: 60, color: '#3B82F6' },
  { name: 'Bonds', value: 30, color: '#D4AF37' },
  { name: 'Alternatives', value: 10, color: '#14B8A6' },
];

export const NET_WORTH_HISTORY: NetWorthPoint[] = [
  { date: 'Jan', value: 1350000 },
  { date: 'Feb', value: 1420000 },
  { date: 'Mar', value: 1480000 },
  { date: 'Apr', value: 1450000 },
  { date: 'May', value: 1410000 },
  { date: 'Jun', value: 1380000 },
  { date: 'Jul', value: 1420000 },
  { date: 'Aug', value: 1480000 },
  { date: 'Sep', value: 1520000 },
  { date: 'Oct', value: 1550000 },
  { date: 'Nov', value: 1540000 },
  { date: 'Dec', value: 1561662.82 },
];

export const RECENT_ACTIVITY: Activity[] = [
  { id: '1', type: 'buy', asset: 'Apple Inc. (AAPL)', amount: -1200.00, date: 'May 15, 2024', icon: 'arrow_upward' },
  { id: '2', type: 'deposit', asset: 'Deposit from Bank', amount: 5000.00, date: 'May 14, 2024', icon: 'vertical_align_bottom' },
  { id: '3', type: 'dividend', asset: 'Microsoft Corp. (MSFT)', amount: 85.50, date: 'May 12, 2024', icon: 'database' },
];
