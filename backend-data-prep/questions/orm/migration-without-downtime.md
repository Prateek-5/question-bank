# Migration without downtime

## Source / Origin
- The "tell me about a hard production change" interview question.
- Concept refs: `backend-data-prep/orm/02-orm-comparison.md` (Migrations section), companion files `expand-then-contract-pattern.md` and `backwards-compatible-schema-change.md`.

## Why this question matters in interviews
Schema migrations are the #1 cause of production outages directly attributable to backend engineering. Senior interviewers gauge whether you've **felt the pain** — long-locking DDL, NOT NULL adds that rewrite a billion-row table, column drops that break still-running app instances. The answer is **never one migration**; it's an **orchestrated multi-step deploy** that keeps old and new code compatible.

## Concepts involved

### The three blocking-DDL families

1. **Metadata-only changes** (instant): ADD COLUMN nullable, DROP CONSTRAINT (without rewrite), RENAME TABLE (with caveats).
2. **Table-rewriting changes** (very slow): ADD COLUMN NOT NULL with default (older Postgres), CHANGE COLUMN TYPE (often), MySQL's many ALTERs.
3. **Index-building changes** (long but non-blocking with the right flag): `CREATE INDEX CONCURRENTLY` (Postgres), online index in InnoDB.

### Syntax to lock in

```sql
-- Safe ADD COLUMN (Postgres ≥ 11)
ALTER TABLE orders ADD COLUMN currency TEXT;            -- metadata only, instant
ALTER TABLE orders ADD COLUMN currency TEXT DEFAULT 'USD' NOT NULL;
-- Postgres 11+: also instant (default stored in catalog, no rewrite).
-- Postgres ≤ 10: rewrites the entire table.

-- Safe NOT NULL add (post-backfill, any Postgres)
ALTER TABLE orders
  ADD CONSTRAINT chk_currency_not_null CHECK (currency IS NOT NULL) NOT VALID;
ALTER TABLE orders VALIDATE CONSTRAINT chk_currency_not_null;   -- scan, no lock
ALTER TABLE orders ALTER COLUMN currency SET NOT NULL;          -- now metadata-only
ALTER TABLE orders DROP CONSTRAINT chk_currency_not_null;

-- Safe index creation
CREATE INDEX CONCURRENTLY idx_orders_user_id ON orders(user_id);
-- Slower than non-concurrent, but doesn't block writers.

-- Unsafe forms to avoid in prod:
ALTER TABLE huge_table ADD COLUMN x TEXT NOT NULL DEFAULT 'foo';  -- old PG: rewrite
ALTER TABLE huge_table ALTER COLUMN amt TYPE BIGINT;              -- rewrite
ALTER TABLE huge_table RENAME COLUMN old TO new;                  -- breaks running code
```

### Edge cases / interview traps

1. **Locks block concurrent writes.** ALTER TABLE takes an `ACCESS EXCLUSIVE` lock by default — blocks *reads too*. Five-second hang on a busy table = visible outage.
2. **`lock_timeout`** — set this on your migration session (`SET lock_timeout = '3s'`) so the migration **fails fast** instead of queueing behind a long-running query.
3. **`pg_attribute` bloat** from many `ADD COLUMN; DROP COLUMN`. Dropped columns leave dead metadata; future migrations get slower.
4. **MySQL's ALTER history** — much worse than Postgres. Even `ADD COLUMN` blocks DML in older MySQL. Use `pt-online-schema-change` or `gh-ost`.
5. **Cascade FK on rename** — renaming a column referenced by FKs can break the FK quietly. Always confirm.
6. **Backfill at scale** — `UPDATE table SET col = ...` on 1B rows takes hours, holds replication slots, generates WAL flood. Batch in chunks with sleep.
7. **Replication lag** — a heavy migration on the primary creates replication lag on replicas. Your read replicas serve stale data for the duration.
8. **App instances see old schema vs new schema during deploy.** This is the entire reason for expand-then-contract — both views must be valid simultaneously.
9. **`CREATE INDEX CONCURRENTLY` can fail and leave INVALID index.** Always check `pg_index.indisvalid`; drop and recreate if so.
10. **Schema-cache stickiness** — Rails, Django, Sequelize cache the schema. Adding a column doesn't take effect until app restart.

