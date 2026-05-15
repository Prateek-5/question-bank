# Top 80 SDE2 Backend Data-Layer Interview Questions

The 80 questions most often asked at SDE2 / senior backend interviews at product companies (Amazon, Google, Microsoft, Atlassian, Stripe, Razorpay, Swiggy, Flipkart, Uber, Booking, Linkedin, Meta, MongoDB-like shops, etc.).

Each question has a short, **interview-ready answer**. Aim for 60–90 seconds per question out loud.

> Drill format: cover the answer, read the question, speak the answer aloud, then check.

---

## SQL — Joins, Subqueries, GROUP BY (1–10)

**1. What's the difference between INNER JOIN and LEFT JOIN, and when would each be appropriate?**

INNER JOIN returns only rows with a match on both sides; LEFT JOIN keeps all rows from the left even when the right has no match (NULL-filled). Use INNER when you want intersection; LEFT when you need every left row plus optional related data (e.g., users + their latest order, where some users have no orders).

**2. Explain anti-joins. Show two SQL ways to write one.**

An anti-join returns left rows that have **no** match on the right. Use cases: find churned users, find unmatched records.
```sql
-- Way 1
SELECT u.* FROM users u
LEFT JOIN orders o ON o.user_id = u.id
WHERE o.id IS NULL;
-- Way 2 (NULL-safe, often preferred)
SELECT u.* FROM users u
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id);
```

**3. What's the logical order of SQL execution?**

FROM → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT. Aliases from SELECT can be referenced in ORDER BY but not WHERE — because WHERE runs before SELECT.

**4. Why is `NOT IN` dangerous with NULL?**

If the subquery returns any NULL, `NOT IN` evaluates to NULL (unknown), so the row is excluded — typically returning zero rows. Switch to `NOT EXISTS`, which is NULL-safe.

**5. WHERE vs HAVING — what's the difference?**

WHERE filters rows *before* aggregation; cannot reference aggregates. HAVING filters *after* GROUP BY and operates on aggregate or group-key values.

**6. Find the second-highest salary three different ways.**

```sql
-- Window
SELECT salary FROM (SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) rk FROM emp) t WHERE rk=2;
-- Subquery (no ties)
SELECT MAX(salary) FROM emp WHERE salary < (SELECT MAX(salary) FROM emp);
-- LIMIT/OFFSET (ties dangerous)
SELECT DISTINCT salary FROM emp ORDER BY salary DESC LIMIT 1 OFFSET 1;
```
Window with `DENSE_RANK` handles ties correctly.

**7. UNION vs UNION ALL?**

UNION concatenates and deduplicates (requires sort/hash). UNION ALL just concatenates — much faster. Default to UNION ALL unless you specifically need dedup.

**8. `COUNT(*)` vs `COUNT(col)` vs `COUNT(DISTINCT col)`?**

`COUNT(*)` = every row. `COUNT(col)` = non-NULL `col`. `COUNT(DISTINCT col)` = unique non-NULL values (expensive due to hashing/sorting).

**9. What does GROUP BY do under the hood?**

The planner either hash-aggregates (build a hash keyed by group columns; fast for unsorted data) or sort-aggregates (sort by group columns; then aggregate adjacent rows). Hash needs work_mem; sort can spill but uses less memory.

**10. Write a self-join: employees and their managers (both columns from `employees`).**
```sql
SELECT e.name AS employee, m.name AS manager
FROM employees e LEFT JOIN employees m ON m.id = e.manager_id;
```

---

## SQL — Window Functions & CTEs (11–20)

**11. ROW_NUMBER vs RANK vs DENSE_RANK?**

For salaries 100,100,90: ROW_NUMBER → 1,2,3 (unique); RANK → 1,1,3 (gap); DENSE_RANK → 1,1,2 (no gap). Use ROW_NUMBER for "pick exactly one" per group; DENSE_RANK for "top N with ties sharing rank."

**12. How do you get the top N records per group?**
```sql
SELECT * FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) rn FROM orders
) t WHERE rn <= 3;
```
Or via `LATERAL` join — often faster with an index on `(user_id, created_at DESC)`.

**13. Running total per user?**
```sql
SUM(amount) OVER (PARTITION BY user_id ORDER BY ts ROWS UNBOUNDED PRECEDING)
```

