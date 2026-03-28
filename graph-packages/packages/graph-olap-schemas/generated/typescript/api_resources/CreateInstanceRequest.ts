/**
 * Source snapshot ID
 */
export type SnapshotId = number;
/**
 * Display name for the instance
 */
export type Name = string;
/**
 * Optional description
 */
export type Description = string | null;
/**
 * Time-to-live (ISO 8601 duration)
 */
export type Ttl = string | null;
/**
 * Terminate after no activity
 */
export type InactivityTimeout = string | null;

/**
 * Request to create an instance from a snapshot.
 *
 * From api.instances.spec.md POST /api/instances.
 */
export interface CreateInstanceRequest {
  snapshot_id: SnapshotId;
  name: Name;
  description?: Description;
  ttl?: Ttl;
  inactivity_timeout?: InactivityTimeout;
  [k: string]: unknown;
}
