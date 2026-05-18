# Pick optimistic vs pessimistic concurrency control for a workload

## Source / Origin
- Standard "design choice" question after a concurrency anomaly is identified.
- Concept reference: `backend-data-prep/sql/08-locks-concurrency.md`.
- Real-world: every domain modeling decision pits "lock and wait" vs "version and retry".

## Why this question matters in interviews
The interviewer hands you a workload and asks: "Would you use pessimistic locking or optimistic concurrency control here?" The wrong answer is "it depends" with no follow-up. The right answer is a 30-second tree: estimate conflict probability, estimate transaction length, weigh deadlock risk vs retry storm risk, pick one, justify it. This is the **decision question** that signals you've made the tradeoff in production, not just read about it.

## Concepts involved

### Syntax to lock in

```sql
-- Pessimistic: lock first, modify, commit
BEGIN;
SELECT * FROM products WHERE id=1 FOR UPDATE;  -- X lock acquired
-- compute new price
UPDATE products SET price = $new WHERE id=1;
COMMIT;  -- lock released

-- Optimistic: version-check at write time
SELECT id, price, version FROM products WHERE id=1;  -- read snapshot
-- compute new price in app
UPDATE products SET price=$new, version=version+1
WHERE id=1 AND version=$expected_version;
-- 0 rows affected → someone else won → refetch + retry
```

### Edge cases / interview traps

1. **Optimistic under high contention degenerates into a retry storm.** Throughput collapses; latency spikes. Pessimistic is faster in this regime even with blocking.
2. **Pessimistic with long transactions = deadlocks + lock-wait latency.** If the work inside the lock takes >100ms, throughput suffers.
3. **You can mix them.** Read-mostly system → optimistic on the read path, pessimistic on the rare write that needs atomicity (`FOR UPDATE`).
4. **Optimistic still needs row locks at write time.** The UPDATE acquires an X lock briefly; the difference is you don't *hold* a lock across the read+compute.
5. **Pessimistic locks held across network calls = catastrophic.** Never make an HTTP call inside a `FOR UPDATE` transaction.
6. **Optimistic doesn't deadlock.** It can livelock under thundering retries; deadlock requires holding locks, which OCC doesn't.
7. **The version column must be incremented atomically with the data change.** Two-step "read version, write data, write version" is broken.

## Mental Model

The **"shirt fitting room"** model.

- **Pessimist**: takes the shirt off the rack, locks themselves in the fitting room. While inside, nobody else can examine that shirt. Total guarantee, but if they spend 20 minutes deciding, the shirt is unavailable to others.
- **Optimist**: takes the shirt home, tries it, comes back to buy. At checkout: "wait, someone else also tried this exact size — let me check if it's still here." If yes, sale closes. If sold meanwhile, optimist leaves empty-handed. Optimist bet conflict was unlikely; lost the bet.

```
   Conflict probability ────►

   LOW (1%):                   MEDIUM (20%):              HIGH (80%):
   optimistic wins             either works, mostly       pessimistic wins
                               optimistic                 (or redesign)

   Tx duration ────►

   SHORT (<10ms):              MEDIUM (10-100ms):         LONG (>100ms):
   pessimistic fine            either                     optimistic / redesign

   Conflict cost ────►

   CHEAP (silent retry):       MEDIUM (user re-edits):    EXPENSIVE (lost work):
   optimistic                  optimistic w/ UX          pessimistic w/ short tx
                                                          or pre-claim pattern
```

## Why interviewers care

- It's a **decision-making test**: can you reason about a workload's *shape* and pick a strategy?
- They want **operational vocabulary**: deadlock rate, retry rate, p99 latency, lock-wait time.
- They probe **hybrid usage** — most production systems mix both; can you describe where?

## Common beginner confusion

- "Optimistic is always better because no blocking." Only when conflicts are rare. Under contention it's a thundering herd.
- "Pessimistic causes deadlocks." Only with inconsistent lock ordering. Locking in canonical order (by ID) eliminates deadlock risk.
- "MVCC means optimistic by default." MVCC = readers don't block writers; doesn't dictate which CC strategy you use on writes.
- "Just use SERIALIZABLE." Postgres SSI is optimistic concurrency *with serializability* — same retry semantics. Not a magic bullet for high-conflict workloads.

