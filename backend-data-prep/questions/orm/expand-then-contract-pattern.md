# The expand-then-contract pattern — multi-deploy migration drill-down

## Source / Origin
- The deep dive on the migration-without-downtime question.
- Concept refs: `backend-data-prep/orm/02-orm-comparison.md`, companion `migration-without-downtime.md`, `backwards-compatible-schema-change.md`.

## Why this question matters in interviews
"Walk me through renaming a column with zero downtime" is the canonical follow-up. The interviewer wants the **deploy choreography**, not just the SQL. Senior candidates name the **five (sometimes six) discrete steps**, articulate **what each step protects against**, and identify the **rollback points**. The pattern generalizes to splitting tables, changing types, adding NOT NULL — anything that can't be done atomically across a live fleet.

## Concepts involved

### The pattern, distilled

```
   EXPAND ─────────────────► MIGRATE ─────────────────► CONTRACT
   (schema grows)            (data + code shift)         (schema shrinks)

   Schema can hold           Code dual-writes;           Once all code is on
   both old and new          backfill; switch reads      new, drop old.
   shapes simultaneously.
```

### The five-step canonical sequence

```
Step 1: SCHEMA EXPAND       — add new column/table; nullable; instant.
Step 2: CODE DUAL-WRITE     — deploy app that writes both shapes; reads old.
Step 3: BACKFILL            — copy existing rows; batched; idle-aware.
Step 4: CODE READ-SWITCH    — deploy app that reads new; still writes both.
Step 5: CODE WRITE-NEW-ONLY — deploy app that only uses new shape.
Step 6: SCHEMA CONTRACT     — drop old column/table after bake period.
```

### Why each step exists

| Step | Why it's separate from the next |
|---|---|
| 1: expand | Schema must accept new shape **before** any code writes it. |
| 2: dual-write | New shape must be populated **for new rows** while old shape still serves reads. |
| 3: backfill | Old rows need the new shape populated **before** anyone reads from it. |
| 4: read-switch | Reads must switch **after** all rows have the new shape; writes stay dual so rollback is safe. |
| 5: write-new-only | Once stable, stop dual-writing — but only after we're confident no one reads old. |
| 6: contract | Old column must be unused by **every** instance before drop. |

### Edge cases / interview traps

1. **Skipping step 5** (going straight to contract while dual-writing) — risks instances still reading from old via stale cache; drop breaks them.
2. **Combining steps in one deploy** — defeats the entire purpose. Each step relies on the previous being live in 100% of instances.
3. **No bake time between steps** — async eventual consistency, schema caches, request-in-flight all need minutes-to-hours to settle.
4. **Rollback during step 3** — backfill is idempotent; you can stop and resume. Restoring after step 6 is much harder.
5. **Backfill that races with live writes** — use `SKIP LOCKED` or `WHERE new IS NULL` to avoid clobbering app-written rows.
6. **App schema cache stickiness** — adding a column to a Rails / Django / Sequelize model often requires app restart to pick up.
7. **DB replication lag during backfill** — heavy UPDATE creates WAL flood; replicas lag; reads serve stale.
8. **Index on the new column** — create it during step 1 (or before backfill) so the backfill doesn't seq-scan repeatedly.
9. **CHECK constraints / NOT NULL** — add as `NOT VALID` first; `VALIDATE` separately to avoid table-scan with lock.
10. **FK constraints on new columns** — same `NOT VALID` + `VALIDATE` pattern.

## Mental Model

The deploy-time invariant: **at every instant, every running instance + the current schema must form a valid system.**

```
                  Schema V1            Schema V2 (expand)         Schema V3 (contract)
                  ─────────            ──────────────────         ────────────────────
                                              ▼                            ▼
   Code V1   ◄────  works              still works (V1 ignores new col)    BREAKS
                                                                           (old col gone)
   Code V2 (dual)   N/A                works                               BREAKS
                                                                           (writes to old col)
   Code V3 (read-switch)  N/A          works                               works (reads new)
   Code V4 (write-new-only)  N/A       works                               works
                                                                           ↑
                                                                   safe to contract here
```

Every pair (code-version × schema-version) along the **deploy path** must be a valid cell in this matrix.

```
   ┌──────────┬─────────────┬─────────────┬─────────────┐
   │          │ Schema V1   │ Schema V2   │ Schema V3   │
   ├──────────┼─────────────┼─────────────┼─────────────┤
   │ Code V1  │     OK      │     OK      │   BROKEN    │
   │ Code V2  │   BROKEN    │     OK      │   BROKEN    │  ← writes to dropped col
   │ Code V3  │   BROKEN    │     OK      │     OK      │
   │ Code V4  │   BROKEN    │     OK      │     OK      │
   └──────────┴─────────────┴─────────────┴─────────────┘

   Path: (V1,V1) → (V1,V2) → (V2,V2) → (V3,V2) → (V4,V2) → (V4,V3)
                   ↑          ↑          ↑           ↑          ↑
                   expand    dual-write read-switch write-new contract
```

Every transition is "all-green to all-green."

## Why interviewers care

