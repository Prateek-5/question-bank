# Backwards-compatible schema change — what's safe to add/drop and what isn't

## Source / Origin
- The "audit my migration PR" question. Strong follow-up to expand-then-contract.
- Concept refs: `backend-data-prep/orm/02-orm-comparison.md`, companions `migration-without-downtime.md`, `expand-then-contract-pattern.md`.

## Why this question matters in interviews
Every senior backend engineer is expected to **review a migration** for safety. The interview question often takes the form "your junior submits this PR — what's wrong?" The answer is a checklist: lock-blocking DDL, NOT NULL without default, FK without `NOT VALID`, dropping a column that running instances still write to. Knowing **which operations are safe**, **which require multi-step orchestration**, and **which are silently catastrophic** is the signal.

## Concepts involved

### The compatibility matrix

```
   Schema change          | Old code   | New code   | Notes
   ──────────────────────┼────────────┼────────────┼─────────────────────────
   ADD COLUMN nullable   | OK         | OK         | Pure metadata; instant.
   ADD COLUMN NOT NULL   | OK         | NEEDS data | Must backfill first.
     with default        |            |            | PG 11+: metadata-only; older: rewrite.
   ADD INDEX             | OK         | OK         | Use CONCURRENTLY.
   DROP COLUMN           | BREAKS     | OK         | Old code writing to it errors.
   RENAME COLUMN         | BREAKS     | needs new  | Both code paths broken at once.
   CHANGE COLUMN TYPE    | usually OK | depends    | Rewrites table; possible read errors.
   ADD UNIQUE            | usually OK | OK         | If existing rows violate → migration fails.
   ADD FOREIGN KEY       | OK         | OK         | NOT VALID + VALIDATE to avoid lock.
   ADD CHECK             | OK         | OK         | NOT VALID + VALIDATE.
   DROP TABLE            | BREAKS     | OK         | Coordinate; usually rare.
   RENAME TABLE          | BREAKS     | needs new  | Catastrophic if not staged.
```

### Syntax for the safe forms

```sql
-- Safe ADD COLUMN
ALTER TABLE orders ADD COLUMN ref TEXT;                          -- nullable, instant.

-- Postgres 11+: safe even with default
ALTER TABLE orders ADD COLUMN currency TEXT NOT NULL DEFAULT 'USD';
-- (catalog default; no rewrite.)

-- Postgres ≤ 10: must split
ALTER TABLE orders ADD COLUMN currency TEXT;
UPDATE orders SET currency = 'USD' WHERE currency IS NULL;       -- batched in production
ALTER TABLE orders ALTER COLUMN currency SET DEFAULT 'USD';
ALTER TABLE orders ADD CONSTRAINT chk CHECK (currency IS NOT NULL) NOT VALID;
ALTER TABLE orders VALIDATE CONSTRAINT chk;
ALTER TABLE orders ALTER COLUMN currency SET NOT NULL;
ALTER TABLE orders DROP CONSTRAINT chk;

-- Safe INDEX
CREATE INDEX CONCURRENTLY idx_orders_user_id ON orders(user_id);
-- Slower but doesn't block writes; check `pg_index.indisvalid` afterward.

-- Safe FOREIGN KEY
ALTER TABLE orders ADD CONSTRAINT fk_user FOREIGN KEY (user_id)
  REFERENCES users(id) NOT VALID;
ALTER TABLE orders VALIDATE CONSTRAINT fk_user;
-- The NOT VALID skips the table scan; VALIDATE does it without ACCESS EXCLUSIVE.

-- Safe DROP COLUMN
-- (preceded by code that no longer writes it; see expand-then-contract)
ALTER TABLE orders DROP COLUMN address;
```

### Edge cases / interview traps

1. **Adding NOT NULL on a populated table in old Postgres** = full table rewrite under lock. Use the `CHECK NOT VALID + VALIDATE + SET NOT NULL` dance.
2. **Renaming a column** is silently catastrophic — running instances reading the old name error immediately.
3. **CREATE INDEX (without CONCURRENTLY)** holds a SHARE lock; blocks writes for the build duration.
4. **CREATE INDEX CONCURRENTLY** can fail mid-build and leave an INVALID index. Always check `pg_index.indisvalid` and recreate.
5. **`SERIAL` → `IDENTITY` migration** — same column, different metadata; conversion path is non-trivial.
6. **JSONB → TEXT or vice versa** — type changes often rewrite; storage format differs.
7. **Lengthening VARCHAR(20) to VARCHAR(50)** — instant on Postgres; rewriting on some MySQL versions.
8. **Adding a UNIQUE constraint on a populated table** — DB does a full scan first; can fail if duplicates exist. Use `CREATE UNIQUE INDEX CONCURRENTLY`, then attach.
9. **Foreign key cascade adds locks across tables** — `ON DELETE CASCADE` reaches into the referenced table at delete time; can block.
10. **Dropping a constraint** is metadata-only and fast, but the constraint was protecting your data — drop deliberately.

