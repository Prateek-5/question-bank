# SAVEPOINT Usage — Nested Transactions and Partial Rollback Patterns

## Source / Origin
- SQL standard since SQL:1999.
- Postgres native; MySQL InnoDB native; SQL Server (`SAVE TRANSACTION`); Oracle.
- Used internally by every ORM that exposes "nested transactions" — Hibernate, Django ORM, SQLAlchemy, ActiveRecord, Sequelize. Their "nested transaction" is implemented as SAVEPOINT under the hood.
- Companion doc: `backend-data-prep/sql/06-transactions.md`.
- Interview prompt: "Inside a single transaction that imports 1000 rows, some rows fail validation. How do you commit the good ones and skip the bad ones?"

## Why this question matters in interviews
Savepoints are the **bulk-import question** at any senior backend interview where you've claimed ORM experience. The trap is that beginners try to wrap each row in its own transaction (slow, defeats atomicity of the higher-level operation), or wrap everything in one transaction and `ROLLBACK` the whole thing on the first bad row (loses all the good work). Savepoints are the correct primitive: partial rollback within one outer transaction. The interviewer also uses this question to test whether you understand that ORMs' "nested transaction" is a fiction — there's no such thing as a true nested transaction in Postgres or MySQL; it's all savepoints. If you can't explain that, you're flagged as someone who doesn't know what your ORM does.

## Concepts involved

### Syntax to lock in

Postgres / MySQL / SQL Standard:
```sql
BEGIN;

SAVEPOINT before_user_insert;
INSERT INTO users(name) VALUES('Alice');
-- something goes wrong:
ROLLBACK TO SAVEPOINT before_user_insert;   -- undoes the INSERT only
-- the outer transaction is still active

SAVEPOINT s2;
INSERT INTO users(name) VALUES('Bob');
RELEASE SAVEPOINT s2;                       -- forgets s2; Bob's insert stays
                                            -- but is still uncommitted

COMMIT;                                     -- everything not rolled back is durable
```

Naming convention: savepoints are *scoped to the transaction*; they live in the transaction's stack. You can have many. They auto-release on outer COMMIT.

Important: after a statement error inside a transaction, Postgres **aborts the whole transaction** and refuses further statements until you `ROLLBACK` (full) or `ROLLBACK TO SAVEPOINT`. MySQL is more lenient by default but you should not rely on that — wrap with savepoints anyway.

### Edge cases / interview traps

1. **There is no real "nested transaction" in Postgres or MySQL.** ORMs implement "begin nested" as `SAVEPOINT sp_<n>`, "commit nested" as `RELEASE SAVEPOINT sp_<n>`, "rollback nested" as `ROLLBACK TO SAVEPOINT sp_<n>`. The "outer" transaction is the real one. Outer COMMIT/ROLLBACK applies to everything.
2. **A failed statement aborts the whole Postgres transaction** unless wrapped in a savepoint. After a single error, you cannot continue — Postgres returns `25P02 in_failed_sql_transaction` on every subsequent statement. Save points are how you opt into "this sub-block can fail safely".
3. **`ROLLBACK TO SAVEPOINT` does not release the savepoint.** You can roll back to the same savepoint multiple times. Use `RELEASE` to pop it off the stack when you're done.
4. **Savepoints don't release locks.** Locks acquired before a savepoint and *not* rolled back are still held. Locks acquired between a savepoint and `ROLLBACK TO SAVEPOINT` *are* released. Caveat: in MySQL, lock release semantics on savepoint rollback have historically varied (5.7 vs 8.0); test before assuming.
5. **Savepoints are not free.** Each savepoint allocates a subtransaction in Postgres. Heavy use creates many `xid` allocations. Postgres has a documented performance cliff around `subtrans_cache_size` (64 by default) — if you have >64 active savepoints in one transaction, lookups slow noticeably.
6. **Savepoint names can collide.** `SAVEPOINT s1; ... SAVEPOINT s1;` is legal — the second one shadows the first. `ROLLBACK TO s1` targets the most recent. Don't rely on this; use unique names.
7. **`RELEASE SAVEPOINT` is not "commit".** It just forgets the savepoint. The work is still uncommitted until the outer COMMIT. Beginners think `RELEASE` is a commit-equivalent — it isn't.
8. **You cannot SAVEPOINT outside a transaction.** Some libraries auto-start one for you; some throw an error. Know your driver.
9. **Distributed savepoints don't exist.** Savepoints are local to one connection's transaction. A microservice making N RPC calls can't "savepoint" across them — use sagas (see `saga-vs-2pc.md`).
10. **ORM "nested transaction commits" are confusing.** Django's `transaction.atomic()` nested call uses savepoints; it commits the savepoint (RELEASE) on success and rolls back to it on exception. The *outer* atomic block decides whether anything actually persists. Most ORM bugs come from misunderstanding this.