- Tests **distributed deploy thinking** — there's no atomic deploy in a load-balanced fleet.
- Tests **rollback awareness** — every step must be revertible.
- Tests **schema-compatibility reasoning** — the code-schema compatibility matrix above is what senior engineers carry in their heads.
- Identifies people who've **felt the pain** of a single-step migration breaking 10% of instances.

## Common beginner confusion

- **"Just do the migration during a deploy window."** Atomic across a fleet doesn't exist; the deploy itself takes 10+ minutes during which both versions run.
- **"Bake time is wasted time."** Bake time catches edge cases: cron jobs running on old code, slow queries holding old plans, replicas serving old reads.
- **"Step 5 is unnecessary; we can drop the old column while dual-writing."** Risky: pre-existing connections / prepared statements may still reference the old column.
- **"Backfill in one big UPDATE."** Locks the table, WAL flood, replica lag. Chunk it.
- **"I'll skip the dual-write step and just backfill once."** Live writes go to old column only; new column drifts from old; rollback isn't safe.
- **"This is over-engineered."** It's the **minimum** for zero-downtime. Skip a step → outage.

## Brute force approach

Take a maintenance window, run the rename, restart everything. Works for B2B with announced downtime; unacceptable for consumer SaaS.

## Optimal approach

The full six-step pattern, with these guardrails:
1. **Bake** each step before moving on (hours for code deploys; days if cron jobs / async paths exist).
2. **Monitor** during each step: error rates, replication lag, query plans.
3. **Reversible at every step before contract** — keep both shapes live until drop.
4. **Automate the backfill** as a resumable job, not a one-off script.
5. **Schema-cache invalidation** strategy — restart workers or use `LISTEN`/`NOTIFY` patterns if available.

## Solution

```sql
-- ============================================================
-- Example: split orders.address (TEXT) into orders.address_line1, address_line2
-- ============================================================

-- ─── STEP 1: EXPAND ─────────────────────────────────────────
-- Migration M1
SET lock_timeout = '3s';
ALTER TABLE orders ADD COLUMN address_line1 TEXT;
ALTER TABLE orders ADD COLUMN address_line2 TEXT;
-- Optional: index for backfill / lookups
CREATE INDEX CONCURRENTLY idx_orders_address_line1 ON orders(address_line1);

-- ─── STEP 2: DUAL-WRITE ─────────────────────────────────────
-- Deploy app V2. New INSERT/UPDATE writes:
--   address          (legacy)
--   address_line1    (new)
--   address_line2    (new)
-- Reads still go to address.

-- ─── STEP 3: BACKFILL ───────────────────────────────────────
-- A worker, batched, idempotent.
DO $$
DECLARE
  rows_updated INT;
BEGIN
  LOOP
    WITH batch AS (
      SELECT id, address FROM orders
      WHERE  address_line1 IS NULL AND address IS NOT NULL
      ORDER BY id LIMIT 10000
      FOR UPDATE SKIP LOCKED
    )
    UPDATE orders o
       SET address_line1 = split_part(b.address, E'\n', 1),
           address_line2 = NULLIF(split_part(b.address, E'\n', 2), '')
      FROM batch b WHERE o.id = b.id;

    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    EXIT WHEN rows_updated = 0;
    PERFORM pg_sleep(0.1);
  END LOOP;
END $$;

-- ─── STEP 4: READ-SWITCH ────────────────────────────────────
-- Deploy app V3. Reads use address_line1/2. Writes still dual.
-- Verify in canary first.

-- ─── STEP 5: WRITE-NEW-ONLY ─────────────────────────────────
-- Deploy app V4. Stop writing to `address`. Only address_line1/2.

-- ─── STEP 6: CONTRACT ───────────────────────────────────────
-- After bake (hours/days):
ALTER TABLE orders DROP COLUMN address;
```

```typescript
// ============================================================
// Code at step 2 (dual-write)
// ============================================================
async function createOrder(input: CreateOrderInput) {
  return repo.save(repo.create({
    ...input,
    address:        input.fullAddress,                          // legacy
    addressLine1:   input.line1,
    addressLine2:   input.line2 ?? null,
  }));
}

// ============================================================
// Code at step 4 (reads switch; still dual-writes)
// ============================================================
async function getOrder(id: number) {
  const o = await repo.findOneByOrFail({ id });
  return {
    line1: o.addressLine1,    // NEW source of truth for reads
    line2: o.addressLine2,
    // legacy `address` is still maintained but not exposed via API
  };
}

// ============================================================
// Code at step 5 (write-new-only)
// ============================================================
async function createOrder(input: CreateOrderInput) {
  return repo.save(repo.create({
    addressLine1: input.line1,
    addressLine2: input.line2 ?? null,
    // no more `address`
  }));
}
```

## Step-by-step dry run

Imagine a 20-instance fleet, rolling deploy of ~30 minutes per code release.

