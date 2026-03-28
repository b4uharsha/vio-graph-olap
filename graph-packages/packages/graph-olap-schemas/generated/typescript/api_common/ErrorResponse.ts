/**
 * Machine-readable error code
 */
export type Code = string;
/**
 * Human-readable error description
 */
export type Message = string;
/**
 * Unique request identifier for tracing
 */
export type RequestId = string | null;

/**
 * Standard error response format.
 *
 * From api.common.spec.md:
 * ```json
 * {
 *   "error": {
 *     "code": "ERROR_CODE",
 *     "message": "Human-readable description",
 *     "details": {...}
 *   },
 *   "meta": {
 *     "request_id": "req-uuid"
 *   }
 * }
 * ```
 */
export interface ErrorResponse {
  error: ErrorDetail;
  meta?: Meta;
  [k: string]: unknown;
}
/**
 * Error detail structure for API error responses.
 *
 * From api.common.spec.md:
 * ```json
 * "error": {
 *   "code": "ERROR_CODE",
 *   "message": "Human-readable description",
 *   "details": {
 *     "field": "specific_field",
 *     "reason": "additional context"
 *   }
 * }
 * ```
 *
 * Error codes from api.common.spec.md Error Codes Reference section.
 */
export interface ErrorDetail {
  code: Code;
  message: Message;
  details?: Details;
  [k: string]: unknown;
}
/**
 * Additional context about the error
 */
export interface Details {
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
