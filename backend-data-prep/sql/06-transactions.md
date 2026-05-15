# Transactions

## Why this matters in backend interviews

- **Transactions are the most fundamental correctness mechanism** in backend systems. Every payment, every booking, every transfer relies on them.
- **System design** rounds frequently ask: "how do you ensure money isn't lost between accounts?" — the answer always starts with transactions.
- **Machine coding**: you'll be asked to write SQL with `BEGIN/COMMIT` or to wrap ORM operations in `transaction()`.
- **Debugging**: half the data-corruption incidents you'll see in production are missing-transaction bugs.

This file pairs tightly with `07-isolation-levels.md` and `08-locks-concurrency.md`.

---

## Core concepts

### ACID

| | Meaning |
|---|---|
| **A**tomicity | All operations succeed or none do. No partial application. |
| **C**onsistency | The database moves from one valid state to another. Constraints (FK, CHECK, UNIQUE) hold at commit. |
| **I**solation | Concurrent transactions don't interfere. (Strength depends on isolation level — see file 07.) |
| **D**urability | Once committed, the change survives crashes, power loss, etc. (Via write-ahead log, fsync.) |

Most interviewers test A and I most heavily.

### Transaction lifecycle

```
BEGIN;
  -- statements
  -- read your own writes (always)
COMMIT;  -- flush WAL, durable
-- or
ROLLBACK;  -- undo
```

In Postgres, a transaction without `BEGIN` is implicit (autocommit per statement).

### What lives inside a transaction

- Reads see a consistent snapshot (the strictness depends on isolation level)
- Writes are buffered (the WAL records them, but the heap may or may not be flushed)
- Locks are acquired and held until commit/rollback
- Triggers fire as part of the transaction
- Sequences (auto-increment) are non-transactional in Postgres (gaps on rollback are expected)

### Read-your-own-writes

Within the same transaction, you always see the rows you just modified. Other transactions see them only after you commit (and only if their snapshot allows).

### Savepoints (nested transactions)

```sql
BEGIN;
  INSERT INTO orders ...;
  SAVEPOINT before_items;
  INSERT INTO order_items ...;
  -- If this fails:
  ROLLBACK TO SAVEPOINT before_items;
  -- Continue
COMMIT;
```

Useful for batch processing where individual sub-operations may fail without aborting the whole batch.

ORMs implement "nested transactions" as savepoints under the hood.

### Two-phase commit (2PC)

For distributed transactions across multiple databases:
1. **Prepare**: each participant writes the change to disk, locks resources, replies "ready"
2. **Commit**: coordinator tells all participants to commit
3. If any participant fails to prepare → rollback all

Problems:
- Blocks if coordinator dies after prepare → resources locked indefinitely
- Slow (network round-trips, fsyncs)
- In microservices, **avoided** in favor of sagas and outbox patterns

### Sagas (compensating transactions)

Long-running multi-service workflow modeled as a sequence of local transactions:

```
Booking saga:
  1. ReserveSeat (in Inventory service)
  2. ChargePayment (in Payments service)
  3. SendConfirmation (in Notifications service)

If step 2 fails → compensate: ReleaseSeat
If step 3 fails → compensate: RefundPayment, ReleaseSeat
```

Two flavors:
- **Choreography**: services react to events
- **Orchestration**: a central orchestrator (Temporal, Camunda) drives steps

Saga is **eventually consistent**, not isolated. The window between steps allows readers to see "in-flight" states.

### Idempotency

A retry-safe operation produces the same result whether called once or N times.

Implementations:
- **Idempotency key**: client generates a UUID; server stores `(key, response)`; duplicate calls return cached response.
- **Unique constraints**: `INSERT … ON CONFLICT DO NOTHING` for natural keys.
- **State machines**: only transition forward (PENDING → SUCCESS, never SUCCESS → PENDING).

Critical for payments, webhooks, retries.

### Outbox pattern (transactional messaging)

Problem: "I want to update the DB and publish a Kafka event atomically."

The naive way:
```python
db.commit()
kafka.publish(event)  # might fail; now DB is updated but no event
```

Outbox:
```sql
BEGIN;
  UPDATE orders SET status='PAID' WHERE id = 1;
  INSERT INTO outbox (topic, payload) VALUES ('order.paid', '{...}');
COMMIT;
```

