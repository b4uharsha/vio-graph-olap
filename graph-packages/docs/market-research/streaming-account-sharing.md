# Streaming Account Sharing Detection

> **Use Case:** Detect and analyze account sharing patterns for streaming services, gaming platforms, and SaaS subscriptions.

---

## The Problem

### Why SQL Fails

Traditional SQL queries for account sharing detection:

```sql
-- This takes 4+ MINUTES with large data
SELECT
    a.account_id,
    COUNT(DISTINCT d.device_id) as unique_devices,
    COUNT(DISTINCT i.ip_address) as unique_ips,
    COUNT(DISTINCT l.city) as unique_cities
FROM accounts a
JOIN sessions s ON a.account_id = s.account_id
JOIN devices d ON s.device_id = d.device_id
JOIN ip_addresses i ON s.ip_id = i.ip_id
JOIN locations l ON i.location_id = l.location_id
WHERE a.account_id = '12345'
AND s.start_time > NOW() - INTERVAL '30 days'
GROUP BY a.account_id;
```

**Problems:**
- 10+ JOINs = exponential performance degradation
- 4+ minutes per query at scale
- Can't visualize sharing patterns
- Expensive to run across all accounts

---

## The Graph Solution

### Data Model

**Nodes (Entities):**
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   ACCOUNT   │     │   DEVICE    │     │  IP_ADDRESS │
│             │     │             │     │             │
│ account_id  │     │ device_id   │     │ ip_address  │
│ email       │     │ device_type │     │ city        │
│ plan_type   │     │ os          │     │ country     │
└─────────────┘     └─────────────┘     └─────────────┘

┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   PROFILE   │     │   SESSION   │     │  LOCATION   │
│             │     │             │     │             │
│ profile_id  │     │ session_id  │     │ lat/long    │
│ name        │     │ start_time  │     │ city        │
│ avatar      │     │ end_time    │     │ country     │
└─────────────┘     └─────────────┘     └─────────────┘
```

**Relationships:**
```
(Account)-[:HAS_PROFILE]->(Profile)
(Account)-[:LOGGED_IN_FROM]->(Device)
(Account)-[:ACCESSED_FROM]->(IP_Address)
(Device)-[:LOCATED_AT]->(Location)
(Session)-[:USED_DEVICE]->(Device)
(Session)-[:FROM_IP]->(IP_Address)
(Profile)-[:WATCHED]->(Content)
```

---

## Query Examples

### 1. How many people are sharing this account?

**Graph Query (2ms):**
```cypher
MATCH (a:Account {account_id: '12345'})-[:LOGGED_IN_FROM]->(d:Device)
MATCH (a)-[:ACCESSED_FROM]->(ip:IP_Address)-[:LOCATED_AT]->(loc:Location)
WHERE a.last_30_days = true
RETURN
    COUNT(DISTINCT d) as unique_devices,
    COUNT(DISTINCT ip) as unique_ips,
    COUNT(DISTINCT loc.city) as unique_cities
```

**Result:**
```
unique_devices: 7
unique_ips: 12
unique_cities: 4  ← SUSPICIOUS: Account used in 4 different cities
```

---

### 2. Visualize the sharing network

**Graph Query:**
```cypher
MATCH path = (a:Account {account_id: '12345'})-[*1..3]-(connected)
RETURN path
```

**Result (Visual Graph):**
```
                    ┌──────────────┐
                    │   Account    │
                    │   "12345"    │
                    └──────┬───────┘
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ Profile  │    │ Profile  │    │ Profile  │
    │  "Dad"   │    │  "Mom"   │    │ "Friend" │
    └────┬─────┘    └────┬─────┘    └────┬─────┘
         │               │               │
         ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  iPhone  │    │ Smart TV │    │  Laptop  │
    │ New York │    │ New York │    │ Chicago  │ ← Different city!
    └──────────┘    └──────────┘    └──────────┘
