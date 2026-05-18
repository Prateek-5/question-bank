# READ UNCOMMITTED — When It's Valid and the MySQL Default Trap

## Source / Origin
- SQL standard isolation level (the weakest one).
- ANSI SQL-92 defines dirty-read as the anomaly READ UNCOMMITTED specifically allows.
- Companion docs: `transactions-concurrency/dirty-read-scenario.md`, `transactions-concurrency/identify-isolation-level.md`, `backend-data-prep/sql/07-isolation-levels.md`.
- Interview prompt: "Name a legitimate use case for READ UNCOMMITTED. Then name three places where you'd never use it."

## Why this question matters in interviews
READ UNCOMMITTED is the **trap-detection question** in isolation interviews. Most candidates dismiss it as "always wrong" — that's the easy half-answer. The senior signal is acknowledging that it has real use cases (analytics dashboards, progress estimators, log-tail scaffolding) and also that it can sneak into production by accident on certain configurations. The MySQL default-level trap (some teams default to RU thinking it's "faster") is a specific industry foot-gun worth flagging. Interviewers want to see (a) you can articulate dirty-read, non-repeatable read, phantom, write skew clearly, (b) you can name a defensible use case for RU, (c) you understand Postgres's silent upgrade quirk and MySQL's actual RU behaviour, and (d) you can spot RU misuse in code review.

## Concepts involved

### Syntax to lock in

Postgres:
```sql
BEGIN ISOLATION LEVEL READ UNCOMMITTED;
SELECT * FROM accounts WHERE balance > 1000;
COMMIT;
-- IMPORTANT: Postgres silently upgrades READ UNCOMMITTED to READ COMMITTED.
-- There is no true RU in Postgres. Confirmable via:
SHOW transaction_isolation;   -- returns 'read committed' even after RU request.
```

MySQL InnoDB (real RU here):
```sql
SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
BEGIN;
SELECT * FROM accounts WHERE balance > 1000;  -- can see uncommitted rows from other sessions
COMMIT;
```

SQL Server (real RU here; `NOLOCK` hint shortcut):
```sql
SELECT * FROM accounts WITH (NOLOCK) WHERE balance > 1000;
-- equivalent to setting isolation = READ UNCOMMITTED for this query.
```

### Edge cases / interview traps

1. **Postgres silently upgrades RU → RC.** The standard requires RU to allow dirty reads. Postgres's MVCC implementation cannot return uncommitted versions efficiently. So Postgres makes RU equivalent to RC. You cannot get true dirty reads in Postgres. If you ask for them, you don't get them; you also don't get an error. Most teams don't notice.
2. **MySQL InnoDB RU is genuine.** You really can see uncommitted writes from other transactions. This is the only mainstream RDBMS where RU is meaningfully different from RC for SELECTs.
3. **SQL Server `WITH (NOLOCK)` is RU per-query.** People sprinkle it everywhere "to speed things up" without realising the implications. Classic legacy-app smell.
4. **Anomalies allowed at RU.** Dirty read (read uncommitted writes), non-repeatable read, phantom, lost update via "read-then-write" race, write skew. Essentially every isolation anomaly is permitted.
5. **Anomalies *not* prevented but rarely matter.** For pure-read aggregate queries (`SELECT count(*)`), the result may be off by a small fraction during concurrent writes; whether that matters depends on the use case.
6. **RU + write = catastrophic.** Reading uncommitted data, deciding based on it, then writing is the classic dirty-read-causes-bad-write bug. Never read RU in transactional logic.
7. **MySQL's default is RR, not RU.** Some teams change the default to RU thinking it's faster. There's almost no measurable performance difference for SELECTs vs RC in modern InnoDB. Choosing RU as the default is usually based on outdated wisdom.
8. **"Locking reads" interact with RU.** `SELECT ... FOR UPDATE` even at RU still acquires locks. RU only relaxes *visibility*, not *locking*.
9. **Replicas often read RC implicitly.** Read replicas typically run at a level chosen at the replica, not what the writer requested. Don't assume "I set RU on the writer" propagates to read paths.
10. **Cassandra/Mongo aren't isolation-level systems.** Don't drag SQL isolation vocabulary to NoSQL — they have their own consistency knobs.
11. **Phantom reads at RU.** Even at RC and RU, the range you SELECTed can change underneath you. Phantoms aren't unique to RU; they're allowed at RC and RR (in standard).
12. **Streaming dashboards' "approximately right" stance.** "I want this metric updated every second; off-by-a-few during concurrent writes is acceptable." This is the legitimate RU niche.

## Mental Model

### Anomalies allowed by each level