A separate worker (or CDC like Debezium) reads `outbox` and publishes to Kafka. The DB write and the "intent to publish" are atomic.

Variants:
- **Polling outbox**: worker polls the table
- **CDC outbox**: stream WAL → Kafka via Debezium

### Common misconceptions

- "Transactions guarantee that two operations are serialized" — only under `SERIALIZABLE` isolation (file 07)
- "ORM `transaction()` is automatic" — it wraps the block, but doesn't promise correctness with concurrency
- "Autocommit is fine for everything" — multi-statement business logic almost always needs explicit transactions
- "Rollback is free" — it isn't; it dirties the snapshot, may leave bloat, and competing transactions may have waited
- "2PC is the answer to distributed transactions" — it's the textbook answer; real systems use sagas + outbox

### Interview traps

1. **"How do you transfer money between two accounts atomically?"** — must `BEGIN`, `UPDATE … debit`, `UPDATE … credit` (or one statement with CTE), `COMMIT`. Use `SELECT … FOR UPDATE` to prevent concurrent debit on insufficient balance.
2. **"What if the server crashes mid-transaction?"** — uncommitted changes are rolled back via WAL on restart. WAL = durability mechanism.
3. **"Difference between A and D?"** — Atomicity = all-or-nothing; Durability = once-committed survives crash.
4. **Saga rollback ≠ DB rollback** — sagas use compensating actions, not rollback. The intermediate state was visible.
5. **"Why not just lock everything?"** — throughput tanks; deadlocks; latency spikes.

---

## Real examples

### Payments — money transfer

```sql
-- INSIDE A TRANSACTION
BEGIN;

-- Lock both account rows to prevent concurrent operations
SELECT balance_cents FROM accounts WHERE id = $from FOR UPDATE;
SELECT balance_cents FROM accounts WHERE id = $to   FOR UPDATE;

-- Validate sufficient balance
UPDATE accounts SET balance_cents = balance_cents - $amount
  WHERE id = $from AND balance_cents >= $amount;
-- If 0 rows affected → ROLLBACK and error

UPDATE accounts SET balance_cents = balance_cents + $amount
  WHERE id = $to;

INSERT INTO transactions (idempotency_key, from_account, to_account, amount_cents, status)
VALUES ($key, $from, $to, $amount, 'SUCCESS')
ON CONFLICT (idempotency_key) DO NOTHING;

COMMIT;
```

Key points:
- **Lock both rows**: prevents lost-update anomaly
- **Always lock in the same order** (e.g., `LEAST(from,to) FOR UPDATE`) to prevent deadlock
- **Idempotency key** on the transaction record
- **Conditional update** for balance check inside the UPDATE

### E-commerce — place order with inventory reservation

```sql
BEGIN;
  -- Reserve inventory atomically
  UPDATE inventory
  SET qty_reserved = qty_reserved + 2
  WHERE product_id = 42 AND qty_on_hand - qty_reserved >= 2;
  -- If 0 rows affected: not enough stock → ROLLBACK

  INSERT INTO orders (user_id, status) VALUES ($1, 'PLACED') RETURNING id INTO _order_id;
  INSERT INTO order_items (order_id, product_id, quantity) VALUES (_order_id, 42, 2);

  INSERT INTO outbox (topic, payload) VALUES ('order.placed', json_build_object('order_id', _order_id));
COMMIT;
```

Note: the `outbox` row enables atomic event publication.

### Chat — mark messages as read

```sql
BEGIN;
  UPDATE conversation_participants
  SET last_read_at = NOW()
  WHERE conv_id = $1 AND user_id = $2;

  INSERT INTO read_receipts (conv_id, user_id, ts) VALUES ($1, $2, NOW())
  ON CONFLICT (conv_id, user_id) DO UPDATE SET ts = EXCLUDED.ts;
COMMIT;
```

### Idempotent webhook ingestion

```sql
INSERT INTO webhook_events (external_id, payload, received_at)
VALUES ($1, $2, NOW())
ON CONFLICT (external_id) DO NOTHING
RETURNING id;
-- If RETURNING is empty → duplicate; skip processing
```

