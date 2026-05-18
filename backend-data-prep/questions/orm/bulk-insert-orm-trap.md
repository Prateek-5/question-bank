# Bulk insert through an ORM — the N-INSERT trap

## Source / Origin
- The "we have to import a million rows; how fast?" question.
- Concept refs: `backend-data-prep/orm/01-orm-internals.md` (hydration cost section).

## Why this question matters in interviews
Naive ORM use turns "insert 10,000 rows" into 10,000 round trips. The interview tests whether you know the **bulk API** (`bulkCreate`, `createMany`, `executeMany`, `COPY`), the **trade-offs** between full-hydration `save()` and raw bulk, and **when to drop to the DB driver** (Postgres `COPY`). Senior candidates also handle the **edge cases**: hook execution, default columns, conflict handling, batch size, transaction scope.

## Concepts involved

### The trap

```javascript
// SLOW — 10,000 round trips
for (const o of orders) {
  await orderRepo.save(o);          // each save = 1 INSERT
}
// 10,000 × 1ms RTT = 10 seconds wall clock; ORM hydration overhead per row.

// SLIGHTLY BETTER — 1 trip per save (still bad)
await orderRepo.save(orders);       // TypeORM iterates internally → N inserts

// FAST — single multi-row INSERT
await orderRepo
  .createQueryBuilder()
  .insert()
  .into(Order)
  .values(orders)                   // becomes INSERT ... VALUES (...),(...),(...)
  .execute();
```

### The actual SQL emitted

```sql
-- Slow path: N statements
INSERT INTO orders (user_id, total, status) VALUES ($1, $2, $3);  -- ×10,000

-- Fast path: 1 multi-row INSERT
INSERT INTO orders (user_id, total, status) VALUES
  ($1,$2,$3), ($4,$5,$6), ($7,$8,$9), ..., ($n-2,$n-1,$n);

-- Faster: COPY (Postgres)
COPY orders (user_id, total, status) FROM STDIN WITH (FORMAT csv);
-- Then stream the CSV bytes. ~10-100x faster than even multi-row INSERT.
```

### Bulk APIs across ORMs

```typescript
// TypeORM
await orderRepo.insert(orders);          // bulk INSERT (but no entity tracking / hooks)
await orderRepo
  .createQueryBuilder()
  .insert()
  .into(Order)
  .values(orders)
  .orIgnore()                            // ON CONFLICT DO NOTHING
  .execute();

// Prisma
await prisma.order.createMany({
  data: orders,
  skipDuplicates: true,                  // ON CONFLICT DO NOTHING
});

// Sequelize
await Order.bulkCreate(orders, {
  ignoreDuplicates: true,
  updateOnDuplicate: ['total', 'status'], // upsert
  validate: false,                        // skip per-row validation for speed
});

// SQLAlchemy
session.execute(insert(Order), orders)   # 2.x core insert with many

// JPA / Hibernate
@Bean
public JdbcTemplate jdbcTemplate(...) { ... }
jdbcTemplate.batchUpdate("INSERT INTO orders (...) VALUES (...)", orders);
// Or use hibernate.jdbc.batch_size = 50 to batch JPA inserts.

// Postgres COPY via pg / pg-copy-streams (Node)
import { from as copyFrom } from 'pg-copy-streams';
const stream = client.query(copyFrom('COPY orders (user_id, total, status) FROM STDIN CSV'));
for (const o of orders) stream.write(`${o.userId},${o.total},${o.status}\n`);
stream.end();
```

### Edge cases / interview traps

