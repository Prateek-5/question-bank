# Backend Data-Layer Interview Prep (SDE2)

A focused 15-day preparation kit for senior backend / SDE2 interviews. Covers everything an interviewer can throw at the **data layer**: SQL, NoSQL, ORMs, transactions, indexing, caching, sharding, and real production design.

> Audience: 3–4 YOE backend engineer who knows the basics, needs depth, debugging readiness, and crisp answers under pressure.

---

## Topic Sequence (Recommended Order)

1. **SQL** — fundamentals → advanced → optimization → indexing → normalization → transactions → isolation → locks
2. **NoSQL** — fundamentals → CAP → replication/sharding → MongoDB → DynamoDB/Cassandra
3. **ORM** — internals → Prisma / Sequelize / TypeORM comparison
4. **Caching** — strategies → Redis patterns
5. **Case Studies** — schema design, data modeling
6. **Interview Scenarios** — top 80 questions + debugging drills

```
backend-data-prep/
├── README.md
├── 15-day-plan.md
├── sql/
│   ├── 01-sql-fundamentals.md
│   ├── 02-advanced-sql.md
│   ├── 03-query-optimization.md
│   ├── 04-indexing.md
│   ├── 05-normalization.md
│   ├── 06-transactions.md
│   ├── 07-isolation-levels.md
│   └── 08-locks-concurrency.md
├── nosql/
│   ├── 01-nosql-fundamentals.md
│   ├── 02-cap-theorem.md
│   ├── 03-replication-sharding.md
│   ├── 04-mongodb.md
│   └── 05-dynamodb-cassandra.md
├── orm/
│   ├── 01-orm-internals.md
│   └── 02-orm-comparison.md
├── caching/
│   ├── 01-caching-strategies.md
│   └── 02-redis-patterns.md
├── case-studies/
│   ├── 01-schema-design.md
│   └── 02-data-modeling.md
└── interview-scenarios/
    ├── 01-top-80-questions.md
    └── 02-debugging-scenarios.md
```

---

## Best Study Order (15-Day Plan)

See [15-day-plan.md](./15-day-plan.md) for the full daily schedule.

**TL;DR:**
- **Days 1–3:** SQL fundamentals + joins + group by + window functions
- **Days 4–6:** Indexing + query plans + optimization
- **Days 7–8:** NoSQL + CAP + Mongo / Dynamo
- **Days 9–10:** ORMs + transactions + isolation
- **Days 11–12:** Caching + Redis patterns
- **Days 13–15:** Mock interviews + case studies + debugging drills

---

## Must-Do Topics (Will Definitely Be Asked)

These come up in nearly every SDE2 backend interview. Do not skip:

| Topic | Why it’s asked |
|---|---|
| **B-tree indexes + EXPLAIN** | Every product company tests this. Read execution plans on sight. |
| **Joins (inner/left/anti/semi)** | Machine coding and SQL rounds. Know the algorithms (hash/merge/nested loop). |
| **Window functions** | Mid-to-senior SQL screens (`ROW_NUMBER`, `RANK`, `LAG/LEAD`, partitioned aggregates). |
| **Transactions + isolation levels** | System design + correctness questions. Know each anomaly. |
| **Locks (row, table, predicate, advisory)** | Debugging deadlocks is a senior signal. |
| **CAP + replication + sharding** | Every system design round. |
| **N+1 problem in ORMs** | Asked in nearly every backend interview that touches a real ORM. |
| **Redis caching patterns** | Cache-aside, write-through, TTL, stampede, invalidation. |
| **Schema design for a real product** | E-commerce, payments, chat — at least one will appear. |

---

## Frequently Skipped but Important

Most candidates underprepare these. Cover them to stand out:

- **MVCC internals** (Postgres vs MySQL InnoDB) — explains every isolation-level question
- **Phantom reads vs non-repeatable reads** — interviewers test the *distinction*
- **Predicate / gap locking** — needed to explain how MySQL prevents phantoms at REPEATABLE READ
- **Index-only scans / covering indexes** — separates seniors from juniors
- **Composite index column order rules** — the equality–range–sort rule
- **Connection pooling** (PgBouncer, HikariCP) — production debugging
- **Read replicas vs replication lag** — comes up in every read-heavy design
- **Idempotency keys** — payments, retries, double-writes
- **Outbox pattern + dual-write problem** — distributed transactions in microservices
- **Cache invalidation strategies** + **thundering herd / stampede** mitigation
- **Composite primary keys + partition keys** in DynamoDB/Cassandra
- **TOAST / large-row handling** in Postgres
- **Optimistic vs pessimistic locking trade-offs**