## Mental Model

The constraint: **at every moment during the deploy, both old and new code instances are running, and both must work against whatever schema state is live.**

```
   Time →

   ────────── Old code only ────────────── Mixed ─────────── New code only ──────────
                                          ┌─────┐
   Schema:  V1 ──────────────────────────►│ V2  │──────────────────────────► V3 ──►
                                          └─────┘
   V1 = original
   V2 = expanded (adds new column, keeps old)   ◄── both old & new code work
   V3 = contracted (drops old after all new code rolled out)

   Multi-deploy contract:
     - Each schema step is backwards-compatible with the previous code.
     - Each code step is forward-compatible with the next schema step.
```

The full sequence in 5 steps:

```
   Step 1: deploy migration that ADDS new column (nullable)
   Step 2: deploy app v2 that DUAL-WRITES to old + new column
   Step 3: backfill new column from old (background job)
   Step 4: deploy app v3 that READS from new column, WRITES to both
   Step 5: deploy app v4 that ONLY reads/writes new column
   Step 6: deploy migration that DROPS old column
```

Every step is independently reversible. Every step is online.

## Why interviewers care

- Tests **production deploy thinking** — not just SQL knowledge.
- Tests **coordination skills** — schema + code + backfill + cutover.
- Tests **observability** — how do you know each step succeeded? Replication lag, error rate, query plan changes.
- Tests **rollback strategy** — can you revert at every step without data loss?

## Common beginner confusion

- **"Just run the migration in one PR."** Fine for prototypes; outage waiting to happen in prod.
- **"`ALTER TABLE` is fast because it's DDL."** It can rewrite the entire table in older Postgres / MySQL.
- **"My migration only locks for 100ms."** Lock acquisition can block behind a slow query, then queue all subsequent writes. The 100ms grows to 5 seconds.
- **"Adding NOT NULL with default is safe."** In Postgres 11+, yes. Before, it rewrites the table.
- **"I'll just deploy code and schema together."** Atomic deploy doesn't exist in a load-balanced fleet — there's always a window where old and new code coexist.
- **"Rename and ship."** Renames are the single most-common cause of "app suddenly errors after deploy."
- **"I'll backfill 100M rows in one UPDATE."** Locks the table, generates massive WAL, breaks replication, takes hours. Chunk it.

## Brute force approach

Take an outage window: stop traffic, ALTER, restart app. Works for B2B with maintenance windows; unacceptable for consumer products and SaaS.

## Optimal approach

The **expand → migrate → contract** discipline:

1. **Expand**: schema can store both old and new shapes. ADD columns; never DROP yet.
2. **Migrate data + code**: dual-write, backfill in batches, switch reads.
3. **Contract**: once all instances are on new code, drop old artifacts in a later release.

Every DDL with these constraints:
- Acquire locks with short `lock_timeout` (fail fast).
- Use `CONCURRENTLY` for index ops.
- Backfill in chunks (10k rows, sleep 100ms, monitor replication lag).
- Watch `pg_stat_activity` for waiters during migration.
- Run on canary first; smoke-test before broad rollout.

## Solution

```sql
-- ============================================================
-- Scenario: rename users.email → users.email_address
-- Live traffic, 50M rows, multi-instance app.
-- ============================================================

-- Release 1 (deploy 1) — schema: add new column
-- =============================================
SET lock_timeout = '3s';
ALTER TABLE users ADD COLUMN email_address TEXT;
-- (instant; nullable; old code unaffected.)

-- Release 1 (deploy 2) — code: dual-write
-- ========================================
-- (deploy app v2)
-- New writes go to BOTH columns:
UPDATE users SET email = $1, email_address = $1 WHERE id = $2;

-- Release 2 (background) — backfill
-- ==================================
-- A worker (cron, batch job) processes rows in chunks:
WITH batch AS (
  SELECT id FROM users
  WHERE email_address IS NULL AND email IS NOT NULL
  ORDER BY id LIMIT 10000
)
UPDATE users u SET email_address = u.email
FROM batch WHERE u.id = batch.id;
-- Sleep 100ms between batches. Monitor pg_stat_replication.

-- Release 2 (deploy) — code: read from new, still write both
-- ===========================================================
SELECT email_address FROM users WHERE id = $1;
-- (deploy and bake for hours/days)

-- Release 3 (deploy) — code: use only new column
-- ===============================================
-- Stop writing to `email`. Read & write only `email_address`.

-- Release 4 — verify, then schema: drop old
-- ==========================================
-- After confirming no code paths still touch `email`:
ALTER TABLE users DROP COLUMN email;
```

