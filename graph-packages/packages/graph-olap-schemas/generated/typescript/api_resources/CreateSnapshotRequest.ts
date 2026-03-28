/**
 * Source mapping ID
 */
export type MappingId = number;
/**
 * Mapping version (defaults to current_version)
 */
export type MappingVersion = number | null;
/**
 * Display name for the snapshot
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
 * Delete after no instances created
 */
export type InactivityTimeout = string | null;

/**
 * Request to create a snapshot from a mapping.
 *
 * From api.snapshots.spec.md POST /api/snapshots.
 */
export interface CreateSnapshotRequest {
  mapping_id: MappingId;
  mapping_version?: MappingVersion;
  name: Name;
  description?: Description;
  ttl?: Ttl;
  inactivity_timeout?: InactivityTimeout;
  [k: string]: unknown;
}