```

---

### 3. Find ALL accounts with suspicious sharing

**Graph Query:**
```cypher
MATCH (a:Account)-[:ACCESSED_FROM]->(ip:IP_Address)-[:LOCATED_AT]->(loc:Location)
WITH a, COUNT(DISTINCT loc.city) as cities, COLLECT(DISTINCT loc.city) as city_list
WHERE cities > 3
RETURN a.account_id, a.email, cities, city_list
ORDER BY cities DESC
LIMIT 1000
```

**Result:**
```
| account_id | email              | cities | city_list                          |
|------------|--------------------|---------|------------------------------------|
| 98765      | user@email.com     | 8       | [NYC, LA, Chicago, Miami, ...]     |
| 54321      | another@email.com  | 6       | [Boston, Seattle, Denver, ...]     |
| ...        | ...                | ...     | ...                                |
```

---

### 4. Detect simultaneous streaming from different locations

**Graph Query:**
```cypher
MATCH (a:Account)-[:HAS_SESSION]->(s:Session {status: 'active'})
MATCH (s)-[:FROM_IP]->(ip:IP_Address)-[:LOCATED_AT]->(loc:Location)
WITH a, COLLECT(DISTINCT loc.city) as active_cities
WHERE SIZE(active_cities) > 1
RETURN a.account_id, a.email, active_cities
```

**Result:**
```
| account_id | email           | active_cities        |
|------------|-----------------|----------------------|
| 12345      | user@email.com  | [New York, Chicago]  | ← Streaming from 2 cities NOW
| 67890      | other@email.com | [LA, Miami, Denver]  | ← Streaming from 3 cities NOW
```

---

### 5. Find accounts sharing with each other

**Graph Query:**
```cypher
MATCH (a1:Account)-[:LOGGED_IN_FROM]->(d:Device)<-[:LOGGED_IN_FROM]-(a2:Account)
WHERE a1 <> a2
RETURN a1.account_id, a2.account_id, d.device_id, d.device_type
```

**Result:**
```
| a1_account | a2_account | device_id | device_type |
|------------|------------|-----------|-------------|
| 12345      | 67890      | DEV-ABC   | Smart TV    | ← Two accounts, one device!
```

---

### 6. Impossible travel detection (velocity check)

**Graph Query:**
```cypher
MATCH (u:User)-[:LOGGED_IN]->(s1:Session)-[:FROM]->(loc1:Location)
MATCH (u)-[:LOGGED_IN]->(s2:Session)-[:FROM]->(loc2:Location)
WHERE s1.time < s2.time
AND duration.between(s1.time, s2.time).minutes < 60
AND point.distance(loc1.coordinates, loc2.coordinates) > 500000
RETURN u.email, loc1.city, loc2.city, s1.time, s2.time
```

**Result:**
```
| email           | city1    | city2   | time1    | time2    |
|-----------------|----------|---------|----------|----------|
| user@email.com  | New York | London  | 10:00 AM | 10:30 AM | ← IMPOSSIBLE!
```

---

---

## Why Graph OLAP is Perfect for This

| Requirement | Graph OLAP Solution |
|-------------|---------------------|
| Analyze 230M accounts | Per-analyst pods scale independently |
| Sub-second queries | 2ms vs 4+ minutes for multi-hop |
| Ad-hoc exploration | Analysts investigate patterns themselves |
| No always-on cost | Pay only during analysis sessions |
| Data stays in warehouse | Compliance-friendly |
| Visual pattern discovery | Graph shows sharing networks |

---

## Beyond Streaming: Other Applications

### Gaming Subscriptions
- Xbox Game Pass, PlayStation Plus
- Detect shared accounts across households

### SaaS License Abuse
- Slack, Zoom, Office 365
- Find single-user licenses used by multiple people

### Credential Sharing
- Enterprise password abuse
- Impossible travel detection

### Subscription Box Services
- Shared family plans abuse
- Address pattern analysis

---

## Getting Started

### 1. Define your graph mapping

```sql
-- Nodes
SELECT account_id, email, plan_type FROM accounts;
SELECT device_id, device_type, os FROM devices;
SELECT ip_address, city, country FROM ip_addresses;

-- Edges
SELECT account_id, device_id, last_used FROM account_devices;
SELECT session_id, ip_address, timestamp FROM session_ips;
```

### 2. Create a snapshot

```python
from graph_olap import GraphOLAPClient

client = GraphOLAPClient(api_url="http://localhost:8080")

# Create snapshot from your warehouse
snapshot = client.snapshots.create(
    mapping_id=account_sharing_mapping,
    name="Account Sharing Analysis - March 2025"
)
```

### 3. Launch your graph workspace

```python
# Create isolated analysis environment
instance = client.instances.create_and_wait(
    snapshot_id=snapshot.id,
    wrapper_type="falkordb"  # In-memory for speed
)

# Connect and query
conn = client.instances.connect(instance.id)

# Find suspicious accounts
results = conn.query("""
    MATCH (a:Account)-[:ACCESSED_FROM]->(ip)-[:LOCATED_AT]->(loc)
    WITH a, COUNT(DISTINCT loc.city) as cities
    WHERE cities > 3
    RETURN a.account_id, cities
    ORDER BY cities DESC
""")

print(results.to_polars())
```

---

## Summary

| Metric | SQL Approach | Graph OLAP |
|--------|--------------|------------|
| Query time | 4+ minutes | 2 milliseconds |
| Visualization | None | Full network graph |
| Pattern detection | Manual, error-prone | Automatic |
| Cost at scale | High (always-on) | Zero when idle |
| Analyst skill required | SQL expert | Any analyst |

**Graph OLAP turns account sharing detection from a weeks-long project into a minutes-long analysis.**

---

## Get Started

Ready to recover millions in lost subscription revenue?

1. **Clone the repository** and run locally
2. **Try the demo notebooks** with sample data
3. **Connect your data** and start detecting sharing patterns

See the [Quick Start guide](../../README.md#quick-start) to begin.