## Mental Model

### The savepoint stack

```
BEGIN                       ┌─ outer txn ─┐
  do work A                 │             │
  SAVEPOINT sp1   ──┐       │  workA      │
    do work B       │       │  workB      │
    SAVEPOINT sp2 ──┤       │  workB+C    │
      do work C     │       │             │
      ROLLBACK TO sp2       │  workB only │
      do work D             │  workB+D    │
    RELEASE sp2             │  workB+D    │
  ROLLBACK TO sp1           │  workA only │
  do work E                 │  workA+E    │
COMMIT                      └─ everything not rolled back is durable ┘
```

The savepoint stack is just a series of "checkpoint markers" inside the outer transaction. Roll back to a marker and everything above it on the stack is undone (logically; physically, locks and tuple versions hang around until COMMIT).

### Mental model: "try/except inside a transaction"

A savepoint is the SQL equivalent of `try: ... except: continue`. The transaction continues even if a sub-block fails. Without savepoints, the only error-handling primitive is `ROLLBACK` (lose everything).

```
BEGIN
  try:
    do_critical_work()
    SAVEPOINT s
      try:
        do_optional_work()
      catch SqlException:
        ROLLBACK TO s
        log("optional work failed, continuing")
      RELEASE s
    do_more_critical_work()
  catch:
    ROLLBACK     # lose everything
COMMIT
```

## Why interviewers care

- It's a direct test of "do you actually know what your ORM does?". Most candidates use savepoints unknowingly via `nested_atomic` and can't explain the mechanism.
- It surfaces understanding of **Postgres' aborted-transaction quirk** — beginners can't continue after an error and don't know why.
- It maps to a real-world problem: bulk imports, idempotent webhook handlers, replaying events with per-item validation.
- It naturally pivots to subtransaction performance, which is a senior Postgres-internals topic.

## Common beginner confusion

- **"Savepoints are nested transactions."** They aren't. They're rollback markers within a single transaction. The outer transaction is the real boundary.
- **"`RELEASE SAVEPOINT` commits."** It does not. The work is still uncommitted until outer COMMIT.
- **"After an error, I can keep going."** In Postgres, you cannot. You must either `ROLLBACK` or `ROLLBACK TO SAVEPOINT`. MySQL InnoDB is more permissive but rely on neither.
- **"Savepoints release locks."** Only locks acquired *between* the savepoint and the rollback are released. Locks before the savepoint stay.
- **"Use one big savepoint for the whole loop."** Defeats the purpose. Each fallible unit needs its own savepoint or one savepoint that's released and recreated per iteration.
- **"Savepoints are free."** Postgres has a subtrans performance cliff at ~64 concurrent subtransactions. ORMs that create a savepoint per row at scale cause issues.
- **"Savepoints work across connections."** They don't — one connection, one transaction.
- **"Just use `INSERT ... ON CONFLICT DO NOTHING`."** That works for duplicate-key cases but not for arbitrary validation errors (FK violations, check constraints, JSON parse errors). Savepoints are the general fallback.