**14. 7-day rolling average over events?**
```sql
AVG(value) OVER (ORDER BY day RANGE BETWEEN INTERVAL '6 days' PRECEDING AND CURRENT ROW)
```
Use RANGE (logical) not ROWS (physical) for date-based windows so missing days don't shift the window.

**15. Find consecutive login days (gaps and islands)?**
Subtract `ROW_NUMBER()` from each date — consecutive dates yield the same offset, so GROUP BY that offset gives the runs.

**16. What's a recursive CTE? Use case?**

Walks a tree/graph by iterating. Use for org charts, comment threads, dependency graphs, category trees, BOM.
```sql
WITH RECURSIVE tree AS (
  SELECT id, parent_id, 0 AS depth FROM cats WHERE id = $root
  UNION ALL
  SELECT c.id, c.parent_id, t.depth+1 FROM cats c JOIN tree t ON c.parent_id = t.id
)
SELECT * FROM tree;
```

**17. CTE vs subquery — performance?**

Modern Postgres (12+) inlines CTEs by default, so performance is similar to subqueries. Use `WITH … AS MATERIALIZED` to pin the boundary. Pre-12 Postgres always materialized — beware on old systems.

**18. What is a LATERAL join and when to use?**

A `LATERAL` subquery in FROM can reference columns from preceding FROM items. Perfect for top-N-per-group, per-row aggregation, or unnesting:
```sql
SELECT u.id, recent.*
FROM users u
LEFT JOIN LATERAL (SELECT * FROM orders WHERE user_id = u.id ORDER BY created_at DESC LIMIT 3) recent ON true;
```

**19. ROWS vs RANGE in a window frame?**

ROWS = physical row offset. RANGE = logical value-based (requires sortable type and ORDER BY). They differ on ties: ROWS may include only some tied rows; RANGE includes all.

**20. Default frame for window functions?**

Aggregate functions with ORDER BY: `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`. Without ORDER BY: entire partition. Ranking functions: entire partition. Watch out — `LAST_VALUE` without explicit frame returns the current row.

---

## SQL — Indexing (21–30)

**21. How does a B-tree index work?**

A balanced multi-way tree where each node fits a disk page. Internal nodes hold keys + child pointers; leaves hold keys + row IDs. Fanout is high (hundreds), so 3–5 levels cover billions of rows. Leaves are doubly linked for fast range scans. O(log N) lookup.

**22. Why is the column order in a composite index important?**

A B-tree is sorted lexicographically by (col1, col2, …). The leading column must appear in an equality (or range) for the index to be used. Order columns by: **Equality → Range → Sort**.

**23. Difference between clustered and non-clustered index?**

Clustered (InnoDB PK, SQL Server clustered) stores table data physically in PK order — PK lookups are 1 read. Non-clustered (any secondary) stores key → pointer; lookups require an extra hop to the heap. Postgres has no clustered indexes — all are secondary.

**24. What's a covering index / index-only scan?**

An index that contains every column the query needs. The DB serves the query without touching the table heap. In Postgres, use `INCLUDE` to add non-key columns. Visibility map must say the page is all-visible for index-only scan to skip the heap.

**25. Seven reasons an existing index isn't used?**

1. Function or cast on the column (`WHERE LOWER(email)=…`)
2. Implicit type cast (`WHERE varchar_col = 123`)
3. Leading wildcard (`LIKE '%abc'`)
4. Low selectivity — seq scan cheaper
5. Stale statistics → planner mis-estimates
6. ORDER BY direction mismatch (mixing ASC/DESC)
7. `NOT` / `<>` operator

**26. Partial index — when useful?**

Index only rows matching a predicate. Saves space, faster updates. Great for skewed columns (e.g., 99% rows are `status='ARCHIVED'`):
```sql
CREATE INDEX ON orders(created_at) WHERE status = 'OPEN';
```

**27. UUID v4 vs auto-increment as PK?**

UUID v4 is random → in InnoDB (clustered) causes page splits and write amplification; bigger secondary indexes. Auto-increment (BIGINT) is small and monotonic — appends cleanly. Modern alternative: UUID v7 (timestamp-ordered).

**28. B-tree vs Hash vs GIN vs BRIN?**

