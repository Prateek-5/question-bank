# Pick the right MongoDB write concern for each scenario — and explain w, j, wtimeout

## Source / Origin
- Frequent in MongoDB-heavy backend rounds, fintech, ad-tech.
- MongoDB docs on Write Concern; replica set durability.
- Concept reference: `backend-data-prep/nosql/mongo-durability.md`.

## Why this question matters in interviews
Write concern is where MongoDB users either reveal they shipped to prod or that they "just used the defaults". The interview signal: can you reason about `w`, `j`, and `wtimeout` separately? Do you know that `w:1` without `j:true` can lose acknowledged writes on a crash? Do you understand that `w:"majority"` is the *correctness* knob and `j:true` is the *single-node durability* knob — and they're orthogonal? Senior candidates also know when to dial it *down* (analytics ingest) and when to dial it *up* (financial transactions).

## Concepts involved

### Syntax to lock in

```javascript
// Three independent knobs
db.orders.insertOne(
  { _id: "ord-1", amount: 100 },
  {
    writeConcern: {
      w: "majority",   // how many replicas must acknowledge
      j: true,         // must be written to journal on disk (durability per node)
      wtimeout: 5000   // max ms to wait for w replicas (does NOT roll back)
    }
  }
);

// w options
//   0           : fire-and-forget; no ack at all
//   1           : primary acks (default in modern drivers... actually "majority" since 4.4)
//   2..N        : that many members ack (rare; use "majority" instead)
//   "majority"  : strict majority of voting members
//   <tag-set>   : custom; e.g., "multi-DC" requires acks from members tagged in 2 DCs

// j options
//   false : in-memory ack only on primary (could lose on crash before fsync)
//   true  : journal (on-disk WAL) on primary

// wtimeout
//   Only meaningful for w >= 2 or "majority".
//   On timeout: write may still apply later. NOT a rollback. App must
//   handle "ambiguous outcome".
```

### Edge cases / interview traps

1. **`w:1` is NOT the modern default.** Since MongoDB 4.4, default is `w:"majority"`. Many older codebases still set `w:1` explicitly.
2. **`w:"majority"` + `j:false` is still durable across cluster** — majority acks include the primary's journal commit in practice. The subtle case is `w:1, j:false`: only the primary, only in memory.
3. **`wtimeout` does NOT roll back the write.** It only stops *waiting*. The write may eventually replicate. Application sees a `WriteConcernError` but the data exists. Idempotency matters.
4. **`w:0` returns before any validation** — even schema errors are silently swallowed. Only for telemetry, never for state.
5. **Rollback on primary failover.** A write acked at `w:1` on a primary that crashes before replication will be rolled back when a new primary is elected. Stored in `rollback/` directory, not auto-recovered.
6. **Causal consistency requires `w:"majority"` + `readConcern:"majority"`.** Sessions tie them together.
7. **`writeConcernError` vs `writeError`.** Different fields in the response. `writeError` = the operation failed; `writeConcernError` = it applied but acknowledgment didn't meet concern.
8. **Arbiters don't count toward `w:"majority"` data durability** but do count for *voting* majority. PSA (primary-secondary-arbiter) can lead to durability surprises.

## Mental Model

The **"two knobs"** model.

```
              ┌─ HOW WIDE (replication) ──┐
              │  w: 0/1/N/"majority"      │
              │  → correctness under      │
   write      │    failover               │
   ───────►   │                           │  ──► ack
              │  j: false/true            │
              │  → durability on one node │
              │    (fsync of WAL)         │
              └─ HOW DEEP (disk) ─────────┘

   wtimeout = "give up waiting (but don't roll back)"
```

`w` answers "how many nodes know about this write". `j` answers "is it safe from a single-node crash". They're orthogonal.

## Why interviewers care

- Surfaces understanding of durability vs. availability tradeoffs.
- Detects whether you've actually run a replica set through failover.
- Tests whether you handle `wtimeout` ambiguity correctly (idempotent retry, not "we lost the write").

## Common beginner confusion

