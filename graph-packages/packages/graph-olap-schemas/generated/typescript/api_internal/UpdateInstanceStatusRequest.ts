/**
 * New instance status
 */
export type Status = string;
/**
 * Kubernetes pod name (when running)
 */
export type PodName = string | null;
/**
 * Internal pod IP (when running)
 */
export type PodIp = string | null;
/**
 * Unique access URL (when running)
 */
export type InstanceUrl = string | null;
/**
 * Loading progress details
 */
export type Progress = {
  [k: string]: unknown;
} | null;
/**
 * Total node count
 */
export type NodeCount = number;
/**
 * Total edge count
 */
export type EdgeCount = number;
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
/**
 * Human-readable error details (when failed)
 */
export type ErrorMessage = string | null;
/**
 * Phase that failed (when failed)
 */
export type FailedPhase = string | null;
/**
 * Stack trace for debugging (when failed)
 */
export type StackTrace = string | null;

/**
 * Request to update instance status.
 *
 * From api.internal.spec.md PUT /instances/:id/status.
 * Called by Wrapper Pod to report status changes.
 */
export interface UpdateInstanceStatusRequest {
  status: Status;
  pod_name?: PodName;
  pod_ip?: PodIp;
  instance_url?: InstanceUrl;
  progress?: Progress;
  /**
   * Graph statistics (when running)
   */
  graph_stats?: GraphStats | null;
  /**
   * Machine-readable error code (when failed)
   */
  error_code?: InstanceErrorCode | null;
  error_message?: ErrorMessage;
  failed_phase?: FailedPhase;
  stack_trace?: StackTrace;
  [k: string]: unknown;
}
/**
 * Graph statistics for running instance.
 */
export interface GraphStats {
  node_count: NodeCount;
  edge_count: EdgeCount;
  [k: string]: unknown;
}
