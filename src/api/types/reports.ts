/**
 * Reports API Response Types
 *
 * TypeScript interfaces for report-related API endpoints.
 */

// Market Regime Types
export type MarketRegime = 'Bull' | 'Bear' | 'Neutral' | 'Recovery' | 'Correction';

// Portfolio Snapshot (from unified_analysis)
export interface PortfolioSnapshot {
  total_value: number;
  total_cost: number;
  total_profit_loss: number;
  total_return_pct: number;
  holdings_count: number;
  currency: string;
  snapshot_date: string;
}

// Asset Allocation Detail
export interface AllocationDetail {
  category: string;
  target_pct: number;
  actual_pct: number;
  market_value: number;
  drift: number;
  drift_status: 'OK' | 'Warning' | 'Critical';
}

// Rebalancing Analysis
export interface RebalancingAnalysis {
  needs_rebalancing: boolean;
  trigger_reason: string | null;
  total_drift: number;
  categories: {
    name: string;
    target_pct: number;
    actual_pct: number;
    drift: number;
    action: 'BUY' | 'SELL' | 'HOLD';
    trade_amount: number;
  }[];
}

// Performance Metrics
export interface PerformanceMetrics {
  xirr: number | null;
  twrr: number | null;
  ytd_return: number | null;
  mtd_return: number | null;
  sharpe_ratio: number | null;
  max_drawdown: number | null;
  volatility: number | null;
}

// Asset Concentration Risk
export interface AssetConcentrationRisk {
  ticker: string;
  name: string;
  percentage: number;
  level: 'Low' | 'Medium' | 'High' | 'Critical';
}

// Unified Analysis Response (from /api/unified_analysis)
export interface UnifiedAnalysisResponse {
  // Portfolio summary
  portfolio_snapshot?: PortfolioSnapshot;

  // Asset allocation
  allocation_analysis?: AllocationDetail[];
  asset_allocation_details?: AllocationDetail[];

  // Rebalancing
  rebalancing_analysis?: RebalancingAnalysis;

  // Performance
  performance_data?: PerformanceMetrics;

  // Risk analysis
  asset_concentration_risk?: AssetConcentrationRisk[];
  correlation_analysis?: Record<string, Record<string, number>>;

  // Market context
  market_regime?: {
    current_regime: MarketRegime;
    confidence: number;
    indicators: Record<string, number>;
  };

  // Stress testing
  stress_test_data?: {
    scenarios: {
      name: string;
      impact_pct: number;
      impact_value: number;
    }[];
  };

  // Error state
  error?: string;
}

// Market Thermometer Indicator (from /api/market_thermometer)
export interface MarketIndicator {
  value: number;
  zone: string;
  level: number;  // 0-4 (0=extreme fear/undervalued, 4=extreme greed/overvalued)
  status: 'success' | 'error';
  error_message?: string;
  data_age_warning?: string;
}

// Market Thermometer Response
export interface MarketThermometerData {
  shiller_pe: MarketIndicator;
  fear_greed: MarketIndicator;
  vix: MarketIndicator;
  buffett_us: MarketIndicator;
  buffett_china: MarketIndicator;
  buffett_japan: MarketIndicator;
  buffett_europe: MarketIndicator;
  last_updated: string;
}

export interface MarketThermometerResponse {
  status: 'success' | 'error';
  data: MarketThermometerData | null;
  generated_at: string;
  error?: string;
}

// Wealth Dashboard Summary
export interface WealthSummaryResponse {
  status: 'success' | 'error';
  data: {
    net_worth: number;
    total_assets: number;
    total_liabilities: number;
    liquid_assets: number;
    investment_assets: number;
    fixed_assets: number;
    currency: string;
    generated_at: string;
  };
}

// Cash Flow Data Point
export interface CashFlowDataPoint {
  date: string;
  income: number;
  expenses: number;
  net: number;
}

// Cash Flow Response
export interface CashFlowResponse {
  status: 'success' | 'error';
  data: {
    monthly: CashFlowDataPoint[];
    summary: {
      total_income: number;
      total_expenses: number;
      net_cash_flow: number;
      savings_rate: number;
    };
    currency: string;
    generated_at: string;
  };
}

// Correlation Matrix Response
export interface CorrelationResponse {
  status: 'success' | 'error';
  data: {
    matrix: Record<string, Record<string, number>>;
    assets: string[];
  };
  generated_at: string;
}

// Simulation Parameters
export interface SimulationParams {
  initial_value: number;
  years: number;
  annual_contribution: number;
  risk_profile: 'Conservative' | 'Moderate' | 'Aggressive';
  inflation_rate?: number;
}

// Simulation Result
export interface SimulationResult {
  year: number;
  p5: number;   // 5th percentile (pessimistic)
  p25: number;  // 25th percentile
  p50: number;  // Median
  p75: number;  // 75th percentile
  p95: number;  // 95th percentile (optimistic)
}

// Simulation Response
export interface SimulationResponse {
  status: 'success' | 'error';
  data: {
    results: SimulationResult[];
    params: SimulationParams;
    success_probability: number;
    iterations: number;
    generated_at: string;
  };
}
