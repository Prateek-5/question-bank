# `FOR UPDATE SKIP LOCKED` — Postgres Job Queue Pattern

## Source / Origin
- `SKIP LOCKED` introduced in Postgres 9.5 (2016). Long present in Oracle as `FOR UPDATE SKIP LOCKED` (since 8i, 1999). MySQL 8.0 added it (2018).
- Productionised in: `pg-boss`, `Que`, `River`, GitLab's Sidekiq-on-Postgres pattern, every team that decided "we don't need Redis for jobs".
- Companion docs: `transactions-concurrency/advisory-lock-use-cases.md`, `transactions-concurrency/transactional-outbox.md`.
- Interview prompt: "Implement a job queue using only Postgres. Multiple workers pull jobs concurrently. No duplicate processing. No blocking. Show the SQL."

## Why this question matters in interviews
This is the **"do you actually use Postgres" question** at backend interviews. Anyone can describe Redis BRPOP. Few candidates know that Postgres has the perfect job-queue primitive sitting in plain sight — `SELECT ... FOR UPDATE SKIP LOCKED`. The senior signal is (a) knowing the primitive exists, (b) being able to write the SQL from memory, (c) explaining *why* it works — locked rows are skipped, not waited for, so N workers each grab a different row in one round-trip, and (d) discussing the failure modes: lock leakage on worker crash, visibility timeout via `FOR UPDATE NOWAIT` or watchdog, ordering guarantees. Bombing this question screams "I'd add Redis for any small problem". Nailing it screams "I know my tools".

## Concepts involved

### Syntax to lock in

The canonical worker query (Postgres):
```sql
BEGIN;
SELECT id, payload
FROM jobs
WHERE status = 'queued'
ORDER BY id
LIMIT 1
FOR UPDATE SKIP LOCKED;

-- worker has now locked one row; no other worker can pick the same row.

UPDATE jobs SET status = 'running', started_at = now()
WHERE id = $picked_id;

COMMIT;
-- locks released; row remains 'running' until the worker finishes.
```

After processing:
```sql
BEGIN;
UPDATE jobs SET status = 'done', finished_at = now() WHERE id = $picked_id;
COMMIT;
```

Or on failure:
```sql
BEGIN;
UPDATE jobs SET status = 'queued', attempts = attempts + 1,
               run_after = now() + interval '1 minute'
WHERE id = $picked_id;
COMMIT;
```

### Edge cases / interview traps

1. **`FOR UPDATE` without `SKIP LOCKED` is the trap.** Vanilla `FOR UPDATE` makes worker #2 *wait* for worker #1's lock. You wanted concurrency; you got a serial queue. `SKIP LOCKED` is non-negotiable for this pattern.
2. **`NOWAIT` returns an error instead of skipping.** Wrong primitive for job queues; right for "I want this exact row or fail fast".
3. **Worker crash leaves row in `running` forever.** If the worker dies between `UPDATE status='running'` and `UPDATE status='done'`, the row is stuck. Add a watchdog: rows in `running` for >5 minutes are reset to `queued`. Or do all work inside one transaction so a crash auto-rolls-back.
4. **All-work-in-one-transaction is the cleanest design but ties up locks.** If the job takes 30 minutes, you've held a row lock for 30 minutes. Fine for short jobs, bad for long ones.
5. **Visibility timeout pattern.** Common alternative: keep job processing *outside* the transaction; set `lease_expires_at = now() + interval '5 minutes'` when claiming. A reaper periodically `UPDATE` reclaims expired leases. This is how SQS works internally.
6. **Ordering guarantees.** `ORDER BY id` + `SKIP LOCKED` gives "roughly FIFO across workers" — not strict FIFO, because a worker can skip an earlier row that's locked and grab a later one. If you need strict ordering, you can't have parallelism — pick one.
7. **`LIMIT 1` vs `LIMIT N`.** Pulling batches (`LIMIT 10`) is more efficient (fewer round-trips) but increases the "one slow row blocks 9 others" risk. Tune to job duration.
8. **`FOR NO KEY UPDATE` is enough.** `FOR UPDATE` acquires a stronger lock than this pattern needs. `FOR NO KEY UPDATE` is lighter and doesn't block FK references. Most production code still uses `FOR UPDATE` because it's the obvious one; `FOR NO KEY UPDATE` is slightly better.
9. **Partial indexes accelerate the queue.** `CREATE INDEX ON jobs (id) WHERE status = 'queued'` makes the "find next queued job" scan O(log n) of pending rows only, not of the whole jobs table. Critical at scale.
10. **Notifications**: Postgres `LISTEN/NOTIFY` lets idle workers wake up when a new job arrives instead of polling. Combine `SKIP LOCKED` polling fallback with `LISTEN` for near-zero idle latency.
11. **Connection per worker.** Each worker needs its own DB connection because `FOR UPDATE` holds locks on the connection. Don't share connections across workers.
12. **`SKIP LOCKED` does not skip rows locked by *other* commands** like `LOCK TABLE`. Don't `LOCK TABLE jobs` in any other code path or you serialise the whole queue.
13. **MySQL 8.0 supports `SKIP LOCKED`.** Same syntax. Pre-8.0 MySQL: not supported. Use `GET_LOCK()` advisory locks or migrate.