## Brute force approach

Pick one strategy globally. Wrong because it ignores per-feature shape: a hot counter row is high-conflict (pessimistic or redesign); a rarely-edited product description is low-conflict (optimistic). Use the right tool per feature.

## Optimal approach

Decision tree:

1. **Estimate conflict probability.** If you can't measure, eyeball: how many concurrent writers per row per second?
2. **Estimate transaction duration.** Short = lock holders release fast; long = blocking dominates.
3. **Estimate retry cost.** UX-visible retries (user re-edits) = expensive; silent retries = cheap.
4. **Pick:**
   - Low conflict + cheap retry → **optimistic** (version column).
   - High conflict + short tx → **pessimistic** (`FOR UPDATE`).
   - High conflict + expensive retry → **redesign** (sharded counters, claim-then-confirm, queue).
   - Multi-row invariant → **SERIALIZABLE** (Postgres SSI; optimistic with retry).
5. **Hybrid is fine.** Reads use MVCC + optimistic version; the one critical write path uses `FOR UPDATE`.

## Solution

```sql
-- ============================================================
-- Recipe: pessimistic (high contention, atomic decision)
-- ============================================================
BEGIN;
-- Lock in canonical order to avoid deadlock
SELECT id FROM accounts
WHERE id IN (LEAST($from, $to), GREATEST($from, $to))
ORDER BY id FOR UPDATE;

UPDATE accounts SET balance = balance - $amount
  WHERE id = $from AND balance >= $amount;
-- rowcount=0 → insufficient → ROLLBACK + error

UPDATE accounts SET balance = balance + $amount WHERE id = $to;
COMMIT;

-- ============================================================
-- Recipe: optimistic (low contention, lightweight)
-- ============================================================
SELECT name, price, version FROM products WHERE id=1;
-- (user edits in UI for 30 seconds)
UPDATE products
SET name=$new_name, price=$new_price, version=version+1
WHERE id=1 AND version=$client_version;
-- rowcount=0 → someone else saved meanwhile → reload UI, ask user to merge

-- ============================================================
-- Recipe: hybrid (read MVCC, write pessimistic-on-the-hot-row)
-- ============================================================
-- Browse: plain SELECT under MVCC — no locks
SELECT * FROM products WHERE category='shoes';

-- Buy: pessimistic on stock row
BEGIN;
SELECT qty FROM inventory WHERE product_id=$pid FOR UPDATE;
UPDATE inventory SET qty = qty - 1 WHERE product_id=$pid AND qty > 0;
INSERT INTO orders ...;
COMMIT;

-- ============================================================
-- Recipe: SERIALIZABLE (optimistic + serializability guarantee)
-- ============================================================
BEGIN ISOLATION LEVEL SERIALIZABLE;
-- multi-row read + decision
COMMIT;  -- may raise 40001; app retries
```

Node retry wrapper for optimistic:

```javascript
async function withOptimisticRetry(loadAndUpdate, attempts = 3) {
  for (let i = 0; i < attempts; i++) {
    const { data, version } = await loadAndUpdate.load();
    const newData = loadAndUpdate.mutate(data);
    const { rowCount } = await db.result(
      `UPDATE t SET ..., version=version+1 WHERE id=$id AND version=$version`,
      newData
    );
    if (rowCount === 1) return newData;
    // conflict; retry with fresh read
  }
  throw new Error('CONCURRENT_MODIFICATION');
}
```

## Step-by-step dry run

Workload: e-commerce product edits, low conflict (1 editor per product per minute).

**Pessimistic** trace:
```
T1 (editor A):  |--BEGIN--|--SELECT FOR UPDATE product 5--|--(user edits 30s)--|--UPDATE--|--COMMIT--|
T2 (editor B):                                            |--BEGIN--|--SELECT FOR UPDATE product 5--BLOCKED 30s---->|--proceeds--|

T2 waited 30 seconds because the lock was held across a UI roundtrip.
Verdict: terrible. Don't hold locks across human time.
```

