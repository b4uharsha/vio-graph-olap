/**
 * New snapshot status
 */
export type Status = string;
/**
 * Current export phase (when status=creating)
 */
export type Phase = string | null;
/**
 * Current entity being exported (node label or edge type)
 */
export type CurrentStep = string | null;
/**
 * Number of completed export steps
 */
export type CompletedSteps = number;
/**
 * Total number of export steps
 */
export type TotalSteps = number;
/**
 * Total storage size (when status=ready)
 */
export type SizeBytes = number | null;
/**
 * Node counts by label (when status=ready)
 */
export type NodeCounts = {
  [k: string]: number;
} | null;
/**
 * Edge counts by type (when status=ready)
 */
export type EdgeCounts = {
  [k: string]: number;
} | null;
/**
 * Error details (when status=failed)
 */
export type ErrorMessage = string | null;
/**
 * Entity name that failed (when status=failed)
 */
export type FailedStep = string | null;
/**
 * Partial node/edge counts (when status=failed)
 */
export type PartialResults = {
  [k: string]: unknown;
} | null;

/**
 * Request to update snapshot status during processing.
 *
 * From api.internal.spec.md PUT /snapshots/:id/status.
 * Called by Export Worker to update snapshot status.
 *
 * Status values: "pending", "creating", "ready", "failed"
 */
export interface UpdateSnapshotStatusRequest {
  status: Status;
  phase?: Phase;
  /**
   * Progress details (when status=creating)
   */
  progress?: SnapshotProgress | null;
  size_bytes?: SizeBytes;
  node_counts?: NodeCounts;
  edge_counts?: EdgeCounts;
  error_message?: ErrorMessage;
  failed_step?: FailedStep;
  partial_results?: PartialResults;
  [k: string]: unknown;
}
/**
 * Progress information for snapshot creation.
 *
 * From api.internal.spec.md PUT /snapshots/:id/status request body.
 */
export interface SnapshotProgress {
  current_step?: CurrentStep;
  completed_steps: CompletedSteps;
  total_steps: TotalSteps;
  [k: string]: unknown;
}