```
                       Dirty   Non-repeat   Phantom   Write   Lost
Level                  Read    Read         Read      Skew    Update
─────────────────────────────────────────────────────────────────────
READ UNCOMMITTED       YES     YES          YES       YES     YES
READ COMMITTED         no      YES          YES       YES     YES
REPEATABLE READ        no      no           depends*  YES     no**
SERIALIZABLE           no      no           no        no      no

* MySQL InnoDB RR prevents phantoms via gap locks; Postgres RR prevents via snapshot.
* Standard RR doesn't prevent phantoms; only SERIALIZABLE does.
** Postgres RR raises 40001 on lost update; MySQL InnoDB RR allows it.
```

RU is the row with all YES. Every other level is a careful subtraction.

### The dirty-read picture

```
T1:  BEGIN;
T1:  UPDATE accounts SET balance = balance - 100 WHERE id = 1;
                                                              ┐
T2 (RU):              SELECT balance FROM accounts WHERE id=1;│  sees -100
                                                              │  uncommitted
T1:  ROLLBACK;        ← writes never happened                 │
                                                              │
T2 used the -100 value. Made a decision on it. Now that decision is based
on data that, by the database's rules, never existed.
```

This is dirty read. The decision T2 made is now invalid. If T2 also wrote based on this — e.g., decremented inventory — the wrong-data wrote *committed* and there's no clean rollback path.

### When RU is fine

```
[Producer of progress events]   COMMIT every 100 rows
        │
        ▼
   import_progress table         row_count column updated
        │
        ▼
[Dashboard]   SELECT row_count FROM import_progress AT RU
        │
        ▼
   shows "73,400 rows processed"  ← off by ≤ 100 but who cares
```

The reader doesn't care about exact correctness; they want a recent number. RU lets them avoid contending with the writer's locks.

## Why interviewers care

- It tests whether you can think about **isolation as a tradeoff**, not a goal. Most candidates default to "stronger is better" without articulating the cost.
- It surfaces awareness of **engine-specific quirks** (Postgres silent upgrade, MySQL RU genuine, SQL Server NOLOCK).
- It maps to real **production smells** — `WITH (NOLOCK)` everywhere, MySQL default set to RU, "we made the dashboard faster" stories.
- It naturally pivots to MVCC internals: *why* doesn't Postgres support true RU? (Because RC is cheaper than RU under MVCC, not more expensive.)

## Common beginner confusion

- **"RU is faster than RC."** Almost universally false in modern engines. Locking-based engines (old SQL Server, MySQL pre-InnoDB) had some benefit. MVCC engines (Postgres, modern InnoDB) get zero perf win from RU on most workloads.
- **"Postgres supports RU."** It accepts the syntax. It does not implement RU semantics. Internally it's RC.
- **"RU is always wrong."** False — analytics dashboards, progress monitors, log-replay scaffolding are legitimate use cases.
- **"`WITH (NOLOCK)` makes my query thread-safe."** It does the opposite: it disables read locks, exposing your query to dirty data.
- **"At RU I can still trust aggregates."** A `COUNT(*)` at RU during writes may double-count rows (visible mid-INSERT) or miss them. Use only when "approximately right" is acceptable.
- **"Setting isolation at the connection is enough."** Depends on framework; many ORMs override on each transaction. Check the actual level with `SHOW transaction_isolation` after BEGIN.
- **"Read replicas inherit the writer's isolation."** No — the replica chooses its own. Don't assume.

## Brute force approach

"Set everything to SERIALIZABLE; it's the safest." Correct on safety, often wrong on throughput. Hot paths bombarded with serialisation failures.

"Set everything to READ UNCOMMITTED; it's the fastest." Wrong on most engines (Postgres silently equates to RC; MySQL barely differs from RC); also incorrect — you've just legalised every anomaly in your transactional code.

Both extremes are wrong. The correct answer is per-workload selection.

## Optimal approach

### Decision matrix

```
Workload                         Recommended isolation     RU acceptable?
─────────────────────────────────────────────────────────────────────────
Transfers, billing               SERIALIZABLE or RC+locks  NO
User profile read                RC                        NO (no real benefit)
Order placement                  RC + FOR UPDATE           NO
Bulk import / staging            RC                        NO
Analytics dashboard refresh      RC                        YES (MySQL/MSSQL only)
Progress estimator               RC                        YES
DB health-check (row counts)     any                       YES
Long-running export             RR or RC                   NO (need consistency)
Reports requiring snapshot      RR (Postgres)              NO
```

### When RU is the right tool

1. **Progress monitors / dashboards** where "approximately right" beats "blocking on a long writer's lock".
2. **Diagnostic queries** at 3 AM where you don't want to interact with running batch jobs.
3. **Log-tail / event-replay scaffolding** during development where the data correctness doesn't matter yet.
4. **DBA-style queries**: "how many rows are roughly in this table during this huge import?" — true row count via RU read, not blocked by the import.

