// Mock data used as fallback when the backend API is unavailable

export interface Mapping {
  id: string;
  name: string;
  description: string;
  owner: string;
  version: number;
  nodes: NodeDefinition[];
  edges: EdgeDefinition[];
  createdAt: string;
  updatedAt: string;
}

export interface NodeDefinition {
  label: string;
  sql: string;
  primaryKey: string;
}

export interface EdgeDefinition {
  type: string;
  sql: string;
  fromColumn: string;
  toColumn: string;
}

export interface Instance {
  id: string;
  name: string;
  mappingId: string;
  mappingName: string;
  status: "running" | "starting" | "failed" | "terminated";
  wrapperType: "falkordb" | "ryugraph";
  memory: string;
  cpuCores: number;
  ttl: number;
  createdAt: string;
  endpoint?: string;
}

export interface InstanceProgress {
  instanceId: string;
  stage: string;
  percent: number;
  message: string;
}

export const mockMappings: Mapping[] = [
  {
    id: "map-001",
    name: "Customer Graph",
    description: "Customer transaction and relationship network for fraud detection",
    owner: "analytics-team",
    version: 3,
    nodes: [
      { label: "Customer", sql: "SELECT id, name, email FROM customers", primaryKey: "id" },
      { label: "Account", sql: "SELECT id, type, balance FROM accounts", primaryKey: "id" },
      { label: "Transaction", sql: "SELECT id, amount, ts FROM transactions", primaryKey: "id" },
    ],
    edges: [
      { type: "OWNS", sql: "SELECT customer_id, account_id FROM customer_accounts", fromColumn: "customer_id", toColumn: "account_id" },
      { type: "TRANSFERRED_TO", sql: "SELECT from_acct, to_acct FROM transfers", fromColumn: "from_acct", toColumn: "to_acct" },
    ],
    createdAt: "2026-03-15T10:30:00Z",
    updatedAt: "2026-03-25T14:20:00Z",
  },
  {
    id: "map-002",
    name: "Supply Chain",
    description: "End-to-end supply chain visibility across warehouses and suppliers",
    owner: "ops-team",
    version: 1,
    nodes: [
      { label: "Supplier", sql: "SELECT id, name, region FROM suppliers", primaryKey: "id" },
      { label: "Warehouse", sql: "SELECT id, location, capacity FROM warehouses", primaryKey: "id" },
      { label: "Product", sql: "SELECT sku, name, category FROM products", primaryKey: "sku" },
    ],
    edges: [
      { type: "SUPPLIES", sql: "SELECT supplier_id, product_sku FROM supply_lines", fromColumn: "supplier_id", toColumn: "product_sku" },
      { type: "STORED_AT", sql: "SELECT product_sku, warehouse_id FROM inventory", fromColumn: "product_sku", toColumn: "warehouse_id" },
    ],
    createdAt: "2026-03-10T08:00:00Z",
    updatedAt: "2026-03-10T08:00:00Z",
  },
  {
    id: "map-003",
    name: "Fraud Network",
    description: "Shared-attribute fraud ring detection across accounts and devices",
    owner: "security-team",
    version: 5,
    nodes: [
      { label: "Person", sql: "SELECT id, name, ssn_hash FROM persons", primaryKey: "id" },
      { label: "Device", sql: "SELECT fingerprint, os, ip FROM devices", primaryKey: "fingerprint" },
      { label: "Address", sql: "SELECT id, street, city, zip FROM addresses", primaryKey: "id" },
    ],
    edges: [
      { type: "USED_DEVICE", sql: "SELECT person_id, device_fp FROM logins", fromColumn: "person_id", toColumn: "device_fp" },
      { type: "LIVES_AT", sql: "SELECT person_id, address_id FROM residences", fromColumn: "person_id", toColumn: "address_id" },
    ],
    createdAt: "2026-02-20T16:45:00Z",
    updatedAt: "2026-03-27T09:15:00Z",
  },
];

export const mockInstances: Instance[] = [
  {
    id: "inst-001",
    name: "fraud-detection-prod",
    mappingId: "map-001",
    mappingName: "Customer Graph",
    status: "running",
    wrapperType: "falkordb",
    memory: "4.2 GB",
    cpuCores: 4,
    ttl: 24,
    createdAt: "2026-03-27T08:00:00Z",
    endpoint: "graph://localhost:6379",
  },
  {
    id: "inst-002",
    name: "supply-chain-analysis",
    mappingId: "map-002",
    mappingName: "Supply Chain",
    status: "terminated",
    wrapperType: "ryugraph",
    memory: "2.1 GB",
    cpuCores: 2,
    ttl: 8,
    createdAt: "2026-03-25T14:00:00Z",
  },
];

export const mockActivities = [
  { id: 1, action: "Instance created", detail: "fraud-detection-prod launched with FalkorDB", time: "2 hours ago", type: "instance" as const },
  { id: 2, action: "Mapping updated", detail: "Fraud Network mapping updated to v5", time: "5 hours ago", type: "mapping" as const },
  { id: 3, action: "Query executed", detail: "PageRank completed on Customer Graph (1,247 nodes)", time: "6 hours ago", type: "query" as const },
  { id: 4, action: "Instance terminated", detail: "supply-chain-analysis TTL expired", time: "1 day ago", type: "instance" as const },
  { id: 5, action: "Mapping created", detail: "Supply Chain mapping created by ops-team", time: "3 days ago", type: "mapping" as const },
];
