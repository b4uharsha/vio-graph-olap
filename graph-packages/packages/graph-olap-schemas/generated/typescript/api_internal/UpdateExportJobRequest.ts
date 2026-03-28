/**
 * New status
 */
export type Status = string | null;
/**
 * Starburst query ID (required when status=running)
 */
export type StarburstQueryId = string | null;
/**
 * Updated Starburst polling URI
 */
export type NextUri = string | null;
/**
 * Final row count (when completed)
 */
export type RowCount = number | null;
/**
 * Final size in bytes (when completed)
 */
export type SizeBytes = number | null;
/**
 * When job completed (default: current time if status=completed)
 */
export type CompletedAt = string | null;
/**
 * Error details (when failed)
 */
export type ErrorMessage = string | null;

/**
 * Request to update a single export job's status.
 *
 * From api.internal.spec.md PATCH /export-jobs/:id.
 * Called by Export Poller to update job status and results.
 */
export interface UpdateExportJobRequest {
  status?: Status;
  starburst_query_id?: StarburstQueryId;
  next_uri?: NextUri;
  row_count?: RowCount;
  size_bytes?: SizeBytes;
  completed_at?: CompletedAt;
  error_message?: ErrorMessage;
  [k: string]: unknown;
}
