# 15-Day Backend Interview Plan (SDE2)

Each day: **2.5 hr theory + 1.5 hr hands-on + 30 min flashcard/revision = ~4.5 hr total**. If you have less time, skip the *Stretch* sections — never skip the *Must do*.

---

## Phase 1 — SQL Foundations (Days 1–3)

### Day 1 — SQL Fundamentals
- **Read:** `sql/01-sql-fundamentals.md`
- **Must do:** joins (inner / left / right / full / cross / anti / semi), GROUP BY + HAVING, subqueries
- **Hands-on:** On a real Postgres (use `docker run postgres`), build a small `users / orders / order_items` schema; write 10 joins
- **Stretch:** LATERAL joins, correlated subqueries
- **End-of-day check:** Can you explain *exactly* what an anti-join is and write it both with `LEFT JOIN ... IS NULL` and `NOT EXISTS`?

### Day 2 — Advanced SQL
- **Read:** `sql/02-advanced-sql.md`
- **Must do:** CTEs (recursive too), window functions (`ROW_NUMBER`, `RANK`, `DENSE_RANK`, `LAG/LEAD`, `SUM() OVER`), pivots
- **Hands-on:** “Top N orders per user”, “running balance”, “7-day rolling average” — write all three from memory
- **Stretch:** `FILTER (WHERE …)` clause, `GROUPING SETS / ROLLUP / CUBE`

### Day 3 — Normalization + Schema Design Basics
- **Read:** `sql/05-normalization.md`
- **Must do:** 1NF–3NF, BCNF intuition, when to denormalize
- **Hands-on:** Design schema for **Instagram comments** (with replies + likes) and **a hotel booking system**
- **Stretch:** EAV anti-pattern, soft-delete patterns, audit tables

---

## Phase 2 — Optimization, Indexing, Transactions (Days 4–6)

### Day 4 — Indexing Deep Dive
- **Read:** `sql/04-indexing.md`
- **Must do:** B-tree internals, composite index column order, covering indexes, partial indexes, functional indexes, hash vs B-tree vs GIN vs BRIN
- **Hands-on:** Take a `EXPLAIN ANALYZE` of three queries; add the right index for each
- **Senior signal:** Explain when a query *won’t* use an index even though one exists (5+ reasons)

### Day 5 — Query Optimization + EXPLAIN
- **Read:** `sql/03-query-optimization.md`
- **Must do:** Read query plans, join algorithms (nested loop / hash / merge), seq scan vs index scan vs index-only scan, statistics + `ANALYZE`
- **Hands-on:** Take a 5-table slow JOIN; tune it with EXPLAIN ANALYZE
- **Stretch:** Postgres planner cost model, `pg_stat_statements`, query rewriting tricks

### Day 6 — Transactions + Isolation + Locks
- **Read:** `sql/06-transactions.md`, `sql/07-isolation-levels.md`, `sql/08-locks-concurrency.md`
- **Must do:** ACID, the 4 anomalies (dirty / non-repeatable / phantom / write-skew), 4 isolation levels, MVCC, row vs predicate vs advisory locks, `SELECT FOR UPDATE`, deadlock detection
- **Hands-on:** Simulate a deadlock between two transactions in two psql sessions; resolve it
- **Senior signal:** Explain *write skew* and why Serializable is the only level that prevents it

---

## Phase 3 — NoSQL (Days 7–8)

### Day 7 — NoSQL Fundamentals + CAP
- **Read:** `nosql/01-nosql-fundamentals.md`, `nosql/02-cap-theorem.md`
- **Must do:** Document / key-value / wide-column / graph; CAP + PACELC; eventual vs strong consistency; quorum (R + W > N)
- **Hands-on:** For a given product (e.g. ride-sharing geo lookup, ad analytics), pick the right DB and justify
- **Stretch:** Conflict resolution (LWW, CRDTs), vector clocks

### Day 8 — Mongo + Dynamo + Cassandra + Replication/Sharding
- **Read:** `nosql/03-replication-sharding.md`, `nosql/04-mongodb.md`, `nosql/05-dynamodb-cassandra.md`
- **Must do:** Mongo schema patterns (embedding vs referencing), aggregation pipeline, indexes; Dynamo partition + sort key + GSI; Cassandra wide-row modeling
- **Hands-on:** Design a Dynamo table for a chat app (messages by conversation, sorted by time)
- **Senior signal:** Explain how Dynamo achieves single-digit ms latency at any scale and the trade-offs (no joins, no ad-hoc queries)