B-tree: default; equality + range + sort. Hash: equality only, rarely better. GIN: multi-valued columns (JSONB, arrays, full-text). BRIN: append-only/naturally-sorted data (time-series); tiny on disk.

**29. How do indexes affect write performance?**

Each INSERT/UPDATE touching an indexed column triggers an index update — random I/O and possible page splits. Rule of thumb: 5–15% write slowdown per index. A table with 10 indexes can be 2x slower to write. Audit indexes regularly.

**30. How to index a JSON column for fast lookup?**

Postgres: GIN on JSONB with `jsonb_path_ops` operator class:
```sql
CREATE INDEX ON users USING gin (data jsonb_path_ops);
SELECT * FROM users WHERE data @> '{"role":"admin"}';
```
Or a functional B-tree index on a specific path: `CREATE INDEX ON users ((data->>'email'))`.

---

## SQL — Query Optimization (31–40)

**31. How do you debug a slow query?**

Run `EXPLAIN (ANALYZE, BUFFERS)`. Look for: Seq Scans on large tables, large estimate vs actual row count mismatch, high `loops` on nested loop inner side, "Rows Removed by Filter" indicating missing index, high disk reads (`Buffers: read`). Verify statistics fresh (`ANALYZE`). Adjust predicates, add indexes, rewrite as needed.

**32. Walk through reading an `EXPLAIN ANALYZE` plan.**

Read from leaves up. Each node has cost (planner estimate), actual time, rows expected vs actual, and loops. Big estimate-actual gaps mean stale stats. Nested loop with high loops × inner cost = problem. Look at the join algorithms (hash/nested-loop/merge) and whether they're appropriate.

**33. Difference between nested loop, hash, and merge join?**

- Nested loop: outer × inner; good when outer is small + inner has an index
- Hash join: build hash on smaller side; good for big unsorted equi-joins (needs work_mem)
- Merge join: both sides pre-sorted on join key; cheap

**34. Why does Postgres choose Seq Scan even when an index exists?**

Predicate is unselective (low cardinality, planner expects most rows match), stats are stale, type cast/function disables index, or table is so small seq scan is cheaper. Verify with `SET enable_seqscan = off` to force; check the cost.

**35. How to optimize an `OR` query?**

Rewrite as `UNION ALL` of the two branches, each using its own index. Or rely on a bitmap-or if multiple suitable indexes exist:
```sql
SELECT … WHERE a = 1
UNION ALL
SELECT … WHERE b = 2 AND a <> 1;
```

**36. What is parameter sniffing?**

A parameterized query gets a plan based on the first parameter value, which may be a poor fit for other values. Fix via custom plan (`plan_cache_mode='force_custom_plan'`), inlining literals, or query hints.

**37. How would you paginate a 100M-row table?**

Keyset pagination using a unique tie-breaker:
```sql
SELECT * FROM events
WHERE (created_at, id) < ($cursor_ts, $cursor_id)
ORDER BY created_at DESC, id DESC LIMIT 50;
```
OFFSET is O(N+offset); keyset is O(log N).

**38. How to find which queries to optimize first?**

Postgres: `pg_stat_statements` → top queries by total_exec_time. MySQL: slow query log + `performance_schema`. Focus on total time consumed (not just average). Watch p99 not just p50.

**39. When to denormalize?**

When reads dominate writes, joins are on the hot path (3+ tables), the duplicated value rarely changes, or the access pattern won't fit a clean normalized schema. Always document the source of truth and refresh mechanism.

**40. Why is `LIKE '%abc%'` slow and how do you fix it?**

Leading wildcard means no sorted-prefix lookup. Fixes: `LIKE 'abc%'` if business permits, trigram index (`pg_trgm` + GIN), or full-text search / Elasticsearch.

---

## SQL — Transactions, Isolation, Locks (41–50)

**41. Explain ACID.**

Atomicity (all-or-nothing), Consistency (constraints hold at commit), Isolation (concurrent transactions don't see each other's partial work, per isolation level), Durability (committed changes survive crashes via WAL).

**42. List the four isolation levels and the anomalies each prevents.**

Read Uncommitted (none), Read Committed (no dirty read), Repeatable Read (no non-repeatable read; phantoms blocked in MySQL InnoDB only), Serializable (all four, including write skew).