### When RU is wrong (much more common)

1. **Any transactional read-then-write logic** — dirty data → bad decisions → bad commits.
2. **Anything billing, financial, or auditable.**
3. **Queries that produce values exposed to other systems** — your downstream consumer doesn't know the value is dirty.
4. **Queries used for cache population** — caching dirty data permanently corrupts your cache.

### Engine-specific notes

- **Postgres**: there's no point asking for RU. You get RC regardless. Set `default_transaction_isolation` to `read committed` and forget about RU.
- **MySQL InnoDB**: RU genuinely allows dirty reads. Default is RR (since 5.6); a team that sets it to RU has chosen poorly unless they really mean it.
- **SQL Server**: `WITH (NOLOCK)` is per-query RU. Common in legacy code. Audit and remove unless you can defend each instance.
- **MariaDB / TiDB / CockroachDB**: vary; check version docs.

## Solution (audit + remediation)

How to spot RU in code review:

```sql
-- Postgres: meaningful only as a smell signal
\df+ ... -- look for functions setting isolation explicitly
SELECT name, setting FROM pg_settings WHERE name = 'default_transaction_isolation';
-- if it returns 'read uncommitted' someone tried; Postgres ignored.

-- MySQL: actually matters
SELECT @@global.transaction_isolation, @@session.transaction_isolation;
-- If global is READ-UNCOMMITTED, alert the team:
SET GLOBAL transaction_isolation = 'REPEATABLE-READ';

-- Scan for SQL Server NOLOCK hints across codebase
$ grep -rni 'with (nolock)' .
```

For legitimate RU use (e.g., dashboard query):

```sql
-- MySQL: explicit per-session RU for a specific read-only worker
SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
SELECT count(*) FROM imports WHERE status = 'in_progress';
-- IMPORTANT: this session only does this read; never use it for transactional work.
```

```sql
-- SQL Server: scoped RU hint with a comment explaining why
-- Dashboard: progress estimate; tolerable error ≤ 100 rows.
SELECT count(*) FROM imports WITH (NOLOCK) WHERE status = 'in_progress';
```

For "I thought RU would be faster" remediation:

1. **Measure**. Run the workload at RC vs RU on the same engine. In Postgres there's no difference (silent upgrade). In MySQL the gap is typically <2% for SELECT-heavy workloads.
2. **Move the perceived "RU benefit" to read replicas**. Reads on a replica don't contend with the primary's locks anyway.
3. **Eliminate NOLOCK hints in SQL Server transactional code**. Keep them only on dashboard queries with explicit comments.

## Step-by-step dry run

Scenario: bank transfer + concurrent dashboard query.

```
T1 (transfer, RC):
  BEGIN;
  UPDATE accounts SET balance = balance - 100 WHERE id = 1;
  -- 50ms of business logic before next statement
  UPDATE accounts SET balance = balance + 100 WHERE id = 2;
  COMMIT;

T2 (dashboard, RU on MySQL):
  SELECT sum(balance) FROM accounts;
  -- Runs in the gap between T1's two UPDATEs.
  -- Sees:  id=1 → -100, id=2 → unchanged
  -- sum = total - 100   ← MISSING $100. Dashboard now displays wrong total.

T1 COMMITs. Real sum back to total. But the snapshot served to dashboard was wrong.

If the dashboard had read at RC (or with FOR SHARE), it would have either
blocked on T1 briefly or seen the *pre*-T1 snapshot — both consistent.
```

Same scenario on Postgres at "RU":
```
T2:  BEGIN ISOLATION LEVEL READ UNCOMMITTED;
     SELECT sum(balance) FROM accounts;     ← Postgres silently used RC.
     Returns the pre-T1 snapshot. Consistent.
```

Postgres saved the team from their own mistake. **Implicit lesson: Postgres's behaviour here is a feature, not a bug.**

Scenario: progress dashboard during long import (legitimate RU):

```
Writer (long import, RC):
  BEGIN;
  for batch in batches:
    INSERT INTO orders ...           -- thousands of rows
    UPDATE import_progress SET row_count = row_count + 1000 WHERE id = 1;
    -- not yet committed
  -- 5 minutes elapse before COMMIT

Reader (dashboard, RU on MySQL):
  SELECT row_count FROM import_progress WHERE id = 1;
  → returns the latest uncommitted row_count (say 432000)
  → dashboard shows "432K rows processed"
  → user sees real-time progress

If writer COMMITs:  reader still shows ~432K, then 433K, etc.
If writer ROLLBACKs: reader briefly showed an inflated number, then drops back to 0.
For a progress meter, that's acceptable.
```

This is the RU sweet spot: read-only, tolerable error, benefit = no blocking.

## How to think aloud in the interview

