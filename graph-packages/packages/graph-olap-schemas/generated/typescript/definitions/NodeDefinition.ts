/**
 * Ryugraph node table name (ASCII letters, numbers, underscore; starts with letter)
 */
export type Label = string;
/**
 * Starburst SQL query (primary_key column must be first in SELECT)
 */
export type Sql = string;
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
 * Property column name (ASCII letters, numbers, underscore; starts with letter)
 */
export type Name1 = string;
/**
 * Ryugraph data type for this property
 */
export type RyugraphType1 =
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
 * Property columns in SELECT order (after primary key)
 *
 * @maxItems 100
 */
export type Properties = PropertyDefinition[];

/**
 * Node definition in a mapping.
 *
 * From requirements.md:
 * ```json
 * {
 *   "label": "Customer",
 *   "sql": "SELECT customer_id, name, city FROM analytics.customers",
 *   "primary_key": {"name": "customer_id", "type": "STRING"},
 *   "properties": [
 *     {"name": "name", "type": "STRING"},
 *     {"name": "city", "type": "STRING"}
 *   ]
 * }
 * ```
 *
 * Constraints:
 * - label: 1-64 chars, ASCII letters/numbers/underscore, starts with letter
 * - label: unique per mapping version
 * - label: cannot be a Cypher reserved word or use system prefix
 * - sql: Starburst SQL query (primary_key column must be first in SELECT)
 * - properties: in SELECT order (after primary key)
 */
export interface NodeDefinition {
  label: Label;
  sql: Sql;
  primary_key: PrimaryKeyDefinition;
  properties?: Properties;
  [k: string]: unknown;
}
/**
 * Primary key column definition
 */
export interface PrimaryKeyDefinition {
  name: Name;
  type: RyugraphType;
  [k: string]: unknown;
}
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
  name: Name1;
  type: RyugraphType1;
  [k: string]: unknown;
}