## Mental Model

The deploy-compatibility matrix from `expand-then-contract-pattern.md`, simplified for "review this PR" mode:

```
   ┌──────────────────────────────────────────────────────────┐
   │                  Is this change SAFE?                    │
   ├──────────────────────────────────────────────────────────┤
   │                                                          │
   │   ADDITIVE? (new column nullable, new index, new table)  │
   │     └─► YES.  Old code ignores; new code uses.           │
   │                                                          │
   │   REMOVAL? (drop column, drop table)                     │
   │     └─► UNSAFE single-step.                              │
   │           Must coordinate: deploy code that stops using  │
   │           it first; bake; then drop.                     │
   │                                                          │
   │   RENAME? (column, table)                                │
   │     └─► UNSAFE single-step.                              │
   │           Use expand-then-contract: add new + dual write │
   │           + backfill + switch + drop.                    │
   │                                                          │
   │   TYPE CHANGE?                                           │
   │     └─► DEPENDS.                                         │
   │           Lengthen VARCHAR: usually safe (instant).      │
   │           INT → BIGINT: rewrite; treat as rename.        │
   │                                                          │
   │   CONSTRAINT? (NOT NULL, FK, CHECK, UNIQUE)              │
   │     └─► SAFE WITH NOT VALID + VALIDATE.                  │
   │           Avoids the full-table-scan lock.               │
   │                                                          │
   └──────────────────────────────────────────────────────────┘
```

## Why interviewers care

- Tests **schema-review judgement**, not just "can you write DDL."
- Tests **knowledge of Postgres / MySQL DDL semantics** at a specific level.
- Catches the candidate who proposes "just add NOT NULL" on a billion-row table.

## Common beginner confusion

- **"ADD COLUMN is always safe."** Mostly true in Postgres 11+; in older PG or MySQL, adding NOT NULL with default rewrites the table.
- **"DROP is fast."** Metadata-only and fast at the DB layer; but running app instances may still write to the column → errors.
- **"Renaming is just a metadata change."** True for the DB; catastrophic for running code that doesn't know the new name.
- **"FK constraints are instantaneous."** Wrong without `NOT VALID`; adding a FK on a populated table does a full scan with `ACCESS EXCLUSIVE` lock by default.
- **"`CONCURRENTLY` makes everything safe."** Only applies to index ops; ALTER COLUMN still locks.
- **"`SET DEFAULT` rewrites the column."** No — sets the catalog default. Existing rows unaffected.
- **"My ORM generates safe migrations."** Auto-generated migrations are starting points; they don't know about uptime or lock impact.

## Brute force approach

Schedule a maintenance window for any non-trivial change. Reasonable for internal tools; unacceptable for SaaS or consumer products.

## Optimal approach

PR-review checklist:

1. **Does this drop or rename anything?** → must be a separate release after dual-write + bake.
2. **Does this add NOT NULL?** → backfill first; use CHECK NOT VALID + VALIDATE.
3. **Does this add an FK or CHECK?** → NOT VALID + VALIDATE.
4. **Does this CREATE INDEX?** → must use CONCURRENTLY (Postgres) or online ALGORITHM (MySQL).
5. **Does this ALTER COLUMN TYPE?** → likely a rewrite; treat as rename.
6. **Does this run on a hot table?** → wrap in `SET lock_timeout = '3s'` to fail fast.
7. **Is there a backfill?** → must be batched, idempotent, replication-lag-aware.

If any answer is "yes, single-step," send it back for orchestration.

## Solution

