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

## How to use this file (read this first)

These are not flashcards. They are **simulated incidents**. You should read each scenario, *pause*, and try to list your own hypotheses *before* reading the answer. The interviewer doesn't grade whether you know the right answer — they grade whether you reach for the right *diagnostic process*.

**The mental loop this file trains:**

```
   read symptoms  ──▶  cover the rest  ──▶  list 3-5 hypotheses
        ▲                                          │
        │                                          ▼
   compare and    ◀──  read "process" and  ◀── pick "most likely +
   note gaps         "fixes" sections          cheapest to check"
```

**Three rules for using this file well:**

1. **Don't peek at hypotheses until you've written your own.** The whole point is to train the *instinct* of "what would I check first" — peeking robs you of the rep.
2. **Practice out loud, on a whiteboard, with a friend asking "and then what?"** Interviewers ask follow-ups; static answers don't train for that.
3. **Map every scenario to a `pg_*` / Redis `INFO` / OS command you'd actually run.** Senior signal is naming the *tool*, not just the concept.

---

## Why interviewers love debugging scenarios (signal density)

A "design X" question takes 30 minutes; a debugging scenario takes 5–10 minutes and reveals just as much. Here's what the interviewer is grading in real time:

1. **Hypothesis quality** — do you list 4–6 plausible causes (breadth), or fixate on one (tunnel vision)?
2. **Prioritization** — do you pick the *highest-likelihood + cheapest-to-check* hypothesis first (senior), or just go alphabetically (junior)?
3. **Tool fluency** — do you name `pg_stat_activity`, `iostat`, `redis-cli INFO`, or hand-wave with "I'd check the metrics"?
4. **Cause vs symptom distinction** — slow query is a symptom; stale stats is a cause. Senior engineers separate them.
5. **Immediate fix vs long-term fix** — do you reach for monitoring, runbooks, postmortem culture *after* the immediate fix?

A junior says: "I'd ANALYZE the table." A senior says: "I'd first check `pg_stat_statements.mean_exec_time` for a regression timeline, then `EXPLAIN ANALYZE` to compare estimated vs actual rows, then `ANALYZE` if stats are stale. Long-term we'd add a dashboard on plan stability."

That difference is the whole interview.

---

## How to think aloud during a debugging scenario

Use this template every time. It's the structure your interviewer is *unconsciously* checking for:

```
   1. RESTATE       "So you're saying the SELECT was 50ms yesterday, now 500ms?"
        │
   2. CLARIFY       "Is it ALL queries or just this one? Did anything deploy?"
        │
   3. HYPOTHESIZE   "Could be A, B, or C. Most likely A because [reason]."
        │
   4. PROBE         "I'd run X first because it's cheap and would rule out A."
        │
   5. ITERATE       "If X shows clean, then check Y. If Y is the culprit, fix is Z."
        │
   6. PREVENT       "Long-term: monitor M, alert at threshold T."
```

**Why this works:** it externalizes your thinking so the interviewer can grade *process*, not just answer. Even if you don't reach the right cause, the structure scores.

**When you're stuck:** verbalize the stuckness. "I'm not sure between hypothesis B and C — let me think about which is cheaper to verify." That single sentence beats silent panic.

---

## Universal diagnostic mini-tree (start here for anything DB-related)

Before diving into the scenarios below, this is the master flowchart most senior engineers run mentally for any DB-related incident:

```
                    ┌── Symptom reported ──┐
                    ▼                      ▼
              Is it slow?            Is it wrong?
                    │                      │
        ┌───────────┴───────────┐          ▼
        ▼                       ▼     [data correctness path]
   Always slow?         Sometimes slow?
        │                       │
        ▼                       ▼
   Plan/index           Lock waits? Cache miss?
   /missing stats        Replication lag?
        │                       │
        ▼                       ▼
   EXPLAIN ANALYZE      pg_stat_activity,
   pg_stat_statements   redis-cli INFO,
                        iostat
```

For correctness ("we charged twice", "stock went negative"):

