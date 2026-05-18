# MongoDB: Multi-document ACID transactions — when they help, when they hurt

## Source / Origin
- Asked at every Mongo interview since 4.0 (replica sets) / 4.2 (sharded).
- Concept reference: `backend-data-prep/nosql/04-mongodb.md` (transactions section).
- Cross-ref: `backend-data-prep/questions/transactions-concurrency/` (general ACID).

## Why this question matters in interviews
Mongo got multi-document transactions late (4.0). Many engineers still think it can't do them. The interviewer is testing whether you (a) know they exist, (b) know they're **expensive** and you should design schemas to avoid needing them, and (c) understand the **TransientTransactionError** retry contract. Senior signal: you use transactions only when single-doc atomicity isn't enough and you have the retry loop nailed.

## Concepts involved

### Syntax to lock in

```javascript
const session = client.startSession();
session.startTransaction({
  readConcern: { level: "snapshot" },
  writeConcern: { w: "majority" },
  readPreference: "primary"
});

try {
  await db.accounts.updateOne({ _id: "A" }, { $inc: { balance: -100 } }, { session });
  await db.accounts.updateOne({ _id: "B" }, { $inc: { balance:  100 } }, { session });
  await db.ledger.insertOne({ from: "A", to: "B", amount: 100 }, { session });
  await session.commitTransaction();
} catch (err) {
  await session.abortTransaction();
  if (err.hasErrorLabel("TransientTransactionError")) {
    // safe to retry — the entire txn body
  }
  throw err;
} finally {
  await session.endSession();
}
```

### Edge cases / interview traps