---

## Common interview questions

1. Explain ACID.
2. How would you atomically transfer $100 between two accounts?
3. What happens to uncommitted changes on a crash?
4. What is a savepoint?
5. Two-phase commit — when, why, and why not?
6. What is the outbox pattern?
7. What is a saga? Trade-offs?
8. What is idempotency? How do you implement it?
9. Difference between `INSERT ON CONFLICT` and explicit lookup?
10. What's a lost update? How do you prevent it?
11. How do you handle a failure between updating the DB and publishing a Kafka event?
12. What's the difference between optimistic and pessimistic concurrency control?

---

## Detailed answers

### 1. ACID
See table above. Drive home with the money transfer example: A = both updates or none; C = constraints hold; I = no one sees the half-transfer; D = once committed, it survives crash.

### 2. Money transfer
Wrap in transaction; `SELECT FOR UPDATE` both rows (in a deterministic order); conditional UPDATE on `from` checking balance; UPDATE on `to`; insert transaction record with idempotency key; commit. Discuss isolation level (RC + locks is enough; or use Serializable for write skew safety in more complex scenarios).

### 3. Crash recovery
On restart, the engine replays WAL records to redo committed transactions and undoes uncommitted ones. This is durability + atomicity working together. WAL is fsync'd on commit (`synchronous_commit=on`).

### 4. Savepoint
A nested marker; you can rollback to it without aborting the whole transaction. Useful in batch processing.

### 5. 2PC
Distributed transaction protocol: prepare phase (all participants vote), then commit phase. Drawback: coordinator failure → resource lock. Modern microservices prefer sagas. 2PC still used inside distributed SQL engines (Spanner, CockroachDB) using Paxos/Raft.

### 6. Outbox pattern
Write the message to an `outbox` table inside the same transaction as the business change. A worker reads outbox and publishes externally. Guarantees: DB write and publish intent are atomic; the publish is at-least-once.

### 7. Sagas
Long-running cross-service transactions modeled as a sequence of local transactions with compensating actions on failure. Choreography vs orchestration. Trade-off: eventually consistent, intermediate states visible. Use Temporal/Camunda/Step Functions for orchestration.

### 8. Idempotency
A client-generated key (UUID) stored server-side along with the response. Duplicate requests return the same response. Critical for retries: payments, webhooks, mobile apps with flaky networks.

### 9. INSERT ON CONFLICT vs lookup
- `INSERT ON CONFLICT … DO NOTHING/UPDATE` is **atomic**: no race window.
- `SELECT … then INSERT` has a race: two concurrent requests can both miss the row, both insert.
- Always prefer `ON CONFLICT` for upserts.

### 10. Lost update
Two transactions read the same row, each modifies based on the value seen, and the second write overwrites the first.

```
T1: SELECT balance → 100
T2: SELECT balance → 100
T1: UPDATE SET balance = 100 - 30 = 70
T2: UPDATE SET balance = 100 - 50 = 50   -- T1's debit is lost!
```

Prevent with:
- `SELECT … FOR UPDATE` (pessimistic lock)
- Conditional update: `UPDATE SET balance = balance - 30 WHERE id = ? AND balance >= 30`
- Version column (optimistic): `UPDATE SET balance = …, version = version + 1 WHERE id = ? AND version = ?`

### 11. DB + Kafka problem
This is the **dual-write problem**. Solutions:
- Outbox pattern (recommended)
- Transactional messaging (Kafka transactions + DB transactions — complex)
- CDC from DB to Kafka (Debezium)
- Event sourcing (events are the only writes; current state is a projection)

### 12. Optimistic vs pessimistic
- **Pessimistic**: lock the row upfront (`FOR UPDATE`). Use when conflict probability is high. Cost: contention.
- **Optimistic**: read with a version, write only if version unchanged (`WHERE version = ?`). Use when conflict is rare. Cost: retry on conflict.

---

## Practical coding examples

### Node + Postgres — transaction with error handling