```
   Is the bug deterministic?
        │
   ┌────┴─────┐
   ▼          ▼
   yes        no
   │          │
   ▼          ▼
   code bug   concurrency bug
   (logic)    (lock / atomic op / idempotency missing)
```

This decision tree maps to the scenarios that follow. Each scenario is a leaf of one of these branches.

---

## Scenario cluster index (group by symptom class)

| Cluster | Scenarios | Symptom class |
|---|---|---|
| Query slowness | 1, 8, 15 | A query that was fine got slow, or stays slow |
| Concurrency correctness | 2, 6, 9, 10, 17 | Race conditions, deadlocks, duplicate work |
| Replication & infrastructure | 3, 12, 13, 16 | Replicas, WAL, search index, cluster topology |
| Cache pathology | 4, 5 | Hit rate drops, stampedes |
| Capacity & contention | 7, 11, 18, 14 | Spikes under load, migrations, disk, hot partitions |

When the interviewer pitches a new scenario, your first job is to mentally classify it into one of these clusters — that determines which checklist to run.

---

## Scenario 1: "A simple SELECT became 10x slower yesterday"

> **Mental model — first thing to suspect when "yesterday it was fine":**
>
> A query getting slower without a code change has *three families* of root cause. Run through them in order of likelihood:
>
> ```
>                     [SELECT got slower]
>                            │
>          ┌─────────────────┼─────────────────┐
>          ▼                 ▼                 ▼
>      Plan changed     Data changed     Environment changed
>      ──────────       ──────────       ──────────────────
>      stale stats      table grew       cache evicted
>      param sniffing   index bloat      neighbor noisy
>      planner regress  hot rows changed disk slowed
> ```
>
> **First-suspicion checklist (in order, cheapest first):**
>
> 1. `EXPLAIN (ANALYZE, BUFFERS)` — is the plan the same as before?
> 2. Compare estimated vs actual rows — large gap → stale stats → `ANALYZE`.
> 3. Check `Buffers: shared read=` — high disk reads → data fell out of cache.
> 4. Check `n_dead_tup` and last `VACUUM` time — bloat from a recent bulk delete?
> 5. Anything deploy/data-load near the regression time?
>
> *How to think aloud:* "Plan changed" is the #1 cause in real life. Open with `EXPLAIN ANALYZE` and ANALYZE. If those don't fix it, escalate to bloat and environment causes.

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

> **Mental model — deadlocks happen when two transactions acquire locks in opposite order.**
>
> ```
>   Txn A:  LOCK row X  ──▶  wants row Y
>                                  ▲
>                                  │   ← cycle, deadlock detector fires
>                                  ▼
>   Txn B:  LOCK row Y  ──▶  wants row X
> ```
>
> Common real-world causes:
> - **Inconsistent lock order across code paths** (Service A locks order then user; Service B locks user then order).
> - **Long transactions** doing external I/O while holding locks.
> - **FK validation** taking implicit locks you didn't think about.
> - **Triggers** acquiring locks invisible from the call site.
>
> **First-suspicion checklist:**
>
> 1. Postgres log will dump the full deadlock graph — *read it first*.
> 2. Identify which two rows / which two code paths.
> 3. Look for `SELECT FOR UPDATE` ordering inconsistency.
> 4. Check transaction duration: anything > 100ms is suspicious.
>
> *Senior framing:* deadlocks are *normal* in concurrent systems — the bug is when they aren't retried, or exceed a threshold (alert at >10/min). Don't panic; treat them as a metric.

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

> **Mental model — replica lag has four root causes:**
>
> ```
>                       [Replica lag growing]
>                              │
>       ┌──────────────┬───────┴─────────┬──────────────┐
>       ▼              ▼                 ▼              ▼
>   Apply slower   Network slow     Primary writes    Conflicts
>   than primary   between nodes    too fast          on replica
>   (disk IOPS)    (bandwidth/RTT)  (batch jobs)      (long reads)
> ```
>
> **First-suspicion checklist:**
>
> 1. `pg_stat_replication` on primary — gap between `flush_lsn` and `replay_lsn`.
> 2. `pg_stat_activity` on replica — any long-running query blocking WAL apply?
> 3. Disk IOPS on replica vs primary — is replica disk slower?
> 4. Did the primary just run a massive batch (bulk delete/update)?
>
> *Why this matters:* replica lag is a *leading indicator* of bigger problems. Don't ignore it just because reads are still working — it usually grows non-linearly until something breaks.

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

