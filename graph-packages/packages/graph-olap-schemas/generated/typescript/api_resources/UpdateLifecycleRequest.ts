/**
 * Time-to-live (ISO 8601 duration)
 */
export type Ttl = string | null;
/**
 * Inactivity timeout (ISO 8601 duration)
 */
export type InactivityTimeout = string | null;

/**
 * Request to update lifecycle settings.
 *
 * From api.mappings.spec.md PUT /api/mappings/:id/lifecycle.
 * Also used for snapshots and instances.
 */
export interface UpdateLifecycleRequest {
  ttl?: Ttl;
  inactivity_timeout?: InactivityTimeout;
  [k: string]: unknown;
}
