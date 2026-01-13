/**
 * API Module Index
 *
 * Main entry point for the API layer.
 * Re-exports client, endpoints, and types.
 */

export { default as api } from './client';
export type { ApiError, ApiResult } from './client';
export { ENDPOINTS } from './endpoints';
export type { EndpointKey, Endpoint } from './endpoints';
export * from './types';