> **Mental model — sudden hit-rate drop has four primary causes:**
>
> ```
>                       [Hit rate crashed]
>                              │
>       ┌──────────────┬───────┴─────────┬──────────────┐
>       ▼              ▼                 ▼              ▼
>   Eviction       Restart wiped    Key namespace     TTL storm
>   (memory full)  cold cache       changed (deploy)  (synced expiry)
> ```
>
> The key diagnostic distinction:
> - **Eviction:** `evicted_keys` growing rapidly in `INFO stats`. Memory under pressure.
> - **Restart:** `uptime_in_seconds` is small. Cache was wiped.
> - **Namespace change:** new keys never hit existing ones; check deploy timeline + prefix audit.
> - **TTL storm:** many keys expire simultaneously; check TTL distribution.
>
> **First-suspicion checklist:**
>
> 1. `INFO memory` — `used_memory` vs `maxmemory`?
> 2. `INFO stats` — `evicted_keys`, `expired_keys` rates.
> 3. Redis uptime — did it restart?
> 4. Deploy log — did key prefixes change?
>
> *Senior framing:* hit rate is the symptom; *evictions* are the cause to alert on. Monitor `evicted_keys` rate — if it's growing, you've already lost.

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

> **Mental model — cache stampede is *correlated* misses hitting cold cache simultaneously:**
>
> ```
>                Time = T (deploy)
>                     │
>           cache cleared / cold
>                     │
>   ┌─────────┬───────┴───────┬─────────┐
>   ▼         ▼               ▼         ▼
>   user 1   user 2   ...   user N (thousands)
>   │         │               │         │
>   └─────────┴───── all miss ┴─────────┘
>                     │
>                     ▼
>            DB hammered (N concurrent
>            heavy queries for same data)
> ```
>
> **First-suspicion checklist:**
>
> 1. Confirm: cache hit rate metric should crater right at deploy time.
> 2. APM trace — which queries are amplifying?
> 3. Top hot keys via sampled `MONITOR` or your top-N profiling.
> 4. DB lock waits, CPU, queue depth.
>
> *Prevention recipes (memorize):* **singleflight** (one client computes, others wait via SETNX), **jittered TTL** (avoid synchronized expiry), **stale-while-revalidate** (serve stale + async refresh), **probabilistic early refresh** (re-fetch before TTL), **pre-warm in deploy pipeline**.

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

> **Mental model — oversold-by-one is a classic concurrency race:**
>
> ```
>   Time   Txn A (Alice)              Txn B (Bob)
>   ────────────────────────────────────────────────
>   t1    SELECT qty → 1
>   t2                                SELECT qty → 1
>   t3    qty >= 1 ? yes
>   t4                                qty >= 1 ? yes
>   t5    UPDATE qty = 0
>   t6                                UPDATE qty = 0 ← BUG: both succeed
>   t7    ORDER CREATED
>   t8                                ORDER CREATED ← oversold!
> ```
>
> The fix family:
> - **Atomic update with WHERE clause:** `UPDATE qty = qty - 1 WHERE sku=? AND qty >= 1` then check rows-affected.
> - **`SELECT ... FOR UPDATE`** inside a transaction — pessimistic row lock.
> - **Optimistic version column:** `WHERE version = ?`, retry on 0 rows.
> - **CHECK constraint** (`qty >= 0`) as the database-level guardrail.
>
> *Why interviewers love this one:* it tests whether you confuse "I read the value" with "I locked the value". Any invariant-critical decision must use atomic ops or `FOR UPDATE`. Caches inform — they never decide.

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