## Brute force approach

"Each row in its own transaction, no savepoints":
```sql
-- for each row:
BEGIN; INSERT ...; COMMIT;
```
Works, but: (a) 10x slower due to fsync per commit, (b) the outer "bulk import" no longer has any atomicity — if the job dies halfway, you have a partial result and no clean way to resume.

"All rows in one transaction, rollback on any error":
```sql
BEGIN; INSERT row1; INSERT row2 (fails); ROLLBACK;
```
Atomic but loses all the good work. Often the wrong choice for bulk imports.

Both extremes are wrong. Savepoints are the right primitive.

## Optimal approach

### Pattern 1: per-row savepoint in bulk import

```sql
BEGIN;
-- one savepoint per row; bad rows skipped, good rows kept

SAVEPOINT row;
INSERT INTO users(email) VALUES('alice@x.com');
RELEASE SAVEPOINT row;

SAVEPOINT row;
INSERT INTO users(email) VALUES('bad-email');  -- check constraint violation
ROLLBACK TO SAVEPOINT row;
-- log "skipped: bad-email"; continue

SAVEPOINT row;
INSERT INTO users(email) VALUES('bob@x.com');
RELEASE SAVEPOINT row;

COMMIT;
-- final state: alice and bob inserted, bad-email skipped.
```

In code, this is typically driven by a loop:

```python
import psycopg2

with conn.cursor() as cur:
    cur.execute("BEGIN")
    for row in batch:
        cur.execute("SAVEPOINT sp")
        try:
            cur.execute("INSERT INTO users(email) VALUES (%s)", (row.email,))
            cur.execute("RELEASE SAVEPOINT sp")
        except psycopg2.Error as e:
            cur.execute("ROLLBACK TO SAVEPOINT sp")
            log.warning("skip row %s: %s", row.id, e.diag.message_primary)
    cur.execute("COMMIT")
```

### Pattern 2: optional side-effects

Main path is critical; an optional side-effect (audit log, denormalised counter update) is best-effort:

```sql
BEGIN;
INSERT INTO orders(...) VALUES (...);          -- critical
SAVEPOINT audit;
INSERT INTO audit_log(...) VALUES (...);       -- best-effort
-- if audit insert fails:
ROLLBACK TO SAVEPOINT audit;
-- audit not recorded; order still inserted
COMMIT;
```

### Pattern 3: retry sub-block with backoff

Sub-block that might fail due to serialisation conflict; retry without re-running everything:

```python
for attempt in range(3):
    cur.execute("SAVEPOINT retry")
    try:
        cur.execute("UPDATE counters SET val = val + 1 WHERE id=1")
        cur.execute("RELEASE SAVEPOINT retry")
        break
    except SerializationFailure:
        cur.execute("ROLLBACK TO SAVEPOINT retry")
        time.sleep(0.05 * (2**attempt))
```

### Pattern 4: ORM "nested transaction"

Django:
```python
with transaction.atomic():            # opens outer txn (or savepoint if already in one)
    do_critical()
    try:
        with transaction.atomic():    # opens savepoint
            do_optional()
    except IntegrityError:
        pass                           # savepoint already rolled back
    do_more_critical()
```

Hibernate/Spring `@Transactional(propagation = NESTED)` is the same mechanism.

## Solution

Complete bulk-import worker:

```python
def bulk_import(rows, conn):
    """
    Insert all valid rows, skip invalid ones, commit once.
    Returns (inserted, skipped) counts.
    """
    inserted, skipped = 0, 0
    with conn.cursor() as cur:
        cur.execute("BEGIN")
        for row in rows:
            cur.execute("SAVEPOINT sp")
            try:
                cur.execute(
                    "INSERT INTO users(email, name) VALUES (%s, %s)",
                    (row.email, row.name),
                )
                cur.execute("RELEASE SAVEPOINT sp")
                inserted += 1
            except psycopg2.Error as e:
                cur.execute("ROLLBACK TO SAVEPOINT sp")
                log.warning("skipped row %s (%s): %s",
                            row.id, e.pgcode, e.diag.message_primary)
                skipped += 1
        cur.execute("COMMIT")
    return inserted, skipped
```