- "`w:1` is fine because primary is durable." Not on primary crash before replication — rolled back.
- "`wtimeout` rolls the write back." It doesn't. The write may still apply.
- "`w:"majority"` is slow, I'll use `w:1`." For state-of-record writes (payments, inventory) the latency difference is small and the correctness gain is enormous.
- "`j:true` and `w:"majority"` are redundant." Different axes. `w:"majority"` doesn't guarantee disk-flush on every node, just acknowledgment.
- "Setting `w:5` makes it more durable than `w:3`." Past majority, you're just adding latency. Use tag sets if you care about *which* nodes.

## Brute force approach

`w:"all"` (every voting member). Maximally durable; any one member down blocks writes. Almost never used; brittle.

## Optimal approach

Decision table by workload:

| Workload | w | j | wtimeout | Rationale |
|---|---|---|---|---|
| Payments, ledger, anything financial | "majority" | true | 5000 | survives primary crash; on-disk WAL on primary |
| Order placement (state of record) | "majority" | false | 5000 | majority gives correctness; j adds ~5ms |
| User profile updates | "majority" | false | 3000 | same |
| Telemetry / clickstream | 1 | false | 1000 | speed > durability; occasional loss OK |
| Audit logs (must not lose) | "majority" | true | 10000 | belt and suspenders |
| Cross-DC writes | tag-set "multi-DC" | true | 15000 | geo-durable |
| Bulk import (re-runnable) | 0 or 1 | false | — | re-run on failure |

## Solution

```javascript
// ===== Scenario 1: Payment processing =====
const paymentsClient = new MongoClient(uri, {
  writeConcern: { w: "majority", j: true, wtimeout: 5000 }
});

async function recordPayment(orderId, amount) {
  const session = paymentsClient.startSession();
  try {
    await session.withTransaction(async () => {
      await db.collection("payments").insertOne(
        { _id: orderId, amount, ts: new Date() },
        { session }
      );
    }, {
      writeConcern: { w: "majority", j: true, wtimeout: 5000 },
      readConcern: { level: "majority" }
    });
  } catch (e) {
    if (e.code === 64 /* WriteConcernFailed */) {
      // AMBIGUOUS: write may have applied. Use idempotent _id and check.
      const exists = await db.collection("payments")
        .findOne({ _id: orderId }, { readConcern: "majority" });
      if (exists) return "ok";
    }
    throw e;
  } finally {
    await session.endSession();
  }
}

// ===== Scenario 2: Telemetry ingest (loss-tolerant, throughput) =====
const telemetryClient = new MongoClient(uri, {
  writeConcern: { w: 1, j: false, wtimeout: 1000 }
});

await db.collection("events").insertMany(batch, { ordered: false });
// 10x throughput vs majority; we accept losing the last few seconds on crash.

// ===== Scenario 3: Custom tag set for multi-DC =====
// Replica set config:
rs.reconfig({
  _id: "rs0",
  members: [
    { _id: 0, host: "p1:27017", tags: { dc: "us-east" } },
    { _id: 1, host: "s1:27017", tags: { dc: "us-east" } },
    { _id: 2, host: "s2:27017", tags: { dc: "eu-west" } }
  ],
  settings: {
    getLastErrorModes: {
      "multi-DC": { dc: 2 }   // require acks from 2 distinct DCs
    }
  }
});

db.orders.insertOne(doc, {
  writeConcern: { w: "multi-DC", j: true, wtimeout: 15000 }
});

// ===== Quiz answers =====
// Q1: Default writeConcern in modern drivers?         A: { w: "majority" }
// Q2: Does wtimeout roll back?                         A: No.
// Q3: w:1 + j:false, primary crashes before sync?     A: Write lost.
// Q4: w:"majority" + arbiter in PSA, secondary down?  A: Writes block.
// Q5: Smallest concern that survives primary loss?    A: w:"majority".
```

## Step-by-step dry run

3-node replica set (P, S1, S2). Write with `w:"majority", j:true`:

```
t=0    Client → Primary: insertOne({...})
t=1    P writes to journal (j:true on primary) — durable on P
t=2    P writes to oplog; replicates to S1, S2
t=20   S1 acks oplog apply
t=22   S2 acks oplog apply
t=23   P has acks from {P, S1} (≥ majority of 3) → ACKs client
       (or from {P, S2}, whichever first)
t=23   Client receives success

If P crashes at t=10 (after journal, before replication):
  - S1/S2 election: new primary chosen.
  - The journal on P is replayed on P's recovery; if oplog entry
    was not replicated, on rejoin P sees its oplog > new P's
    common point → its uncommitted ops move to rollback/.
  - Client got NO ack (we crashed at t=10 < t=23) → it retries.
  - Idempotent _id ensures retry is safe.

Same write with w:1, j:false:
  t=0    Client → P: insertOne
  t=1    P applies in-memory
  t=2    P ACKs client (in-memory only!)
  t=3    P crashes before journal flush
  t=4    S1 promoted; doesn't have this write
  CLIENT BELIEVES WRITE HAPPENED. IT DIDN'T.
```

Timeout dry run, `w:"majority", wtimeout:1000`:

```
t=0     Insert to P, j:true done at t=2
t=2     P starts waiting for replication
t=3     Network partition: S1, S2 unreachable
t=1002  wtimeout fires → P returns WriteConcernError
        But the doc is in P's oplog. Partition heals at t=5000.
        S1, S2 replicate it. Now everyone has it.
APP MUST: treat error as "ambiguous"; use idempotent retry to verify.
```

## How to think aloud in the interview

> "Three independent knobs: `w` = how many replicas must ack, `j` = does the primary fsync the journal before acking, `wtimeout` = how long to wait. The trap is that `wtimeout` is a *give-up* timer, not a rollback — the write may still apply.
>
> My defaults:
> - Anything financial or audit-relevant: `w:"majority", j:true, wtimeout:5s`.
> - State-of-record (orders, profiles): `w:"majority", j:false, wtimeout:3-5s`.
> - Telemetry / loss-tolerant: `w:1, j:false` for throughput.
>
> The critical app-side discipline: every write must be idempotent (deterministic `_id` or upsert with natural key), because `wtimeout` and network partitions create ambiguous outcomes that you resolve by retry-with-verify.
>
> One gotcha: in PSA (primary-secondary-arbiter) topologies, losing the one data-bearing secondary blocks `w:"majority"` writes. I prefer PSS or PSSA for production."

## Important takeaways

- `w`, `j`, `wtimeout` are orthogonal; reason about each.
- Modern default is `w:"majority"`; older codebases may have `w:1` — audit them.
- `wtimeout` is NOT a rollback. Treat its error as "ambiguous"; verify with idempotent retry.
- `w:1, j:false` can lose acknowledged writes on primary crash.
- Use tag sets for multi-DC / cross-region durability requirements.
- Arbiters don't store data; PSA topologies have durability sharp edges.

## Variants

1. **Read concern matches write concern** — for read-your-write across the cluster, use `readConcern:"majority"` paired with `w:"majority"` writes; use session-based causal consistency.
2. **Transactions** — multi-document transactions require `w:"majority"` on the commit; participating ops inherit.
3. **Change streams** — only emit events that have reached majority commit point; if you read changes with `w:1` writes, you'll see them later than majority readers do.
4. **Bulk writes with `ordered:false`** — write concern applies to the whole batch; partial failures surface in `writeErrors[]`.
5. **Tunable consistency vs CosmosDB Mongo API** — CosmosDB exposes 5 levels (strong → eventual); semantically similar to dialing `w` and `readConcern` together.

## Revision notes

> **mongo write concern — 60s recap**
> - `w` = replicas to ack (1, N, "majority", tag); `j` = on-disk journal on primary; `wtimeout` = give-up timer (not rollback).
> - Default modern: `w:"majority"`.
> - Financial / audit: `w:"majority", j:true`. Telemetry: `w:1, j:false`.
> - `wtimeout` error = ambiguous; verify with idempotent retry.
> - `w:1` + primary crash before replicate = silent loss.
> - PSA topologies block on secondary loss for `w:"majority"`.
> - Use tag sets for multi-DC requirements.