## Mental Model

### Visualising `SKIP LOCKED` vs `FOR UPDATE`

```
Vanilla FOR UPDATE — workers serialise:

  W1: SELECT FOR UPDATE LIMIT 1 → row 1 locked
  W2: SELECT FOR UPDATE LIMIT 1 → BLOCKS on row 1's lock
  W3: SELECT FOR UPDATE LIMIT 1 → BLOCKS on row 1's lock
  ...
  All workers wait for W1.

With FOR UPDATE SKIP LOCKED — workers parallelise:

  W1: SELECT FOR UPDATE SKIP LOCKED LIMIT 1 → row 1 locked
  W2: SELECT FOR UPDATE SKIP LOCKED LIMIT 1 → skips row 1, locks row 2
  W3: SELECT FOR UPDATE SKIP LOCKED LIMIT 1 → skips rows 1 & 2, locks row 3
  ...
  N workers, N rows, no blocking.
```

### Visualising the queue state machine

```
                     ┌──────────┐
   producer ────────►│  queued  │◄──────── retry (reset on failure)
                     └────┬─────┘
       worker picks ─────│ FOR UPDATE SKIP LOCKED
                          ▼
                     ┌──────────┐
                     │ running  │ ─── worker crashes ─► (stuck; watchdog resets to queued)
                     └────┬─────┘
       worker completes  │
                          ▼
                     ┌──────────┐
                     │   done   │
                     └──────────┘
                          │
                          ▼
                     ┌──────────┐
                     │  failed  │ (after max retries)
                     └──────────┘
```

### Inside the planner

`SELECT ... FOR UPDATE SKIP LOCKED` is implemented as: scan rows in index order; for each row, attempt to acquire the row-level lock with `LW_EXCLUSIVE` and `dontWait = true`; if it fails, advance to the next row. The planner doesn't know in advance which rows will be locked, so it streams rows until `LIMIT` is satisfied.

## Why interviewers care

- It tests **knowledge of Postgres-specific features** beyond ANSI SQL. Many candidates know Redis but couldn't enumerate Postgres power tools.
- It maps to the real **"do we need Redis?"** architectural conversation. Knowing this primitive lets you defend Postgres for medium-volume queues (10s of thousands/sec sustained on modern hardware).
- It probes understanding of **lock semantics** — what `FOR UPDATE` actually does, what `SKIP LOCKED` changes, how locks interact with transactions.
- It surfaces awareness of **production gotchas**: stuck rows on worker crash, watchdog patterns, partial indexes, `LISTEN/NOTIFY`.

## Common beginner confusion

- **"`FOR UPDATE` alone gives concurrent workers."** It doesn't — it serialises them. You need `SKIP LOCKED`.
- **"`SKIP LOCKED` skips rows that satisfy the WHERE."** No — it skips rows that *are currently locked by another transaction* and also satisfy the WHERE.
- **"Locks release on `COMMIT`."** True, but you want to hold them only briefly. Long-held locks defeat the parallelism.
- **"I can put a 30-minute job inside the transaction."** You can; you'll hold the lock for 30 minutes. Better: claim with `lease_expires_at`, process outside the transaction, watchdog reclaims expired leases.
- **"`SKIP LOCKED` ignores `ORDER BY`."** It doesn't. It evaluates rows in index/order, just skipping locked ones. Order is preserved among returned rows.
- **"`LIMIT 1` and `LIMIT 10` are equivalent."** Different tradeoffs: `LIMIT 1` = minimum round-trips for the worker, `LIMIT 10` = batch processing efficiency vs slow-row risk.
- **"Postgres can't do queues at scale."** A properly indexed `jobs` table with `SKIP LOCKED` handles 10k+ jobs/sec on modest hardware. The bottleneck is usually fsync on the WAL, not the lock primitive.
- **"I need Redis for fair scheduling."** Postgres can do it with `priority` columns and proper ORDER BY. Redis is faster for very high throughput, but the gap is smaller than people assume.

