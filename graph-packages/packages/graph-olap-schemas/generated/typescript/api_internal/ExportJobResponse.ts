export type Id = number;
export type SnapshotId = number;
export type JobType = string;
export type EntityName = string;
/**
 * Export job states.
 */
export type ExportJobStatus = "pending" | "running" | "completed" | "failed";
export type StarburstQueryId = string | null;
export type NextUri = string | null;
export type GcsPath = string;
export type RowCount = number | null;
export type SizeBytes = number | null;
export type SubmittedAt = string | null;
export type CompletedAt = string | null;
export type ErrorMessage = string | null;

/**
 * Export job response.
 *
 * From api.internal.spec.md GET /snapshots/:id/export-jobs response.
 */
export interface ExportJobResponse {
  id: Id;
  snapshot_id: SnapshotId;
  job_type: JobType;
  entity_name: EntityName;
  status: ExportJobStatus;
  starburst_query_id: StarburstQueryId;
  next_uri: NextUri;
  gcs_path: GcsPath;
  row_count: RowCount;
  size_bytes: SizeBytes;
  submitted_at: SubmittedAt;
  completed_at: CompletedAt;
  error_message: ErrorMessage;
  [k: string]: unknown;
}
