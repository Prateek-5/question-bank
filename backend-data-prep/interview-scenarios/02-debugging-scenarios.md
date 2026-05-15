# Debugging Scenarios (Senior Interview Focus)

The hardest interview questions are not "what's an index?" but **"production is on fire; what do you do?"** Senior interviewers love these because they test instinct + structured thinking.

For each scenario:
- **Symptoms** (what they tell you)
- **Hypotheses** (what could cause it)
- **What you'd check, in order**
- **Fixes**
- **What an SDE2 should additionally discuss**

> Tip: walk through the diagnostic *process*. Don't jump to the answer — show how you'd narrow it down.

---

## Scenario 1: "A simple SELECT became 10x slower yesterday"

**Symptoms**: same query, no code change, suddenly p99 jumped from 50 ms to 500 ms.

**Hypotheses**
- Statistics are stale → planner chose a different plan
- Index bloat after a bulk delete
- Table grew across a threshold (planner switched from index scan to seq scan)
- Cache eviction (working set no longer fits in shared_buffers)
- Replication catch-up I/O saturating disks
- Parameter sniffing: first plan was for a different param value

**Process**
1. Run `EXPLAIN (ANALYZE, BUFFERS)` for the slow query
2. Compare against the *known good* plan (from history or a different env)
3. Look at row estimates: planner expects 100, actual 100k → stats stale → `ANALYZE`
4. Check disk read counts (`Buffers: shared read=…`) — high = data not in cache
5. Check `pg_stat_user_tables` for `n_dead_tup` (bloat)
6. Check timeline: was there a deploy, bulk load, or VACUUM activity?

**Fixes**
- `ANALYZE table` → stats refresh
- `VACUUM (ANALYZE)` or `VACUUM FULL` for bloat
- Add/adjust index if access pattern changed
- Pin a plan with hints if parameter sniffing

**Senior point**: monitor `pg_stat_statements.mean_exec_time` over time to catch regressions; don't wait for users to report.

---

## Scenario 2: "We're getting deadlocks every few minutes in production"

**Symptoms**: random `40P01 deadlock_detected` errors, mostly on the order-placement code path.

**Hypotheses**
- Two code paths acquire locks in different orders
- Long-held locks (transactions doing external API calls inside)
- A specific frequently-touched row is the contention point
- Triggers acquiring locks that aren't obvious

**Process**
1. Check Postgres log for the deadlock graph (every deadlock gets a detailed entry)
2. Identify the two transactions and the rows they were waiting for
3. Trace the code paths — what's the lock order?
4. Look for `SELECT FOR UPDATE` patterns that vary across paths
5. Check for foreign-key-triggered locks (FK validation may take an X lock briefly)

**Fixes**
- **Consistent lock ordering** (e.g., always by entity ID ascending)
- Move external API calls *outside* transactions
- Shorter transactions (commit before any I/O)
- Application-level retry on deadlock error (with exponential backoff)

**Senior point**: deadlocks are normal in any concurrent system. The bug is when they exceed a threshold (set an alert at, say, 10/min) or aren't retried.

---

## Scenario 3: "Read replicas lag is creeping up over time"

**Symptoms**: replica lag was < 1s, now growing to minutes; reads from replica return stale data.

**Hypotheses**
- Long-running queries on replica blocking WAL apply (Postgres specifically)
- Network throughput saturated between primary and replica
- Replica disk too slow (WAL apply I/O bound)
- A huge transaction on primary generating massive WAL
- Primary doing batch operations (bulk delete/update)

**Process**
1. `pg_stat_replication` on primary: check `flush_lsn`, `replay_lsn`, gap
2. On replica: check `pg_stat_activity` for long-running queries (they block replay if hot_standby_feedback or `max_standby_streaming_delay` triggers cancellation)
3. Compare replica disk IOPS / throughput to primary
4. Check what happened on primary: any massive write (`pg_stat_user_tables`)?
5. Check timeline alignment with deploys / data jobs