## Brute force approach

`SELECT * FROM jobs WHERE status='queued' LIMIT 1` then `UPDATE` — has a classic race: two workers can read the same row before either UPDATEs.

`SELECT ... FOR UPDATE` (no SKIP) — solves the race; serialises workers.

`Redis BRPOP` — works fine but introduces a second datastore. If you already have Postgres, this is unnecessary infrastructure.

`Advisory locks (pg_try_advisory_lock)` — works but is per-key; `SKIP LOCKED` is cleaner and supports `LIMIT N`.

## Optimal approach

### Single-tx pattern (short jobs, <1 second)

```sql
BEGIN;
WITH next_job AS (
  SELECT id FROM jobs
  WHERE status = 'queued' AND run_after <= now()
  ORDER BY id
  LIMIT 1
  FOR UPDATE SKIP LOCKED
)
UPDATE jobs SET status = 'running', started_at = now()
FROM next_job
WHERE jobs.id = next_job.id
RETURNING jobs.id, jobs.payload;
-- worker processes the job here
UPDATE jobs SET status='done', finished_at=now() WHERE id = $1;
COMMIT;
```

The CTE compresses the SELECT and UPDATE into one statement so the lock is held briefly. The RETURNING gives the worker the row in the same round-trip.

### Lease pattern (long jobs, minutes)

```sql
-- Claim phase
BEGIN;
UPDATE jobs SET
  status = 'running',
  worker_id = $worker_id,
  lease_expires_at = now() + interval '5 minutes',
  started_at = now()
WHERE id = (
  SELECT id FROM jobs
  WHERE status = 'queued' AND run_after <= now()
  ORDER BY id
  LIMIT 1
  FOR UPDATE SKIP LOCKED
)
RETURNING id, payload;
COMMIT;

-- Worker processes outside the transaction.
-- Heartbeat extends the lease every 60 seconds:
UPDATE jobs SET lease_expires_at = now() + interval '5 minutes'
WHERE id = $id AND worker_id = $worker_id;

-- Reaper (separate process or cron):
UPDATE jobs SET status = 'queued', worker_id = NULL, lease_expires_at = NULL
WHERE status = 'running' AND lease_expires_at < now();
```

### Partial index for performance

```sql
CREATE INDEX jobs_queued_idx ON jobs (id) WHERE status = 'queued';
```

This index contains only queued rows. As jobs complete, they leave the index (HOT update keeps it lean). The "find next queued" scan walks only the few pending rows.

### LISTEN/NOTIFY for low-latency wake-up

```sql
-- Producer
INSERT INTO jobs(payload) VALUES (...);
NOTIFY jobs;

-- Worker (in addition to polling every 5 seconds)
LISTEN jobs;
-- Block on connection.read(); on NOTIFY, wake up and poll once.
```

## Solution (Node.js worker)

```javascript
const { Client } = require('pg');

class JobWorker {
  constructor({ pollIntervalMs = 5000, workerId }) {
    this.pollIntervalMs = pollIntervalMs;
    this.workerId = workerId;
    this.client = new Client();
    this.notifyClient = new Client();
    this.running = false;
  }

  async start() {
    await this.client.connect();
    await this.notifyClient.connect();
    await this.notifyClient.query('LISTEN jobs');
    this.notifyClient.on('notification', () => this._tryPickOne());
    this.running = true;
    this._loop();
  }

  async _loop() {
    while (this.running) {
      const picked = await this._tryPickOne();
      if (!picked) {
        await new Promise(r => setTimeout(r, this.pollIntervalMs));
      }
    }
  }

  async _tryPickOne() {
    const { rows } = await this.client.query(`
      WITH next_job AS (
        SELECT id FROM jobs
        WHERE status = 'queued' AND run_after <= now()
        ORDER BY id
        LIMIT 1
        FOR UPDATE SKIP LOCKED
      )
      UPDATE jobs SET
        status = 'running',
        worker_id = $1,
        lease_expires_at = now() + interval '5 minutes',
        started_at = now()
      FROM next_job
      WHERE jobs.id = next_job.id
      RETURNING jobs.id, jobs.payload, jobs.attempts;
    `, [this.workerId]);

    if (rows.length === 0) return false;

    const job = rows[0];
    try {
      await this._process(job);
      await this.client.query(
        `UPDATE jobs SET status='done', finished_at=now() WHERE id=$1`,
        [job.id]
      );
    } catch (e) {
      const maxAttempts = 5;
      if (job.attempts + 1 >= maxAttempts) {
        await this.client.query(
          `UPDATE jobs SET status='failed', last_error=$2 WHERE id=$1`,
          [job.id, e.message]
        );
      } else {
        const backoff = Math.min(60 * (2 ** job.attempts), 3600);
        await this.client.query(`
          UPDATE jobs SET
            status='queued',
            attempts = attempts + 1,
            run_after = now() + ($2 || ' seconds')::interval,
            last_error = $3
          WHERE id = $1
        `, [job.id, backoff, e.message]);
      }
    }
    return true;
  }

  async _process(job) {
    // do the actual work here
  }
}
```

