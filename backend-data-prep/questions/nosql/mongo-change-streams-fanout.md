# MongoDB: Change streams — resume tokens, oplog tailing, fanout

## Source / Origin
- Standard Mongo-since-3.6 question. Asked at any event-driven shop using Mongo.
- Concept reference: `backend-data-prep/nosql/04-mongodb.md` (change streams section).
- Cross-ref: messaging patterns / outbox / CDC.

## Why this question matters in interviews
Change streams are Mongo's **built-in CDC**. Used wrong, you lose events on broker restart, double-process, or drift. Used right, you replace Kafka Connect for medium-throughput use cases. Senior signal: you understand **resume tokens**, **at-least-once semantics**, **invalidate events**, and the **oplog window**.

## Concepts involved

### Syntax to lock in

```javascript
// Open a change stream on a collection
const cs = db.orders.watch(
  [ { $match: { "fullDocument.status": "PAID" } } ],
  { fullDocument: "updateLookup", resumeAfter: lastToken }
);

for await (const change of cs) {
  // change.operationType:  "insert" | "update" | "replace" | "delete" | "invalidate"
  // change.fullDocument:    full doc post-change (with updateLookup)
  // change.documentKey:     { _id }
  // change.updateDescription.updatedFields:  partial diff
  // change._id:             RESUME TOKEN — persist this!
  await handle(change);
  await persistToken(change._id);            // checkpoint AFTER handle, at-least-once
}
```

### Edge cases / interview traps

1. **Lose your resume token, lose your spot.** Without a token, you start at "now" and miss everything during the gap.
2. **Oplog window is your retention budget.** If the consumer is down longer than the oplog covers (typically hours), the resume token is invalid → catastrophe. Monitor oplog size vs lag.
3. **`fullDocument: "updateLookup"`** fetches the *current* doc at the time of lookup, not at the time of the change — could be a later version. For exact post-image, use Mongo 6.0+ pre/post images.
4. **Invalidate events** — collection dropped/renamed → stream closes; you must reopen with a new pipeline.
5. **At-least-once delivery.** Plan for idempotency on consumer side.
6. **Causal consistency** — events arrive in the **oplog order**, which is the commit order on the primary. Cross-shard ordering is global via the `clusterTime`.
7. **Sharded change streams** must be opened via `mongos`; merging is handled.
8. **Pipeline stages allowed**: `$match`, `$project`, `$addFields`, `$replaceRoot`, `$redact`. Filter early to reduce network.

## Mental Model

> Change stream = **tail of the oplog**. The oplog is Mongo's replication WAL — every write is logged with a `clusterTime`. The change stream cursor reads forward from a token; resuming means "pick up at this token in the oplog."

```
   Time →

   oplog:  e1 e2 e3 e4 e5 e6 e7 e8 e9 e10 e11 ...
                        ▲                   ▲
                  lastToken                 now

   consumer:  ◀─── reads e5,e6,... using lastToken to resume

   FAN-OUT to Kafka / WebSocket / search indexer:
     change stream → handler → publish → ack resume token

   If consumer dies after handle(e7) but before persistToken:
     on restart, resumeAfter = e6 → e7 re-delivered → idempotency required
```

## Why interviewers care

- Tests **CDC vocabulary** — operation types, resume tokens, oplog window.
- Tests **at-least-once reasoning** — no exactly-once; idempotency or dedup required.
- Tests **operational maturity** — oplog sizing, lag monitoring, invalidate handling.

## Common beginner confusion

- "Exactly-once." It's at-least-once.
- "Polling for changes." Wasteful; use the stream.
- "If the consumer disconnects, I'll just start at now." Lose events.
- "Watch the whole DB, filter in app." Bandwidth waste; use a `$match` pipeline.
- "Change stream replaces transactions." Different problem; CS observes commits, doesn't enforce atomicity.
- "Updates always carry full doc." Only with `fullDocument: 'updateLookup'`. Default is the diff.

## Brute force approach

Poll the collection every second with `find({ updatedAt: { $gt: lastSeen } })`. Wastes IOPS, misses deletes, fights with concurrent writes on `updatedAt`. Don't.

## Optimal approach

`db.collection.watch(pipeline, { resumeAfter })`. Persist the resume token after every handled event (or every N events with a batched checkpoint). Build the consumer to be **idempotent** (e.g., upsert by `documentKey._id`).

## Solution (Mongo shell + Node)

```javascript
// === Persist resume token in a side collection ===
async function loadToken() {
  const doc = await db.cursors.findOne({ _id: "orders-to-kafka" });
  return doc?.token;
}
async function saveToken(token) {
  await db.cursors.updateOne(
    { _id: "orders-to-kafka" },
    { $set: { token, at: new Date() } },
    { upsert: true }
  );
}

// === Run consumer ===
async function run() {
  while (true) {
    const resumeAfter = await loadToken();
    const cs = db.orders.watch(
      [ { $match: { operationType: { $in: ["insert","update","replace","delete"] } } } ],
      { fullDocument: "updateLookup", resumeAfter, maxAwaitTimeMS: 1000 }
    );

    try {
      for await (const change of cs) {
        if (change.operationType === "invalidate") {
          // Collection dropped/renamed — reopen from now
          await saveToken(null);
          break;
        }
        await publishToKafka(change);     // idempotent on documentKey._id
        await saveToken(change._id);       // checkpoint AFTER handle
      }
    } catch (err) {
      if (err.codeName === "ChangeStreamHistoryLost") {
        // resume token outside oplog window → unrecoverable
        await alert("Oplog rolled past resume token; require full resync");
        await saveToken(null);
      }
      await sleep(1000);
    }
  }
}

// === Idempotent publisher ===
async function publishToKafka(change) {
  const key = change.documentKey._id.toString();
  await kafka.produce("orders", {
    key,                       // partition by _id → keeps order per doc
    value: JSON.stringify(change),
    headers: { "operation": change.operationType, "clusterTime": change.clusterTime }
  });
}
```