> **Mental model — when "DB looks fine, cache looks fine, but requests fail" — the bottleneck is something in between:**
>
> ```
>   [client] → [LB] → [app pool] → [DB pool] → [DB]
>                          ▲           ▲
>                          │           │
>                       checked     checked
>                       (maybe!)    (probably)
>
>   The unchecked layers are usually the culprit:
>   - App-server thread/connection pool
>   - DB connection pool (queue wait time, not query time)
>   - External API timeouts (payment, email, etc.)
>   - Network: LB → app, app → DB
> ```
>
> **First-suspicion checklist (when load hits hard):**
>
> 1. APM trace — *where* in the request does latency live? Find the slow span.
> 2. App pool: active connections vs max; queue wait time.
> 3. DB connection pool: `pg_stat_activity` count vs max_connections.
> 4. External API latency / error rate.
> 5. Is one endpoint dominating? (Pareto principle: 80% of traffic on 20% of endpoints.)
>
> *Key insight:* "DB is fine" usually means "DB CPU and IO are fine". It does *not* rule out connection saturation, which manifests as queue wait time, not slow queries.

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

> **Mental model — JSONB indexing requires picking the *right operator and index type*:**
>
> ```
>   Query pattern              | Right index
>   ──────────────────────────────────────────────────────
>   data->>'role' = 'admin'   | B-tree on (data->>'role')
>   data @> '{"role":"admin"}' | GIN with jsonb_path_ops
>   data ? 'key'               | GIN (default ops)
>   full text in JSON          | GIN with to_tsvector
> ```
>
> **First-suspicion checklist:**
>
> 1. `EXPLAIN ANALYZE` — is it `Seq Scan`? Look at `Filter:` line.
> 2. List existing indexes on the table (`\d table`).
> 3. Does the operator match the index type?
>
> *Senior framing:* JSONB is great for *truly unstructured* fields. The moment you find yourself indexing 3+ paths, those should be promoted to typed columns. Treat JSONB as the exception, not the default.

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

> **Mental model — webhooks are always at-least-once. Plan accordingly:**
>
> ```
>   Sender (Stripe, etc.)            Receiver (you)
>   ─────────────────────────────────────────────────
>   POST /webhook                  ─▶ process
>                                      │
>                                      ├── crashes after side effect
>                                      ▼
>   "no 2xx" → retry               ─▶ process AGAIN (duplicate!)
>                                      │
>                                      ▼
>                                  charge applied twice ✗
> ```
>
> The fix is **defense in depth at every layer**:
> 1. **Transport-level idempotency**: `external_id` unique constraint on the webhook receipts table.
> 2. **Business-level idempotency**: idempotency key on the action itself (debit), not just the receipt log.
> 3. **Atomic insert pattern**: `INSERT ... ON CONFLICT DO NOTHING RETURNING ...`; check rows-affected to decide whether to process.
> 4. **2xx only after success**: don't ack the webhook until the side effect is committed.
>
> *Senior framing:* "webhooks are at-least-once" is a *system contract* you must defend in code review. Anyone who writes a webhook handler without idempotency is shipping a bug.

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

> **Mental model — SSI (Serializable Snapshot Isolation) trades blocking for optimistic aborts:**
>
> ```
>   Lower isolation (RC):   writers block writers, no aborts
>   SERIALIZABLE (SSI):     readers + writers track dependencies;
>                           conflict detected → ABORT (not block)
>
>   Implication: SERIALIZABLE = MANDATORY retry loop in app.
>                If retry rate stays high, the workload may be wrong for SSI.
> ```
>
> **First-suspicion checklist:**
>
> 1. Which endpoint is hitting the aborts? (Look at error rate by route.)
> 2. `pg_stat_database` — `xact_rollback / xact_commit` ratio.
> 3. Do app handlers have a retry-with-backoff loop? Often added later, often forgotten.
> 4. Is SERIALIZABLE actually *required* here? Often a `SELECT FOR UPDATE` on the contended row plus READ COMMITTED is simpler.
>
> *Decision rule:* if retry rate > ~5%, you're using SERIALIZABLE wrong. Either reduce overlap (shorter txns, less data touched) or switch to explicit pessimistic locks for the contended path.

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