```typescript
// ============================================================
// Backfill worker (Node + TypeORM)
// ============================================================
async function backfillEmails(batchSize = 10_000, sleepMs = 100) {
  for (;;) {
    const result = await ds.query(`
      WITH batch AS (
        SELECT id FROM users
        WHERE email_address IS NULL AND email IS NOT NULL
        ORDER BY id LIMIT $1
        FOR UPDATE SKIP LOCKED        -- don't fight live writes
      )
      UPDATE users u SET email_address = u.email
      FROM batch WHERE u.id = batch.id
      RETURNING u.id;
    `, [batchSize]);

    if (result.length === 0) break;

    // Monitor replication lag; back off if high
    const lagMs = await checkReplicationLag();
    await new Promise(r => setTimeout(r, Math.max(sleepMs, lagMs > 1000 ? 5000 : sleepMs)));
  }
}
```

```sql
-- ============================================================
-- Adding NOT NULL safely (Postgres ≥ 12)
-- ============================================================
-- 1. Add column nullable
ALTER TABLE orders ADD COLUMN currency TEXT;

-- 2. Backfill in batches (above pattern)

-- 3. Add NOT VALID CHECK
ALTER TABLE orders ADD CONSTRAINT chk_currency_not_null CHECK (currency IS NOT NULL) NOT VALID;

-- 4. VALIDATE (scans table, doesn't lock writes)
ALTER TABLE orders VALIDATE CONSTRAINT chk_currency_not_null;

-- 5. Convert to NOT NULL using validated constraint (metadata only in PG 12+)
ALTER TABLE orders ALTER COLUMN currency SET NOT NULL;
ALTER TABLE orders DROP CONSTRAINT chk_currency_not_null;
```

## Step-by-step dry run

Scenario: rename `users.email` → `users.email_address`. 50M rows, 20 app instances.

```
─────────────────────────────────────────────────────────────
Day 0: V1 schema, V1 code (reads/writes only `email`)
─────────────────────────────────────────────────────────────
       Schema:  users(id, email, ...)
       Code:    SELECT email FROM users ...; INSERT(...email...);

─────────────────────────────────────────────────────────────
Day 1: Migration M1 → V2 schema (adds email_address)
─────────────────────────────────────────────────────────────
       Schema:  users(id, email, email_address NULL, ...)
       Code:    V1 still running. Reads/writes only `email`. OK.
       Status:  email_address is NULL for all rows.

─────────────────────────────────────────────────────────────
Day 1: Deploy V2 code (dual-write)
─────────────────────────────────────────────────────────────
       Schema:  users(id, email, email_address NULL, ...)
       Code:    Writes both columns; reads `email` only.
       Status:  New rows have both filled. Old rows still NULL email_address.

─────────────────────────────────────────────────────────────
Day 2-5: Background backfill
─────────────────────────────────────────────────────────────
       Schema:  unchanged.
       Code:    V2 dual-writes.
       Status:  10k rows / batch, 100ms sleep, ~7 hours total for 50M.
                Backed off when replication lag > 1s.

─────────────────────────────────────────────────────────────
Day 5: Verify backfill complete
─────────────────────────────────────────────────────────────
       SELECT COUNT(*) FROM users WHERE email_address IS NULL AND email IS NOT NULL;
       Expect: 0.

─────────────────────────────────────────────────────────────
Day 5: Deploy V3 code (read from email_address, dual-write)
─────────────────────────────────────────────────────────────
       Schema:  unchanged.
       Code:    Reads email_address; writes both.
       Risk:    Mixed V2/V3 fleet during rollout. Both work because both write both columns.

─────────────────────────────────────────────────────────────
Day 7: Deploy V4 code (only email_address)
─────────────────────────────────────────────────────────────
       Schema:  unchanged.
       Code:    Reads/writes only email_address.
       Risk:    Mixed V3/V4 fleet during rollout. V3 still writes both; V4 only writes email_address.
                Since V3 doesn't read email (V3 reads email_address), email going stale is fine.

─────────────────────────────────────────────────────────────
Day 14: Migration M2 → V5 schema (drop email)
─────────────────────────────────────────────────────────────
       Schema:  users(id, email_address NOT NULL, ...)
       Code:    All instances on V4 (only email_address). Safe to drop.

ALTER TABLE users DROP COLUMN email;
ALTER TABLE users ALTER COLUMN email_address SET NOT NULL;
```