**43. What's write skew? Give an example.**

Two transactions read overlapping data, each makes a decision based on what they saw, both write, and the combination violates an invariant. Classic: two on-call doctors each going off call simultaneously, with a "≥ 1 doctor on call" rule. Only Serializable prevents it.

**44. Postgres REPEATABLE READ vs MySQL REPEATABLE READ?**

Postgres RR is pure snapshot isolation; doesn't prevent phantoms because writes acting on observations can still differ. MySQL InnoDB RR uses next-key (gap) locks → blocks INSERTs that would create phantoms during your transaction.

**45. What is MVCC?**

Multi-Version Concurrency Control: each write creates a new tuple version (Postgres: tagged with xmin/xmax; MySQL: undo log). Readers see versions visible to their snapshot. Readers don't block writers; writer-writer conflicts still acquire row locks.

**46. Walk through a money transfer transaction.**
```sql
BEGIN;
SELECT * FROM accounts WHERE id IN ($from, $to) ORDER BY id FOR UPDATE;
UPDATE accounts SET balance = balance - $amt WHERE id = $from AND balance >= $amt;
-- 0 rows → ROLLBACK
UPDATE accounts SET balance = balance + $amt WHERE id = $to;
INSERT INTO transactions (idempotency_key, …) VALUES (…) ON CONFLICT DO NOTHING;
COMMIT;
```
Lock both rows in consistent order to avoid deadlocks.

**47. What's a deadlock and how is it resolved?**

Two transactions waiting on each other's locks → cycle. DB detects via deadlock_timeout (Postgres) or detector (MySQL) and aborts one transaction. Application must retry. Prevention: acquire locks in consistent order, keep transactions short.

**48. Optimistic vs pessimistic concurrency control?**

Pessimistic: `SELECT FOR UPDATE` locks the row; safest for high-contention. Optimistic: version column checked on update (`WHERE version = ?`); zero locks; retry on conflict. Pick based on conflict probability.

**49. How would you build a job queue in Postgres?**

`SELECT ... FOR UPDATE SKIP LOCKED LIMIT 1`. Multiple workers can pull jobs concurrently without contention.

**50. What is the outbox pattern?**

Write the "event-to-publish" row to a DB table inside the same transaction as the business change. A worker (or CDC) reads outbox and publishes externally. Solves the dual-write problem (DB write + Kafka publish atomically).

---

## NoSQL & Distributed Systems (51–60)

**51. State the CAP theorem precisely. Why is "pick two" wrong?**

When a partition occurs in a distributed system, you must choose between consistency (refuse stale reads) or availability (serve responses). Partition tolerance isn't optional — networks fail. "Pick two" implies a static choice; the real choice is *what to do during a partition*: CP or AP.

**52. What's PACELC?**

Extends CAP: during Partition choose A or C; Else (normal operation) choose L (low latency) or C (consistency). Useful: Spanner is PC + EC; Cassandra is PA + EL; DynamoDB default is PA + EL.

**53. Quorum reads/writes — explain R + W > N.**

For N replicas, if R + W > N, any read overlaps with the latest write → strong consistency for single-key reads. Common: W=quorum, R=quorum, balanced for latency and availability.

**54. Hash vs range vs directory sharding?**

Hash: even distribution; no efficient range queries. Range: range queries efficient; hotspot risk (monotonic IDs). Directory: lookup service maps key→shard; flexible but SPOF.

**55. What's a hot partition and how do you mitigate it?**

One partition gets disproportionate traffic (bad shard key, celebrity user, sequential timestamps). Mitigations: hash-prefix the key, cache aggressively, L1 in-process cache, sub-shard, redesign.

**56. When would you choose Mongo over Postgres?**

Truly nested document model (deep arrays, varied schemas across tenants), multi-region writes you can't get in Postgres, large schema flexibility that JSONB can't satisfy. Honest answer: most apps are better off with Postgres + JSONB. Only choose Mongo when measured.

**57. Difference between DynamoDB GSI and LSI?**

GSI = global secondary index, any (PK, SK), created/dropped any time, eventually consistent. LSI = local secondary index, same PK as base table with different SK, defined at table creation, can be strongly consistent, shares the 10GB partition limit.

