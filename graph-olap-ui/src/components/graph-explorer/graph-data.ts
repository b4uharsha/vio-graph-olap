import Graph from "graphology";

export type NodeType = "Customer" | "Account" | "Address" | "Phone";

export interface NodeAttributes {
  label: string;
  type: NodeType;
  color: string;
  size: number;
  x: number;
  y: number;
  flagged?: boolean;
  // Extra properties per type
  balance?: number;
  since?: string;
  street?: string;
  city?: string;
  number?: string;
}

export interface EdgeAttributes {
  label: string;
  color: string;
  size: number;
  weight?: number;
  amount?: number;
}

const NODE_COLORS: Record<NodeType, string> = {
  Customer: "#3b82f6", // blue-500
  Account: "#22c55e", // green-500
  Address: "#f97316", // orange-500
  Phone: "#a855f7", // purple-500
};

/**
 * Build a sample fraud-network graph with realistic patterns.
 *
 * Layout:
 *  - Fraud Ring A (top-left): 4 customers sharing addresses/phones, linked accounts w/ transfers
 *  - Fraud Ring B (bottom-left): 3 customers with shared phone + address, circular transfers
 *  - Normal Cluster (right): 8 customers with independent addresses/phones/accounts
 */
export function createFraudGraph(): Graph<NodeAttributes, EdgeAttributes> {
  const graph = new Graph<NodeAttributes, EdgeAttributes>({ multi: true });

  // --- Helper -----------------------------------------------------------
  let nodeCount = 0;
  function addNode(
    id: string,
    type: NodeType,
    label: string,
    extra: Partial<NodeAttributes> = {},
  ) {
    const angle = (nodeCount / 50) * Math.PI * 2;
    const radius = 3 + Math.random() * 2;
    graph.addNode(id, {
      label,
      type,
      color: NODE_COLORS[type],
      size: 6,
      x: Math.cos(angle) * radius + (Math.random() - 0.5),
      y: Math.sin(angle) * radius + (Math.random() - 0.5),
      ...extra,
    });
    nodeCount++;
  }

  function addEdge(
    src: string,
    dst: string,
    label: string,
    extra: Partial<EdgeAttributes> = {},
  ) {
    graph.addEdge(src, dst, {
      label,
      color: "rgba(255,255,255,0.15)",
      size: 1,
      ...extra,
    });
  }

  // =====================================================================
  // FRAUD RING A  (top-left cluster)
  // 4 customers, 3 accounts, 2 addresses, 1 phone — heavy sharing
  // =====================================================================
  const ringA_cx = -5;
  const ringA_cy = 4;

  addNode("c1", "Customer", "Viktor Petrov", { flagged: true, x: ringA_cx - 1, y: ringA_cy + 1 });
  addNode("c2", "Customer", "Elena Morozova", { flagged: true, x: ringA_cx + 1, y: ringA_cy + 1 });
  addNode("c3", "Customer", "Dmitri Volkov", { flagged: true, x: ringA_cx - 1, y: ringA_cy - 1 });
  addNode("c4", "Customer", "Irina Kuznetsova", { flagged: true, x: ringA_cx + 1, y: ringA_cy - 1 });

  addNode("a1", "Account", "ACC-7891", { balance: 142300, since: "2023-01", x: ringA_cx - 2, y: ringA_cy });
  addNode("a2", "Account", "ACC-7892", { balance: 89400, since: "2023-03", x: ringA_cx, y: ringA_cy + 2 });
  addNode("a3", "Account", "ACC-7893", { balance: 215700, since: "2023-02", x: ringA_cx + 2, y: ringA_cy });

  addNode("addr1", "Address", "42 Elm Street, Newark", { street: "42 Elm Street", city: "Newark", x: ringA_cx, y: ringA_cy - 2 });
  addNode("addr2", "Address", "15 Oak Avenue, Newark", { street: "15 Oak Avenue", city: "Newark", x: ringA_cx - 2, y: ringA_cy - 2 });

  addNode("ph1", "Phone", "+1-555-0147", { number: "+1-555-0147", x: ringA_cx + 2, y: ringA_cy + 2 });

  // ownership
  addEdge("c1", "a1", "OWNS_ACCOUNT");
  addEdge("c2", "a2", "OWNS_ACCOUNT");
  addEdge("c3", "a3", "OWNS_ACCOUNT");
  addEdge("c4", "a1", "OWNS_ACCOUNT"); // shared account!
  addEdge("c4", "a2", "OWNS_ACCOUNT"); // shared account!

  // addresses — shared
  addEdge("c1", "addr1", "LIVES_AT");
  addEdge("c2", "addr1", "LIVES_AT"); // same address as c1
  addEdge("c3", "addr2", "LIVES_AT");
  addEdge("c4", "addr2", "LIVES_AT"); // same address as c3

  // phone — shared
  addEdge("c1", "ph1", "HAS_PHONE");
  addEdge("c2", "ph1", "HAS_PHONE");
  addEdge("c4", "ph1", "HAS_PHONE");

  // circular transfers
  addEdge("a1", "a2", "TRANSFERS_TO", { amount: 45000, color: "rgba(239,68,68,0.4)", size: 2 });
  addEdge("a2", "a3", "TRANSFERS_TO", { amount: 43500, color: "rgba(239,68,68,0.4)", size: 2 });
  addEdge("a3", "a1", "TRANSFERS_TO", { amount: 42000, color: "rgba(239,68,68,0.4)", size: 2 });
  addEdge("a1", "a3", "TRANSFERS_TO", { amount: 18000, color: "rgba(239,68,68,0.4)", size: 2 });

  // =====================================================================
  // FRAUD RING B  (bottom-left cluster)
  // 3 customers, 2 accounts, 1 address, 1 phone
  // =====================================================================
  const ringB_cx = -5;
  const ringB_cy = -4;

  addNode("c5", "Customer", "Marco Silva", { flagged: true, x: ringB_cx, y: ringB_cy + 1 });
  addNode("c6", "Customer", "Ana Costa", { flagged: true, x: ringB_cx - 1.5, y: ringB_cy - 1 });
  addNode("c7", "Customer", "Luis Ferreira", { flagged: true, x: ringB_cx + 1.5, y: ringB_cy - 1 });

  addNode("a4", "Account", "ACC-3310", { balance: 67800, since: "2022-11", x: ringB_cx - 2, y: ringB_cy });
  addNode("a5", "Account", "ACC-3311", { balance: 98200, since: "2023-05", x: ringB_cx + 2, y: ringB_cy });

  addNode("addr3", "Address", "8 Pine Road, Camden", { street: "8 Pine Road", city: "Camden", x: ringB_cx, y: ringB_cy - 2 });

  addNode("ph2", "Phone", "+1-555-0298", { number: "+1-555-0298", x: ringB_cx, y: ringB_cy + 2 });

  addEdge("c5", "a4", "OWNS_ACCOUNT");
  addEdge("c6", "a4", "OWNS_ACCOUNT"); // shared
  addEdge("c7", "a5", "OWNS_ACCOUNT");
  addEdge("c5", "a5", "OWNS_ACCOUNT"); // shared

  addEdge("c5", "addr3", "LIVES_AT");
  addEdge("c6", "addr3", "LIVES_AT");
  addEdge("c7", "addr3", "LIVES_AT"); // all same address

  addEdge("c5", "ph2", "HAS_PHONE");
  addEdge("c6", "ph2", "HAS_PHONE");

  addEdge("a4", "a5", "TRANSFERS_TO", { amount: 32000, color: "rgba(239,68,68,0.4)", size: 2 });
  addEdge("a5", "a4", "TRANSFERS_TO", { amount: 31500, color: "rgba(239,68,68,0.4)", size: 2 });

  // =====================================================================
  // NORMAL CLUSTER  (right side)
  // 8 customers, 5 accounts, 5 addresses, 3 phones — no sharing
  // =====================================================================
  const norm_cx = 5;
  const norm_cy = 0;

  const normalCustomers = [
    { id: "c8", name: "Sarah Johnson", x: norm_cx - 1, y: norm_cy + 3 },
    { id: "c9", name: "Michael Chen", x: norm_cx + 2, y: norm_cy + 2 },
    { id: "c10", name: "Jessica Williams", x: norm_cx + 3, y: norm_cy },
    { id: "c11", name: "David Brown", x: norm_cx + 2, y: norm_cy - 2 },
    { id: "c12", name: "Emily Davis", x: norm_cx - 1, y: norm_cy - 3 },
    { id: "c13", name: "Robert Wilson", x: norm_cx - 2, y: norm_cy - 1 },
    { id: "c14", name: "Amanda Taylor", x: norm_cx - 2, y: norm_cy + 1 },
    { id: "c15", name: "James Anderson", x: norm_cx + 1, y: norm_cy },
  ];

  normalCustomers.forEach((c) =>
    addNode(c.id, "Customer", c.name, { flagged: false, x: c.x, y: c.y }),
  );

  // accounts
  addNode("a6", "Account", "ACC-1001", { balance: 24500, since: "2021-06", x: norm_cx - 2, y: norm_cy + 3.5 });
  addNode("a7", "Account", "ACC-1002", { balance: 53200, since: "2020-02", x: norm_cx + 3, y: norm_cy + 3 });
  addNode("a8", "Account", "ACC-1003", { balance: 15800, since: "2022-08", x: norm_cx + 4, y: norm_cy - 1 });
  addNode("a9", "Account", "ACC-1004", { balance: 78900, since: "2019-12", x: norm_cx + 3, y: norm_cy - 3 });
  addNode("a10", "Account", "ACC-1005", { balance: 42100, since: "2021-04", x: norm_cx - 3, y: norm_cy });

  // addresses
  addNode("addr4", "Address", "100 Broadway, NYC", { street: "100 Broadway", city: "NYC", x: norm_cx, y: norm_cy + 4 });
  addNode("addr5", "Address", "250 Park Ave, NYC", { street: "250 Park Ave", city: "NYC", x: norm_cx + 4, y: norm_cy + 1 });
  addNode("addr6", "Address", "78 Maple Dr, Hoboken", { street: "78 Maple Dr", city: "Hoboken", x: norm_cx + 1, y: norm_cy - 4 });
  addNode("addr7", "Address", "55 River Rd, Hoboken", { street: "55 River Rd", city: "Hoboken", x: norm_cx - 3, y: norm_cy - 2 });
  addNode("addr8", "Address", "12 Cedar Ln, Princeton", { street: "12 Cedar Ln", city: "Princeton", x: norm_cx - 3, y: norm_cy + 2 });

  // phones
  addNode("ph3", "Phone", "+1-555-1001", { number: "+1-555-1001", x: norm_cx - 1, y: norm_cy + 5 });
  addNode("ph4", "Phone", "+1-555-1002", { number: "+1-555-1002", x: norm_cx + 5, y: norm_cy });
  addNode("ph5", "Phone", "+1-555-1003", { number: "+1-555-1003", x: norm_cx - 4, y: norm_cy - 1 });

  // Normal edges — each customer has their own account, address, phone
  addEdge("c8", "a6", "OWNS_ACCOUNT");
  addEdge("c9", "a7", "OWNS_ACCOUNT");
  addEdge("c10", "a8", "OWNS_ACCOUNT");
  addEdge("c11", "a9", "OWNS_ACCOUNT");
  addEdge("c12", "a9", "OWNS_ACCOUNT"); // two share an account (legitimate joint)
  addEdge("c13", "a10", "OWNS_ACCOUNT");
  addEdge("c14", "a10", "OWNS_ACCOUNT"); // joint account
  addEdge("c15", "a8", "OWNS_ACCOUNT");  // joint account

  addEdge("c8", "addr4", "LIVES_AT");
  addEdge("c9", "addr4", "LIVES_AT");
  addEdge("c10", "addr5", "LIVES_AT");
  addEdge("c11", "addr5", "LIVES_AT");
  addEdge("c12", "addr6", "LIVES_AT");
  addEdge("c13", "addr7", "LIVES_AT");
  addEdge("c14", "addr8", "LIVES_AT");
  addEdge("c15", "addr6", "LIVES_AT");

  addEdge("c8", "ph3", "HAS_PHONE");
  addEdge("c9", "ph3", "HAS_PHONE");
  addEdge("c10", "ph4", "HAS_PHONE");
  addEdge("c11", "ph4", "HAS_PHONE");
  addEdge("c12", "ph5", "HAS_PHONE");
  addEdge("c13", "ph5", "HAS_PHONE");
  addEdge("c14", "ph5", "HAS_PHONE");
  addEdge("c15", "ph4", "HAS_PHONE");

  // some legitimate transfers between normal accounts
  addEdge("a6", "a7", "TRANSFERS_TO", { amount: 500 });
  addEdge("a7", "a8", "TRANSFERS_TO", { amount: 1200 });
  addEdge("a9", "a10", "TRANSFERS_TO", { amount: 800 });
  addEdge("a10", "a6", "TRANSFERS_TO", { amount: 350 });
  addEdge("a8", "a9", "TRANSFERS_TO", { amount: 2100 });

  // cross-cluster: a fraud account sends money into the normal cluster
  addEdge("a3", "a7", "TRANSFERS_TO", { amount: 15000, color: "rgba(239,68,68,0.4)", size: 2 });
  addEdge("a5", "a9", "TRANSFERS_TO", { amount: 12000, color: "rgba(239,68,68,0.4)", size: 2 });

  // --- Size nodes by degree ---
  graph.forEachNode((node) => {
    const degree = graph.degree(node);
    graph.setNodeAttribute(node, "size", 4 + degree * 1.5);
  });

  return graph;
}