```javascript
const client = await pool.connect();
try {
  await client.query('BEGIN');

  const { rows } = await client.query(
    `UPDATE accounts SET balance_cents = balance_cents - $1
     WHERE id = $2 AND balance_cents >= $1 RETURNING balance_cents`,
    [amount, fromId]
  );
  if (rows.length === 0) throw new Error('INSUFFICIENT_FUNDS');

  await client.query(
    `UPDATE accounts SET balance_cents = balance_cents + $1 WHERE id = $2`,
    [amount, toId]
  );

  await client.query(
    `INSERT INTO transactions (idempotency_key, from_account, to_account, amount_cents, status)
     VALUES ($1, $2, $3, $4, 'SUCCESS')
     ON CONFLICT (idempotency_key) DO NOTHING`,
    [key, fromId, toId, amount]
  );

  await client.query('COMMIT');
} catch (err) {
  await client.query('ROLLBACK');
  throw err;
} finally {
  client.release();
}
```

### Prisma — transaction

```typescript
const result = await prisma.$transaction(async (tx) => {
  const updated = await tx.account.updateMany({
    where: { id: fromId, balanceCents: { gte: amount } },
    data: { balanceCents: { decrement: amount } },
  });
  if (updated.count === 0) throw new Error('INSUFFICIENT_FUNDS');

  await tx.account.update({
    where: { id: toId },
    data: { balanceCents: { increment: amount } },
  });

  return tx.transaction.create({
    data: { idempotencyKey: key, fromAccount: fromId, toAccount: toId, amountCents: amount, status: 'SUCCESS' },
  });
}, { isolationLevel: 'Serializable', timeout: 5000 });
```

### Optimistic locking

```sql
UPDATE products
SET price_cents = $1, version = version + 1
WHERE id = $2 AND version = $3;
-- If 0 rows affected → someone else updated; retry or surface conflict
```

### Outbox worker (pseudo)

```sql
-- Worker query (with FOR UPDATE SKIP LOCKED for concurrent workers)
WITH job AS (
  SELECT id, topic, payload FROM outbox
  WHERE published_at IS NULL
  ORDER BY id LIMIT 100 FOR UPDATE SKIP LOCKED
)
UPDATE outbox SET published_at = NOW()
WHERE id IN (SELECT id FROM job)
RETURNING id, topic, payload;
```

Then publish to Kafka. Worker can retry on failure (`published_at` stays NULL).

---

## Common mistakes

- Forgetting to wrap multi-step operations in a transaction
- Not handling `ROLLBACK` in catch blocks (connection released in a transaction = bug)
- Long transactions (locks held, snapshot ages, bloat grows)
- Doing external API calls inside a transaction (network latency = locks held)
- Not setting a transaction timeout / statement_timeout (a stuck transaction can wedge the DB)
- Mixing autocommit and transaction code (some statements escape the transaction)
- Treating transactions as a substitute for idempotency (they're not — retries still need keys)

---

## Senior engineer discussion points

- **`statement_timeout` and `idle_in_transaction_session_timeout`** to prevent runaway transactions
- **`SELECT FOR UPDATE SKIP LOCKED`** for queue-like workers (Postgres ≥ 9.5)
- **Outbox + Debezium** is the modern recipe for transactional messaging
- **CockroachDB / Spanner / YugabyteDB**: distributed SQL with serializable global transactions
- **Why microservices don't share databases**: precludes ACID across services; pushes you to sagas/outbox
- **HTAP databases** (TiDB, SingleStore) try to be ACID and OLAP at once
- **Read replicas + transactions**: replicas are read-only and may lag; transactions usually run on primary
- **Trigger pitfalls**: triggers run inside the transaction → can deadlock, can balloon write time

---

## Revision notes

- ACID: Atomicity, Consistency, Isolation, Durability
- Transaction = BEGIN … COMMIT/ROLLBACK; WAL ensures durability
- Lock both rows in money transfer; **same lock order to avoid deadlock**
- Lost update prevention: SELECT FOR UPDATE, conditional UPDATE, or version column
- 2PC = blocking; sagas + outbox = modern distributed answer
- Outbox: DB write + event row in one transaction; worker publishes
- Idempotency = retry-safe; use idempotency keys + UNIQUE / ON CONFLICT
- Never call external APIs inside a transaction
- Set `statement_timeout` and `idle_in_transaction_session_timeout` in production
- `SELECT FOR UPDATE SKIP LOCKED` for concurrent queue workers