> **Mental model — every migration must be assessed for "lock duration in worst case":**
>
> ```
>   Operation                              | Lock duration
>   ──────────────────────────────────────────────────────────
>   ADD COLUMN (no default, nullable)      | instant (modern PG)
>   ADD COLUMN with CONSTANT default       | instant (PG 11+)
>   ADD COLUMN with VOLATILE default       | rewrite — minutes/hours
>   ALTER COLUMN TYPE (compatible)         | varies; often rewrite
>   ALTER COLUMN TYPE (incompatible)       | rewrite — long
>   ADD CONSTRAINT NOT NULL                | scan — proportional to rows
>   CREATE INDEX                           | full lock (use CONCURRENTLY!)
>   CREATE INDEX CONCURRENTLY              | no blocking, slower
> ```
>
> **First-suspicion checklist (before running any migration):**
>
> 1. Read it. What does it actually do?
> 2. Is it on a huge table? If yes, model the worst case.
> 3. Does it rewrite the table? Type changes, volatile defaults → yes.
> 4. Is there a long-running transaction holding a lock the migration would wait for?
>
> *Multi-step migration recipe:* add nullable → backfill in batches → add CHECK NOT NULL as NOT VALID → VALIDATE → ALTER COLUMN SET NOT NULL. Slow but safe.

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

> **Mental model — WAL disk fills when retention pins more WAL than disk can hold:**
>
> ```
>   Causes of pinned WAL:
>     - Replication slot with inactive consumer (replica died — WAL kept "for it")
>     - archive_command failing silently (backup target unreachable)
>     - Huge in-flight transaction (WAL can't be released until commit/abort)
>     - max_wal_size mis-configured for write volume
> ```
>
> **First-suspicion checklist:**
>
> 1. `pg_replication_slots` — any with `active = false`? That's the most common cause.
> 2. `pg_stat_archiver` — `last_archived_time`, `failed_count`.
> 3. `pg_stat_activity` — any txn open for > 1 hour?
> 4. Disk metrics to backup destination.
>
> *Brutal lesson:* a replication slot for a dead replica will eventually fill your disk and crash your primary. Monitor `pg_replication_slots.active` and `restart_lsn` lag aggressively.

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

> **Mental model — leader thrashing means heartbeats are failing reliably enough to trigger elections:**
>
> ```
>   Primary    ───── heartbeat ─────▶  Secondary
>                  (must succeed within
>                   electionTimeoutMillis,
>                   default 10s)
>
>   Cause families:
>     - Network: packet loss, RTT spike, AZ partition
>     - Load: primary too busy to respond (lock, journal stall)
>     - Disk: journal write blocked → heartbeat stalls
>     - Config: weird priority settings making elections oscillate
> ```
>
> **First-suspicion checklist:**
>
> 1. `rs.status()` — member states, last heartbeat, optime.
> 2. Logs on each node for election events.
> 3. Network RTT between nodes (AZ → AZ).
> 4. Disk I/O on the (now ex-)primary at election times.
>
> *Senior framing:* every election pauses writes. A flapping cluster is functionally a partial outage. Stability > speed — favor higher election timeouts and stable nodes.

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

> **Mental model — DynamoDB throttling is *per-partition*, not per-table:**
>
> ```
>   Table (provisioned: 10k WCU)
>     │
>     ▼ (hashed by PK)
>   ┌──────────┬──────────┬──────────┐
>   │ part. 1  │ part. 2  │ part. 3  │   each gets ~3.3k WCU
>   │          │ HOT      │          │
>   │ user A   │ user B   │ user C   │
>   │ user D   │          │ user E   │
>   └──────────┴──────────┴──────────┘
>           user B exceeds partition WCU → ThrottledException
>           (even though table-wide WCU is fine)
> ```
>
> **First-suspicion checklist:**
>
> 1. Confirm: throttle is `ProvisionedThroughputExceeded` per-partition.
> 2. CloudWatch — which partition is hot?
> 3. Item distribution under that user's PK.
>
> *Fix patterns:* sub-shard the hot key (`user_id#bucket`), cache upstream, switch to on-demand (auto-scales partitions but takes a few minutes). Adaptive capacity helps but is *not instant* — design for distribution from the start.

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

