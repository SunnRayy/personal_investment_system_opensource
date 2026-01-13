/**
 * Portfolio API Response Types
 *
 * TypeScript interfaces that mirror the Flask backend response structures.
 */

// Trend data for charts
export interface TrendData {
  dates: string[];
  values: number[];
}

// Portfolio Overview Response (from /api/portfolio_overview)
export interface PortfolioOverviewResponse {
  status: 'success' | 'error';
  data: {
    total_portfolio_value: number;
    current_holdings_count: number;
    historical_records: number;
    allocation: Record<string, number>;
    trend: TrendData;
    holdings_available: boolean;
    balance_sheet_available: boolean;
    currency: string;
    generated_at: string;
  };
  message?: string;
  component?: string;
}

// Convenience type for just the data portion
export type PortfolioOverviewData = PortfolioOverviewResponse['data'];

// Asset list item
export interface Asset {
  Asset_ID: string;
  Asset_Name: string;
}

// Assets List Response (from /api/assets/list)
export interface AssetsListResponse {
  assets: Asset[];
  count: number;
  error?: string;
}

// Data Quality Check Result
export interface DataQualityCheck {
  check_name: string;
  status: 'pass' | 'warning' | 'fail';
  message: string;
  details?: Record<string, unknown>;
}

// Data Quality Response (from /api/data_quality)
export interface DataQualityResponse {
  status: 'success' | 'error';
  data: DataQualityCheck[];
  generated_at: string;
}

// Health Check Response (from /api/health)
export interface HealthCheckResponse {
  status: 'healthy' | 'degraded';
  app: string;
  version: string;
  environment: string;
  system_state: string;
  timestamp: string;
  database: string;
  demo_mode: boolean;
}