**58. Cassandra: how would you model a chat message store?**
```sql
CREATE TABLE messages (
  conv_id UUID, sent_at TIMESTAMP, msg_id UUID, sender UUID, body TEXT,
  PRIMARY KEY ((conv_id), sent_at, msg_id)
) WITH CLUSTERING ORDER BY (sent_at DESC);
```
Partition by conversation; clustering by time DESC for fast "latest N". For very wide conversations, bucket by month: PK `((conv_id, month))`.

**59. What's eventual consistency and is it dangerous?**

Replicas converge "eventually" after writes. Not data loss — propagation delay. Most internet-scale features (feeds, search, sessions) are fine with it. Not OK for: money invariants, locks, anything where invariants span replicas.

**60. How does Redis Cluster handle multi-key operations?**

Each node owns a range of 16384 hash slots; key → slot via CRC16. Multi-key operations require all keys on the same slot — use hashtags `{}`: `user:{42}:profile` and `user:{42}:cart` hash to the same slot. Multi-key across slots is rejected.

---

## ORM (61–68)

**61. What is the N+1 problem and how do you fix it?**

A parent query returns N rows; each parent triggers a child query → N+1 queries total. Fixes: eager loading (`include`/`relations`), separate batched query with `IN (ids)`, DataLoader pattern (batches + caches per-request), or raw SQL.

**62. Lazy vs eager loading?**

Lazy: relation loaded on access (risks N+1). Eager: loaded with the parent in one query (JOIN or follow-up SELECT). Eager prevents N+1 but can over-fetch or cause cartesian explosion. Mix per use case; Prisma intentionally has no lazy mode.

**63. Why doesn't Prisma have lazy loading?**

By design — lazy loading is the #1 source of accidental N+1 in production. Forcing explicit `include`/`select` makes the query cost visible at the call site.

**64. Active Record vs Data Mapper?**

Active Record: object has `save()`/`delete()` (Rails, Sequelize). Data Mapper: a separate repository persists plain objects (Hibernate, TypeORM Repository). Data Mapper separates domain from persistence; better for testing and complex domains.

**65. How do you write a transaction with retry on serialization failure?**
```javascript
async function withTx(fn, attempts = 3) {
  for (let i = 0; i < attempts; i++) {
    try { return await prisma.$transaction(fn, { isolationLevel: 'Serializable' }); }
    catch (e) {
      if (e.code === 'P2034' || e.meta?.code === '40001' || e.code === '40P01') {
        await sleep(50 * Math.random() * (i+1)); continue;
      }
      throw e;
    }
  }
  throw new Error('TX_RETRY_EXHAUSTED');
}
```

**66. When would you drop down to raw SQL in an ORM project?**

Complex SQL features (window functions, recursive CTEs, JSONB ops, full-text), bulk operations (10k+ rows), performance-critical hot paths, reports/exports, DB-specific features the ORM doesn't expose.

**67. How do you safely add a NOT NULL column to a 100M-row table?**

Phase: 1) add nullable column; 2) backfill in batches (`UPDATE ... LIMIT 10000` in a loop, sleep between); 3) add CHECK NOT NULL as NOT VALID, then VALIDATE; 4) ALTER COLUMN SET NOT NULL. For huge ALTERs in MySQL: `pt-online-schema-change` or `gh-ost`.

**68. How does connection pooling work and how do you size it?**

A bounded set of DB connections reused across requests. Per app instance: 10–25 typical. Total connections (instances × pool) must stay under DB `max_connections`. For thousands of instances: PgBouncer in transaction-mode multiplexes connections. Monitor wait time.

---

## Caching & Redis (69–76)

**69. Compare cache-aside, write-through, write-behind.**

- Cache-aside: app reads from cache, falls back to DB, populates cache. Most common.
- Write-through: writes go to cache + DB synchronously. Cache always consistent.
- Write-behind: writes ack'd by cache; DB write async. Fast, risky on cache crash. Use for high-volume non-critical (counters).

**70. What's a cache stampede and how do you prevent it?**

When a popular key expires, many concurrent requests miss → all hit DB simultaneously. Fixes: singleflight (one client computes via SETNX lock, others wait or serve stale), probabilistic early refresh, stale-while-revalidate, jittered TTL.