Schema:
```sql
CREATE TABLE jobs (
  id              BIGSERIAL PRIMARY KEY,
  payload         JSONB NOT NULL,
  status          TEXT NOT NULL DEFAULT 'queued',
  attempts        INT NOT NULL DEFAULT 0,
  run_after       TIMESTAMPTZ NOT NULL DEFAULT now(),
  started_at      TIMESTAMPTZ,
  finished_at     TIMESTAMPTZ,
  worker_id       TEXT,
  lease_expires_at TIMESTAMPTZ,
  last_error      TEXT
);

CREATE INDEX jobs_queued_idx
  ON jobs (run_after, id)
  WHERE status = 'queued';

CREATE INDEX jobs_running_lease_idx
  ON jobs (lease_expires_at)
  WHERE status = 'running';
```

Reaper (runs every 30 seconds):
```sql
UPDATE jobs SET
  status = 'queued',
  worker_id = NULL,
  lease_expires_at = NULL,
  attempts = attempts + 1,
  last_error = 'lease expired'
WHERE status = 'running' AND lease_expires_at < now();
```

## Step-by-step dry run

Setup: 3 workers W1/W2/W3 polling. Queue contains rows 1-5 (all status='queued').

```
T=0    W1 begins:  SELECT FOR UPDATE SKIP LOCKED LIMIT 1 → row 1, lock acquired
T=0+ε  W2 begins:  SELECT FOR UPDATE SKIP LOCKED LIMIT 1
                   - scans row 1 → locked by W1 → skip
                   - row 2 → not locked → lock acquired
T=0+ε  W3 begins:  SELECT FOR UPDATE SKIP LOCKED LIMIT 1
                   - scans row 1 → locked → skip
                   - row 2 → locked → skip
                   - row 3 → not locked → lock acquired

State: W1 holds row 1, W2 holds row 2, W3 holds row 3.
All three made progress in parallel without any blocking.

T=5    W1 finishes, COMMITs. Row 1 status='done'. Lock released.
T=6    W1 begins:  SELECT FOR UPDATE SKIP LOCKED LIMIT 1
                   - scans row 4 (rows 1-3 are running/done; index walks past them) → not locked → lock acquired
```

Compare with vanilla `FOR UPDATE`:
```
T=0    W1: SELECT FOR UPDATE LIMIT 1 → row 1
T=0+ε  W2: SELECT FOR UPDATE LIMIT 1 → row 1 locked → W2 BLOCKS
T=0+ε  W3: SELECT FOR UPDATE LIMIT 1 → row 1 locked → W3 BLOCKS

Effective parallelism: 1 worker. The other two waste connections waiting.
```

Scenario: W2 crashes after claim, before completion.

```
T=10   W2 claims row 2: UPDATE status='running', lease=now()+5min. COMMIT.
T=11   W2 crashes (process dies).
T=11   Row 2 is stuck in 'running' with W2's worker_id and lease_expires_at = T=16.
T=16   Reaper runs: WHERE status='running' AND lease < now() → row 2 matches.
       UPDATE row 2 SET status='queued', worker_id=NULL, attempts++.
T=20   W1 (or any worker) picks row 2 fresh.
```

This is the visibility-timeout pattern in action. SQS, RabbitMQ work the same way.

## How to think aloud in the interview