1. **Parameter limit.** Postgres caps at 65,535 placeholders per statement. 10,000 rows × 5 cols = 50,000 — OK. 20,000 rows × 5 cols = 100,000 — fails. Chunk in batches of (limit / col_count).
2. **Default columns aren't filled.** ORM `bulkCreate`/`insert` often skips default-column derivation (timestamps, UUIDs). Either provide values explicitly or use `RETURNING` to read back.
3. **Hooks don't fire.** `@BeforeInsert`, audit triggers, validations — bypassed by bulk APIs in most ORMs. Be intentional.
4. **No identity map population.** Bulk insert returns IDs but doesn't hydrate entities into the session. Subsequent finds will re-fetch.
5. **`ON CONFLICT DO UPDATE` (upsert).** Common pattern; each ORM exposes it differently. TypeORM's `orUpdate`, Prisma's `upsert` (per-row, not bulk), Sequelize `updateOnDuplicate`.
6. **Transaction scope.** A million-row insert in one transaction = long-running TX = replication lag, lock-wait, vacuum starvation. Split into chunks per TX.
7. **Triggers and FKs.** Per-row triggers fire for every row in a multi-row INSERT; can dominate cost. Disable temporarily for huge imports (`ALTER TABLE ... DISABLE TRIGGER`).
8. **WAL / redo log explosion.** Massive imports generate huge WAL; replicas lag, backups balloon. Throttle.
9. **COPY's quirks.** No `ON CONFLICT` clause; load into a temp table then `INSERT ... SELECT ... ON CONFLICT` to handle dupes.
10. **JSON columns** — Prisma serializes; Sequelize is fine; raw bulk insert needs explicit JSON casting.

## Mental Model

```
   Round trips                Time per insert       Total for 10k rows
   ──────────                 ──────────────        ──────────────────

   N (loop save)              ~1ms                  ~10 s
   Multi-row INSERT (single)  ~30 ms total          ~30 ms
   COPY (streaming)           ~10 ms total          ~10 ms

   Hydration                  ~50 μs per row        ~0.5 s
   Hook + validation          ~100 μs per row       ~1 s

   So: full-fat save() of 10k rows ~12 s.
       Bulk INSERT      ~30 ms wire + 0.5 s hydration if entities returned = ~0.5 s.
       Bulk INSERT (no hydration) ~30 ms.
       COPY              ~10 ms.

   COPY wins for 100k+ rows; multi-row INSERT wins for ~100-10k; ORM save() wins for ≤10 rows.
```

## Why interviewers care

- Tests **awareness of ORM overhead** vs the wire cost.
- Tests **knowledge of bulk APIs** in specific ORMs.
- Tests **production sizing**: 1M-row import strategy, batch size choice, COPY vs INSERT.
- Catches the "I'll just use save() in a loop" answer.

## Common beginner confusion

- **"`Promise.all` on N saves will be fast."** Concurrent round trips, but the connection pool is small (10-20); you serialize on the pool. Total time unchanged.
- **"`bulkCreate` is just a loop over `create`."** No — most ORMs emit a multi-row INSERT.
- **"Hooks always fire."** Bulk APIs commonly skip hooks for speed. Read the docs.
- **"COPY is just for CSV import."** It's a streaming protocol; you can drive it programmatically from any language.
- **"Default values fill themselves."** Some ORMs skip default population in bulk; explicitly pass or use DB defaults.
- **"I can dump 10M rows in one INSERT."** Parameter limits, WAL bloat, transaction duration — chunk.
- **"COPY into the live table is fine."** Triggers and FKs still fire; for huge imports, use a staging table and atomic swap.

## Brute force approach

`for (const x of items) await repo.save(x)`. Works for tiny inputs; catastrophic for anything > 100 rows.

## Optimal approach

1. **≤10 rows**: ORM `save()` — keeps hooks, identity map, returned entities.
2. **10–10,000 rows**: ORM bulk insert (`bulkCreate`, `createMany`, `insert([])`). Single multi-row INSERT.
3. **10k–1M rows**: chunked multi-row INSERT (1000–10000 per chunk) inside per-chunk transactions; with `ON CONFLICT DO NOTHING` if dedupe needed.
4. **1M+ rows**: `COPY` from a stream into a staging table; `INSERT ... SELECT` from staging to live with conflict handling.
5. **Sizing**: chunk size = `(param_limit / cols_per_row)`; for Postgres ~10,000 / 10 cols = 1000 rows per chunk.
6. **Transaction**: one TX per chunk, not one TX for the whole import.
7. **Triggers / FKs**: for huge static imports, disable triggers and use deferred FKs.
8. **Monitor**: replication lag during the import; throttle.

## Solution

