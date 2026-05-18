# Postgres advisory locks: when, why, and how

## Source / Origin
- Postgres-specific feature; widely used by Sidekiq-Postgres, gh-ost, schema migration tools.
- Reference: Postgres `pg_advisory_lock` family (https://www.postgresql.org/docs/current/functions-admin.html#FUNCTIONS-ADVISORY-LOCKS).
- Concept reference: `backend-data-prep/sql/08-locks-concurrency.md`.

## Why this question matters in interviews
Advisory locks are the "I need a mutex but I'm already on Postgres" answer. Senior engineers reach for them instead of spinning up Redis Redlock or ZooKeeper for many use cases. The interview signal: can you name 3-4 concrete use cases (singleton job, cross-row coordination, idempotent migrations) and articulate the trade-offs (session vs transaction scope, pgbouncer compatibility)?

## Concepts involved

### Syntax to lock in

```sql
-- Session-scoped: lock held until pg_advisory_unlock or session ends
SELECT pg_advisory_lock(12345);      -- blocks if held by another session
SELECT pg_try_advisory_lock(12345);  -- returns true/false; non-blocking
-- ... critical section ...
SELECT pg_advisory_unlock(12345);

-- Transaction-scoped: lock released at COMMIT/ROLLBACK automatically
BEGIN;
SELECT pg_advisory_xact_lock(12345);
SELECT pg_try_advisory_xact_lock(12345);  -- non-blocking variant
-- ... critical section ...
COMMIT;  -- lock released

-- Two-integer key (for namespacing)
SELECT pg_advisory_lock(42, 100);  -- (classroom_id=42, resource=100)

-- Inspect held advisory locks
SELECT * FROM pg_locks WHERE locktype = 'advisory';
```

### Edge cases / interview traps

1. **Session-scoped vs transaction-scoped.** Session-scoped survives across transactions but requires explicit unlock; transaction-scoped is auto-released on COMMIT/ROLLBACK. **Use xact when possible** — eliminates leak class entirely.
2. **pgbouncer transaction pooling breaks session-scoped advisory locks.** The connection is recycled between transactions; the session that holds the lock may not be reused. Use xact-scoped, or pin to session-pooling mode.
3. **Cluster-local only.** Advisory locks don't replicate. For cross-cluster mutex you need Redis / ZooKeeper / etcd.
4. **Integer keys.** Two flavors: single `bigint` or `(int, int)`. Most code hashes a string: `pg_advisory_xact_lock(hashtext('user:' || $user_id))`.
5. **No deadlock detection across advisory + row locks.** The detector treats advisory locks as opaque; deadlocks involving them won't be detected automatically. Use try-advisory or NOWAIT to avoid.
6. **Reentrant** — same session can acquire the same advisory lock multiple times; must unlock the same number of times.
7. **Crash-safe** — if the holding session dies (connection drop), the lock is released. Better than a "lock row" pattern that requires a cleanup job.

## Mental Model

The **"name your own mutex"** model. Postgres has a high-quality, deadlock-detecting lock manager. Advisory locks let *you* register named mutexes inside it, identified by integers you pick. No table, no row, no constraint — pure synchronization.

```
   Application code
        │
        │ "I'd like a mutex on key=12345"
        ▼
   ┌─────────────────────────┐
   │  Postgres lock manager  │
   │  (the same one used     │
   │   for row, table locks) │
   │  ─────────────────────  │
   │  advisory key 12345 → session A
   │  advisory key 67890 → session B
   └─────────────────────────┘
        ▲                       ▲
        │                       │
   session A                session B (waiting for 12345 if it asks)
```

Compared to alternatives:

```
   Need                          Best tool
   ─────                         ─────────
   In-process mutex              Language primitive (no DB)
   Single-process cron singleton Advisory lock
   Cross-host (one cluster)      Advisory lock
   Cross-cluster                 Redis Redlock / ZooKeeper / etcd
   Per-row mutex                 SELECT ... FOR UPDATE
   Cross-row coordination        Advisory lock
```

## Why interviewers care

- Tests knowledge of a **Postgres-specific operational tool** that solves real problems.
- Probes **trade-off thinking**: when do you reach for Redis vs use what's already in your DB?
- Asks about **session vs transaction scope** — a real production trap.

## Common beginner confusion

- "Advisory locks lock rows." They don't — they're pure logical mutexes. The DB doesn't know what the integer means.
- "Slow because it's the DB." Sub-millisecond. Cheap.
- "Replicated." No — cluster-local.
- "Auto-released on transaction end." Only `pg_advisory_xact_lock`. Session-scoped requires explicit unlock or session death.
- "Same as row locks." No — row locks block other locks on that row's data; advisory locks block on a key only your app understands.

## Brute force approach

Set up Redis or ZooKeeper for every mutex need. Works; adds operational dependency and another point of failure for what Postgres already does.

## Optimal approach

Reach for advisory locks when:

- You need a singleton job within a Postgres cluster.
- You want to serialize work on a logical entity that doesn't have a single row (e.g., "all user 42's invoices").
- You want a cheap, crash-safe mutex without adding Redis/ZK.
- You want transaction-scoped automatic cleanup.

Reach for Redis Redlock / ZooKeeper when:

- Multiple Postgres clusters must coordinate.
- You need explicit lease/TTL semantics with renewal.
- You need the mutex to be observable from non-DB clients.

## Solution

```sql
-- ============================================================
-- Use case 1: singleton periodic job
-- ============================================================
-- Cron fires the same script on N hosts; only one should execute.

DO $$
BEGIN
  IF NOT pg_try_advisory_lock(hashtext('nightly-rollup')) THEN
    RAISE NOTICE 'Another worker is running; skipping.';
    RETURN;
  END IF;
  -- ... do work ...
  PERFORM pg_advisory_unlock(hashtext('nightly-rollup'));
END $$;

-- ============================================================
-- Use case 2: per-user serialization (cross-row coordination)
-- ============================================================
-- "Don't process two invoices for the same user concurrently"

BEGIN;
SELECT pg_advisory_xact_lock(hashtext('invoice-process:' || $user_id::text));
-- Now no other tx can grab this user's invoice-process lock
INSERT INTO invoices ...;
UPDATE accounts ...;
COMMIT;  -- lock released

-- ============================================================
-- Use case 3: idempotent migration step
-- ============================================================
-- Migration runner executes the same step on multiple hosts at startup;
-- only the first one should run.

BEGIN;
IF pg_try_advisory_xact_lock(hashtext('migration:add_email_to_users')) THEN
  ALTER TABLE users ADD COLUMN email TEXT;
  INSERT INTO schema_migrations (id) VALUES ('add_email_to_users');
END IF;
COMMIT;

-- ============================================================
-- Use case 4: rate-limited critical section
-- ============================================================
-- Allow at most one concurrent webhook processor per source

BEGIN;
SELECT pg_advisory_xact_lock(hashtext('webhook-source:' || $source_id::text));
-- process the webhook
COMMIT;

-- ============================================================
-- Inspect held advisory locks
-- ============================================================
SELECT pid, classid, objid, mode, granted
FROM pg_locks
WHERE locktype = 'advisory';
```

Node usage:

```javascript
async function withAdvisoryLock(db, key, fn) {
  // Transaction-scoped is safer
  return db.tx(async tx => {
    const ok = await tx.one(
      'SELECT pg_try_advisory_xact_lock($1) AS got',
      [hashKey(key)]
    );
    if (!ok.got) throw new Error('LOCK_BUSY');
    return fn(tx);
  });
}

function hashKey(str) {
  // Stable 64-bit hash → bigint
  let h = 0n;
  for (const c of str) h = (h * 31n + BigInt(c.charCodeAt(0))) & 0xFFFFFFFFFFFFFFFFn;
  return h.toString();
}
```

## Step-by-step dry run

Singleton job — two cron-fired processes on different hosts:

```
time →

Host A: |--connect--|--pg_try_advisory_lock(K)=true--|--do work (5 min)--|--pg_advisory_unlock(K)--|--disconnect--|

Host B (fires at the same second):
        |--connect--|--pg_try_advisory_lock(K)=false--|--log "skipping"--|--exit--|

Only Host A runs. Crash-safe: if Host A dies mid-work, the connection closes, the lock auto-releases, the next cron fire on either host can claim it.
```

Cross-row coordination — two webhooks for the same user:

```
T1 (webhook from user 42):
  |--BEGIN--|--pg_advisory_xact_lock(hash('user:42'))--|--process--|--COMMIT (lock released)--|

T2 (second webhook from user 42, arrives concurrently):
                                                                   |--BEGIN--|--pg_advisory_xact_lock(hash('user:42')) WAITS--|--T1 done, T2 acquires--|--process--|--COMMIT--|

Serialised on user 42; users 43, 44 unaffected. Granular lock without touching any user row.
```

pgbouncer trap with session-scoped:

```
Client → pgbouncer → backend session B1
SELECT pg_advisory_lock(42);  -- held by B1
-- request 1 ends; pgbouncer returns B1 to pool

Client → pgbouncer → backend session B2 (different!)
-- expects the advisory lock to still be "held" from its POV
-- but B2 doesn't hold it; another client could grab it via B1
SELECT pg_try_advisory_lock(42);  -- might return true unexpectedly

Fix: use pg_advisory_xact_lock; it's released at COMMIT, so the pool returns a clean session.
```

## How to think aloud in the interview

> "Advisory locks are application-defined mutexes living inside Postgres' lock manager. You pick an integer (or hash a string into one) and Postgres treats it as a named mutex. Two flavors: session-scoped (`pg_advisory_lock`) and transaction-scoped (`pg_advisory_xact_lock`). I default to xact-scoped because it auto-releases at COMMIT — eliminates the leak class.
>
> Use cases:
> 1. Singleton periodic job — `pg_try_advisory_lock` on a job name hash; if false, skip.
> 2. Cross-row coordination — `pg_advisory_xact_lock(hash('user:'||id))` to serialize on a logical entity that's not a single row.
> 3. Idempotent migrations — only one host runs the DDL step.
> 4. Rate-limited critical section — one webhook processor per source.
>
> Trade-offs: cluster-local, doesn't replicate, breaks under pgbouncer transaction pooling for session-scoped. Sub-millisecond. Crash-safe (lock released on connection drop).
>
> For cross-cluster mutex I'd reach for Redis Redlock or ZooKeeper. For one Postgres cluster, advisory locks are the cheapest correct answer."

## Important takeaways

- Application-defined integer-keyed mutex in Postgres' lock manager.
- Two scopes: session (`pg_advisory_lock`) and transaction (`pg_advisory_xact_lock`).
- **Prefer xact-scoped** — auto-released on COMMIT/ROLLBACK.
- Cluster-local. Doesn't replicate.
- Sub-millisecond. Crash-safe (released on connection close).
- **Breaks under pgbouncer transaction pooling for session-scoped** — use xact-scoped.
- Use cases: singleton job, cross-row coordination, migration step, rate-limited critical section.
- For cross-cluster: Redis Redlock or ZooKeeper.

## Variants

1. **`pg_advisory_lock_shared`** — multiple shared holders, blocked by exclusive. Rarely used.
2. **MySQL `GET_LOCK(name, timeout)`** — analogous, named string keys.
3. **Sidekiq-Postgres uses advisory locks** for queue worker singleton-job logic.
4. **`pg_try_advisory_xact_lock`** — non-blocking, returns false if held. Use for opportunistic concurrency.
5. **Hashing strategy**: `hashtext('namespace:' || id)` is the conventional pattern. Watch for collisions on hot keys.
6. **`pg_advisory_unlock_all`** — releases everything session-scoped. Use in a finally block as belt-and-suspenders.

## Revision notes

> **advisory-lock — 60 second recap**
> - Application-defined int-keyed mutex in Postgres' lock manager.
> - `pg_advisory_lock` (session) vs `pg_advisory_xact_lock` (transaction). **Prefer xact**.
> - `pg_try_*` variant: non-blocking, returns bool.
> - Sub-ms; crash-safe (released on connection drop).
> - Cluster-local; doesn't replicate.
> - **pgbouncer transaction pooling breaks session-scoped** — use xact.
> - Use: singleton job, cross-row coordination, migration step, rate-limited section.
> - For cross-cluster mutex: Redis Redlock / ZooKeeper.
> - Hashing: `hashtext('namespace:' || id)`.