7 days, no downtime, every step reversible until day 14 (drop).

## How to think aloud in the interview

> "I never do schema changes in a single migration in production. The constraint: during deploy, old and new code instances coexist, both must work against whatever schema state is live. So I follow **expand → migrate → contract**:
>
> 1. **Expand**: add the new column / table, nullable, no default. Metadata-only, instant.
> 2. **Dual-write**: deploy code that writes both old and new shapes. Reads still go to old.
> 3. **Backfill**: process existing rows in 10k chunks with sleep, monitoring replication lag.
> 4. **Switch reads**: deploy code that reads new, still writes both.
> 5. **Single write**: deploy code that only uses new. Old column goes stale (but harmless).
> 6. **Contract**: drop old column in a later release.
>
> Each step is independently reversible. Each is online.
>
> Operational discipline:
> - `SET lock_timeout = '3s'` on the migration session — fail fast rather than queue behind a slow query.
> - `CREATE INDEX CONCURRENTLY` for any index op.
> - For NOT NULL adds (Postgres < 11), use the `CHECK NOT VALID + VALIDATE + SET NOT NULL` dance to avoid table rewrite.
> - For MySQL, use `gh-ost` or `pt-online-schema-change` for anything beyond ADD COLUMN.
> - For huge tables, use `pg_repack` or table-replace strategies.
>
> Rollback: at every step before the contract, I can revert the code change and the schema is still compatible. Once dropped, rollback requires restoring from backup or re-adding the column from the dual-write data."

## Important takeaways

- Never single-PR schema changes in prod — use expand-then-contract over multiple releases.
- Each step is independently reversible; each is backwards-compatible with the prior code.
- ADD COLUMN nullable is instant; ADD NOT NULL with default rewrites in old Postgres.
- Always `SET lock_timeout = '3s'` to fail fast vs queue behind slow queries.
- `CREATE INDEX CONCURRENTLY` is non-blocking but can fail and leave INVALID indexes — check and retry.
- Backfill in 10k chunks, sleep between, watch replication lag.
- MySQL ALTERs are far worse than Postgres — use `gh-ost` / `pt-online-schema-change`.
- App schema caches may need a restart to see new columns.

## Variants

1. **Splitting a table** (a column moves to a new table). Expand: create new table, dual-write. Migrate: backfill. Switch reads. Contract: drop column.
2. **Type change** (TEXT → JSONB, INT → BIGINT). Add new column with new type; dual-write; backfill; switch.
3. **Adding a foreign key on an existing column** — `ADD CONSTRAINT ... NOT VALID` then `VALIDATE` to avoid full scan with lock.
4. **Dropping an index in production** — fast on Postgres; check for queries that depend on it first via `pg_stat_user_indexes`.
5. **Renaming a table** — `ALTER TABLE old RENAME TO new` is metadata-only but invalidates every app cache and prepared statement. Often replaced with a view named `old` over the new table during transition.
6. **Schema migrations across services** — coordinate when shared DB; prefer per-service DBs with API contracts.

## Revision notes

> **migration-without-downtime — 60 second recap**
> - Expand → dual-write → backfill → switch reads → single write → contract.
> - Each step backwards-compatible; each reversible.
> - `SET lock_timeout = '3s'` so migration fails fast vs queues behind long queries.
> - `CREATE INDEX CONCURRENTLY` (Postgres) / `gh-ost` (MySQL) for online schema change.
> - Backfill: 10k chunks, sleep, monitor replication lag.
> - NOT NULL add on old PG: `CHECK NOT VALID + VALIDATE + SET NOT NULL` to avoid rewrite.
> - Never `RENAME COLUMN` in one step in prod — break the deploy by definition.