> **Mental model — CPU is one of *four* resources; idle CPU means the bottleneck is elsewhere:**
>
> ```
>             CPU       Disk      Network    Lock waits
>             ───       ────      ───────    ──────────
>   busy:     hot      iowait    bandwidth   wait_event
>   signal:   load1     await     RTT         pg_blocking_pids
>
>   "CPU fine + slow queries" = the bottleneck is one of the other three.
> ```
>
> **First-suspicion checklist:**
>
> 1. `pg_stat_activity` — what `wait_event` is showing? `Lock`? `IO`? `Client`?
> 2. `iostat -x 1` — disk `await` and `%util`.
> 3. App-side: connection pool wait time.
> 4. Network: is DB in same VPC/AZ as app?
>
> *Senior framing:* "DB CPU is fine" is the most misleading metric. Real signal lives in `wait_event`, connection saturation, and disk latency. Memorize this — it's an interviewer favorite.

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

> **Mental model — any "DB → derived store" pipeline is *eventually consistent by design* and *broken in practice* without verification:**
>
> ```
>   Postgres  ──CDC/outbox──▶  Kafka  ──worker──▶  Elasticsearch
>      │            │             │                    │
>      └────────────┴─────────────┴────────────────────┘
>                        any break here → drift
>
>   Without a reconcile job, drift accumulates *silently*.
> ```
>
> **First-suspicion checklist:**
>
> 1. Outbox/CDC lag — is the worker processing? (Worker heartbeat, lag metric.)
> 2. Kafka queue depth / Logstash status.
> 3. Recent-document count: DB vs ES (sampling).
>
> *Architectural rule:* every cross-store sync needs (a) monitoring on lag, (b) a periodic reconcile job, (c) versioned writes so the indexer can skip stale updates. "It usually works" is not a strategy — eventually it won't, silently.

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

> **Mental model — "wrong data for the right request" is *always* a state-leak bug:**
>
> ```
>   Where state leaks across requests:
>     1. Cache key missing user_id (everyone shares one key)
>     2. Global variable holding req.user from a previous request
>     3. DB connection reused with an open transaction from prior request
>     4. ORM identity map / EntityManager scope leaking across requests
>     5. Shared mutable singleton (auth context, headers map)
> ```
>
> **First-suspicion checklist:**
>
> 1. Read the *recent* code changes — what was deployed?
> 2. Search for `req.user` set into anything global.
> 3. Audit cache keys for missing user_id discriminator.
> 4. Connection lifecycle — is it always released in `finally`?
>
> *Severity escalation:* "wrong user data returned" is a **P0 security incident**, not a performance bug. Page someone, freeze deploys, audit the affected window. Treat it that way in interview — that escalation instinct is the senior signal.

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

> **Mental model — disk fills from four families of cause:**
>
> ```
>                     [Disk full]
>                          │
>      ┌───────────────────┼───────────────────┐
>      ▼                   ▼                   ▼
>   Data growth      Bloat            WAL retention
>   (real)           (vacuum lag)     (replication slot,
>                                      archiver failure)
>      │                   │                   │
>      ▼                   ▼                   ▼
>   Largest tables    n_dead_tup high   pg_replication_slots
>   (unbounded logs?) → VACUUM FULL     → drop / fix
>   → archive/truncate
> ```
>
> **First-suspicion checklist:**
>
> 1. `df -h` to confirm; `du -sh /var/lib/postgresql/data/*` to localize.
> 2. `pg_database_size`, then largest tables (`pg_total_relation_size`).
> 3. Are there backups / dumps on the data disk? (Common operational mistake.)
> 4. `pg_replication_slots` — pinned WAL?
> 5. Bloat estimator queries.
>
> *Operational lesson:* alert at **80% disk usage**, not 95%. At 95% you're already an hour from outage. Senior teams have a documented growth-and-retention policy reviewed quarterly.

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