```typescript
// ============================================================
// Chunked bulk insert with ON CONFLICT (Prisma)
// ============================================================
async function bulkImport(orders: OrderInput[]) {
  const CHUNK = 1000;
  for (let i = 0; i < orders.length; i += CHUNK) {
    const slice = orders.slice(i, i + CHUNK);
    await prisma.order.createMany({
      data: slice,
      skipDuplicates: true,
    });
    await sleepUntilReplicationLagOk();
  }
}

// ============================================================
// TypeORM — multi-row INSERT, chunked, with hooks bypassed
// ============================================================
async function bulkImport(rows: OrderInput[]) {
  const CHUNK = 1000;
  for (let i = 0; i < rows.length; i += CHUNK) {
    await ds.transaction(async (mgr) => {
      await mgr.createQueryBuilder()
        .insert()
        .into(Order)
        .values(rows.slice(i, i + CHUNK))
        .orIgnore()                                  // ON CONFLICT DO NOTHING
        .execute();
    });
  }
}

// ============================================================
// Postgres COPY for huge imports (Node + pg-copy-streams)
// ============================================================
import { Pool } from 'pg';
import { from as copyFrom } from 'pg-copy-streams';
import { Readable, pipeline } from 'stream';
import { promisify } from 'util';
const pipe = promisify(pipeline);

async function copyOrders(orderStream: Readable) {
  const client = await pool.connect();
  try {
    // Stage table avoids ON CONFLICT issue with COPY
    await client.query(`CREATE TEMP TABLE orders_stage (LIKE orders INCLUDING DEFAULTS) ON COMMIT DROP`);
    const stream = client.query(copyFrom(`COPY orders_stage (user_id, total, status) FROM STDIN CSV`));
    await pipe(orderStream, stream);
    await client.query(`
      INSERT INTO orders (user_id, total, status)
      SELECT user_id, total, status FROM orders_stage
      ON CONFLICT DO NOTHING
    `);
  } finally {
    client.release();
  }
}

// ============================================================
// Sequelize — bulkCreate with updateOnDuplicate (upsert)
// ============================================================
await Order.bulkCreate(orders, {
  validate: false,                         // skip per-row validation
  updateOnDuplicate: ['total', 'status'],  // upsert
  benchmark: true,
});

// ============================================================
// SQLAlchemy 2.x — Core bulk insert
// ============================================================
from sqlalchemy import insert
with engine.begin() as conn:
    conn.execute(insert(Order), [
        {"user_id": ..., "total": ..., "status": ...}
        for ... in batch
    ])
```

## Step-by-step dry run

### Workload: insert 100,000 orders

#### Path 1: naive ORM loop (TypeORM `save` in loop)
```
for (const o of orders) await repo.save(o);
```
- Each `save()`: pool acquire → BEGIN → INSERT ... RETURNING id → COMMIT → release.
- Round trips per row: ~3 (BEGIN, INSERT, COMMIT).
- 100k × 3 × 1ms = 300s = **5 minutes**.
- Hydration cost ignored.

#### Path 2: ORM bulk insert (single statement)
```
await repo.insert(orders);
```
- ORM constructs `INSERT INTO orders (...) VALUES (...),(...),...` with 100k rows.
- Param count: 100k × 5 = 500k → EXCEEDS Postgres 65k limit. Fails.
- Fix: chunk to 10k rows × 5 cols = 50k params → 10 statements.
- 10 × ~50ms = **0.5 seconds**.

#### Path 3: chunked bulk with TX per chunk
```
for (const chunk of chunks(orders, 1000)) {
  await ds.transaction(mgr => mgr.insert(Order, chunk));
}
```
- 100 chunks × 1000 rows × 5 cols = 5000 params each — well under limit.
- 100 × ~10ms = **1 second**.
- Each TX is short → no replication lag, no long lock holds.

#### Path 4: COPY into staging then INSERT SELECT
```
COPY orders_stage (...) FROM STDIN CSV     -- ~100ms for 100k rows
INSERT INTO orders SELECT ... FROM orders_stage ON CONFLICT DO NOTHING   -- ~200ms
```
- Total: **~300ms**.
- Best path for 1M+ rows where INSERT becomes WAL-dominated.