For very large imports (>10k rows), batch the savepoints — group every 100 inserts under one savepoint to avoid hitting Postgres' subtrans cache cliff:

```python
def bulk_import_chunked(rows, conn, chunk_size=100):
    with conn.cursor() as cur:
        cur.execute("BEGIN")
        for chunk in chunks(rows, chunk_size):
            cur.execute("SAVEPOINT chunk")
            try:
                for row in chunk:
                    cur.execute("INSERT INTO users(email) VALUES (%s)", (row.email,))
                cur.execute("RELEASE SAVEPOINT chunk")
            except psycopg2.Error:
                cur.execute("ROLLBACK TO SAVEPOINT chunk")
                # fall back to per-row mode for this chunk
                for row in chunk:
                    cur.execute("SAVEPOINT row")
                    try:
                        cur.execute("INSERT INTO users(email) VALUES (%s)", (row.email,))
                        cur.execute("RELEASE SAVEPOINT row")
                    except psycopg2.Error:
                        cur.execute("ROLLBACK TO SAVEPOINT row")
        cur.execute("COMMIT")
```

This is the "chunk-then-fallback" pattern: fast path for all-good chunks, isolated retry for chunks with errors.

## Step-by-step dry run

Input: import 5 rows; row 3 has bad email.

```
T=0   BEGIN
T=1   SAVEPOINT sp;     INSERT row1 (alice);     RELEASE sp        → stack: []
T=2   SAVEPOINT sp;     INSERT row2 (bob);       RELEASE sp        → stack: []
T=3   SAVEPOINT sp;     INSERT row3 (bad-email)  ← raises 23514 check_violation
T=3   ROLLBACK TO sp                                                → stack: [sp]
       (row3 logically gone; sp still on stack, not released)
T=4   We don't release sp here in this implementation; we re-savepoint next iter
T=5   SAVEPOINT sp;     INSERT row4 (carol);     RELEASE sp        → stack: []
T=6   SAVEPOINT sp;     INSERT row5 (dave);      RELEASE sp        → stack: []
T=7   COMMIT
                                                                    
Final state: alice, bob, carol, dave persisted. bad-email rejected and skipped.
Outer transaction was atomic w.r.t. anyone watching (one COMMIT timestamp).
```

What happens without savepoints:
```
T=3   INSERT row3 raises 23514.
T=4   Try: INSERT row4 → ERROR: current transaction is aborted, commands ignored
                          (Postgres state 25P02)
T=5+  Every subsequent statement returns the same error.
T=∞   You must ROLLBACK and start over. All work lost.
```

That `25P02` error is the most common Postgres confusion in code reviews — and savepoints are the answer.

## How to think aloud in the interview

> "Bulk import with per-row validation. The naive options both lose: per-row transactions are slow and break atomicity of the outer operation; one big transaction loses all good work on the first bad row. The correct primitive is `SAVEPOINT`.
>
> The pattern: open one outer transaction. Before each row, `SAVEPOINT sp`. Insert the row. On success, `RELEASE SAVEPOINT sp`. On error, `ROLLBACK TO SAVEPOINT sp` — that undoes only that row, the outer transaction continues. Commit at the end.
>
> Three things to flag:
>
> 1. **Postgres aborts the entire transaction on any error** unless wrapped in a savepoint. Without savepoints, you can't continue. This is the `25P02 in_failed_sql_transaction` error that confuses every new Postgres user.
> 2. **Savepoints are not free.** Each one creates a subtransaction in Postgres. Past ~64 active subtransactions, lookups slow. For 10k-row imports, batch them: one savepoint per chunk of 100, fall back to per-row only when a chunk fails.
> 3. **'Nested transactions' in ORMs are savepoints under the hood.** Django's `transaction.atomic()` nested, Hibernate's `PROPAGATION_NESTED`, SQLAlchemy's `nested transaction` — all `SAVEPOINT sp_n; ... RELEASE sp_n` or `ROLLBACK TO sp_n`. There's no true nesting in Postgres or MySQL.
>
> For the optional-side-effect pattern (e.g., audit log alongside business write), the same primitive: outer transaction commits the business write; savepoint around the audit insert lets it fail silently.
>
> For serialisation-retry within a longer transaction, savepoints let you retry one sub-block with backoff without redoing the prior work."

