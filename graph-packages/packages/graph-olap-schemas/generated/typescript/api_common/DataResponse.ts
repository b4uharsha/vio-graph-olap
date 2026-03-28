/**
 * Unique request identifier for tracing
 */
export type RequestId = string | null;

/**
 * Standard single-resource response wrapper.
 *
 * From api.common.spec.md:
 * ```json
 * {
 *   "data": {...},
 *   "meta": {
 *     "request_id": "req-uuid"
 *   }
 * }
 * ```
 */
export interface DataResponse {
  data: Data;
  meta?: Meta;
  [k: string]: unknown;
}
export interface Data {
  [k: string]: unknown;
}
/**
 * Response metadata included in all API responses.
 *
 * From api.common.spec.md:
 * ```json
 * "meta": {
 *   "request_id": "550e8400-e29b-41d4-a716-446655440000"
 * }
 * ```
 */
export interface Meta {
  request_id?: RequestId;
  [k: string]: unknown;
}
