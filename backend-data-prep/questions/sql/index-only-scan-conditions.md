# Index-Only Scan — What Blocks It

## Source / Origin
- Senior Postgres interview, "you built a covering index but EXPLAIN still shows Heap Fetches > 0 — why?"
- Real prod: a slowly-bloating table whose covering index quietly stopped serving index-only scans.

## Why this question matters in interviews
Building a covering index is half the battle — actually **getting an index-only scan** is the other half. Postgres has a *visibility map* (VM) that tracks which heap pages contain only rows visible to all current transactions. The planner uses index-only scans **only** for pages marked all-visible. Otherwise, it must visit the heap to check row visibility (MVCC), defeating the optimization.

The interviewer wants to see that you understand: (1) MVCC stores multiple row versions, (2) the index alone can't tell you which version is "live", (3) the VM is the optimization that lets us skip the heap visit, (4) VACUUM is what maintains the VM.

## Concepts involved

### Syntax to lock in
```sql
-- Build a covering index
CREATE INDEX ix_users_email_cov ON users(email) INCLUDE (name);

-- Check VM coverage
SELECT relname, pg_relpages.relpages, n_live_tup, n_dead_tup, last_vacuum
FROM   pg_stat_user_tables
WHERE  relname = 'users';

-- Force VM update
VACUUM users;            -- ordinary vacuum updates VM
VACUUM (ANALYZE) users;  -- + refreshes stats

-- Verify index-only scan
EXPLAIN (ANALYZE, BUFFERS)
SELECT name FROM users WHERE email = 'a@x.com';
-- Want: Heap Fetches: 0
```

### Edge cases / interview traps
1. **Recent writes ⇒ no all-visible page ⇒ heap fetch required.** Right after a bulk insert / update, index-only scans degrade until VACUUM runs.
2. **Long-running transactions** prevent VACUUM from marking pages all-visible because xmin horizons can't advance.
3. **HOT (Heap-Only Tuple) updates** — if columns updated are NOT indexed, Postgres can do a HOT update, leaving the index unchanged. Helpful for write-throughput but doesn't directly affect VM.
4. **`pg_visibility` extension** lets you inspect VM page by page.
5. **Index-only scan still verifies xmin** in some cases (sub-transactions, hint-bit not set). Look at `Heap Fetches` in EXPLAIN.
6. **autovacuum thresholds** — by default fires when 20% of table is dead. For hot tables, tune `autovacuum_vacuum_scale_factor` lower.
7. **MVCC bloat** = heap rows that are dead-but-not-vacuumed. Bloat correlates with heap fetches.
8. **MySQL InnoDB** doesn't have a visibility map; covering index hits are simpler (uses PK to verify if needed).

## Mental Model

```
   Postgres heap page status (visibility map per page):

   page  state                       index-only scan from this page?
   ────  ──────────────────          ────────────────────────────────
    1   all-visible                  YES  ← VM says "all rows visible"
    2   recently-updated             NO   ← heap visit to check xmin/xmax
    3   dead-tuples-present          NO   ← VACUUM needed
    4   bulk-insert                  NO   ← until VACUUM stamps the bit

   Plan: Index Only Scan
     For each index leaf entry:
       look up VM for the row's page.
       if VM says "all-visible": emit row from index.
       else: fetch heap row, check xmin/xmax, then emit (or skip).
```

The VM is **the** thing that turns a "could be an index-only scan" into "actually was an index-only scan". `Heap Fetches: N` in EXPLAIN tells you how many rows failed the VM check.

## Why interviewers care
- Connects MVCC + indexes + VACUUM into one coherent story.
- Tests whether the candidate has actually shipped covering indexes in production.
- Reveals understanding that "perf optimization doesn't stick without maintenance".

## Common beginner confusion
- "I added INCLUDE, why am I still hitting the heap?" — VM isn't up to date.
- "VACUUM is just for space reclamation" — also updates the VM, which is what enables index-only scans.
- "Long-running transactions only block other writes" — they also block VACUUM from advancing horizons.
- "Postgres can always do an index-only scan when the index covers" — only when the VM says all-visible.

## Brute force approach
Ignore the issue and accept heap fetches. Works but loses 5-10× perf on hot endpoints.

Or: force VACUUM after every batch insert — works but doesn't scale and locks resources.