### Sizing decisions

For 10k rows: **path 2** (chunked bulk) wins on simplicity.
For 100k rows: **path 3 or 4**, depending on whether ON CONFLICT handling is needed.
For 10M rows: **path 4** with throttling.
For 100M rows: COPY + table partitioning + parallel imports per partition.

## How to think aloud in the interview

> "The naive loop is N round trips — kills you immediately. There are three improvements:
>
> 1. **ORM bulk API** — `createMany` / `bulkCreate` / `insert([])`. Generates a multi-row INSERT, single round trip. Watch for the param limit (~65k in Postgres); chunk in 1000-row batches.
> 2. **Postgres `COPY`** — streaming protocol, no SQL parsing per row, ~10-100x faster than even multi-row INSERT. Limitations: no `ON CONFLICT` directly. Workaround: COPY into a staging table, then `INSERT ... SELECT ... ON CONFLICT DO NOTHING`.
> 3. **Disable triggers / FKs** for huge bulk imports of trusted data, then re-enable.
>
> Sizing:
> - ≤10 rows: regular ORM save().
> - 10–10k: bulk API.
> - 10k–1M: chunked bulk, one TX per chunk.
> - 1M+: COPY + staging table.
>
> Edge cases:
> - Hooks usually don't fire on bulk inserts — provide defaults explicitly.
> - Default columns may not auto-fill in bulk paths.
> - One huge TX is worse than 100 small ones — replication lag, WAL flood.
> - Identity map isn't populated — subsequent finds will re-fetch.
>
> For upserts: TypeORM `orUpdate`, Sequelize `updateOnDuplicate`, Prisma's `upsert` (per-row only), or raw `INSERT ... ON CONFLICT DO UPDATE`."

## Important takeaways

- Naive loop = N round trips = O(N) wall time. Always wrong above a handful of rows.
- ORM bulk API emits a single multi-row INSERT.
- Postgres parameter limit (~65k) caps single-statement row count; chunk to ~1000 rows.
- COPY is 10-100x faster than INSERT for large imports; use staging table to combine with ON CONFLICT.
- One huge TX is dangerous (replication lag, WAL flood); one TX per chunk.
- Bulk APIs typically skip hooks and identity-map updates — provide defaults and don't expect entity hydration.
- For repeated upserts, prefer raw `ON CONFLICT DO UPDATE` over per-row `upsert()`.

## Variants

1. **Streaming export** — opposite direction; use `COPY TO` or cursor with batch fetch.
2. **Server-side cursor + chunked transform** — for ETL, read source rows in pages, transform, COPY into target.
3. **Partitioned tables** — bulk insert into a freshly-created partition is fast; attach with `ALTER TABLE ATTACH PARTITION`.
4. **CTE-based upsert** — `WITH new AS (...) INSERT INTO main SELECT ... FROM new ON CONFLICT DO UPDATE`.
5. **MERGE statement** (Postgres 15+, Oracle, SQL Server) — clean upsert syntax.
6. **Async / parallel chunking** — split into N concurrent workers, each handling a slice; coordinate with advisory locks if order matters.
7. **Schema-less staging** — load into `unprocessed_data(payload JSONB)`, validate and transform via SQL later.

## Revision notes

> **bulk-insert-orm-trap — 60 second recap**
> - Naive loop = N round trips. Always wrong.
> - ORM bulk: `bulkCreate` / `createMany` / `insert([])` → single multi-row INSERT.
> - Postgres ~65k param limit; chunk ~1000 rows.
> - COPY is 10-100x faster; use staging table + INSERT SELECT to handle ON CONFLICT.
> - One TX per chunk; never one TX for the whole import.
> - Hooks usually skipped on bulk paths.
> - Upserts: TypeORM `orUpdate`, Sequelize `updateOnDuplicate`, Prisma `upsert` per-row, or raw `ON CONFLICT DO UPDATE`.
> - Sizing: ≤10 → save(); 10–10k → bulk; 10k–1M → chunked bulk; 1M+ → COPY + staging.
