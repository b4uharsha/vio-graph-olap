/**
 * Updated display name
 */
export type Name = string | null;
/**
 * Updated description
 */
export type Description = string | null;
/**
 * Updated node definitions (creates new version)
 */
export type NodeDefinitions = NodeDefinition[] | null;
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
export type Name1 = string;
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
export type Name2 = string;
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
 * Updated edge definitions (creates new version)
 */
export type EdgeDefinitions = EdgeDefinition[] | null;
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
export type Sql1 = string;
/**
 * Column name for source node reference (first in SELECT)
 */
export type FromKey = string;
/**
 * Column name for target node reference (second in SELECT)
 */
export type ToKey = string;
/**
 * Property columns in SELECT order (after from/to keys)
 *
 * @maxItems 100
 */
export type Properties1 = PropertyDefinition[];
/**
 * Description of changes (required for updates)
 */
export type ChangeDescription = string;
/**
 * Updated time-to-live
 */
export type Ttl = string | null;
/**
 * Updated inactivity timeout
 */
export type InactivityTimeout = string | null;

/**
 * Request to update a mapping.
 *
 * From api.mappings.spec.md PUT /api/mappings/:id.
 * Creates a new version if definitions changed. Requires change_description.
 */
export interface UpdateMappingRequest {
  name?: Name;
  description?: Description;
  node_definitions?: NodeDefinitions;
  edge_definitions?: EdgeDefinitions;
  change_description: ChangeDescription;
  ttl?: Ttl;
  inactivity_timeout?: InactivityTimeout;
  [k: string]: unknown;
}
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
  name: Name1;
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
  name: Name2;
  type: RyugraphType1;
  [k: string]: unknown;
}
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
  sql: Sql1;
  from_key: FromKey;
  to_key: ToKey;
  properties?: Properties1;
  [k: string]: unknown;
}