**Optimistic** trace:
```
T1 (editor A):  |--SELECT (v=7)--|--(user edits 30s)--|--UPDATE WHERE v=7 → 1 row OK--|
T2 (editor B):                   |--SELECT (v=7)--|--(user edits 25s)--|--UPDATE WHERE v=7 → 0 rows--|--reload page, see A's change--|--merge or overwrite--|

T2 doesn't wait. Conflict surfaces as a UX prompt: "your version is out of date, reload?"
Verdict: correct. Optimistic shines when the lock window would be longer than the conflict probability allows.
```

Workload: payments hot path, high contention on account row.

**Optimistic** trace under contention:
```
T1: read v=10, compute, UPDATE WHERE v=10 → OK
T2: read v=10, compute, UPDATE WHERE v=10 → 0 rows (T1 won)
    refetch v=11, compute, UPDATE WHERE v=11 → OK
T3: read v=10, conflict, refetch v=12, UPDATE WHERE v=12 → 0 rows (T2 won)
    refetch v=13, UPDATE → OK
...

Under 100 concurrent transfers: most retry 1-5 times. Throughput collapses.
Verdict: pessimistic is better here — short transaction, hot row, retries amplify.
```

**Pessimistic** trace under contention:
```
T1: BEGIN, FOR UPDATE, UPDATE, COMMIT (10ms inside lock)
T2: BEGIN, FOR UPDATE waits, gets lock, UPDATE, COMMIT (waited 10ms)
T3: BEGIN, FOR UPDATE waits 20ms, then 10ms work
...

Linear queue. p99 = N * 10ms for N concurrent. Throughput stable, latency degrades gracefully.
Verdict: better than optimistic retry storm.
```

## How to think aloud in the interview

> "Decision tree: conflict probability and transaction duration drive the choice.
>
> **Low conflict + short tx**: either works; I'd default to optimistic with a version column because it avoids blocking on the rare conflict.
>
> **High conflict + short tx**: pessimistic. `SELECT ... FOR UPDATE` inside a tight BEGIN/COMMIT. Retries under optimistic become a thundering herd.
>
> **Long tx (UI roundtrip)**: never pessimistic — you'd hold a lock across human time. Always optimistic, surface conflict in UX.
>
> **Multi-row invariant**: SERIALIZABLE (Postgres SSI) — optimistic with serializability, app retries on 40001.
>
> Production: hybrid. Reads use MVCC unblocked. The one or two write paths that touch a hot row (counter, account balance) use pessimistic with consistent lock ordering. The rest use optimistic version columns. I never let a transaction span a network call to an external service."

## Important takeaways

- **Optimistic**: zero blocking, conflict at write time, app retries. Best for low-conflict, long-tx (UI editing), read-mostly.
- **Pessimistic**: lock first, blocks others, no retry. Best for high-conflict, short-tx, atomic decisions.
- **Never** hold a pessimistic lock across human / network time.
- **Lock in canonical order** to avoid deadlocks (by ID).
- **Hybrid is normal**: most apps use both, per-feature.
- **SERIALIZABLE = optimistic with serializability**, abort on 40001.

## Variants

1. **"How would you handle a hot row (counter) under high contention?"** Re-design: per-shard counters with periodic aggregation; or move to Redis with periodic DB flush.
2. **"Optimistic on append-only event stream?"** Use a monotonic version per aggregate (event sourcing). Two writers append → version conflict → retry.
3. **`SELECT ... FOR NO KEY UPDATE`** — Postgres-specific weaker pessimistic lock that still blocks updates but allows FK references to read.
4. **HTTP `If-Match` / ETag** — same optimistic pattern at the HTTP layer.
5. **CRDT** — eliminates the conflict entirely by making operations commutative. Different paradigm for offline-first apps.
6. **`SKIP LOCKED`** — pessimistic-but-non-blocking: skip rows others are working on. Queue worker pattern.

## Revision notes

> **optimistic-vs-pessimistic — 60 second recap**
> - Low conflict + long tx → **optimistic** (version column).
> - High conflict + short tx → **pessimistic** (`FOR UPDATE`).
> - Long tx across UI / network → never pessimistic.
> - Hybrid is normal: reads MVCC, hot writes pessimistic, edits optimistic.
> - Pessimistic + canonical lock order = no deadlock.
> - Optimistic under contention = thundering herd; redesign.
> - SERIALIZABLE = optimistic + serializability; retry on 40001.
> - `SKIP LOCKED` for queue workers; pessimistic without head-of-line blocking.