```
T0  Schema V1: orders(id, address)
    Code V1 (20/20 instances): reads/writes address.

T1  Run M1: ADD COLUMN address_line1, address_line2.
    Schema V2.
    Code V1 still 20/20 — fine, ignores new cols.

T2  Begin deploy of Code V2 (dual-write).
    Mid-deploy: 10 instances on V1, 10 on V2.
    V1 writes: address only. New rows have NULL in new cols.
    V2 writes: address + new cols. New rows have all three.
    Reads (by both): address only. All good.

T3  Code V2 fully deployed (20/20). 30 minutes after T2.

T4  Start backfill worker. Processes ~10M rows / hour.

T5  Backfill completes. Verify:
    SELECT COUNT(*) FROM orders WHERE address_line1 IS NULL AND address IS NOT NULL;
    → 0.

T6  Begin deploy of Code V3 (read from new, still dual-write).
    Mid-deploy: 10 instances on V2, 10 on V3.
    V2 reads: address. V3 reads: address_line1/2.
    Since backfill is complete, both see the same data. OK.

T7  Code V3 fully deployed.

T8  Bake for 24 hours. Watch error rates, slow query log.

T9  Begin deploy of Code V4 (write-new-only).
    Mid-deploy: 10 instances on V3, 10 on V4.
    V3 writes: both. V4 writes: new only.
    Old `address` column goes stale on V4 writes, fresh on V3 writes.
    Since no one reads `address` anymore, the staleness is invisible.

T10 Code V4 fully deployed.

T11 Bake 24 hours more. Run audit:
    -- Are any code paths still touching `address`?
    SELECT query, calls FROM pg_stat_statements
    WHERE query LIKE '%orders.address %';
    → 0 (or only the backfill query).

T12 Run M2: ALTER TABLE orders DROP COLUMN address.
    Schema V3.
    Code V4 unaffected (never read or wrote `address`).

T13 Done.
```

**Rollback options:**
- At T1–T5: revert code, drop the new columns. Cheap.
- At T6–T8: revert Code V3 to V2; new columns still backfilled. Cheap.
- At T9–T11: revert Code V4 to V3. New column reads still work; old `address` is stale but harmless if no reads.
- After T12: cannot easily rollback without restoring backup.

## How to think aloud in the interview

> "Expand-then-contract is the formalization of zero-downtime schema change. Five-or-six discrete deploys with bake time between each. The reasoning:
>
> - **Expand** the schema so it can hold both shapes.
> - **Dual-write** so new rows populate both shapes.
> - **Backfill** existing rows in batches.
> - **Switch reads** to the new shape (still dual-writing as safety net).
> - **Stop writing to the old shape**.
> - **Contract** by dropping the old shape.
>
> Each step is reversible. Each step is online. The constraint is that during deploy, both code versions run simultaneously, and both must work against the current schema.
>
> Practical guardrails:
> - Bake time of hours to a day between code releases — captures async paths, cron jobs, prepared-statement caches.
> - Monitor each step: replication lag, error rates, query plans.
> - Backfill is a resumable job, not a one-off script. Use `WHERE new IS NULL AND old IS NOT NULL` so it's idempotent.
> - Index the new column before backfill so the backfill isn't a seq-scan.
> - Use `NOT VALID` + `VALIDATE` for adding constraints/FKs without a long table-scan lock.
>
> What I check before contracting:
> - `pg_stat_statements` for any query mentioning the old column.
> - All deployed app versions confirmed off the old column.
> - 24+ hours of bake with no surprises."

## Important takeaways

- Expand → dual-write → backfill → read-switch → write-new-only → contract.
- Every step is independently reversible (until contract).
- Every step is backwards-compatible with the previous code version.
- Bake between steps — async, cron, schema caches all need time to settle.
- Backfill is batched, idempotent (`WHERE new IS NULL`), and replication-lag-aware.
- Don't compress steps; the whole point is "always-green at every point."
- Before contracting, verify via `pg_stat_statements` that no query touches the old column.

## Variants

1. **Splitting a table** (column moves out). Same pattern: expand new table → dual-write → backfill → switch reads → write-new-only → drop column.
2. **Type change** (TEXT → JSONB). Add new column, dual-write, backfill, switch.
3. **Merging two columns** into one. Add merged column, dual-write with concat, backfill, switch reads, stop writing to two, drop.
4. **Adding a NOT NULL column.** Same first three steps; "switch reads" replaced by "add NOT NULL CHECK NOT VALID + VALIDATE + SET NOT NULL".
5. **Renaming a table.** Trickier; usually combined with a view named for the old table that aliases the new, then drop the view in the contract step.
6. **Multi-region / multi-DB** — replicate the pattern across regions; staggered rollout.
7. **API version migration** — the same pattern at a higher abstraction layer.

## Revision notes

> **expand-then-contract-pattern — 60 second recap**
> - 6 steps: expand schema → dual-write code → backfill → read-switch code → write-new-only code → contract schema.
> - Every step backwards-compatible; every step reversible (except contract).
> - Bake hours/days between code releases.
> - Backfill: batched, idempotent (`WHERE new IS NULL`), replication-lag-aware.
> - Verify before contract via `pg_stat_statements` — no queries on old column.
> - Skipping a step or combining = outage; this is the minimum.
> - The constraint: at every instant, every running instance × current schema must form a valid system.
