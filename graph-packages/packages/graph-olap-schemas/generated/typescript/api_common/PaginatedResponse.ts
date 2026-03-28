export type Data = unknown[];
/**
 * Unique request identifier for tracing
 */
export type RequestId = string | null;
/**
 * Total number of matching records
 */
export type Total = number;
/**
 * Current offset (records skipped)
 */
export type Offset = number;
/**
 * Current limit (records per page)
 */
export type Limit = number;

/**
 * Standard paginated list response wrapper.
 *
 * From api.common.spec.md:
 * ```json
 * {
 *   "data": [{...}, {...}],
 *   "meta": {
 *     "request_id": "req-uuid",
 *     "total": 150,
 *     "offset": 0,
 *     "limit": 50
 *   }
 * }
 * ```
 */
export interface PaginatedResponse {
  data: Data;
  meta: PaginationMeta;
  [k: string]: unknown;
}
/**
 * Metadata for paginated list responses.
 *
 * From api.common.spec.md:
 * ```json
 * "meta": {
 *   "request_id": "req-uuid",
 *   "total": 150,
 *   "offset": 0,
 *   "limit": 50
 * }
 * ```
 */
export interface PaginationMeta {
  request_id?: RequestId;
  total: Total;
  offset: Offset;
  limit: Limit;
  [k: string]: unknown;
}