---

## Last-Minute Revision Checklist (Day 15 morning)

Run through the “Revision notes” section at the bottom of every file. Then test yourself on:

- [ ] Draw a B-tree, then explain why it’s shallow on disk
- [ ] Write `ROW_NUMBER() OVER (PARTITION BY ...)` from memory
- [ ] Explain READ COMMITTED vs REPEATABLE READ in 30 seconds
- [ ] Explain MVCC in 60 seconds (Postgres tuple visibility, vacuum)
- [ ] Diagnose a slow query without running EXPLAIN (look for: missing index, wrong join order, type cast, function on indexed column)
- [ ] Cache-aside read + write flow on a whiteboard
- [ ] When to pick Mongo over Postgres, and the honest answer is: usually you shouldn't
- [ ] DynamoDB partition key vs sort key vs GSI
- [ ] N+1 in TypeORM + how to fix it
- [ ] Outbox pattern flow for payments
- [ ] CAP: PACELC trade-offs
- [ ] Redis: cache stampede mitigation (singleflight / probabilistic early expiry)
- [ ] Two-phase commit vs saga

---

## Backend Interview Cheat Sheet

### SQL one-liners

```sql
-- Top N per group
SELECT * FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS rn
  FROM orders
) t WHERE rn <= 3;

-- Anti-join (users with no orders)
SELECT u.* FROM users u
LEFT JOIN orders o ON o.user_id = u.id
WHERE o.id IS NULL;

-- Upsert
INSERT INTO inventory (sku, qty) VALUES ('A1', 10)
ON CONFLICT (sku) DO UPDATE SET qty = inventory.qty + EXCLUDED.qty;

-- Pagination (keyset, scales)
SELECT * FROM events WHERE (created_at, id) < ($1, $2) ORDER BY created_at DESC, id DESC LIMIT 50;

-- Lock for update
SELECT balance FROM accounts WHERE id = $1 FOR UPDATE;
```

### Index rules of thumb
- Equality columns first, then range, then sort
- WHERE column in a function → index unused (use functional index)
- LIKE 'abc%' uses index; LIKE '%abc' doesn’t
- Covering index = index that includes all SELECTed columns (avoids heap fetch)
- High-cardinality + selective = good index candidate

### Isolation cheat
| Anomaly | RC | RR (Pg) | RR (MySQL) | Serializable |
|---|---|---|---|---|
| Dirty read | ✗ | ✗ | ✗ | ✗ |
| Non-repeatable read | ✓ allowed | ✗ | ✗ | ✗ |
| Phantom | ✓ allowed | ✓ allowed | ✗ (gap locks) | ✗ |
| Write skew | ✓ | ✓ | ✓ | ✗ |

### CAP / PACELC
- During Partition: pick **C or A**
- Else: pick **L (latency) or C (consistency)**
- Postgres = CP, Dynamo eventually-consistent = AP, Spanner ≈ CP

### Redis patterns
- Cache-aside (lazy)
- Write-through
- Write-behind (risk: data loss)
- Refresh-ahead
- TTL + jitter to avoid stampede
- `SETNX` for distributed locks → prefer Redlock for correctness

### Common debugging signals
- Slow query → `EXPLAIN ANALYZE`
- Connection storm → check pool size vs Postgres `max_connections`
- Locks growing → `pg_stat_activity` / `SHOW ENGINE INNODB STATUS`
- Replica lag → monitor `pg_stat_replication` / `Seconds_Behind_Master`
- Cache miss spike → check key TTL distribution, add jitter

---

## How to Use This Repo

1. Start with `15-day-plan.md`
2. Read the topic file in order
3. After each file, do the **Common interview questions** section without looking
4. Spend Day 13–15 on `interview-scenarios/01-top-80-questions.md`
5. On the day before the interview, only re-read **Revision notes** sections + this README cheat sheet

Good luck. The interviewer wants depth + intuition + production scars. Every file in this repo aims at exactly that.
