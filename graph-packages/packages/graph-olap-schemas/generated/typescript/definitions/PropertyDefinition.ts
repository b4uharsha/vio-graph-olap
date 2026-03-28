/**
 * Property column name (ASCII letters, numbers, underscore; starts with letter)
 */
export type Name = string;
/**
 * Ryugraph data type for this property
 */
export type RyugraphType =
  | "STRING"
  | "INT64"
  | "INT32"
  | "INT16"
  | "INT8"
  | "DOUBLE"
  | "FLOAT"
  | "DATE"
  | "TIMESTAMP"
  | "BOOL"
  | "BLOB"
  | "UUID"
  | "LIST"
  | "MAP"
  | "STRUCT";

/**
 * Property definition for nodes or edges.
 *
 * From requirements.md Node/Edge Definition Structure:
 * ```json
 * {"name": "city", "type": "STRING"}
 * ```
 *
 * Properties define additional data columns beyond the primary/foreign keys.
 * The order of properties in the array must match the SELECT column order.
 */
export interface PropertyDefinition {
  name: Name;
  type: RyugraphType;
  [k: string]: unknown;
}