> "READ UNCOMMITTED is the weakest isolation level. It allows dirty reads — seeing writes from transactions that haven't committed yet — plus every weaker anomaly: non-repeatable read, phantom, lost update, write skew. So in transactional code paths it's almost always wrong: you make decisions on data that the engine, by its own rules, hasn't promised exists.
>
> Three engine-specific things I'd flag:
>
> 1. **Postgres silently upgrades RU to RC.** Postgres's MVCC implementation cannot return uncommitted tuples efficiently, so it just ignores the RU request and runs RC. No error, no warning. If your team thinks they're using RU on Postgres, they're not.
> 2. **MySQL InnoDB RU is genuine.** Real dirty reads possible. The default since 5.6 has been REPEATABLE READ; some teams change it to RU under the impression it's faster. It's not — modern InnoDB doesn't get measurable benefit from RU for typical SELECT workloads.
> 3. **SQL Server `WITH (NOLOCK)` is per-query RU.** Legacy codebases sprinkle it everywhere. Almost always a smell.
>
> Legitimate use cases exist:
> - **Progress monitors / dashboards** where 'approximately right' beats blocking on a long writer's lock.
> - **Diagnostic queries during heavy load** where you don't want to acquire any locks.
> - **Quick scaffolding** during development of analytics queries.
>
> Never use RU for transactional logic, billing, anything that drives a write, or anything exposed to consumers as a source-of-truth value.
>
> Practical recommendation: leave Postgres alone; Postgres protects you. On MySQL, default to REPEATABLE READ (which is the InnoDB default anyway); use session-scoped RU for one specific dashboard worker if you genuinely need it. On SQL Server, audit `NOLOCK` hints and keep them only where commented as 'approximate metric'."

## Important takeaways

- **RU permits every isolation anomaly.** Dirty read, non-repeatable, phantom, lost update, write skew.
- **Postgres silently upgrades RU to RC.** No true RU on Postgres.
- **MySQL InnoDB RU is genuine.** SQL Server RU/NOLOCK is genuine.
- **RU is rarely faster.** Modern MVCC engines get little benefit; switching defaults to RU is usually misguided.
- **Legitimate uses**: progress dashboards, diagnostic queries during contention, scaffolding.
- **Never use RU** for transactional read-then-write logic, billing, exposed source-of-truth values, or cache population.
- **`WITH (NOLOCK)` is per-query RU** on SQL Server; audit ruthlessly.
- **Read replicas** choose their own level; don't assume the writer's level propagates.
- **Check actual level**: `SHOW transaction_isolation` (Postgres) / `SELECT @@transaction_isolation` (MySQL).
- **Defaults**: Postgres = RC, MySQL InnoDB = RR. Both reasonable.

## Variants

1. **`STATEMENT_TIMEOUT` instead of RU** — the most common reason teams reach for RU is "I don't want a long write to block my dashboard." A short statement timeout on the dashboard query is a cleaner answer.
2. **Read replica for analytics** — physically separate the read traffic so it can't contend with writes. Modern best practice.
3. **Materialised views** — precompute the analytics result at convenient intervals. Reader never touches the write path.
4. **`READ COMMITTED` with `FOR SHARE` removed** — sometimes "the dashboard slows the writer" is fixed not by RU but by removing accidental shared-lock acquisition in the read path.
5. **Cassandra `CONSISTENCY ONE`** — the NoSQL analogue: serve from the nearest replica without quorum. Different model, similar tradeoff.
6. **MongoDB `readConcern: "local"`** — return potentially uncommitted data on the local node. See `mongo-read-preference-quiz.md`.
7. **DynamoDB eventually-consistent reads** — same family: cheaper, can return stale data, fine for non-critical reads.
8. **`SET LOCAL TRANSACTION ISOLATION LEVEL`** — Postgres scope-limited within a transaction; useful if you want one block to differ from the connection default.

## Revision notes

> **READ UNCOMMITTED — 60 second recap**
> - **Allows every anomaly:** dirty read, non-repeatable, phantom, lost update, write skew.
> - **Postgres silently upgrades to RC.** No true RU on Postgres.
> - **MySQL InnoDB RU genuine.** SQL Server `WITH (NOLOCK)` = per-query RU.
> - **Rarely faster** on modern MVCC engines. Switching defaults to RU is almost always wrong.
> - **Legitimate use:** progress dashboards, diagnostic queries, scaffolding. Read-only with tolerable error.
> - **Never use for:** transactional logic, billing, exposed source-of-truth values, cache population.
> - **MySQL default = RR; Postgres default = RC.** Both fine; don't lower for "performance".
> - **Better alternatives** to RU: statement_timeout, read replicas, materialised views.
> - **Check actual level**: `SHOW transaction_isolation` or `SELECT @@transaction_isolation`.
