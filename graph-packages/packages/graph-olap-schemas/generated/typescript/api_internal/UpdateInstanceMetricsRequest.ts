/**
 * Current memory consumption
 */
export type MemoryUsageBytes = number | null;
/**
 * Current disk consumption
 */
export type DiskUsageBytes = number | null;
/**
 * Last activity timestamp
 */
export type LastActivityAt = string | null;
/**
 * Queries since last metrics update
 */
export type QueryCountSinceLast = number | null;
/**
 * Average query time in milliseconds
 */
export type AvgQueryTimeMs = number | null;

/**
 * Request to update instance resource metrics.
 *
 * From api.internal.spec.md PUT /instances/:id/metrics.
 * Called periodically by Wrapper Pod to report resource usage.
 */
export interface UpdateInstanceMetricsRequest {
  memory_usage_bytes?: MemoryUsageBytes;
  disk_usage_bytes?: DiskUsageBytes;
  last_activity_at?: LastActivityAt;
  query_count_since_last?: QueryCountSinceLast;
  avg_query_time_ms?: AvgQueryTimeMs;
  [k: string]: unknown;
}