**Fixes**
- Kill long-running replica queries (or set shorter `max_standby_streaming_delay`)
- Add replica disk capacity (sometimes the WAL apply is bottlenecked)
- Move heavy batch jobs to off-peak
- Add another replica if reads are the bottleneck
- For read-your-writes: route critical reads to primary

**Senior point**: replica lag is a leading indicator. Alert at 5s and at 30s thresholds. Document RPO target.

---

## Scenario 4: "Redis cache hit rate dropped suddenly to 50%"

**Symptoms**: average response time tripled overnight; cache hit rate metric crashed.

**Hypotheses**
- Eviction storm — memory limit hit, LRU evicting hot keys
- A new feature flooding cache with low-utility keys
- TTL distribution misconfigured (everyone expires at the same minute)
- Redis instance restart wiped the cache (no AOF/RDB)
- Key namespace changed (new code uses different prefix)

**Process**
1. `INFO memory` — check `used_memory`, `maxmemory`, `evicted_keys`
2. `INFO stats` — `evicted_keys` rate; `expired_keys` spike?
3. Check the keyspace distribution (`SCAN` + tally prefixes)
4. Look at TTL of recently-set keys
5. Check Redis restart history (logs / uptime)
6. Check for deploys around the regression time

**Fixes**
- Add memory (vertical) or shard (horizontal)
- Add jitter to TTLs to avoid synchronized expiration
- Remove low-utility keys (audit what's being cached)
- Add AOF persistence so a restart doesn't lose state
- Pre-warm cache after a restart

**Senior point**: monitor `evicted_keys` rate, not just hit rate. Evictions happening = memory under pressure = degraded behavior coming.

---

## Scenario 5: "Cache stampede took down the DB after a deploy"

**Symptoms**: deploy at 2 PM → all caches cleared (TTL reset) → 5 minutes later, DB CPU 100%, query queue, API timeouts.

**Hypotheses**
- Cold cache → all reads bypass to DB
- Many concurrent reads for the same hot key
- TTL synchronized at deploy time → simultaneous expiry
- No singleflight protection

**Process**
1. Confirm via cache hit rate metric (should go to ~0 right at deploy)
2. Trace which queries are amplifying
3. Identify the hot keys via sampled `MONITOR` or top-N profiling
4. Confirm DB lock waits, CPU, connection count

**Fixes immediate**
- Increase DB connection pool slightly (controlled — don't worsen lock contention)
- Add singleflight (SETNX-based mutex) around expensive recomputes
- Pre-warm cache before/during deploy

**Fixes long-term**
- Jittered TTL: never let many keys expire together
- Stale-while-revalidate pattern
- Probabilistic early refresh
- Cache warming routine in deploy pipeline

**Senior point**: cache layer is part of the deploy plan. Discuss it in incident review.

---

## Scenario 6: "Inventory says we have stock, but two customers got the last item"

**Symptoms**: oversold by one. Both orders show as PAID. Inventory record shows 0.

**Hypotheses**
- Race condition between two cart checkouts
- `SELECT then UPDATE` pattern without locking
- Read-only check + non-atomic decrement
- Eventual consistency in a cache that lied

**Process**
1. Read the order placement code path
2. Look for: SELECT … check quantity … UPDATE — non-atomic
3. Or: cached quantity (Redis) checked while DB is the actual SoT
4. Validate via logs: was a `SELECT FOR UPDATE` taken? Was the WHERE atomic?

**Fixes**
- Atomic decrement: `UPDATE inventory SET qty = qty - 1 WHERE sku = ? AND qty >= 1; -- check rows affected`
- Or: `SELECT … FOR UPDATE` then validate then update, inside one transaction
- Don't trust cached counts for invariants — DB is the source of truth
- Add a CHECK constraint (`qty >= 0`) as a safety net

**Senior point**: any invariant-critical decision (money, stock, locks) must use atomic ops or `FOR UPDATE`. Caches inform; they don't decide.

---

## Scenario 7: "API timeouts during a marketing campaign"

**Symptoms**: 1M users hit the site at noon; 5% of requests fail; DB looks fine; cache looks fine.

**Hypotheses**
- App-server connection pool exhausted (more concurrent requests than pool slots)
- DB connection pool exhausted (request queueing)
- A specific endpoint is slow under load (was OK in normal traffic)
- External dependency (payment gateway) timing out
- Thundering herd on a cache key

**Process**
1. APM trace — find the slow span
2. Check app-side: pool active vs max; queue wait time
3. DB: `pg_stat_activity` (active queries), max_connections vs current
4. External APIs: latency / error rate
5. Look for a single endpoint dominating traffic

**Fixes**
- Increase pool sizes (carefully — don't exceed DB max_connections)
- Add caching for the hot endpoint
- Add circuit breaker around external APIs
- Pre-scale infrastructure for known campaigns

**Senior point**: load tests catch this pre-prod. Discuss capacity planning and pre-warming. Distinguish queue wait from execution time in metrics.

---

## Scenario 8: "JSON column queries are slow"

**Symptoms**: `WHERE data->>'role' = 'admin'` does a sequential scan on a 100M row table.

**Hypotheses**
- No index on the JSON path
- Index exists but is GIN on whole doc, not on extracted path
- Operator mismatch (`->>` vs `@>`)
- Cast in the predicate

**Process**
1. `EXPLAIN ANALYZE` confirms Seq Scan
2. List existing indexes; check operator class
3. Plan should mention `Filter:` for unindexed predicate

**Fixes**
- Functional B-tree index on the path:
  ```sql
  CREATE INDEX ON users ((data->>'role'));
  ```
- For containment queries (`@>`), GIN with `jsonb_path_ops`:
  ```sql
  CREATE INDEX ON users USING gin (data jsonb_path_ops);
  WHERE data @> '{"role":"admin"}'
  ```
- For multiple paths, consider extracted columns (generated columns)

**Senior point**: don't dump everything in JSONB. Frequently queried fields should be promoted to typed columns with proper indexes.

---

## Scenario 9: "Some webhooks are processed twice"

**Symptoms**: payment gateway retried a webhook; we charged the customer's account twice.

**Hypotheses**
- Webhook handler not idempotent
- 2xx returned but processing failed → retry → second insert
- No external ID checked
- Race between two retries

**Process**
1. Check `webhook_events` table — is there a unique constraint on external ID?
2. Look at order/payment code — INSERT with idempotency key?
3. Race window: two retries arrive simultaneously, both see no existing record, both INSERT

**Fixes**
- Unique constraint on `(external_id)` in events table
- `INSERT … ON CONFLICT DO NOTHING` and check rows-affected
- Idempotency key on the actual financial action (debit) — not just receipt logging
- Return 2xx only after the financial action completes successfully

**Senior point**: webhooks are *always* at-least-once. Idempotency at every layer. Discuss as a system contract.

---

## Scenario 10: "Suddenly half our writes fail with serialization_failure"

**Symptoms**: Postgres SERIALIZABLE isolation; many concurrent writes; `40001` errors flooding logs.

**Hypotheses**
- A new feature introduced overlapping read/write patterns (more dependencies → more aborts)
- Volume grew, hitting concurrency hot spots
- A previously serialized operation now runs concurrently
- No retry logic in app

**Process**
1. Look at the error pattern: which endpoint? Which rows?
2. Check `pg_stat_database` `xact_rollback` / `xact_commit` ratio
3. Identify the conflicting transactions (logs include affected pids)
4. Decide: is SERIALIZABLE actually needed for this path?

**Fixes**
- Add retry with exponential backoff in app
- Re-evaluate: drop to READ COMMITTED + explicit `SELECT FOR UPDATE` for the contended rows
- Reduce overlap: shorter transactions, less data touched
- Add a higher-level coordinator (queue) for hot rows

**Senior point**: SERIALIZABLE isn't free; it trades blocking for optimistic aborts. Retries are mandatory. If retry rate stays high, the workload may be wrong for SSI.

---

## Scenario 11: "An ALTER TABLE blocked the application for 20 minutes"

**Symptoms**: deploy ran a migration that added a column; production was down/degraded during the migration.

**Hypotheses**
- ALTER TABLE acquired ACCESS EXCLUSIVE lock for a long time (e.g., adding column with default in old Postgres)
- Long-running transaction held a lock; migration waited; everyone waited
- Migration rewrote the table (unsafe operations)

**Process**
1. Read the migration — what does it do?
2. Postgres 11+: adding a column with a constant default is instant. Adding NOT NULL without default is also fast.
3. But: adding a column with a VOLATILE default or non-trivial expression triggers a rewrite.
4. Or: `ALTER COLUMN TYPE` changing type → rewrite

**Fixes**
- Use the multi-step migration pattern (add nullable → backfill → mark NOT NULL)
- For type changes: add new column, dual-write, backfill, swap
- For huge tables in MySQL: `gh-ost` or `pt-online-schema-change`
- For Postgres: `CREATE INDEX CONCURRENTLY`; never run blocking DDL during peak

**Senior point**: every migration plan must include a "what's the worst case lock duration" analysis. Reviewer asks: "would this take a table lock if the table were huge?"

---

## Scenario 12: "Backups can't keep up; the WAL directory is filling"

**Symptoms**: alert on Postgres `pg_wal` disk usage; backups failing.

**Hypotheses**
- Replication slot holding old WAL because a replica is offline/lagging
- Backup target slow/unreachable
- A massive transaction holding WAL retention
- Misconfigured retention

**Process**
1. `pg_replication_slots` — any inactive slots?
2. `pg_stat_replication` — replica progress
3. `pg_stat_activity` — long-running transactions
4. Disk IOPS to backup destination

**Fixes**
- Drop unused replication slots (data on replica is gone, but cluster keeps growing)
- Pause writers if catastrophic, fix replica, then resume
- Move WAL to higher-IOPS disk
- Configure `max_wal_size` and check archiving health

**Senior point**: replication slots are silent killers. Monitor them aggressively. Test failover and slot cleanup procedures.

---

## Scenario 13: "Mongo replica set keeps re-electing leaders"

**Symptoms**: cluster flipping primary every minute; clients see `NotMaster` errors intermittently.

**Hypotheses**
- Network partitions / flapping
- High primary load → secondaries can't get heartbeats
- Disk I/O on the primary causing journal stalls
- Misconfigured priorities making election volatile

**Process**
1. `rs.status()` — check member states, last heartbeat, optime
2. Logs on each node — election events
3. Check network round-trip times between nodes
4. Disk I/O graphs on primary

**Fixes**
- Increase election timeout if appropriate
- Move noisy neighbor off primary node
- Use priority/arbiter setup carefully
- Add bandwidth between AZs

**Senior point**: leader thrashing is bad — every election pauses writes. Stability over speed.

---

## Scenario 14: "DynamoDB returns ThrottledException only for a specific user"

**Symptoms**: most users are fine; one customer's reads/writes throttle constantly.

**Hypotheses**
- Hot partition (this customer's data is one partition)
- They're hammering the API
- Their PK is low-cardinality (e.g., shared with other users in skewed way)

**Process**
1. Confirm: throttle is partition-level (`ProvisionedThroughputExceeded` per-partition)
2. CloudWatch metrics: which partition?
3. Look at item distribution under this user

**Fixes**
- Sub-shard: write to `user_id#bucket` where bucket = `hash(item_id) % 16`
- Read across buckets for collection queries
- Cache hot reads upstream
- Switch to on-demand if traffic is bursty (auto-scales partitions)

**Senior point**: adaptive capacity helps but isn't instant. Design for distribution from the start.

---

## Scenario 15: "Postgres CPU is fine, but query latency is high"

**Symptoms**: low CPU on DB, but app sees slow responses.

**Hypotheses**
- Lock waits (CPU is idle while waiting)
- Disk I/O bottleneck (not CPU)
- Connection pool exhaustion (queue at app layer)
- Network latency between app and DB
- Connection establishment overhead (no pooler)

**Process**
1. `pg_stat_activity` for waiting queries / `wait_event`
2. Disk metrics — iostat, IOPS, throughput, await
3. App pool metrics
4. Connection setup time (try a non-pooled connection for comparison)

**Fixes**
- Investigate locks; resolve via consistent ordering or shorter transactions
- Move to faster storage (NVMe, gp3 with provisioned IOPS)
- Add PgBouncer for many-connection apps
- Use prepared statements
- Co-locate app and DB in same AZ/VPC

**Senior point**: "DB CPU is fine" is misleading. Real signal is wait events and connection saturation.

---

## Scenario 16: "Search index is out of sync with the DB"

**Symptoms**: a product was renamed in the DB; old name still shows in search results.

**Hypotheses**
- Outbox/CDC worker is behind or dead
- Indexer is missing certain change types
- Order of events / replays out of order

**Process**
1. Check outbox lag — is the worker processing?
2. ES queue / Logstash pipeline status
3. Compare counts of recent records between DB and ES

**Fixes immediate**
- Reindex affected documents
- Resume CDC pipeline if stalled

**Fixes long-term**
- Monitoring on CDC lag
- Periodic reconcile job (compare counts, repair drift)
- Versioned records (timestamp + monotonic): indexer only writes if newer than existing

**Senior point**: any cross-store sync must have a reconcile/verification job. Don't trust the pipeline to be perfect forever.

---

## Scenario 17: "After a deploy, GET /me returns the previous user occasionally"

**Symptoms**: occasional wrong-user response; security incident risk.

**Hypotheses**
- Cached response by user ID, but the cache key is wrong (no user_id in key)
- Connection-level state leaking across requests (Sequelize/pg `client` reused with stale TX)
- Shared mutable global state
- ORM identity map confusion across requests

**Process**
1. Read the recent changes
2. Look for `req.user` set globally
3. Look for cache key construction — missing user_id?
4. Check connection lifecycle — is a transaction left open?

**Fixes**
- Include user_id in every cache key
- Never store request-scoped state globally
- Always release connections in `finally`
- ORM: use per-request scope (Prisma, EntityManager)

**Senior point**: any "wrong data returned" bug should escalate immediately — it's a security/privacy issue, not a perf one.

---

## Scenario 18: "Database disk is full"

**Symptoms**: out-of-space; writes failing.

**Hypotheses**
- Logs (audit table, event log) growing unbounded
- WAL retention because of stuck replication slot
- Table bloat from non-vacuumed deletes
- Backup files left on the data disk

**Process**
1. `df -h` and `du` per directory
2. `pg_database_size` per DB
3. Largest tables (`pg_total_relation_size`)
4. Check WAL retention
5. Bloat estimator

**Fixes**
- Move backups off the data disk
- VACUUM FULL the bloated tables (locks; off-hours)
- Drop unused replication slots
- Add disk capacity
- Truncate / archive old log tables

**Senior point**: alerting at 80% disk gives time. 95% is too late. Plan growth + retention policy.

---

## How to use these in interviews

When asked a debugging scenario:

1. **Restate the symptoms** to confirm understanding
2. **List your hypotheses** — show breadth of mental model
3. **Choose the highest-likelihood first** — show prioritization
4. **Describe the data you'd gather** — show systematic approach
5. **Propose a fix and explain the trade-off**
6. **Mention the long-term improvement** (monitoring, process, architecture)

This structure communicates senior-engineer instincts even if you don't know the exact answer.

---

## Revision notes

- Always start with measurement (`EXPLAIN ANALYZE`, metrics, logs) — never guess
- Discuss the *process*, not just the answer
- Mention monitoring/alerting as the long-term answer to every reactive scenario
- Distinguish symptoms from causes
- Have a clear story of immediate fix + long-term fix
- Senior signal: hypotheses listed in order of likelihood + cost-to-check