## Important takeaways

- **Savepoint = rollback marker inside one transaction.** Not a nested transaction.
- **`SAVEPOINT n` / `ROLLBACK TO SAVEPOINT n` / `RELEASE SAVEPOINT n`** — the three operations.
- **`RELEASE` is not commit.** Outer `COMMIT` is the only commit.
- **Postgres aborts the whole transaction on any error** without savepoints. Savepoints are how you opt into partial recovery.
- **Performance cliff at ~64 subtransactions in Postgres.** Batch savepoints for large imports.
- **ORM "nested transactions" are savepoints.** Django, Hibernate, SQLAlchemy, ActiveRecord, Sequelize all implement them this way.
- **Locks are released only for the portion rolled back to the savepoint**, not pre-savepoint locks.
- **Per-row savepoint for bulk import** is the canonical pattern; chunk-then-fallback is the optimisation.
- **Distributed savepoints don't exist.** For cross-service rollback, use sagas.

## Variants

1. **`INSERT ... ON CONFLICT DO NOTHING`** (Postgres) or `INSERT IGNORE` (MySQL) — handles duplicate-key cases without savepoints. Use this when the only failure mode is unique constraint violation.
2. **`COPY` with `WHERE`-style validation upstream** — for true bulk loads, pre-validate in app code and `COPY` only good rows. Faster than savepoints for >100k rows.
3. **`SET LOCAL statement_timeout`** before risky statements — pairs well with savepoints if you also want to bound long-running operations.
4. **`SAVEPOINT` + `SELECT ... FOR UPDATE`** — useful when retrying a sub-block that touched locked rows; savepoint rollback releases those locks.
5. **MySQL `SAVEPOINT`** — same syntax. Lock-release-on-rollback behaviour has differed across 5.6/5.7/8.0; check the version's docs.
6. **SQL Server `SAVE TRANSACTION sp`** + `ROLLBACK TRANSACTION sp` — same semantics, different keyword. No `RELEASE`; savepoint auto-discarded on next commit.
7. **Oracle savepoints** — auto-released on commit; otherwise standard.
8. **Postgres subtransaction performance** — Postgres 14+ improved subtrans handling; older versions had a sharper cliff. Mention for currency.

## Revision notes

> **savepoint — 60 second recap**
> - **What it is:** rollback marker inside a single transaction.
> - **Operations:** `SAVEPOINT n`, `ROLLBACK TO SAVEPOINT n`, `RELEASE SAVEPOINT n`.
> - **Use case 1:** bulk import — skip bad rows, keep good ones. Per-row savepoint.
> - **Use case 2:** optional side-effects — savepoint around best-effort writes.
> - **Use case 3:** retry sub-block on serialisation failure with backoff.
> - **Postgres trap:** any error aborts entire transaction; savepoints are the recovery mechanism (avoids `25P02`).
> - **Perf trap:** >64 subtransactions in Postgres slows down. Batch savepoints for >1000-row imports.
> - **ORM trap:** "nested transactions" are savepoints; outer `COMMIT` is the only real commit.
> - **No distributed savepoints** — use sagas across services.
> - **`RELEASE` ≠ commit** — outer `COMMIT` decides what persists.
