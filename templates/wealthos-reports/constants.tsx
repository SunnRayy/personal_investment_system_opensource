
import React from 'react';
import { 
  LayoutDashboard, 
  Database, 
  BrainCircuit, 
  PieChart, 
  Wallet, 
  Compass, 
  FlaskConical, 
  Cable, 
  HeartPulse,
  TrendingUp,
  Activity,
  BarChart3
} from 'lucide-react';
import { ReportView } from './types';

export const NAVIGATION_ITEMS = [
  { group: 'Main', items: [
    { name: ReportView.DASHBOARD, icon: <LayoutDashboard size={20} /> },
    { name: ReportView.DATA_WORKBENCH, icon: <Database size={20} /> },
    { name: ReportView.LOGIC_STUDIO, icon: <BrainCircuit size={20} /> },
  ]},
  { group: 'Analysis', items: [
    { name: ReportView.PORTFOLIO_OVERVIEW, icon: <Activity size={20} /> },
    { name: ReportView.ALLOCATION_RISK, icon: <PieChart size={20} /> },
    { name: ReportView.GAINS_ANALYSIS, icon: <TrendingUp size={20} /> },
    { name: ReportView.CASH_FLOW, icon: <Wallet size={20} /> },
    { name: ReportView.COMPASS, icon: <Compass size={20} /> },
    { name: ReportView.SIMULATION, icon: <FlaskConical size={20} /> },
  ]},
  { group: 'System', items: [
    { name: ReportView.INTEGRATIONS, icon: <Cable size={20} /> },
    { name: ReportView.HEALTH, icon: <HeartPulse size={20} /> },
  ]}
];
