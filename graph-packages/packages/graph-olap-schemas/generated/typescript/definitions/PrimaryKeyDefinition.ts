/**
 * Primary key column name
 */
export type Name = string;
/**
 * Ryugraph data type for the primary key
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
 * Primary key definition for nodes.
 *
 * From requirements.md Node Definition Structure:
 * ```json
 * "primary_key": {"name": "customer_id", "type": "STRING"}
 * ```
 *
 * The primary key column must be the first column in the SQL SELECT statement.
 */
export interface PrimaryKeyDefinition {
  name: Name;
  type: RyugraphType;
  [k: string]: unknown;
}