1. **Single-doc updates are already atomic.** Don't wrap them in a transaction.
2. **TransientTransactionError must be retried.** It's not a permanent failure; the engine asks you to retry the *whole* txn body.
3. **UnknownTransactionCommitResult** — commit may have succeeded or not; safe to retry commit (idempotent).
4. **Default txn timeout is 60s.** Long transactions block snapshot history; set per-txn timeout.
5. **Sharded transactions** — 4.2+, but cross-shard adds 2PC latency. Avoid unless necessary.
6. **Cannot create collections inside a txn** (well, since 4.4 you can — but it's slow). Pre-create.
7. **`readConcern: "snapshot"` is the default and correct** — gives you a consistent point-in-time view.
8. **`writeConcern: "majority"`** required for durable commit on a replica set.
9. **No DDL inside txn** (mostly).

## Mental Model

> A Mongo transaction is a **WiredTiger snapshot + commit barrier**, equivalent to Postgres' REPEATABLE READ (snapshot isolation). Not serializable. Same anomalies as Postgres RR — including write skew.

```
   Client                    Mongo Primary
     │                            │
     ├──startTransaction────────▶│   open WT snapshot
     │                            │
     ├──update A balance --100 ─▶│   write to in-memory snapshot
     │                            │
     ├──update B balance +100  ─▶│   write to in-memory snapshot
     │                            │
     ├──commitTransaction ──────▶│   wait for majority ack on oplog
     │                            │
     │◀── ok / TransientError ──┤
     │
     │   if TransientError: retry whole block
```

## Why interviewers care

- Tests **honesty about Mongo's cost** — transactions are 2–10× slower than single-doc writes.
- Tests **schema-design instinct** — the right answer is often *redesign so you don't need a txn*.
- Tests **retry contract literacy** — many engineers don't know TransientTransactionError must be retried.

## Common beginner confusion

- "Mongo can't do transactions." Outdated since 4.0.
- "Wrap everything in a transaction to be safe." Performance disaster.
- "Transactions are serializable." No — snapshot isolation. Write skew is possible.
- "Commit fails → data is gone." No — if commit returns UnknownTransactionCommitResult, retry; it's idempotent.
- "Use 2PC manually across shards." Mongo handles cross-shard commit internally in 4.2+.

## Brute force approach

Wrap every write in `withTransaction`. Latency triples. Replica lag spikes. Don't.

## Optimal approach

**Default: redesign for single-doc atomicity.** Embed related data so one write covers the change. Only use multi-doc transactions when the change *must* span documents (transfer between two accounts, order + inventory + ledger).

When you do use them:
- `session.withTransaction()` helper handles the retry contract.
- `readConcern: snapshot`, `writeConcern: majority`.
- Keep the txn body small and fast — ideally <100ms.
- No external I/O inside the txn (no API calls, no email sends).

## Solution (Mongo shell + Node driver)

```javascript
// === Helper: withTransaction handles retry contract ===
const { MongoClient } = require("mongodb");
const client = new MongoClient(uri);
const db     = client.db("bank");

async function transfer(fromId, toId, amount) {
  const session = client.startSession();
  try {
    await session.withTransaction(async () => {
      const from = await db.collection("accounts").findOne({ _id: fromId }, { session });
      if (!from || from.balance < amount) {
        throw new Error("INSUFFICIENT_FUNDS");
      }
      await db.collection("accounts").updateOne(
        { _id: fromId, balance: { $gte: amount } },           // guard
        { $inc: { balance: -amount } },
        { session }
      );
      await db.collection("accounts").updateOne(
        { _id: toId },
        { $inc: { balance: amount } },
        { session }
      );
      await db.collection("ledger").insertOne(
        { from: fromId, to: toId, amount, at: new Date() },
        { session }
      );
    }, {
      readConcern:    { level: "snapshot" },
      writeConcern:   { w: "majority", wtimeout: 5000 },
      readPreference: "primary"
    });
  } finally {
    await session.endSession();
  }
}

// === Manual retry contract (if you can't use withTransaction) ===
async function manualTxn() {
  for (let attempt = 0; attempt < 5; attempt++) {
    const session = client.startSession();
    session.startTransaction();
    try {
      // ... operations ...
      await commitWithRetry(session);
      return;
    } catch (err) {
      await session.abortTransaction().catch(() => {});
      if (err.hasErrorLabel && err.hasErrorLabel("TransientTransactionError")) {
        await sleep(50 * (1 << attempt));   // backoff
        continue;
      }
      throw err;
    } finally {
      await session.endSession();
    }
  }
  throw new Error("TXN_RETRIES_EXHAUSTED");
}

async function commitWithRetry(session) {
  for (;;) {
    try {
      await session.commitTransaction();
      return;
    } catch (err) {
      if (err.hasErrorLabel && err.hasErrorLabel("UnknownTransactionCommitResult")) {
        continue;        // safe to retry the commit
      }
      throw err;
    }
  }
}
```

### Write-skew warning

```javascript
// Mongo transactions = snapshot isolation, NOT serializable.
// The classic doctor-on-call write skew is still possible.
// Mitigations:
// 1. Use a guard predicate in the UPDATE filter ({ balance: { $gte: amount } })
//    — this turns it into a write-write conflict.
// 2. Materialise the invariant into a single doc all txns update.
// 3. Use `findOneAndUpdate` with optimistic version field.
```

## Step-by-step dry run

```
Transfer $100 from A to B (both balance $200 initially)

t=0  Client calls transfer("A","B",100). withTransaction starts session, txn.
t=1  findOne A → balance=200. snapshot recorded.
t=2  updateOne A balance >= 100 → matched=1, modified=1. balance pending=100.
t=3  updateOne B → balance pending=300.
t=4  insertOne ledger row.
t=5  commitTransaction → primary writes commit to oplog, awaits majority ack.
t=6  Two of three replicas ack within 30ms → COMMITTED.
     Client returns OK.

Concurrent attempt: at t=2, another txn tries to debit A.
  WiredTiger detects write-write conflict (same row, same window).
  One txn errors with TransientTransactionError → withTransaction retries.
  Retry observes A.balance=100, succeeds or fails INSUFFICIENT_FUNDS based on logic.

Failure scenarios:
  - Primary crashes mid-commit → driver sees UnknownTransactionCommitResult →
    retries commit; if oplog had it, idempotent success; else retried.
  - wtimeout 5s exceeded → commit returns error; not safe to assume rolled back;
    re-check application-level invariants.
```

## How to think aloud in the interview

> "First, multi-doc transactions exist in Mongo since 4.0 on replica sets, 4.2 sharded. But they're 2–10× the cost of a single-doc write, so I design schemas to avoid them. Embedding line items in an order doc, for instance, removes the need for an order+items transaction.
>
> When I do need them — a money transfer is the canonical example — I use `withTransaction` which handles the two-error retry contract: `TransientTransactionError` (retry the whole body) and `UnknownTransactionCommitResult` (retry just the commit, idempotent).
>
> Settings: `readConcern: snapshot`, `writeConcern: majority` for durability. The txn body must be small (<100ms) and contain no external I/O — no API calls, no email sends. Side effects go to an outbox row inside the txn, processed by a worker after commit.
>
> One trap: Mongo txns are snapshot isolation, not serializable. Write skew is possible. I add guard predicates in update filters (`balance >= amount`) to convert it into a write-write conflict that the engine detects."

## Important takeaways

- **Multi-doc transactions exist** (4.0 replica set, 4.2 sharded), but are expensive.
- **Prefer single-doc atomicity by schema design.** Embed when possible.
- **`withTransaction` handles the retry contract.** Use it.
- **Two errors matter**: `TransientTransactionError` (retry body) and `UnknownTransactionCommitResult` (retry commit).
- **Snapshot isolation, not serializable.** Write skew still possible — guard predicates or invariant materialization.
- **No external I/O inside txn.** Use an outbox.
- **<100ms body, default 60s timeout.** Long txns block snapshot history.
- **Sharded txns** add 2PC latency; avoid if you can.

## Variants

1. **Outbox pattern** — write to `events` collection inside the txn; worker reads and publishes to Kafka.
2. **Saga compensation** — when txns can't span services, use compensating actions.
3. **Optimistic concurrency** — `findOneAndUpdate({_id, version}, {$inc:{version:1}})` for single-doc cases.
4. **Change streams + idempotent consumer** — read from oplog post-commit instead of in-txn fan-out.
5. **Causally consistent sessions** — `client.startSession({ causalConsistency: true })` for read-your-write across replicas.
6. **Read-only transactions** — `readConcern: snapshot` without writes; consistent point-in-time read across docs.

## Revision notes

> **mongo transactions — 60s recap**
> - 4.0 replica set, 4.2 sharded. Multi-doc ACID with snapshot isolation.
> - Costly — design for single-doc atomicity first.
> - `session.withTransaction(fn, opts)` handles retry contract.
> - Two error labels: `TransientTransactionError` (retry body), `UnknownTransactionCommitResult` (retry commit, idempotent).
> - `readConcern: snapshot`, `writeConcern: majority` for durability.
> - No external I/O inside txn — use outbox.
> - <100ms body; 60s default timeout.
> - Snapshot isolation, NOT serializable → write skew possible → guard predicates.
> - Sharded txn = 2PC latency; avoid unless needed.