### Multi-consumer fanout pattern

```
                ┌─────────────┐
                │  Mongo CS   │  (one shared change stream)
                └──────┬──────┘
                       │
                       ▼
                ┌─────────────┐
                │  Dispatcher │  ← single consumer, persists token
                └──┬──┬──┬────┘
                   │  │  │
       ┌───────────┘  │  └───────────┐
       ▼              ▼              ▼
   Kafka topic    Elasticsearch    WebSocket fanout
                  indexer          (per-user routing)
```

**Anti-pattern:** opening N change streams (one per downstream consumer). Burns oplog read bandwidth N×. Use a single CS + dispatcher.

## Step-by-step dry run

```
Setup: orders collection, change stream consumer pushing to Kafka.

t=0   Consumer starts. loadToken() returns last token from yesterday.
t=1   Open watch(resumeAfter=lastToken). Mongo starts replay from oplog entry.
t=1.1 First batch: e500..e520 (500 events since yesterday).
t=1.2 For each:
        publishKafka(change)   → success
        saveToken(change._id)  → success
      Process all 500 in ~1s.

t=10  Live tail: events arrive as they're written.
t=120 Consumer crash.
t=130 Consumer restart. loadToken() → e520's token.
      Open watch(resumeAfter=e520). Resume from e521.
      No events lost. Some events (e520 itself, if checkpoint happened mid-batch)
      may be re-delivered → idempotent publisher dedupes by documentKey + clusterTime.

t=200 Oplog window: 24h. Suppose consumer was down for 48h.
      resumeAfter token is now older than oldest oplog entry.
      Mongo throws ChangeStreamHistoryLost.
      Operator must trigger a FULL RESYNC: load current snapshot to Kafka,
      then open a fresh CS with no resumeAfter (starts at now).
```

## How to think aloud in the interview

> "Change streams are oplog tailing exposed as a cursor. The driver hides the polling; I treat it like a Kafka consumer with a resume token.
>
> Three things matter operationally: persisting the resume token (lose it, lose your spot), monitoring the oplog window vs consumer lag (resume token expires when oplog rolls past), and idempotent handling (at-least-once delivery, no exactly-once).
>
> For fanout to multiple downstream systems I run a single consumer that publishes to Kafka, and let other systems read from Kafka. Opening N change streams against Mongo wastes oplog bandwidth.
>
> The `fullDocument: 'updateLookup'` option fetches the post-change doc — handy, but note it's a *current* read at lookup time, so racing updates can give you a later version. Mongo 6.0+ has pre/post image support for exact change semantics.
>
> Invalidate events close the stream — collection dropped or renamed. The consumer must handle that gracefully and decide whether to reopen on the new collection or alert."

## Important takeaways

- **At-least-once delivery.** Idempotent consumers or dedup tables.
- **Resume token = oplog position.** Persist after handle, not before.
- **Oplog window = retention.** Monitor consumer lag vs oplog size.
- **`fullDocument: 'updateLookup'`** is a current-time read, not snapshot at change time.
- **One CS + dispatcher** beats N CS consumers.
- **Invalidate events** close the stream — handle gracefully.
- **ChangeStreamHistoryLost** = oplog rolled past your token; requires resync.
- **Pipeline stages allowed**: `$match`, `$project`, `$addFields`, `$replaceRoot`, `$redact`.

## Variants

1. **Watch the whole deployment** — `client.watch()` for cluster-wide CS.
2. **Pre/post images (6.0+)** — exact before/after doc per change.
3. **Resume after vs start at operation time** — `startAtOperationTime` for replaying from a known cluster time.
4. **Outbox pattern alternative** — write event doc inside a txn; CS picks it up. Tighter atomicity.
5. **Filter at source with $match** — reduces consumer work and network.
6. **Sharded CS** — open via `mongos`; merging handled; events ordered globally by `clusterTime`.

## Revision notes

> **change streams — 60s recap**
> - Oplog tailing exposed as a cursor. At-least-once delivery.
> - `db.coll.watch(pipeline, { resumeAfter, fullDocument: 'updateLookup' })`.
> - Persist resume token (`change._id`) AFTER handle. Lose it, lose your spot.
> - Oplog window > consumer lag, ALWAYS. Else `ChangeStreamHistoryLost`.
> - Idempotent consumer required.
> - Operation types: insert / update / replace / delete / invalidate.
> - Invalidate = collection dropped/renamed; reopen.
> - Fanout: one CS → dispatcher → Kafka → many consumers.
> - 6.0+ has pre/post images for exact change semantics.
