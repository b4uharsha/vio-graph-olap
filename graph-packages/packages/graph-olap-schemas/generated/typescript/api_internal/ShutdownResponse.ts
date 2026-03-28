export type Acknowledged = boolean;
/**
 * Number of active queries
 */
export type ActiveQueries = number;
/**
 * Whether an algorithm lock is held
 */
export type LockHeld = boolean;

/**
 * Response to shutdown request.
 *
 * From api.internal.spec.md POST /shutdown response.
 */
export interface ShutdownResponse {
  acknowledged?: Acknowledged;
  active_queries?: ActiveQueries;
  lock_held?: LockHeld;
  [k: string]: unknown;
}
