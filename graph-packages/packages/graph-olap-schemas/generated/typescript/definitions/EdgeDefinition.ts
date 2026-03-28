/**
 * Ryugraph relationship table name (ASCII uppercase letters, numbers, underscore)
 */
export type Type = string;
/**
 * Source node label (must exist in node_definitions)
 */
export type FromNode = string;
/**
 * Target node label (must exist in node_definitions)
 */
export type ToNode = string;
/**
 * Starburst SQL query (from_key first, to_key second, then properties)
 */
export type Sql = string;
/**
 * Column name for source node reference (first in SELECT)
 */
export type FromKey = string;
/**
 * Column name for target node reference (second in SELECT)
 */
export type ToKey = string;
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
 * Property columns in SELECT order (after from/to keys)
 *
 * @maxItems 100
 */
export type Properties = PropertyDefinition[];

/**
 * Edge definition in a mapping.
 *
 * From requirements.md:
 * ```json
 * {
 *   "type": "PURCHASED",
 *   "from_node": "Customer",
 *   "to_node": "Product",
 *   "sql": "SELECT customer_id, product_id, amount, purchase_date FROM analytics.transactions",
 *   "from_key": "customer_id",
 *   "to_key": "product_id",
 *   "properties": [
 *     {"name": "amount", "type": "DOUBLE"},
 *     {"name": "purchase_date", "type": "DATE"}
 *   ]
 * }
 * ```
 *
 * Constraints:
 * - type: 1-64 chars, ASCII uppercase letters/numbers/underscore
 * - type: unique per mapping version
 * - type: cannot be a Cypher reserved word or use system prefix
 * - from_node/to_node: must reference existing node labels in the mapping
 * - sql: Starburst SQL (from_key first, to_key second, then properties in SELECT)
 * - from_key/to_key: types inferred from referenced node primary keys
 */
export interface EdgeDefinition {
  type: Type;
  from_node: FromNode;
  to_node: ToNode;
  sql: Sql;
  from_key: FromKey;
  to_key: ToKey;
  properties?: Properties;
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
  name: Name;
  type: RyugraphType;
  [k: string]: unknown;
}