```sql
-- ============================================================
-- AUDIT: this PR adds a NOT NULL `currency` column to `orders` (1B rows)
-- ============================================================

-- The submitted migration (UNSAFE):
ALTER TABLE orders ADD COLUMN currency TEXT NOT NULL DEFAULT 'USD';
-- Postgres ≤ 10: rewrites 1B rows under ACCESS EXCLUSIVE.
-- Postgres 11+: catalog-default, instant. But still: NOT NULL with default
-- means existing reads might see the constant 'USD' even though we don't know
-- if that's correct for every legacy row.

-- ============================================================
-- SAFE REWRITE — multi-migration, multi-deploy
-- ============================================================

-- M1 (schema): nullable column, optionally with default for FUTURE rows
ALTER TABLE orders ADD COLUMN currency TEXT;

-- D1 (deploy code v2): dual-write currency on every new INSERT/UPDATE.

-- M2 (background): backfill in batches
DO $$
DECLARE rows_updated INT;
BEGIN
  LOOP
    WITH batch AS (
      SELECT id FROM orders
      WHERE currency IS NULL
      ORDER BY id LIMIT 10000
      FOR UPDATE SKIP LOCKED
    )
    UPDATE orders o SET currency = 'USD'   -- derive correct value per row in real cases
      FROM batch WHERE o.id = batch.id;
    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    EXIT WHEN rows_updated = 0;
    PERFORM pg_sleep(0.1);
  END LOOP;
END $$;

-- M3 (schema): enforce NOT NULL safely
ALTER TABLE orders ADD CONSTRAINT chk_currency_not_null CHECK (currency IS NOT NULL) NOT VALID;
ALTER TABLE orders VALIDATE CONSTRAINT chk_currency_not_null;  -- scans, no exclusive lock
ALTER TABLE orders ALTER COLUMN currency SET NOT NULL;          -- now metadata only
ALTER TABLE orders DROP CONSTRAINT chk_currency_not_null;

-- ============================================================
-- AUDIT: this PR drops `address`. Code still writes to it.
-- ============================================================

-- The submitted migration (UNSAFE):
ALTER TABLE orders DROP COLUMN address;
-- Any running instance that INSERTs/UPDATEs `address` immediately errors.

-- The SAFE path requires expand-then-contract first (see other file).

-- ============================================================
-- AUDIT: this PR adds a FK orders.user_id -> users.id
-- ============================================================

-- UNSAFE:
ALTER TABLE orders ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id);
-- ACCESS EXCLUSIVE lock on `orders` for the duration of the scan.

-- SAFE:
ALTER TABLE orders ADD CONSTRAINT fk_user FOREIGN KEY (user_id)
  REFERENCES users(id) NOT VALID;          -- no scan; just blocks future invalids
ALTER TABLE orders VALIDATE CONSTRAINT fk_user;  -- scans w/ SHARE UPDATE EXCLUSIVE
-- Background scan runs without blocking concurrent DML.
```

```typescript
// ============================================================
// TypeORM migration that's been hand-reviewed for safety
// ============================================================
import type { MigrationInterface, QueryRunner } from 'typeorm';

export class AddCurrencyToOrders1700000000 implements MigrationInterface {
  async up(q: QueryRunner): Promise<void> {
    await q.query(`SET lock_timeout = '3s'`);
    await q.query(`ALTER TABLE orders ADD COLUMN currency TEXT`);
    // backfill + NOT NULL come in separate migrations
  }
  async down(q: QueryRunner): Promise<void> {
    await q.query(`ALTER TABLE orders DROP COLUMN currency`);
  }
}
```

## Step-by-step dry run

PR review: "Add NOT NULL `currency` column to orders."

```
Reviewer thinks:
  1. Is `orders` populated? Yes (1B rows).
  2. NOT NULL with default in Postgres 11+: instant; OK.
  3. NOT NULL with default in Postgres ≤ 10: full rewrite → blocks for ~hours.
  4. NOT NULL without default: violates 1B rows → migration fails.
  5. What's the Postgres version on prod? PG 12. → safe with default.
  6. Is 'USD' the right default semantically? Need product confirmation.

Decision tree:
  - If PG 11+ AND default makes sense semantically:
        → safe to ship as single migration.
  - Else:
        → split into 4 migrations + 1 deploy:
            M1: ADD COLUMN nullable
            D1: dual-write code
            M2: backfill (background)
            M3: NOT VALID CHECK + VALIDATE + SET NOT NULL

Outcome: ask "what's the prod PG version" and "is 'USD' the right default?"
```

PR review: "Drop `address` column."

