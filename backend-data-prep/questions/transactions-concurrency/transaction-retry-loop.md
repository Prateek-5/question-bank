# Transaction Retry Loop — Serializable Failures, Idempotency, Exponential Backoff

## Source / Origin
- Postgres SSI (Serializable Snapshot Isolation), 9.1+. Raises `40001 serialization_failure` on detected rw-cycles.
- CockroachDB, YugabyteDB, FoundationDB, Spanner all expose serializable transactions with retryable conflicts.
- MySQL InnoDB: returns `1213` (deadlock) and `1205` (lock wait timeout) — semantically similar, requires retry.
- Companion docs: `transactions-concurrency/write-skew-scenario.md`, `transactions-concurrency/optimistic-vs-pessimistic-decision.md`, `transactions-concurrency/idempotency-key-design.md`.
- Interview prompt: "You're using SERIALIZABLE on Postgres. A retryable error pops up. Show me the retry loop you'd write — and what should *never* be inside it."

## Why this question matters in interviews
Retry loops sound trivial until you write a wrong one in production and double-charge a customer. This question is the **convergence point** of three senior topics: isolation levels (why does the retry exist?), idempotency (what's safe to retry?), and backoff (how do you not melt the DB?). Interviewers want to see (a) you know which SQLSTATEs are retryable, (b) you know what goes *inside* the transaction vs *outside*, (c) you can correctly implement exponential backoff with jitter, (d) you mention idempotency keys for any external side-effects, and (e) you cap retries. Most candidates write a `try/except: continue` loop and call it done. The senior writes the version that won't take down the DB.

## Concepts involved

### Syntax to lock in

The canonical retry skeleton:
```python
import time, random

RETRYABLE = {"40001", "40P01"}   # serialization_failure, deadlock_detected

def with_serializable_retry(work, max_attempts=5, base_ms=20, cap_ms=2000):
    for attempt in range(max_attempts):
        try:
            with conn.transaction(isolation_level="SERIALIZABLE"):
                return work(conn)            # <-- transactional work here
        except psycopg2.OperationalError as e:
            if e.pgcode not in RETRYABLE or attempt == max_attempts - 1:
                raise
            backoff_ms = min(cap_ms, base_ms * (2 ** attempt))
            sleep_ms = random.uniform(0, backoff_ms)   # full jitter
            time.sleep(sleep_ms / 1000)
    raise RuntimeError("unreachable")
```

The classic mistake — what goes *inside* the loop:

```python
# WRONG
for attempt in range(5):
    with conn.transaction():
        charge_card(amount)         # ← external side-effect inside retried tx
        db.insert_order(...)
```

If `db.insert_order` raises `40001`, you retry, you charge the card *again*. Double charge.

Correct shape:

```python
# RIGHT
idempotency_key = uuid.uuid4()
charge_result = charge_card_idempotent(amount, idempotency_key)   # outside loop OR idempotent

with_serializable_retry(lambda c: db.insert_order(c, charge_result))
```

Only **idempotent or transactional** operations belong inside the retry. External side-effects either go outside the loop or use an idempotency key.

### Edge cases / interview traps

1. **Retry the *whole* transaction, not just the failed statement.** A `40001` invalidates the entire snapshot. You cannot continue from the failure point.
2. **Catch only retryable SQLSTATEs.** A `23505 unique_violation` is *not* retryable — retrying gets the same error. A `42P01 undefined_table` is also not retryable. Whitelist `40001` (serialization), `40P01` (deadlock); maybe `08006 connection_failure` with caveats.
3. **External side-effects don't belong inside a retried transaction.** Sending an email, charging a card, calling a remote API — these don't roll back. Put them after the transaction succeeds, or wrap them in idempotency keys so retrying is safe.
4. **Random jitter is mandatory, not optional.** Without jitter, all retries from a thundering herd collide on the same retry slot. With jitter (full jitter or decorrelated jitter), retries spread out and conflicts decay exponentially.
5. **Cap the retries.** Infinite retry = infinite latency = upstream timeout cascade. Typical cap: 3-5 attempts.
6. **Cap the backoff.** `2 ** 30 ms` is 12 days. Cap at a few seconds.
7. **"Full jitter" vs "exponential":** full jitter samples uniformly from `[0, exponential_cap]`. Lower mean wait but same worst-case. Better than fixed exponential in practice (AWS Architecture blog, 2015).
8. **MySQL's `1213` (deadlock) and `1205` (lock wait timeout)** are equivalents of `40P01` / `40001` for retry purposes. Different error codes, same loop shape.
9. **Postgres `40001` from SSI** = "the conflict graph has a cycle; aborting one". MySQL deadlock = "two transactions waiting on each other; aborting one". Different mechanisms, same retry treatment.
10. **Read-only transactions don't get `40001` in Postgres**. Only writers can lose a serialization conflict. (Caveat: PG 14+ tracks reads too; rare cases.)
11. **Don't retry in a `BEGIN; ... COMMIT;` script** — once the transaction is aborted by `40001`, every subsequent statement returns `25P02`. You must explicitly `ROLLBACK` and start a new transaction.
12. **The retry must restart from the application-level boundary.** Inside the retry, re-read all inputs you previously fetched; they may have been stale.
13. **Don't log retries as errors at the same level.** A `40001` is expected behaviour under SSI. Log at INFO/DEBUG with a counter. Only `max_attempts_exhausted` should be ERROR.
14. **Connection pool interaction**: returning a connection that was in a failed transaction to the pool requires `ROLLBACK` first; many pool libs handle this automatically.

## Mental Model

### The retry triangle

```
                Isolation level
                   chosen
                      │
                      ▼
        ┌─────────────┴─────────────┐
        │ Serializable / repeatable  │
        │ → some transactions abort │
        │   with retryable errors   │
        └─────────────┬─────────────┘
                      │
        ┌─────────────┴─────────────┐
        │       Retry loop          │
        │ - whitelist SQLSTATEs     │
        │ - exponential + jitter    │
        │ - cap attempts            │
        │ - cap backoff             │
        └─────────────┬─────────────┘
                      │
        ┌─────────────┴─────────────┐
        │      Idempotency          │
        │ - external calls outside  │
        │ - or idempotency keys      │
        └───────────────────────────┘

   Each corner is necessary. Miss any one → bug.
```

### Why backoff jitter matters

```
Without jitter (all retry at the same instant):

  T1, T2, T3, T4: all abort at t=0
                  retry at t=10ms, all collide again
                  retry at t=30ms, all collide again
                  retry at t=70ms, all collide again
   → cycle of synchronised stampedes

With full jitter:

  T1: sleep uniformly in [0, 10ms]   → wake at 4ms
  T2: sleep uniformly in [0, 10ms]   → wake at 7ms
  T3: sleep uniformly in [0, 10ms]   → wake at 2ms
  T4: sleep uniformly in [0, 10ms]   → wake at 9ms
  → spread out; first to retry succeeds; others find clear runway
```

The math: with N transactions and jitter window W, expected number of collisions per slot decays geometrically. Without jitter, all transactions converge.

### What's safe inside vs outside the retry

```
Inside the retry (transactional, reversible):
  - SQL reads, writes, locks
  - Application-level decisions based on those reads
  - Computation
  - Idempotent calls (with idempotency keys)

Outside the retry:
  - External API calls (payments, emails, push)
  - File I/O, queue publishes
  - Non-transactional cache writes
  - User-facing notifications

If you must call externally from inside, use an idempotency key
+ design the external service to dedupe by key.
```

## Why interviewers care

- Maps to **real production**: serializable isolation, optimistic concurrency, OCC retry loops, message-queue redelivery — all the same retry pattern.
- It surfaces **correctness understanding** (idempotency) and **throughput understanding** (backoff/jitter).
- It distinguishes "I read the docs" from "I've debugged a thundering-herd-after-retry incident".
- It naturally pivots to broader topics: idempotency key design, exactly-once delivery, saga retries.

## Common beginner confusion

- **"Retry every error."** No — only retryable ones. Constraint violations, missing tables, syntax errors will repeat forever.
- **"Loop without backoff."** Crushes the DB; sustains the contention; never resolves.
- **"Fixed sleep is fine."** Synchronises herds; same problem.
- **"Email send inside the transaction is fine — the transaction will roll back."** SMTP doesn't roll back. Once sent, it's sent.
- **"Set `max_attempts = ∞`."** Means a user request can hang forever. Pick 3-5.
- **"Idempotency means the operation is naturally repeatable."** Idempotency is a property of the operation as composed with a key — `charge_card(amount, key)` is idempotent if the payment provider dedupes by key. A naive `charge_card(amount)` is not.
- **"Retry only on `40001`."** Also `40P01` (deadlock_detected) on Postgres, `1213`/`1205` on MySQL, and arguably some transient connection errors with extra care.
- **"The same transaction handle can be retried."** No — start a fresh transaction; close the old one.
- **"`40001` is a bug."** It's the *contract* of SERIALIZABLE under contention. You must handle it.
- **"Backoff means linear ramp-up."** No — exponential with jitter. Linear under sustained contention still synchronises.

## Brute force approach

```python
# Anti-pattern: catch-all retry with fixed sleep
while True:
    try:
        do_transaction()
        break
    except Exception:
        time.sleep(0.1)
```

Three things wrong: (1) retries every error including unretryable ones; (2) infinite attempts; (3) no jitter → herd synchronisation. Use this code and you'll write the postmortem yourself.

## Optimal approach

### Decision: when to use a retry loop

- **Postgres SSI (SERIALIZABLE)**: mandatory.
- **Postgres RR (REPEATABLE READ)**: can also raise `40001` on lost updates. Retry recommended.
- **Postgres OCC patterns**: `UPDATE ... WHERE version = $1` — handle the "0 rows updated" case as a retry trigger.
- **MySQL InnoDB**: `1213` deadlock retry mandatory under contention. `1205` lock wait timeout often retried, with caveats.
- **CockroachDB / Spanner / FoundationDB**: native serializable; retryable errors are part of the API contract.

### The skeleton you should have memorised

```python
import random, time, logging
import psycopg2

RETRYABLE = {"40001", "40P01"}     # PG: serialization_failure, deadlock_detected

def run_serializable(work_fn, *,
                     max_attempts=5,
                     base_ms=20,
                     cap_ms=2000,
                     conn_factory=None):
    """
    Run `work_fn(conn)` inside a SERIALIZABLE transaction.
    Retries on whitelisted SQLSTATEs with exponential backoff + full jitter.
    Idempotent operations only. External side-effects must be handled outside
    or behind an idempotency key.
    """
    last_exc = None
    for attempt in range(max_attempts):
        conn = conn_factory()
        try:
            conn.set_session(isolation_level="SERIALIZABLE", autocommit=False)
            result = work_fn(conn)
            conn.commit()
            if attempt > 0:
                logging.info("serializable_retry.success",
                             extra={"attempt": attempt})
            return result
        except psycopg2.OperationalError as e:
            conn.rollback()
            code = getattr(e, "pgcode", None)
            if code not in RETRYABLE:
                raise
            last_exc = e
            if attempt == max_attempts - 1:
                logging.error("serializable_retry.exhausted",
                              extra={"attempts": max_attempts})
                raise
            backoff_ms = min(cap_ms, base_ms * (2 ** attempt))
            sleep_ms = random.uniform(0, backoff_ms)
            logging.debug("serializable_retry.backoff",
                          extra={"attempt": attempt,
                                 "sleep_ms": int(sleep_ms),
                                 "code": code})
            time.sleep(sleep_ms / 1000)
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    raise last_exc
```

### What to pull out of the transaction

```python
def place_order(order_data, payment_token):
    # 1. PRECONDITION reads (cheap; can be inside or outside)
    user = db.get_user(order_data.user_id)
    if not user.active:
        raise InvalidUser()

    # 2. EXTERNAL CALL with idempotency key (outside retry, before tx)
    idempotency_key = generate_idempotency_key(order_data)
    charge = payments.charge(
        amount=order_data.total,
        token=payment_token,
        idempotency_key=idempotency_key,
    )

    # 3. TRANSACTIONAL WORK (inside retry)
    def tx_work(conn):
        with conn.cursor() as cur:
            cur.execute("INSERT INTO orders ... RETURNING id", (...))
            order_id = cur.fetchone()[0]
            cur.execute("UPDATE inventory SET qty = qty - %s WHERE sku = %s",
                        (order_data.qty, order_data.sku))
            cur.execute("INSERT INTO payments(order_id, charge_id, ...) VALUES ...",
                        (order_id, charge.id))
            return order_id

    order_id = run_serializable(tx_work)

    # 4. POST-COMMIT SIDE-EFFECTS (outside, after success)
    event_bus.publish("OrderPlaced", {"order_id": order_id})
    return order_id
```

Two payment-related charges + a transaction retry now cannot double-charge: the idempotency key dedupes on the payment provider's side. If the transaction fails permanently, the charge is reversed (refund) as a compensating action.

## Solution

### Full jitter (recommended default)

```python
def backoff_full_jitter(attempt, base_ms=20, cap_ms=2000):
    """AWS-recommended full jitter strategy."""
    return random.uniform(0, min(cap_ms, base_ms * (2 ** attempt)))
```

### Decorrelated jitter (alternative, slightly lower variance)

```python
class DecorrelatedJitter:
    def __init__(self, base_ms=20, cap_ms=2000):
        self.base = base_ms
        self.cap = cap_ms
        self.last = base_ms

    def next(self):
        wait = random.uniform(self.base, self.last * 3)
        self.last = min(self.cap, wait)
        return self.last
```

### Node.js equivalent

```javascript
const RETRYABLE = new Set(['40001', '40P01']);

async function withSerializableRetry(workFn, {
  maxAttempts = 5,
  baseMs = 20,
  capMs = 2000,
  poolFn,
} = {}) {
  let lastErr;
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const client = await poolFn();
    try {
      await client.query('BEGIN ISOLATION LEVEL SERIALIZABLE');
      const result = await workFn(client);
      await client.query('COMMIT');
      return result;
    } catch (e) {
      await client.query('ROLLBACK').catch(() => {});
      if (!RETRYABLE.has(e.code) || attempt === maxAttempts - 1) {
        throw e;
      }
      lastErr = e;
      const sleepMs = Math.random() * Math.min(capMs, baseMs * (2 ** attempt));
      await new Promise(r => setTimeout(r, sleepMs));
    } finally {
      client.release();
    }
  }
  throw lastErr;
}
```

### MySQL flavour

```python
MYSQL_RETRYABLE = {1213, 1205}   # deadlock, lock wait timeout

def run_mysql_with_retry(work_fn, ...):
    for attempt in range(max_attempts):
        try:
            with conn:
                conn.execute("START TRANSACTION")
                result = work_fn(conn)
                conn.execute("COMMIT")
                return result
        except pymysql.err.OperationalError as e:
            conn.rollback()
            errno = e.args[0]
            if errno not in MYSQL_RETRYABLE or attempt == max_attempts - 1:
                raise
            time.sleep(random.uniform(0, min(2000, 20 * (2 ** attempt))) / 1000)
```

## Step-by-step dry run

Scenario: SSI on Postgres. Two transactions T1 and T2 both updating the same invariant (e.g., doctor on-call). Both reach COMMIT; SSI aborts T2 with `40001`.

```
T=0   T1 BEGIN SER; SELECT ...; UPDATE ...; ...
T=0   T2 BEGIN SER; SELECT ...; UPDATE ...; ...
T=10  T1 COMMIT  → success
T=11  T2 COMMIT  → ERROR 40001 serialization_failure

T2 retry loop kicks in:

attempt=0:
  caught 40001
  backoff_ms = min(2000, 20 * 2^0) = 20
  sleep = random.uniform(0, 20) = e.g. 13ms
  sleep 13ms

attempt=1:
  T2 BEGIN SER (fresh transaction)
  T2 SELECT ... (sees T1's committed state — fresh data!)
  T2 application-level check: "given current state, do we still want this write?"
        → in the doctor on-call example, count is now 1; T2's request to go off-duty rejected.
  T2 returns "cannot go off-duty" to user. SUCCESS (different outcome).

If T2 had retried without re-reading the state, it would have used the stale
"two doctors on call" decision and re-raised 40001 forever.
The retry semantically means "redo the whole logic against fresh data".
```

Contended scenario: 100 concurrent transactions on hot row.

```
attempt=0: 60 succeed, 40 hit 40001
attempt=1 (after jitter): jitter spreads them; another 30 succeed, 10 hit 40001
attempt=2: 8 succeed, 2 hit 40001
attempt=3: 2 succeed
Total: 100 succeed; aggregate latency p99 = ~300ms.

Without jitter:
attempt=0: 60 succeed, 40 fail
attempt=1: all 40 retry at t=20ms; only ~24 succeed (same collision pattern)
attempt=2: 16 retry; ~10 succeed
...
This decays slower because herd is preserved.
```

External side-effect dry run (double-charge bug):

```
attempt=0:
  BEGIN
  charge_card($100)  → succeeds, $100 charged
  INSERT order      → ERROR 40001
  ROLLBACK

attempt=1:
  BEGIN
  charge_card($100)  → succeeds, $100 charged AGAIN
                       (no idempotency key, no dedup)
  INSERT order      → succeeds
  COMMIT

Final: customer charged $200; record of one order.
```

With idempotency key:

```
attempt=0:
  External: charge_card($100, key="xyz") → charged $100
  BEGIN
  INSERT order(charge_id=...)            → ERROR 40001
  ROLLBACK

attempt=1:
  BEGIN
  INSERT order(charge_id=...)            → succeeds
  COMMIT
  (charge was outside the retry; no second call)
```

Or with the call inside but idempotent:
```
attempt=1:
  BEGIN
  charge_card($100, key="xyz") → provider sees same key, returns prior result, no second charge
  INSERT order                  → succeeds
  COMMIT
```

## How to think aloud in the interview

> "Three parts to this loop, in order of importance.
>
> **Part 1 — which SQLSTATEs to retry.**
> Whitelist, not blacklist. On Postgres: `40001` (serialization_failure), `40P01` (deadlock_detected). On MySQL: `1213` (deadlock), `1205` (lock wait timeout). Anything else — unique violation, syntax error, missing column — is not retryable; retrying will repeat the same error.
>
> **Part 2 — backoff.**
> Exponential with full jitter. `sleep = uniform(0, min(cap, base * 2^attempt))`. Three reasons:
> - Exponential: gives more time as contention persists.
> - Jitter: prevents thundering-herd synchronisation. Without jitter, all retries collide on the same time slot.
> - Cap: prevents 12-day sleeps from `2 ** 30`.
>
> Cap attempts at 3-5; cap backoff at 1-2 seconds.
>
> **Part 3 — what's inside the loop.**
> Only transactional, reversible work. No emails, no payment charges, no queue publishes inside the retried transaction — those don't roll back. Either move them outside (post-commit) or wrap them in idempotency keys so retrying is safe.
>
> The most common bug here is calling Stripe inside the retry. Transaction fails, retries, charges the card again. Idempotency key on the Stripe call fixes it.
>
> One more nuance: when the retry runs again, re-read all inputs you read the first time. The whole point of the retry is that the database state changed; the application logic must re-evaluate. If you cached intermediate values from the first attempt and use them on the retry, you've defeated the retry.
>
> For logging: `40001` is *expected* under SSI, not an error. Log at INFO with a metric. Only `max_attempts_exhausted` should be a logged error."

## Important takeaways

- **Whitelist retryable SQLSTATEs**: PG `40001`/`40P01`, MySQL `1213`/`1205`.
- **Exponential backoff + full jitter** is the canonical strategy.
- **Cap attempts (3-5) and cap backoff (1-2s)**; never infinite.
- **External side-effects outside the loop** or behind idempotency keys.
- **Retry the *whole* transaction**, not the failed statement.
- **Re-read inputs on each attempt** — the world changed; old decisions are stale.
- **`ROLLBACK` between attempts** — a fresh transaction is required.
- **Log retries at INFO/DEBUG** with metrics; only exhaustion is ERROR.
- **Connection pool**: ensure failed connections are returned cleanly (most pools handle).
- **MySQL deadlocks and Postgres SSI conflicts** use the same loop shape; different error codes.
- **OCC patterns** (version-column writes) use a "0 rows updated → retry" trigger; same retry loop, different signal.

## Variants

1. **Decorrelated jitter** — alternative to full jitter; can have slightly lower latency variance.
2. **Adaptive concurrency** — track retry rate; if high, reduce concurrent attempts upstream rather than retry harder.
3. **OCC explicit version column** — `UPDATE ... SET version = version + 1 WHERE id = $1 AND version = $2` — if 0 rows, retry. See `optimistic-vs-pessimistic-decision.md`.
4. **Saga retry** — retry an individual saga step, not the whole saga. Each step has its own idempotency key.
5. **MySQL deadlock retries** — same loop, error codes 1213 (deadlock_detected) and 1205 (lock_wait_timeout_exceeded).
6. **CockroachDB**: client libraries provide built-in retry primitives (`crdb.execute_with_retry`). Use them.
7. **Spanner**: SDK auto-retries on `ABORTED`. Configure the limit.
8. **Connection pool & retries**: pools like HikariCP, pgbouncer can interact with retries; ensure connection state is reset on rollback.
9. **Idempotency key design**: see `idempotency-key-design.md`. Keys must be: client-generated, unique per logical operation, deterministic across retries, scoped to a request.
10. **Circuit breaker around the retry**: if the retry rate exceeds X, open the breaker and fail fast for a window. Prevents cascading retry storms.

## Revision notes

> **transaction retry loop — 60 second recap**
> - **Why**: SERIALIZABLE / SSI / OCC / deadlocks raise retryable errors.
> - **Whitelist SQLSTATEs**: PG `40001`, `40P01`; MySQL `1213`, `1205`.
> - **Exponential backoff + full jitter**: `uniform(0, min(cap, base * 2^attempt))`.
> - **Cap attempts (3-5)** and **cap backoff (1-2s)**.
> - **ROLLBACK and start fresh transaction** each attempt.
> - **Re-read inputs**; old data is stale.
> - **External side-effects outside the loop** OR use idempotency keys.
> - **Trap**: payment call inside retry → double charge. Use idempotency keys.
> - **Trap**: no jitter → thundering herd synchronisation.
> - **Trap**: catch-all `except` → retries unretryable errors forever.
> - **Trap**: infinite attempts → upstream timeouts cascade.
> - **Log retries at INFO/DEBUG**; only exhaustion is ERROR.
