/**
 * Export jobs to create (one per node/edge definition)
 *
 * @minItems 1
 */
export type Jobs = [ExportJobDefinition, ...ExportJobDefinition[]];
/**
 * Type of export: 'node' or 'edge'
 */
export type JobType = string;
/**
 * Node label or edge type name
 */
export type EntityName = string;
/**
 * Starburst query ID from submission
 */
export type StarburstQueryId = string;
/**
 * Starburst polling URI
 */
export type NextUri = string;
/**
 * GCS destination path
 */
export type GcsPath = string;
/**
 * Initial status (default: 'running')
 */
export type Status = string;
/**
 * When query was submitted (default: current time)
 */
export type SubmittedAt = string | null;

/**
 * Request to create export jobs for a snapshot.
 *
 * From api.internal.spec.md POST /snapshots/:id/export-jobs.
 * Called by Export Submitter after submitting UNLOAD queries to Starburst.
 */
export interface CreateExportJobsRequest {
  jobs: Jobs;
  [k: string]: unknown;
}
/**
 * Single export job definition for batch creation.
 *
 * From api.internal.spec.md POST /snapshots/:id/export-jobs request.
 */
export interface ExportJobDefinition {
  job_type: JobType;
  entity_name: EntityName;
  starburst_query_id: StarburstQueryId;
  next_uri: NextUri;
  gcs_path: GcsPath;
  status?: Status;
  submitted_at?: SubmittedAt;
  [k: string]: unknown;
}
