# Design an idempotency-key system for retryable API calls

## Source / Origin
- Stripe's public API design (https://stripe.com/docs/api/idempotent_requests) — the canonical reference.
- Standard payments / webhooks system-design question.
- Concept reference: `backend-data-prep/sql/06-transactions.md`.

## Why this question matters in interviews
Every payment, every webhook, every "submit order" button needs idempotency. The interview tests four things at once: (1) you understand that **transactions are not retry-safe by themselves**, (2) you can design the dedupe table, (3) you handle the in-flight-duplicate race, and (4) you reason about TTL/cleanup. Stripe's API is the gold standard; if you can describe its semantics and replicate the design on a whiteboard, you signal production-grade thinking.

## Concepts involved

### Syntax to lock in

```sql
-- The dedupe table
CREATE TABLE idempotency_keys (
  key             TEXT PRIMARY KEY,
  request_hash    TEXT NOT NULL,
  response_status INT,
  response_body   JSONB,
  state           TEXT NOT NULL CHECK (state IN ('in_progress', 'complete')),
  created_at      TIMESTAMPTZ DEFAULT now(),
  completed_at    TIMESTAMPTZ,
  expires_at      TIMESTAMPTZ NOT NULL  -- typical: now() + 24h
);
CREATE INDEX ON idempotency_keys (expires_at) WHERE state = 'complete';

-- Atomic claim
INSERT INTO idempotency_keys (key, request_hash, state, expires_at)
VALUES ($1, $2, 'in_progress', now() + interval '24 hours')
ON CONFLICT (key) DO NOTHING
RETURNING key;
```

### Edge cases / interview traps

1. **In-flight duplicate.** Client retries before the first request finished. The naive design returns "no record found, run again", causing double-execution. Fix: insert a row with `state='in_progress'` *first*; the second request sees it and waits or returns 409.
2. **Request body mismatch.** Same idempotency key with different payloads is a client bug. Store a hash of the request and 422 on mismatch — Stripe does this.
3. **Replay of stored response must include the original status code.** Storing only the body and returning 200 silently changes the contract.
4. **TTL.** Keep keys around 24h-7d typically. Too short = retries fail; too long = table bloat. Sweep with a periodic job, not a per-row TTL trigger.
5. **Idempotency key is not the same as a transaction.** A transaction is atomic; idempotency is retry-safe across separate transactions. You need both.
6. **The "happy path commits but the response is lost" race.** Network blip kills the response. Client retries. The key is in `state='complete'` — return the stored response. This is the most important case the design must handle.
7. **In-flight crash recovery.** If the first request crashes mid-processing, the key is stuck in `in_progress` forever. Add a stale-check: `state='in_progress' AND created_at < now() - 5 minutes` → treat as expired, allow retry.

## Mental Model