> "Postgres has a perfect primitive for this: `SELECT ... FOR UPDATE SKIP LOCKED`. It's the lock equivalent of 'try to lock; if you can't, skip and keep going'. Combined with `LIMIT 1`, each worker gets a different row in one round-trip.
>
> Schema: `jobs(id, payload, status, attempts, run_after, lease_expires_at, ...)`. A partial index on `WHERE status='queued'` keeps the queue scan O(log n) of pending rows only.
>
> Worker query, compressed into one statement with a CTE so the lock is held for microseconds:
>
> ```
> WITH next_job AS (
>   SELECT id FROM jobs WHERE status='queued' AND run_after <= now()
>   ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED
> )
> UPDATE jobs SET status='running', lease_expires_at = now() + interval '5 minutes'
> FROM next_job WHERE jobs.id = next_job.id
> RETURNING jobs.id, jobs.payload;
> ```
>
> Then process outside the transaction. On success, set status='done'. On failure, decide retry or fail-permanent based on attempts.
>
> Two production patterns to flag:
>
> 1. **Short jobs (<1s)**: do everything in one transaction; lock holds for the job duration; auto-rollback on crash. Clean.
> 2. **Long jobs (minutes)**: lease pattern. Claim with `lease_expires_at`. Heartbeat extends it. Reaper resets expired leases. Same model SQS uses.
>
> Wake-up latency: `LISTEN/NOTIFY` for instant; poll every 5 seconds as fallback.
>
> Throughput: a single Postgres instance with this pattern sustains tens of thousands of jobs/sec on modern hardware. Bottleneck is WAL fsync, not the lock primitive. If you're below that ceiling, you don't need Redis for jobs.
>
> Trap: vanilla `FOR UPDATE` *without* `SKIP LOCKED` serialises workers — they wait for each other instead of parallelising. The `SKIP LOCKED` clause is the entire point of this pattern."

## Important takeaways

- **`FOR UPDATE SKIP LOCKED`** = "lock the next available row; skip locked ones" → parallel workers in one round-trip.
- **Without `SKIP LOCKED`**, workers serialise. The clause is the entire pattern.
- **Single-tx pattern** for short jobs (<1s); lock auto-releases on COMMIT.
- **Lease pattern** for long jobs; heartbeat to extend; reaper resets expired leases.
- **Partial index** `WHERE status='queued'` for O(log n) queue scan.
- **`LISTEN/NOTIFY`** for low-latency wake-up; polling fallback for resilience.
- **Crash recovery**: in-transaction commits handle automatically; out-of-transaction processing needs leases + reaper.
- **`FOR NO KEY UPDATE`** is slightly lighter than `FOR UPDATE` and sufficient here.
- **One connection per worker**; locks are connection-scoped.
- **Postgres can handle 10k+ jobs/sec** with this pattern; bottleneck is WAL fsync.

## Variants

1. **Priority queues**: add a `priority` column, `ORDER BY priority DESC, id`.
2. **Per-queue worker pools**: filter `WHERE queue_name = $1` plus partial index.
3. **Delayed jobs**: `run_after` column gates eligibility.
4. **Rate-limited workers**: token bucket external to the queue logic.
5. **MySQL 8.0**: same `FOR UPDATE SKIP LOCKED` syntax. Pre-8.0: `GET_LOCK()` advisory locks or migrate.
6. **Oracle**: native `FOR UPDATE SKIP LOCKED` since 8i (1999).
7. **CockroachDB**: supports `SKIP LOCKED` as of 22.x.
8. **SQS-style**: lease pattern is literally what SQS does internally. If you want SQS semantics on Postgres, you've built it.
9. **`pg_try_advisory_lock`** alternative: one lock per worker-id pair; less elegant but workable. See `advisory-lock-use-cases.md`.
10. **Fan-out via outbox**: combine outbox pattern (`transactional-outbox.md`) with `SKIP LOCKED` for guaranteed delivery + parallel consumers.

## Revision notes

> **SKIP LOCKED job queue — 60 second recap**
> - **Primitive**: `SELECT ... FOR UPDATE SKIP LOCKED` (Postgres ≥9.5, MySQL ≥8.0).
> - **Semantics**: lock available rows; skip rows locked by other transactions.
> - **Without SKIP LOCKED**: workers serialise — wrong.
> - **CTE pattern**: SELECT+UPDATE in one statement; lock held briefly.
> - **Short jobs**: do everything in transaction; auto-rollback on crash.
> - **Long jobs**: lease pattern (`lease_expires_at`) + heartbeat + reaper.
> - **Partial index** `WHERE status='queued'` for fast queue scan.
> - **LISTEN/NOTIFY** for low-latency wake-up + polling fallback.
> - **One DB connection per worker**.
> - **Postgres can sustain 10k+ jobs/sec** with this; usually you don't need Redis.
> - **MySQL 8.0+ supports the same syntax.** Oracle since 8i.
> - **Trap**: vanilla `FOR UPDATE` (no SKIP) — serialises workers.
> - **Trap**: holding lock across a 30-minute job — use lease pattern instead.