```
Reviewer thinks:
  1. Are any running code paths writing to `address`?
       grep across services → yes, `OrderService.createOrder` writes it.
  2. Are any reading it?
       Yes, `OrderApi.fullAddress` returns it.
  3. Has there been an expand-then-contract for this column?
       No — this is the first migration touching it.

Decision: REJECT. Send back with:
  "This requires expand-then-contract:
   1. New columns address_line1/2 + dual-write code already shipped.
   2. Backfill complete.
   3. Switch reads to new fields.
   4. Stop writing `address`.
   5. Bake 24h.
   6. THEN this drop is safe."
```

PR review: "Add FK orders.user_id → users(id)."

```
Reviewer thinks:
  1. Is `orders` large? Yes.
  2. Submitted as single `ALTER TABLE ADD CONSTRAINT FOREIGN KEY` — full scan + ACCESS EXCLUSIVE.
  3. Safer form: NOT VALID + VALIDATE.

Outcome: rewrite to:
  ALTER TABLE orders ADD CONSTRAINT fk_user FK (user_id) REFERENCES users(id) NOT VALID;
  ALTER TABLE orders VALIDATE CONSTRAINT fk_user;
```

## How to think aloud in the interview

> "When reviewing a migration PR, my mental checklist is:
>
> 1. **Is it purely additive?** (New nullable column, new index, new table.) Safe — old code ignores, new code uses.
> 2. **Does it remove or rename anything?** Then it must be the *last step* of an expand-then-contract dance; bake required before this PR.
> 3. **Does it add a constraint (NOT NULL, FK, CHECK, UNIQUE)?** Use `NOT VALID + VALIDATE` to avoid the full-table-scan lock. For NOT NULL on large tables, the `CHECK NOT VALID + VALIDATE + SET NOT NULL` pattern in three steps.
> 4. **Does it `CREATE INDEX`?** Must be `CONCURRENTLY` (Postgres) or online (MySQL).
> 5. **Does it `ALTER COLUMN TYPE`?** Treat as a rewrite unless it's a simple lengthening. Probably needs expand-then-contract.
> 6. **Is it on a hot table?** `SET lock_timeout = '3s'` so it fails fast instead of queueing behind a long query.
>
> Postgres version matters: PG 11+ made ADD COLUMN with default instant; older versions rewrite. MySQL is uniformly painful — reach for `gh-ost`.
>
> The discipline I demand from juniors: **no single PR can both add a column *and* drop the old one**. That's six PRs across multiple deploys."

## Important takeaways

- Additive changes are safe by default; removals and renames require multi-step orchestration.
- NOT NULL adds on large tables need the CHECK NOT VALID + VALIDATE + SET NOT NULL pattern.
- FK and CHECK constraints use NOT VALID + VALIDATE to avoid the full-scan lock.
- `CREATE INDEX CONCURRENTLY` for any production index op.
- Type changes are usually rewrites; treat as expand-then-contract.
- Set `lock_timeout` short so DDL fails fast instead of queueing.
- Renaming a column in one step in production = guaranteed outage during deploy.

## Variants

1. **MySQL-specific online ALTER**: `ALGORITHM=INPLACE` and `LOCK=NONE` — works for some ALTERs.
2. **`pt-online-schema-change` / `gh-ost`**: creates a shadow table, copies data via triggers, swaps. Online for ANY ALTER.
3. **`pg_repack`**: rewrites a table online without long locks.
4. **Logical replication** for type changes: replicate to a new schema, switch over.
5. **Schema-version handshake** at app startup: refuse to start if app schema-version expectations don't match.
6. **Backfill via async stream** (Postgres `COPY` to a worker, transform, write back) — for huge datasets.
7. **Zero-downtime FK addition on a child table that grows fast** — partition first, then add FK per partition.

## Revision notes

> **backwards-compatible-schema-change — 60 second recap**
> - Additive (new column nullable, new index, new table) → safe single PR.
> - Removal / rename → must be expand-then-contract across many deploys.
> - NOT NULL on populated table → CHECK NOT VALID + VALIDATE + SET NOT NULL.
> - FK / CHECK → ADD ... NOT VALID, then VALIDATE.
> - `CREATE INDEX CONCURRENTLY` (PG) or `ALGORITHM=INPLACE` (MySQL).
> - Type change → usually a rewrite; treat as rename.
> - `SET lock_timeout = '3s'` so migration fails fast.
> - MySQL DDL is much worse than Postgres — reach for `gh-ost`.
