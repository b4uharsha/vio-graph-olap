import { CypherResult } from "@/lib/cypher-ai";

interface DemoEntry {
  keywords: string[];
  result: CypherResult;
}

const demoEntries: DemoEntry[] = [
  {
    keywords: ["fraud", "flagged", "customer"],
    result: {
      cypher: `MATCH (c:Customer {flagged: true})
RETURN c.id, c.name, c.risk_score
ORDER BY c.risk_score DESC`,
      explanation:
        "This query finds all customers where the flagged property is true and returns their details, sorted by risk score in descending order.",
    },
  },
  {
    keywords: ["fraud", "connected", "hop"],
    result: {
      cypher: `MATCH (c:Customer {flagged: true})-[:OWNS_ACCOUNT]->(a:Account)
      -[:TRANSFERS_TO*1..3]->(b:Account)<-[:OWNS_ACCOUNT]-(c2:Customer)
WHERE c2 <> c
RETURN DISTINCT c2.id, c2.name, c2.risk_score,
       length(shortestPath((c)-[*]-(c2))) AS distance
ORDER BY distance ASC`,
      explanation:
        "This query starts from fraud-flagged customers, follows their accounts through up to 3 transfer hops, and finds other customers connected to those accounts. It returns the connected customers sorted by their distance from the flagged customer.",
    },
  },
  {
    keywords: ["highest", "transfer", "volume"],
    result: {
      cypher: `MATCH (a:Account)-[t:TRANSFERS_TO]->()
WITH a, COUNT(t) AS txn_count, SUM(t.amount) AS total_volume
RETURN a.id, a.number, a.type, txn_count, total_volume
ORDER BY total_volume DESC
LIMIT 10`,
      explanation:
        "This query aggregates all outgoing transfers for each account, calculating both the number of transactions and the total amount transferred. It returns the top 10 accounts by total transfer volume.",
    },
  },
  {
    keywords: ["shared", "address", "flagged"],
    result: {
      cypher: `MATCH (c1:Customer {flagged: true})-[:LIVES_AT]->(addr:Address)
      <-[:LIVES_AT]-(c2:Customer {flagged: true})
WHERE c1.id < c2.id
RETURN c1.name AS customer_1, c2.name AS customer_2,
       addr.street, addr.city, addr.country`,
      explanation:
        "This query finds pairs of flagged customers who share the same address. The WHERE clause with c1.id < c2.id prevents duplicate pairs from appearing in the results.",
    },
  },
  {
    keywords: ["pagerank", "rank", "network"],
    result: {
      cypher: `CALL algo.pageRank('Customer', 'OWNS_ACCOUNT|TRANSFERS_TO', {
  iterations: 20,
  dampingFactor: 0.85,
  writeProperty: 'pagerank'
})
YIELD nodes, iterations, loadMillis, computeMillis, writeMillis
RETURN nodes, iterations, loadMillis, computeMillis, writeMillis`,
      explanation:
        "This query runs the PageRank algorithm on the customer network, considering both account ownership and transfer relationships. It uses 20 iterations with a standard damping factor of 0.85 and writes the result back to a pagerank property on each node.",
    },
  },
  {
    keywords: ["large", "amount", "transaction", "over", "above"],
    result: {
      cypher: `MATCH (a1:Account)-[t:TRANSFERS_TO]->(a2:Account)
WHERE t.amount > $threshold
RETURN a1.number AS from_account, a2.number AS to_account,
       t.amount, t.date
ORDER BY t.amount DESC
LIMIT 25`,
      explanation:
        "This query finds all transfers above a given threshold amount. It uses a parameterized query ($threshold) so you can set the value at runtime. Results are sorted by amount descending.",
    },
  },
  {
    keywords: ["customer", "account", "balance"],
    result: {
      cypher: `MATCH (c:Customer)-[:OWNS_ACCOUNT]->(a:Account)
RETURN c.name, COLLECT(a.number) AS accounts,
       SUM(a.balance) AS total_balance,
       COUNT(a) AS account_count
ORDER BY total_balance DESC`,
      explanation:
        "This query lists each customer along with all their accounts, total balance across all accounts, and the number of accounts they own, sorted by total balance.",
    },
  },
  {
    keywords: ["circular", "loop", "cycle", "ring"],
    result: {
      cypher: `MATCH path = (a:Account)-[:TRANSFERS_TO*3..6]->(a)
WITH a, path, length(path) AS cycle_length
RETURN a.number AS account,
       [n IN nodes(path) | n.number] AS cycle_accounts,
       cycle_length
ORDER BY cycle_length ASC
LIMIT 20`,
      explanation:
        "This query detects circular transfer patterns (money laundering rings) by finding paths of 3 to 6 hops that return to the starting account. These cycles can indicate suspicious activity.",
    },
  },
  {
    keywords: ["country", "international", "cross-border"],
    result: {
      cypher: `MATCH (c1:Customer)-[:OWNS_ACCOUNT]->(a1:Account)-[t:TRANSFERS_TO]->(a2:Account)
      <-[:OWNS_ACCOUNT]-(c2:Customer),
      (c1)-[:LIVES_AT]->(addr1:Address),
      (c2)-[:LIVES_AT]->(addr2:Address)
WHERE addr1.country <> addr2.country
RETURN addr1.country AS from_country, addr2.country AS to_country,
       COUNT(t) AS transfer_count, SUM(t.amount) AS total_amount
ORDER BY total_amount DESC`,
      explanation:
        "This query identifies cross-border transfers by matching customers who live in different countries and have transfer relationships between their accounts. Results are grouped by country pair.",
    },
  },
  {
    keywords: ["phone", "number", "shared", "common"],
    result: {
      cypher: `MATCH (c1:Customer)-[:HAS_PHONE]->(p:Phone)<-[:HAS_PHONE]-(c2:Customer)
WHERE c1.id < c2.id
RETURN c1.name AS customer_1, c2.name AS customer_2,
       p.number AS shared_phone
ORDER BY p.number`,
      explanation:
        "This query finds customers who share the same phone number, which can be an indicator of identity fraud or related accounts. The WHERE clause prevents duplicate pairs.",
    },
  },
];

function matchScore(question: string, keywords: string[]): number {
  const lower = question.toLowerCase();
  let score = 0;
  for (const kw of keywords) {
    if (lower.includes(kw)) {
      score += 1;
    }
  }
  return score;
}

export function getDemoResponse(question: string): CypherResult {
  let bestMatch: DemoEntry | null = null;
  let bestScore = 0;

  for (const entry of demoEntries) {
    const score = matchScore(question, entry.keywords);
    if (score > bestScore) {
      bestScore = score;
      bestMatch = entry;
    }
  }

  if (bestMatch && bestScore > 0) {
    return bestMatch.result;
  }

  // Fallback for unmatched questions
  return {
    cypher: `MATCH (c:Customer)-[:OWNS_ACCOUNT]->(a:Account)
RETURN c.name, a.number, a.balance
LIMIT 25`,
    explanation:
      "This is a default query that returns customers and their accounts. For more specific results, try asking about fraud detection, transfers, shared addresses, or graph algorithms.",
  };
}
