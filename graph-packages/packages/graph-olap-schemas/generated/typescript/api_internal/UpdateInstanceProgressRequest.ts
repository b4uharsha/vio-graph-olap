/**
 * Current loading phase
 */
export type Phase = string;
/**
 * Step name (e.g., 'pod_scheduled', 'Customer', 'PURCHASED')
 */
export type Name = string;
/**
 * Step status
 */
export type Status = string;
/**
 * Step type for data loading steps
 */
export type Type = string | null;
/**
 * Row count (when completed)
 */
export type RowCount = number | null;
/**
 * Progress steps
 */
export type Steps = InstanceProgressStep[];

/**
 * Request to update instance loading progress.
 *
 * From api.internal.spec.md PUT /instances/:id/progress.
 * Called during instance startup to report loading progress.
 */
export interface UpdateInstanceProgressRequest {
  phase: Phase;
  steps?: Steps;
  [k: string]: unknown;
}
/**
 * Single step in instance loading progress.
 *
 * From api.internal.spec.md PUT /instances/:id/progress request.
 */
export interface InstanceProgressStep {
  name: Name;
  status: Status;
  type?: Type;
  row_count?: RowCount;
  [k: string]: unknown;
}