---

## Senior-engineer debugging principles (memorize these)

After 18 scenarios, the *patterns* are more important than the specific answers. These are the principles that separate seniors from mids:

### 1. Symptom is not cause
"The query is slow" is a symptom. The cause is one of: stale stats, missing index, lock wait, disk I/O, replication catch-up, etc. *Always* ask "what does the symptom *imply* about the cause?"

### 2. Cheapest test first
List your hypotheses, then sort by **cost-to-check × likelihood**. A 1-minute query against `pg_stat_activity` beats a 1-hour code review of all order paths. Always probe the cheapest hypothesis first — even if it's not the most likely.

### 3. Trust the metric — but verify the metric
"DB CPU is fine" might mean "DB is fine" or might mean "we're not measuring the actual bottleneck". Cross-check with at least two independent signals before concluding.

### 4. The five whys (apply to every incident)
Don't stop at "we found the bug". Keep asking:
- Why did it happen?
- Why did our tests miss it?
- Why didn't monitoring catch it?
- Why didn't code review catch it?
- Why is this class of bug *possible* in our architecture?

The fifth "why" is where the senior-level fix lives.

### 5. Every reactive scenario has a proactive fix
For each incident class:
- **Immediate**: what unblocks production now
- **Short-term**: what prevents recurrence this week
- **Long-term**: what makes this class of bug architecturally impossible

Interviewers love hearing all three.

### 6. Measure → hypothesize → verify → fix → confirm → document
Skip any step and you're guessing. The "document" step (postmortem, runbook update) is what compounds over time. Most teams skip it. Mention it in interviews.

### 7. Production debugging is forensics, not coding
You will rarely write code during an incident. You will read logs, query system tables, correlate timestamps, and *infer* from incomplete data. Get good at:
- Reading `EXPLAIN ANALYZE` output
- Reading Postgres logs (deadlock graphs, lock waits, slow queries)
- Reading Redis `INFO` output
- Reading `iostat`, `vmstat`, `pg_stat_*`
- Correlating metrics on a timeline

### 8. The fire-fighter trap
There is always one more fire. If you only fire-fight, the fires never stop. Senior engineers schedule *post-incident* time to fix the root cause, not just the symptom. Mention this in interviews — it shows organizational maturity.

---

## How to map any new debugging scenario to a known one

When the interviewer pitches a scenario you haven't seen, classify it within 30 seconds:

```
   Is it about         ─▶  cluster it belongs to
   ───────────────────────────────────────────────
   "slow query"        ─▶  Scenarios 1, 8, 15
   "wrong data"        ─▶  Scenarios 6, 9, 17
   "stale data"        ─▶  Scenarios 3, 16
   "overload/timeout"  ─▶  Scenarios 5, 7
   "infrastructure"    ─▶  Scenarios 11, 12, 13, 18
   "concurrency"       ─▶  Scenarios 2, 6, 10
   "cache pathology"   ─▶  Scenarios 4, 5
   "hot partition"     ─▶  Scenario 14
```

Then run that cluster's mental model and first-suspicion checklist. You won't know every scenario, but you can always classify and pattern-match — and that's what the interviewer is grading.

---

## Final framing: why these scenarios are the highest-signal interview round

A "design Twitter" question gives the candidate 30 minutes to construct an answer. A debugging scenario gives them 5 minutes to *react*. Reaction reveals instinct. Instinct comes from experience. Experience can't be faked.

If you can walk through 18 debugging scenarios with structured hypotheses, prioritized checks, and clear short/long-term fixes — you're an SDE2. If you also catch the *meta-pattern* (every scenario reduces to "measure, classify, probe, fix, monitor") — you're senior. Aim for both.
