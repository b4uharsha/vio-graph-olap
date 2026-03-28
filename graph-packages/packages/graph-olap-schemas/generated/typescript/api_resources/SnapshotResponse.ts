export type Id = number;
export type MappingId = number;
export type MappingVersion = number;
export type OwnerUsername = string;
export type Name = string;
export type Description = string | null;
export type GcsPath = string;
/**
 * Snapshot lifecycle states.
 *
 * From requirements.md: "status | enum | pending, creating, ready, failed, cancelled"
 */
export type SnapshotStatus = "pending" | "creating" | "ready" | "failed" | "cancelled";
export type SizeBytes = number | null;
export type NodeCounts = {
  [k: string]: number;
} | null;
export type EdgeCounts = {
  [k: string]: number;
} | null;
export type Progress = {
  [k: string]: unknown;
} | null;
export type ErrorMessage = string | null;
export type CreatedAt = string | null;
export type UpdatedAt = string | null;
export type Ttl = string | null;
export type InactivityTimeout = string | null;
export type LastUsedAt = string | null;

/**
 * Snapshot response.
 *
 * From api.snapshots.spec.md GET /api/snapshots/:id response.
 */
export interface SnapshotResponse {
  id: Id;
  mapping_id: MappingId;
  mapping_version: MappingVersion;
  owner_username: OwnerUsername;
  name: Name;
  description: Description;
  gcs_path: GcsPath;
  status: SnapshotStatus;
  size_bytes: SizeBytes;
  node_counts: NodeCounts;
  edge_counts: EdgeCounts;
  progress: Progress;
  error_message: ErrorMessage;
  created_at: CreatedAt;
  updated_at: UpdatedAt;
  ttl: Ttl;
  inactivity_timeout: InactivityTimeout;
  last_used_at: LastUsedAt;
  [k: string]: unknown;
}
