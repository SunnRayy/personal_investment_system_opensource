/**
 * API Endpoint Constants
 *
 * Centralized endpoint definitions for the Flask backend.
 * All endpoints are relative to the API_BASE_URL defined in client.ts.
 */

export const ENDPOINTS = {
  // Health & Status
  HEALTH: '/api/health',

  // Portfolio & Dashboard
  PORTFOLIO_OVERVIEW: '/api/portfolio_overview',
  UNIFIED_ANALYSIS: '/api/unified_analysis',
  ASSETS_LIST: '/api/assets/list',
  DATA_QUALITY: '/api/data_quality',
  MARKET_THERMOMETER: '/api/market_thermometer',

  // Cache Management
  CACHE_REFRESH: '/api/cache/refresh',

  // Wealth Dashboard
  WEALTH_SUMMARY: '/wealth/api/summary',
  WEALTH_BALANCE_SHEET: '/wealth/api/balance-sheet',
  WEALTH_CASH_FLOW: '/wealth/api/cash-flow',
  WEALTH_PARITY: '/wealth/api/parity',

  // Reports
  REPORTS_CORRELATION: '/reports/api/correlation',

  // Simulation
  SIMULATION_RUN: '/reports/simulation/api/run',
  SIMULATION_METADATA: '/reports/simulation/api/metadata',
  SIMULATION_GOALS: '/reports/simulation/api/goals',

  // Logic Studio
  LOGIC_RULES: '/logic-studio/api/rules',
  LOGIC_TAXONOMIES: '/logic-studio/api/taxonomies',
  LOGIC_TAGS: (taxonomyId: number) => `/logic-studio/api/taxonomies/${taxonomyId}/tags`,
  LOGIC_TAG_DETAILS: (tagId: number) => `/logic-studio/api/tags/${tagId}`,
  LOGIC_RISK_PROFILES: '/logic-studio/api/risk-profiles',
  LOGIC_PROFILE_ALLOCATIONS: (profileId: number) => `/logic-studio/api/risk-profiles/${profileId}/allocations`,
  LOGIC_PROFILE_ACTIVATE: (profileId: number) => `/logic-studio/api/risk-profiles/${profileId}/activate`,

  // Authentication (JSON API for SPA)
  AUTH_API_LOGIN: '/auth/api/login',
  AUTH_API_LOGOUT: '/auth/api/logout',
  AUTH_API_STATUS: '/auth/api/status',
} as const;

// Type for endpoint keys
export type EndpointKey = keyof typeof ENDPOINTS;

// Type for endpoint values
export type Endpoint = (typeof ENDPOINTS)[EndpointKey];