## Optimal approach
1. Build the covering index.
2. Tune autovacuum to fire often on this table (`alter table users set (autovacuum_vacuum_scale_factor = 0.05)`).
3. Avoid long-running transactions; if unavoidable, ensure they're read-only on the same DB.
4. Monitor `Heap Fetches` in `EXPLAIN ANALYZE`. Trend it on a dashboard.

## Solution (SQL)

```sql
CREATE TABLE users (
  id    BIGSERIAL PRIMARY KEY,
  email TEXT,
  name  TEXT,
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX ix_users_email_cov ON users(email) INCLUDE (name);

-- Insert 10K rows
INSERT INTO users(email, name)
SELECT 'u'||g||'@x.com', 'User '||g FROM generate_series(1,10000) g;

-- Before VACUUM:
EXPLAIN (ANALYZE, BUFFERS)
SELECT name FROM users WHERE email='u5000@x.com';
-- Index Only Scan using ix_users_email_cov on users
--   Heap Fetches: 1    ← VM not stamped yet for the just-inserted pages
--   Buffers: shared hit=4 read=1   ← 1 heap page read

VACUUM users;

-- After VACUUM:
EXPLAIN (ANALYZE, BUFFERS)
SELECT name FROM users WHERE email='u5000@x.com';
-- Index Only Scan using ix_users_email_cov on users
--   Heap Fetches: 0    ← now it's index-only
--   Buffers: shared hit=4
```

Tighten autovacuum on the table:

```sql
ALTER TABLE users SET (
  autovacuum_vacuum_scale_factor = 0.05,
  autovacuum_vacuum_cost_limit   = 1000
);
```

## Step-by-step dry run

```
Newly inserted rows → on pages that VM doesn't yet flag all-visible.
Query: SELECT name FROM users WHERE email='u5000@x.com'
  Step 1: descend ix_users_email_cov → leaf has (email, name, tid).
  Step 2: check VM for tid's page → "not all-visible".
  Step 3: heap fetch → read row → check xmin/xmax → row visible.
  Step 4: emit name. (Heap Fetches: 1)

After VACUUM:
  Step 1: descend index → leaf entry.
  Step 2: VM says "all-visible".
  Step 3: NO heap fetch. Emit name directly from leaf.
  (Heap Fetches: 0)
```

The "index-only scan plan" exists in both cases; whether it actually skips the heap depends on the VM at runtime.

## How to think aloud in the interview
1. *"Index-only scan needs more than the covering index — it needs the visibility map to say the heap page is all-visible to my snapshot."*
2. *"VM is updated by VACUUM. Bulk inserts or updates push VM behind; recent writes degrade index-only scans temporarily."*
3. *"I'd monitor `Heap Fetches` in EXPLAIN ANALYZE and tune autovacuum's scale factor down for hot tables."*
4. *"Long-running transactions are a hidden killer — they hold back the xmin horizon and prevent VACUUM from advancing."*
5. *"MySQL/InnoDB doesn't have this model; secondary indexes look up the clustered PK to verify visibility — different mechanism, same goal."*

## Important takeaways
- Index-only scan in Postgres requires the visibility map to mark the heap page all-visible.
- VACUUM is what updates the VM. autovacuum thresholds matter.
- `Heap Fetches > 0` in EXPLAIN ⇒ index-only scan degraded to heap fetch.
- Long-running transactions block VM advancement.
- MySQL InnoDB doesn't use a VM; its covering-index story is simpler.
- See `backend-data-prep/sql/04-indexing.md` and `06-transactions.md` for MVCC context.

## Variants
1. **`pg_visibility` extension** — `pg_visibility_map(oid)` shows which pages are flagged. Diagnostic gold.
2. **HOT updates** — keep updates of non-indexed columns from invalidating indexes; mention as adjacent optimization.
3. **Btree partial + INCLUDE** — combine partial index with INCLUDE for ultra-narrow, ultra-fast hot path indexes.

## Revision notes

> **Index-only scan cram block**
> - Plan label: `Index Only Scan` ≠ guarantee no heap visit.
> - Postgres: VM (visibility map) per heap page; planner consults at runtime.
> - VM stamped by VACUUM. autovacuum tunes scale factor.
> - `Heap Fetches: N` in EXPLAIN — if N>0, VM behind.
> - Recent writes / long-running transactions degrade VM.
> - Fix: VACUUM, lower autovacuum scale, kill long txns.
> - MySQL InnoDB: no VM; secondary index includes PK implicitly.
> - Maintenance is part of perf — covering index without VACUUM under-delivers.
