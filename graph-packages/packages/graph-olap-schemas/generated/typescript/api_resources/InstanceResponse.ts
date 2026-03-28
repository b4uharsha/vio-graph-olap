export type Id = number;
export type SnapshotId = number;
export type OwnerUsername = string;
export type Name = string;
export type Description = string | null;
/**
 * Instance lifecycle states.
 *
 * From requirements.md: "status | enum | starting, running, stopping, failed"
 * Note: "stopping = terminating, instance deleted when complete"
 */
export type InstanceStatus = "starting" | "running" | "stopping" | "failed";
export type InstanceUrl = string | null;
export type PodName = string | null;
export type Progress = {
  [k: string]: unknown;
} | null;
/**
 * Machine-readable error codes for instance failures.
 *
 * From api.internal.spec.md PUT /instances/:id/status.
 * Used to categorize failure types for debugging and display.
 */
export type InstanceErrorCode =
  | "STARTUP_FAILED"
  | "MAPPING_FETCH_ERROR"
  | "SCHEMA_CREATE_ERROR"
  | "DATA_LOAD_ERROR"
  | "DATABASE_ERROR"
  | "OOM_KILLED";
export type ErrorMessage = string | null;
export type StackTrace = string | null;
export type CreatedAt = string | null;
export type UpdatedAt = string | null;
export type StartedAt = string | null;
export type LastActivityAt = string | null;
export type Ttl = string | null;
export type InactivityTimeout = string | null;
export type MemoryUsageBytes = number | null;
export type DiskUsageBytes = number | null;

/**
 * Instance response.
 *
 * From api.instances.spec.md GET /api/instances/:id response.
 */
export interface InstanceResponse {
  id: Id;
  snapshot_id: SnapshotId;
  owner_username: OwnerUsername;
  name: Name;
  description: Description;
  status: InstanceStatus;
  instance_url: InstanceUrl;
  pod_name: PodName;
  progress: Progress;
  error_code?: InstanceErrorCode | null;
  error_message: ErrorMessage;
  stack_trace?: StackTrace;
  created_at: CreatedAt;
  updated_at: UpdatedAt;
  started_at: StartedAt;
  last_activity_at: LastActivityAt;
  ttl: Ttl;
  inactivity_timeout: InactivityTimeout;
  memory_usage_bytes: MemoryUsageBytes;
  disk_usage_bytes: DiskUsageBytes;
  [k: string]: unknown;
}
