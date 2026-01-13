/**
 * Reports Data Hooks
 *
 * React Query hooks for fetching report-related data from the Flask backend.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../api/client';
import { ENDPOINTS } from '../api/endpoints';
import type {
  UnifiedAnalysisResponse,
  WealthSummaryResponse,
  CashFlowResponse,
  CorrelationResponse,
  SimulationResponse,
  SimulationParams,
} from '../api/types';

// Query keys for cache management
export const REPORTS_QUERY_KEYS = {
  unifiedAnalysis: ['reports', 'unified'] as const,
  wealthSummary: ['reports', 'wealth', 'summary'] as const,
  cashFlow: ['reports', 'wealth', 'cashflow'] as const,
  correlation: ['reports', 'correlation'] as const,
  simulation: (params: SimulationParams) => ['reports', 'simulation', params] as const,
};

/**
 * Fetch unified analysis data
 *
 * This is the main data source for:
 * - Portfolio snapshot
 * - Asset allocation details
 * - Rebalancing analysis
 * - Performance metrics
 * - Market regime
 */
export function useUnifiedAnalysis() {
  return useQuery({
    queryKey: REPORTS_QUERY_KEYS.unifiedAnalysis,
    queryFn: async () => {
      const result = await api.get<UnifiedAnalysisResponse>(ENDPOINTS.UNIFIED_ANALYSIS);

      if (!result.success) {
        throw new Error(result.error.message);
      }

      return result.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000,   // 30 minutes
    retry: 2,
    refetchOnWindowFocus: false,
  });
}

/**
 * Fetch wealth dashboard summary
 */
export function useWealthSummary() {
  return useQuery({
    queryKey: REPORTS_QUERY_KEYS.wealthSummary,
    queryFn: async () => {
      const result = await api.get<WealthSummaryResponse>(ENDPOINTS.WEALTH_SUMMARY);

      if (!result.success) {
        throw new Error(result.error.message);
      }

      return result.data.data;
    },
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}

/**
 * Fetch cash flow analysis data
 */
export function useCashFlow() {
  return useQuery({
    queryKey: REPORTS_QUERY_KEYS.cashFlow,
    queryFn: async () => {
      const result = await api.get<CashFlowResponse>(ENDPOINTS.WEALTH_CASH_FLOW);

      if (!result.success) {
        throw new Error(result.error.message);
      }

      return result.data.data;
    },
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}

/**
 * Fetch correlation matrix (lazy-loaded due to size)
 *
 * Only fetches when explicitly enabled to avoid loading large dataset
 * on pages that don't need it.
 */
export function useCorrelation(enabled: boolean = false) {
  return useQuery({
    queryKey: REPORTS_QUERY_KEYS.correlation,
    queryFn: async () => {
      const result = await api.get<CorrelationResponse>(ENDPOINTS.REPORTS_CORRELATION);

      if (!result.success) {
        throw new Error(result.error.message);
      }

      return result.data.data;
    },
    enabled,
    staleTime: 30 * 60 * 1000, // 30 minutes (changes rarely)
    gcTime: 60 * 60 * 1000,    // 1 hour
    retry: 1,
  });
}

/**
 * Run Monte Carlo simulation
 *
 * Uses mutation because it's a POST endpoint that computes results
 * based on user-provided parameters.
 */
export function useSimulationMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (params: SimulationParams) => {
      const result = await api.post<SimulationResponse>(ENDPOINTS.SIMULATION_RUN, params);

      if (!result.success) {
        throw new Error(result.error.message);
      }

      return result.data.data;
    },
    onSuccess: (data, variables) => {
      // Cache the results for this specific parameter set
      queryClient.setQueryData(REPORTS_QUERY_KEYS.simulation(variables), data);
    },
  });
}

/**
 * Refresh cache mutation
 *
 * Forces refresh of all cached report data on the backend.
 */
export function useRefreshCacheMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const result = await api.post<{ status: string; message: string }>(ENDPOINTS.CACHE_REFRESH);

      if (!result.success) {
        throw new Error(result.error.message);
      }

      return result.data;
    },
    onSuccess: () => {
      // Invalidate all report queries to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
    },
  });
}
