/**
 * Portfolio Data Hooks
 *
 * React Query hooks for fetching portfolio-related data from the Flask backend.
 */

import { useQuery } from '@tanstack/react-query';
import api from '../api/client';
import { ENDPOINTS } from '../api/endpoints';
import type {
  PortfolioOverviewResponse,
  AssetsListResponse,
  DataQualityResponse,
  HealthCheckResponse,
} from '../api/types';

// Query keys for cache management
export const PORTFOLIO_QUERY_KEYS = {
  overview: ['portfolio', 'overview'] as const,
  assets: ['portfolio', 'assets'] as const,
  dataQuality: ['portfolio', 'dataQuality'] as const,
  health: ['health'] as const,
};

/**
 * Fetch portfolio overview data
 *
 * Includes: total value, holdings count, allocation breakdown, trend data
 */
export function usePortfolioOverview() {
  return useQuery({
    queryKey: PORTFOLIO_QUERY_KEYS.overview,
    queryFn: async () => {
      const result = await api.get<PortfolioOverviewResponse>(ENDPOINTS.PORTFOLIO_OVERVIEW);

      if (!result.success) {
        throw new Error(result.error.message);
      }

      return result.data.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000,   // 30 minutes (formerly cacheTime)
    retry: 2,
    refetchOnWindowFocus: false,
  });
}

/**
 * Fetch list of assets for dropdowns
 */
export function useAssetsList() {
  return useQuery({
    queryKey: PORTFOLIO_QUERY_KEYS.assets,
    queryFn: async () => {
      const result = await api.get<AssetsListResponse>(ENDPOINTS.ASSETS_LIST);

      if (!result.success) {
        throw new Error(result.error.message);
      }

      return result.data;
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 60 * 60 * 1000,    // 1 hour
  });
}

/**
 * Fetch data quality health check results
 */
export function useDataQuality() {
  return useQuery({
    queryKey: PORTFOLIO_QUERY_KEYS.dataQuality,
    queryFn: async () => {
      const result = await api.get<DataQualityResponse>(ENDPOINTS.DATA_QUALITY);

      if (!result.success) {
        throw new Error(result.error.message);
      }

      return result.data.data;
    },
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

/**
 * Fetch application health status
 */
export function useHealthCheck() {
  return useQuery({
    queryKey: PORTFOLIO_QUERY_KEYS.health,
    queryFn: async () => {
      const result = await api.get<HealthCheckResponse>(ENDPOINTS.HEALTH);

      if (!result.success) {
        throw new Error(result.error.message);
      }

      return result.data;
    },
    staleTime: 60 * 1000, // 1 minute
    retry: 0,
    refetchInterval: 60 * 1000, // Poll every minute
  });
}