**71. LRU vs LFU vs TTL eviction?**

LRU evicts least-recently used (general default). LFU evicts least-frequently used (good for stable hot keys). TTL evicts by expiry only. W-TinyLFU (Caffeine) combines LRU + LFU + admission filter for top-tier hit rates.

**72. How would you build a distributed lock in Redis?**

Basic: `SET key value NX EX 30`; release via Lua to atomically check the owner before deleting. For cluster: Redlock — controversial (Kleppmann argues it doesn't ensure mutual exclusion in all failure modes). For correctness-critical locks, ZooKeeper or etcd.

**73. How would you build a rate limiter in Redis?**

Fixed window: `INCR key EX 60`; reject if > limit. Sliding window: sorted set with timestamps + Lua to atomically expire + count + add. Token bucket: hash with tokens + refill via Lua.

**74. Pub/Sub vs Streams?**

Pub/Sub: fire-and-forget broadcast; messages dropped if no subscriber; no replay. Streams: durable append-only log with consumer groups, ACKs, and replay (Kafka-lite). Use Streams for anything resembling event processing.

**75. How do you keep cache and DB consistent?**

Choose by staleness tolerance. Options: TTL (best-effort), explicit invalidation on write, versioned keys (bump version on change), CDC-based invalidation (Debezium → invalidator). Strict consistency is hard; embrace bounded staleness for most workloads.

**76. What happens if Redis goes down?**

Detect via circuit breaker / timeout. Gracefully fall back to DB with rate limiting (to avoid stampede). Pre-warm on recovery. Architectural rule: app must still function without cache (degraded performance, not broken).

---

## System Design & Senior Topics (77–80)

**77. Design a URL shortener that handles 100k QPS reads.**

- Store `short_code → long_url` in KV (Redis or DynamoDB)
- CDN in front for cacheable redirects (huge hit rate)
- Hash-based code (random) + base62 encoding
- Counter or DB sequence to generate codes; collisions checked
- Analytics: log to Kafka → ClickHouse for aggregations
- Postgres canonical store; Redis as read cache with TTL
- Discuss hot links (cache more aggressively) and abuse (rate limit by IP/user)

**78. Design Instagram's "Recent Photos" feed.**

- Fan-out write: when user posts, push to followers' feed lists in Redis (sorted set, capped at N)
- Cold users (no recent reads): fan-out lazily on demand
- Mixed: pull from celebs (millions of followers — fan-out write expensive)
- Postgres canonical: posts, follows
- Cassandra/Redis per-user feed
- CDN for image delivery
- Discuss fan-out at write vs read trade-offs

**79. Design a payment system. What goes wrong if you skip idempotency?**

- Postgres for accounts + transactions (ACID)
- Double-entry ledger
- Idempotency keys for every external call
- Outbox pattern for webhooks/events
- Sagas for cross-service flow (charge → reserve inventory → confirm order)
Without idempotency: network retries → double charges, double inventory deductions, double notifications. Disaster.

**80. You're seeing tail latency spikes only on writes. What do you check?**

1. Lock contention (`pg_stat_activity`, `pg_blocking_pids`)
2. Long-running transactions blocking VACUUM (Postgres) → bloat → slower writes
3. Replication lag holding sync replica → primary stalls on sync_commit
4. Disk I/O (iostat) — write amplification, fsync wait
5. Connection pool exhaustion
6. WAL bottleneck (consider faster disk, bigger WAL buffers)
7. Index bloat — REINDEX CONCURRENTLY
8. Lock waits visible in `pg_stat_database.deadlocks` and `wait_event`

---

## How to use this list

- Day 14 morning: read silently, mark questions you stumbled on
- Day 14 afternoon: redo the marked ones out loud
- Day 15: mock interview — partner asks questions in random order; 60s/question, no fumbling
- Day of interview: skim only the questions where you previously fumbled

---

## Revision strategy

| Round | Goal |
|---|---|
| 1 | Read all 80; pick 20 weakest |
| 2 | Master the 20 weakest |
| 3 | Random-order practice; time yourself 60s/question |
| 4 | Day-before lightning round |

> The interviewer doesn't reward perfect recall; they reward **clear, structured, confidently-stated answers**. Practice talking through these, not just reading.