---

## Phase 4 — ORM + Transactions in App Layer (Days 9–10)

### Day 9 — ORM Internals
- **Read:** `orm/01-orm-internals.md`
- **Must do:** N+1 problem (the #1 ORM interview question), lazy vs eager, identity map, unit of work, query builder vs ORM
- **Hands-on:** Build an N+1 example in TypeORM / Sequelize, fix it with eager loading + DataLoader pattern
- **Stretch:** Repository pattern vs Active Record, ORM-generated SQL pitfalls

### Day 10 — Prisma / Sequelize / TypeORM + Migrations
- **Read:** `orm/02-orm-comparison.md`
- **Must do:** Transactions across multiple operations, migration strategy (additive only, no destructive in prod), connection pooling
- **Hands-on:** Write a transaction in each of Prisma + Sequelize + TypeORM
- **Senior signal:** Explain *why* Prisma is now leading and the catch (no lazy loading, no models in the OOP sense)

---

## Phase 5 — Caching + Redis (Days 11–12)

### Day 11 — Caching Strategies
- **Read:** `caching/01-caching-strategies.md`
- **Must do:** cache-aside (lazy), write-through, write-behind, refresh-ahead, TTL strategies, eviction (LRU/LFU/TTL), cache stampede + mitigation
- **Hands-on:** Build a cache-aside read path with Redis + Postgres; add stampede protection with `SETNX` lock
- **Stretch:** Multi-tier caching (CDN → app cache → DB)

### Day 12 — Redis Patterns
- **Read:** `caching/02-redis-patterns.md`
- **Must do:** Data types (string / list / set / sorted set / hash / stream), pub/sub, distributed locks, rate limiting (token bucket via Lua), leaderboard, session store
- **Hands-on:** Build a sliding-window rate limiter in Redis using a sorted set
- **Senior signal:** When NOT to use Redis (large blobs, cold data, secondary index needs)

---

## Phase 6 — Mock Practice (Days 13–15)

### Day 13 — Case Studies
- **Read:** `case-studies/01-schema-design.md`, `case-studies/02-data-modeling.md`
- **Do all four mock designs** in the case-studies files (e-commerce, chat, payments, analytics)
- **Senior signal:** Discuss CAP trade-offs and indexing for each

### Day 14 — Top 80 Questions
- **Do:** `interview-scenarios/01-top-80-questions.md` — go through every one out loud, even the easy ones; pace yourself like an interview (60–90s per answer)
- Mark the 10 you fumbled and re-do them tomorrow

### Day 15 — Debugging Scenarios + Final Revision
- **Do:** `interview-scenarios/02-debugging-scenarios.md` — these are the scenario-based questions interviewers love
- **Then:** Re-read the **Revision notes** section of every topic file
- **Last hour:** Re-read the README cheat sheet

---

## Daily Rituals

- **Spaced repetition:** Each day, redo 3 questions from yesterday before starting today
- **Out loud:** Practice answers verbally — interviews are spoken, not typed
- **Whiteboard:** Schema design must be drawn, not typed
- **Don’t skip the “Why this matters” sections** — interviewers reward intuition over recall

---

## If You Have Less Time

| Days available | What to drop |
|---|---|
| 10 days | Drop Day 1 (basics), Day 12 stretch, Day 13 case studies (skim only) |
| 7 days | Skip MongoDB deep dive, Cassandra; skim ORMs; focus on SQL + indexing + transactions + Redis |
| 5 days | SQL fundamentals (1 day) + Indexing/Transactions (2 days) + NoSQL/CAP (1 day) + Top 80 questions (1 day). Cut everything else. |

---

## What Interviewers Are Really Testing

For SDE2 backend, every data-layer question is one of:
1. **Do you understand the engine?** (storage, indexes, locks, MVCC)
2. **Have you debugged production?** (slow queries, deadlocks, replication lag, cache stampedes)
3. **Can you design for scale?** (sharding, caching layers, CAP trade-offs)
4. **Are your fundamentals strong enough to teach a junior?** (normalization, joins, ACID)

This plan targets all four.
