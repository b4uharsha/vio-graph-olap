/**
 * Shutdown reason
 */
export type Reason = string;
/**
 * Grace period for shutdown
 */
export type GracePeriodSeconds = number;

/**
 * Request to initiate graceful shutdown.
 *
 * From api.internal.spec.md POST /shutdown.
 * Called by Control Plane when terminating an instance.
 */
export interface ShutdownRequest {
  reason: Reason;
  grace_period_seconds?: GracePeriodSeconds;
  [k: string]: unknown;
}