The **"deli counter ticket"** model. You walk in, take a ticket numbered 42. You hand it to the cashier with your order. If you panic and re-submit ticket 42 (because the cashier didn't say "got it"), the cashier checks her log: "ticket 42, already processed, here's your receipt again." If the ticket isn't in her log, she processes it and writes it down. The ticket itself is the idempotency key; the log is the dedupe table.

```
   Client                     Server                    DB
     │                          │                       │
     │ POST /charge             │                       │
     │ Idempotency-Key: 42      │                       │
     │ Body: {amount: 100}      │                       │
     ├─────────────────────────▶│                       │
     │                          │ INSERT ON CONFLICT    │
     │                          ├──────────────────────▶│ insert OK
     │                          │                       │
     │                          │ do work, commit       │
     │                          ├──────────────────────▶│ work + state=complete
     │                          │                       │
     │ ◀───────── 200 OK ───────│                       │
     │  (network blip; client doesn't get response)     │
     │                          │                       │
     │ POST /charge (retry)     │                       │
     │ Idempotency-Key: 42      │                       │
     ├─────────────────────────▶│                       │
     │                          │ INSERT ON CONFLICT    │
     │                          ├──────────────────────▶│ key exists, state=complete
     │                          │ load stored response  │
     │ ◀───────── 200 OK ───────│ (same as before)      │
```

## Why interviewers care

- It's the **payments / webhooks litmus test** — failure here means real money lost or duplicated.
- They want to see you **separate transactional atomicity from retry safety** — they're orthogonal guarantees.
- They probe edge cases: in-flight retry, body mismatch, crash recovery, TTL.
- They want a **production-shaped design**, not a toy "store the key and skip duplicates".

## Common beginner confusion

- "Transactions are idempotent." They're atomic, not idempotent. A retried transaction does the work twice unless dedupe is added.
- "UNIQUE constraint is enough." Almost — but you also need to *return the original response* on retry, not just reject the duplicate.
- "Use a UUID and trust the client." Clients regenerate keys on retry sometimes (bug); the server should validate the request hash matches.
- "Just check if the result exists." Race: two requests both see "no result", both run the work, both insert.

## Brute force approach

`UNIQUE(idempotency_key)` on the orders table. Returns "duplicate key" on retry. Problem: (a) error code instead of original response, (b) doesn't handle in-flight duplicates (key not yet inserted), (c) couples idempotency to business table.

## Optimal approach

Dedicated `idempotency_keys` table with three-state lifecycle:

1. **Claim** the key with `INSERT ON CONFLICT DO NOTHING` returning the inserted row.
2. **If claim succeeded**: do the work in the same transaction (or with the same key in the outbox), set `state='complete'`, store response.
3. **If claim failed**: look up the existing key; if `state='complete'`, replay the response; if `in_progress`, return 409 (or wait briefly); if stale `in_progress`, allow retry.

## Solution

```sql
-- Schema
CREATE TABLE idempotency_keys (
  key             TEXT PRIMARY KEY,
  request_hash    TEXT NOT NULL,
  response_status INT,
  response_body   JSONB,
  state           TEXT NOT NULL CHECK (state IN ('in_progress', 'complete')),
  created_at      TIMESTAMPTZ DEFAULT now(),
  completed_at    TIMESTAMPTZ,
  expires_at      TIMESTAMPTZ NOT NULL
);

-- Cleanup job (run hourly)
DELETE FROM idempotency_keys WHERE expires_at < now();
```

Node handler:

```javascript
const crypto = require('crypto');

async function withIdempotency(req, res, doWork) {
  const key = req.headers['idempotency-key'];
  if (!key) return res.status(400).json({ error: 'missing_idempotency_key' });

  const reqHash = crypto.createHash('sha256')
    .update(JSON.stringify(req.body)).digest('hex');

  // 1. Try to claim
  const claim = await db.query(
    `INSERT INTO idempotency_keys (key, request_hash, state, expires_at)
     VALUES ($1, $2, 'in_progress', now() + interval '24 hours')
     ON CONFLICT (key) DO NOTHING
     RETURNING key`,
    [key, reqHash]
  );

  if (claim.rows.length === 1) {
    // Claim succeeded — do the work
    try {
      const { status, body } = await doWork();
      await db.query(
        `UPDATE idempotency_keys
         SET state='complete', response_status=$2, response_body=$3, completed_at=now()
         WHERE key=$1`,
        [key, status, body]
      );
      return res.status(status).json(body);
    } catch (err) {
      // Mark complete with error response so the retry sees it
      await db.query(
        `UPDATE idempotency_keys
         SET state='complete', response_status=500,
             response_body=$2, completed_at=now()
         WHERE key=$1`,
        [key, { error: err.message }]
      );
      throw err;
    }
  }

  // 2. Claim failed → key already exists. Inspect.
  const existing = (await db.query(
    `SELECT request_hash, state, response_status, response_body, created_at
     FROM idempotency_keys WHERE key=$1`,
    [key]
  )).rows[0];

  if (existing.request_hash !== reqHash) {
    return res.status(422).json({ error: 'idempotency_key_request_mismatch' });
  }

  if (existing.state === 'complete') {
    // Replay stored response
    return res.status(existing.response_status).json(existing.response_body);
  }

  // in_progress: another worker is doing the work
  const ageMs = Date.now() - new Date(existing.created_at).getTime();
  if (ageMs > 5 * 60 * 1000) {
    // Stale: previous worker crashed. Mark and retry once.
    // (In production: usually return 409 and let the client retry after a moment.)
    return res.status(409).json({ error: 'previous_attempt_stale_retry' });
  }
  return res.status(409).json({ error: 'request_in_progress' });
}
```

Wire it up:

```javascript
app.post('/charge', (req, res) =>
  withIdempotency(req, res, async () => {
    const { amount, accountId } = req.body;
    // ... do the charge inside a DB transaction ...
    return { status: 200, body: { id: chargeId } };
  })
);
```

## Step-by-step dry run

T1/T2 timeline — second request after first completes (the common case):

```
time →

T1 (first POST):
  |--claim key=42 OK (state=in_progress)--|--do work--|--commit + state=complete--|--HTTP 200--|
                                                                                      ^ network blip; client gets timeout

T2 (client retries with key=42):
                                                                                       |--claim key=42 FAILS--|--lookup: state=complete--|--replay response--|--HTTP 200--|

DB state: charge happened once. Two API calls. One charge.
```

In-flight duplicate (worst race):

```
T1 (first POST):
  |--claim key=42 OK (state=in_progress)--|--charging.....................longer than usual.......|--commit--|--HTTP 200--|

T2 (client retries impatiently):
                                            |--claim key=42 FAILS--|--lookup: state=in_progress, age=2s--|--HTTP 409 'in progress'--|

T2 client: receives 409, waits and retries. By then T1 finished:
                                                                                                            |--claim FAILS--|--state=complete--|--replay 200--|
```

Crashed in-progress:

```
T1: |--claim key=42 OK--|--start work--|--PROCESS CRASH--|
                                          ^ key stuck in_progress forever?

T2 (client retries after 10 minutes):
                                                          |--claim FAILS--|--state=in_progress, age=10min > 5min--|--HTTP 409 'stale, retry'--|
T2 retries:
                                                                                                                    |--admin tool clears stale key, T2 retries successfully--|
-- Or: cleanup job sweeps in_progress rows older than 5min and deletes/marks them.
```

## How to think aloud in the interview

> "Idempotency is about retry safety, not atomicity. A transaction guarantees all-or-nothing for one execution; idempotency guarantees same-outcome across N executions of the same logical request. The Stripe pattern: client generates a UUID `Idempotency-Key`, sends in a header. Server has a dedupe table:
>
> 1. Try to INSERT (key, request_hash, state='in_progress') with ON CONFLICT DO NOTHING.
> 2. If you got the row, do the work and UPDATE the row to state='complete' with the stored response.
> 3. If the row already existed: if state='complete', replay the stored response; if 'in_progress' and fresh, 409; if stale (>5 min), maybe allow retry.
>
> Three subtleties: (a) hash the request body so a client reusing the same key with different params gets 422; (b) TTL the rows (24h-7d) and sweep; (c) the work itself should be transactional so a crash mid-work doesn't leak partial state — but that's separate from idempotency. The two are complementary."

## Important takeaways

- Idempotency ≠ atomicity. Transactions are atomic for one run; idempotency is retry-safe across runs.
- Dedupe table with `state ∈ {in_progress, complete}` is the canonical design.
- `INSERT ... ON CONFLICT DO NOTHING RETURNING` is the atomic claim primitive.
- Store request_hash to detect body mismatch (Stripe behaviour).
- Store status code + body for accurate replay.
- TTL + sweep job to bound table size.
- Handle in-flight duplicates (state='in_progress') and stale claims explicitly.

## Variants

1. **Webhook ingestion** — webhook providers send `Idempotency-Key`-style ID; same table, same pattern.
2. **Pure DB-side** — combine the idempotency_key into the business table as a UNIQUE column. Loses the response-replay feature.
3. **Multi-step workflows** — Stripe uses idempotency keys *per step* of a workflow; one key per HTTP request.
4. **Distributed across services** — idempotency key flows through messages; each service has its own dedupe table.
5. **TTL strategies** — Stripe: 24h. Some teams: 7d. The trade-off is table size vs retry tolerance.
6. **Redis for the in-progress lock** — speeds up the claim path; still need durable storage for the complete state.

## Revision notes

> **idempotency-key-design — 60 second recap**
> - Client sends `Idempotency-Key` header (UUID).
> - Server: dedupe table (key, request_hash, state, response_status, response_body, expires_at).
> - Atomic claim: `INSERT ... ON CONFLICT DO NOTHING RETURNING`.
> - State machine: in_progress → complete; on retry, replay stored response.
> - Hash request body; 422 on mismatch (Stripe behaviour).
> - TTL 24h-7d; sweep with hourly job.
> - In-progress duplicate → 409. Stale in_progress (>5 min) → admin cleanup or allow retry.
> - Idempotency ≠ atomicity. You need both: transaction for the work, key for the retry safety.
