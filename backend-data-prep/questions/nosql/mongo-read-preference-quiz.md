# Pick the right MongoDB read preference and explain its consistency cost

## Source / Origin
- Common MongoDB systems-design follow-up after write concern.
- MongoDB docs: Read Preference, Read Concern.
- Concept reference: `backend-data-prep/nosql/mongo-read-paths.md`.

## Why this question matters in interviews
Read preference is where MongoDB candidates conflate **routing** (which node) with **consistency** (what view of the data). The interview signal: do you know `readPreference` answers "which member do I talk to" and `readConcern` answers "what data am I guaranteed to see"? Can you defend `secondaryPreferred` for analytics, `primary` for read-your-write, and never recommend `secondary` for OLTP without a use-case justification? Senior candidates also know maxStalenessSeconds, tag-set routing, and that hedge reads / latency-aware routing exist.

## Concepts involved

### Syntax to lock in

```javascript
// Five read preferences
db.collection.find().readPref("primary");             // default; strong, RYW
db.collection.find().readPref("primaryPreferred");    // primary if up, else any secondary
db.collection.find().readPref("secondary");           // secondary only; FAILS if none
db.collection.find().readPref("secondaryPreferred");  // secondary if any, else primary
db.collection.find().readPref("nearest");             // lowest latency, any role

// With tag set + max staleness
db.collection.find()
  .readPref("secondaryPreferred",
            [{ region: "eu-west" }, { region: "us-east" }],  // ordered prefs
            { maxStalenessSeconds: 90 });

// readConcern is independent of readPreference
db.collection.find().readConcern("majority");
// Levels: local | available | majority | linearizable | snapshot
//   local        = whatever this node has (default for primary reads)
//   available    = sharded; allows orphan docs; fastest
//   majority     = data acknowledged by majority; survives rollback
//   linearizable = strongest; primary only; reads recent acked write
//   snapshot     = used inside transactions; consistent snapshot
```

### Edge cases / interview traps

1. **`secondary` reads can be stale by minutes** during high write load. `maxStalenessSeconds` (min 90s) is a *cap*, not a guarantee of freshness — it just refuses overly stale members.
2. **`readPreference` ≠ `readConcern`.** Routing is independent of consistency. `primary + readConcern:"local"` reads from primary but doesn't wait for majority commit (rollback-vulnerable read).
3. **Read-your-write needs causal consistency.** `primary` doesn't give RYW across sessions — only within a session. Use `session.startTransaction()` or causal-consistent sessions.
4. **`nearest` is latency-based.** Driver pings all nodes; pick lowest. Stale data risk same as `secondary`.
5. **`linearizable` is read-only and slow.** Primary contacts a majority to verify it's still primary. Use sparingly.
6. **Sharded clusters: read preference applies per-shard.** A `nearest` read may hit different members on different shards.
7. **`available` read concern is sharded-only.** It allows reading orphan documents during migration; faster but can show data twice.
8. **PSA topology: a `secondary` read may not exist.** Only one data-bearing secondary; if it's down, `secondary` read fails. `secondaryPreferred` falls back to primary.
9. **Capped collections and tailable cursors** must read from primary (or the same secondary throughout the cursor's life).

## Mental Model

The **"routing vs view"** model.

```
   ┌────────────── readPreference (ROUTING) ───────────────┐
   │ "which physical node does my driver talk to?"         │
   │  primary  primaryPref  secondary  secondaryPref       │
   │  nearest                                              │
   │  + tag set + maxStalenessSeconds                      │
   └───────────────────────────────────────────────────────┘
                              │
                              ▼
   ┌────────────── readConcern (VIEW) ─────────────────────┐
   │ "what guarantees about the data I receive?"           │
   │  local  available  majority  linearizable  snapshot   │
   └───────────────────────────────────────────────────────┘
```

The two combine: `primary + linearizable` is the strongest, slowest. `secondary + local` is the fastest, least safe. Pick deliberately.

## Why interviewers care

- Tests whether you understand replica set physics: oplog tailing, replication lag, election windows.
- Surfaces system-design instincts: when is staleness OK, when is it dangerous.
- Detects whether you've ever debugged "this query returns the new doc on machine A but not machine B" — a classic secondary-read foot-gun.

## Common beginner confusion

- "`secondary` makes reads faster." Only for the workload at the cost of staleness — and only if secondaries aren't already overloaded.
- "Setting readPreference to secondary scales my cluster." Reads from secondaries don't reduce write load — secondaries still replicate every write. You get *read* throughput, not *write*.
- "`primaryPreferred` is safer than `primary`." It's *more available*, not more consistent. During primary failover, you may read from a stale secondary.
- "`maxStalenessSeconds:90` means data is at most 90s old." It means the driver refuses to read from members reported as more than 90s behind. Lag can spike between heartbeats.
- "`readConcern:"majority"` makes reads slower." Slightly — on primary it's barely measurable; on secondary it waits for the majority commit point.

## Brute force approach

`primary + linearizable` for every read. Maximally correct; serialises through primary; defeats horizontal read scaling; primary becomes bottleneck. Used only when the read must be globally fresh.

## Optimal approach

Decision tree:

```
  Is this read for state-of-record (post-write display, balance, inventory)?
  │
  ├─ YES → primary + readConcern:"majority" (RYW across cluster, rollback-safe)
  │         OR session with causal consistency
  │
  └─ NO → Is this analytics / reporting / batch?
          │
          ├─ YES → secondaryPreferred + maxStalenessSeconds + tag (analytics nodes)
          │         readConcern:"local" or "available" (sharded)
          │
          └─ NO → Is this a low-latency user-facing query that tolerates staleness?
                  │
                  ├─ YES → nearest + maxStalenessSeconds:120 + readConcern:"local"
                  │
                  └─ Conservative default → primary + "majority"
```

## Solution

```javascript
// ===== Scenario 1: order detail page right after checkout =====
// Must show the order that was just written. RYW required.
const order = await db.collection("orders").findOne(
  { _id: orderId },
  { readPreference: "primary", readConcern: { level: "majority" } }
);

// ===== Scenario 2: analytics dashboard, hourly aggregations =====
const pipeline = [
  { $match: { ts: { $gte: lastHour } } },
  { $group: { _id: "$category", total: { $sum: "$amount" } } }
];
const cur = db.collection("orders").aggregate(pipeline, {
  readPreference: {
    mode: "secondaryPreferred",
    tags: [{ workload: "analytics" }, {}],   // prefer tagged nodes, else any secondary
    maxStalenessSeconds: 300
  },
  readConcern: { level: "local" }
});

// ===== Scenario 3: globally distributed read, latency-sensitive =====
// Product catalog; eventual consistency fine.
const product = await db.collection("catalog").findOne(
  { sku },
  {
    readPreference: { mode: "nearest", maxStalenessSeconds: 120 },
    readConcern: { level: "local" }
  }
);

// ===== Scenario 4: causal consistency across operations =====
const session = client.startSession({ causalConsistency: true });
try {
  await db.collection("cart").updateOne(
    { _id: userId },
    { $push: { items: sku } },
    { session, writeConcern: { w: "majority" } }
  );
  // Subsequent read in same session sees the write, even on a secondary
  // (driver tracks operationTime and waits for it).
  const cart = await db.collection("cart").findOne(
    { _id: userId },
    {
      session,
      readPreference: "secondaryPreferred",
      readConcern: { level: "majority" }
    }
  );
} finally {
  await session.endSession();
}

// ===== Scenario 5: linearizable read (rare; e.g., distributed-lock check) =====
const heldBy = await db.collection("locks").findOne(
  { _id: "leader" },
  { readPreference: "primary", readConcern: { level: "linearizable" }, maxTimeMS: 5000 }
);
// Primary verifies its still primary by contacting majority — slow but safe.

// ===== Tag set replica config (analytics nodes) =====
rs.reconfig({
  _id: "rs0",
  members: [
    { _id: 0, host: "p:27017", tags: { role: "oltp" } },
    { _id: 1, host: "s1:27017", tags: { role: "oltp" } },
    { _id: 2, host: "s2:27017", tags: { role: "analytics", workload: "analytics" }, priority: 0, hidden: true }
  ]
});
// Hidden + priority 0 = won't be elected primary; analytics-only.

// ===== Quiz =====
// Q1: Fastest read, least guarantee?              A: nearest + local
// Q2: RYW across cluster, no session?              A: primary + majority
// Q3: Analytics, isolate from OLTP?                A: tag-set secondary
// Q4: Distributed-lock leader check?               A: primary + linearizable
// Q5: Default read preference?                     A: primary
// Q6: Default read concern on primary?             A: local
// Q7: Will secondaryPreferred + majority guarantee RYW?
//     A: Only with causal-consistent session; otherwise no.
```

## Step-by-step dry run

3-node replica set under steady write load (replication lag ~50ms). Same logical sequence under different settings:

```
t=0    Client A writes order ord-7 with w:"majority"  → ack at t=20
t=20   Client B (different process) reads ord-7

Case readPref:primary, readConcern:local        → finds ord-7  ✓ (RYW for B)
Case readPref:primary, readConcern:majority     → finds ord-7  ✓ (rollback-safe)
Case readPref:secondaryPreferred, local         → may NOT find ord-7 if S not caught up
Case readPref:nearest, local                     → may hit primary or secondary; uncertain
Case readPref:secondary + maxStaleness:90       → reads from S; ~50ms lag → finds ord-7
                                                  (but if lag spikes to 100s, refuses)
Case secondaryPreferred + causal session         → driver tracks opTime;
                                                   waits for S to catch up. Finds ord-7. ✓
```

Failover dry run:

```
Initial: P, S1, S2.   Client uses readPref:primary.
t=0    P partitioned away.
t=5    Election: S1 becomes new P. S1's oplog may lag P by some ops.
t=6    Client sees connection drop; driver discovers new P.
t=7    Reads from new P. Some recently-acked writes at old P (only w:1)
       may have been rolled back. Reads with majority readConcern would
       never have seen them; reads with local readConcern may have, then
       see them disappear. Use majority for rollback-safety.
```

## How to think aloud in the interview

> "I separate routing from consistency. `readPreference` picks the node; `readConcern` picks what view I get. Defaults: `primary + majority` for state-of-record, `secondaryPreferred + local + maxStaleness` for analytics, `nearest + local` for latency-sensitive eventually-consistent reads.
>
> The senior moves: I use tag sets to isolate analytics traffic on dedicated, hidden secondaries — protects OLTP from heavy aggregations. For RYW after a write without paying primary cost everywhere, I use causal-consistent sessions: the driver tracks the operation time and the secondary waits to catch up.
>
> I avoid bare `secondary` reads — `secondaryPreferred` is almost always better (falls back on failure). I reserve `linearizable` for genuinely linearizable use cases like leader-election checks; it's expensive.
>
> One gotcha I always audit: `readConcern:"local"` reads from primary can return data later rolled back if the primary loses an election. For correctness-critical reads, always pair primary with `majority`."

## Important takeaways

- Routing (`readPreference`) and consistency (`readConcern`) are orthogonal.
- Defaults: `primary + majority` for OLTP truth-of-record; `secondaryPreferred + local` for analytics.
- Use tag sets to isolate analytics from OLTP.
- Causal-consistent sessions give RYW even when reading from secondaries.
- `maxStalenessSeconds` is a *cap* not a *guarantee*.
- `linearizable` is slow; use only when you truly need it.
- Prefer `secondaryPreferred` over `secondary` for availability.

## Variants

1. **Hedged reads (sharded)** — sends to two members; uses first response. Reduces tail latency.
2. **Aggregation pipeline reads on secondaries** — fine, but `$out`/`$merge` must write to primary; pipeline routing rules matter.
3. **Tailable cursors on change streams** — bound to a single member; if it fails, resume with `resumeAfter` token.
4. **MongoDB Atlas analytics nodes** — managed equivalent of hidden, tagged secondaries; isolates BI traffic.
5. **`available` vs `local` on sharded clusters** — `available` ignores orphan-doc filtering, faster but may double-count during chunk migration.

## Revision notes

> **mongo read preference — 60s recap**
> - Two axes: `readPreference` (which node) + `readConcern` (what view).
> - OLTP truth-of-record: `primary + majority`.
> - Analytics: `secondaryPreferred + local + maxStalenessSeconds`, tagged nodes.
> - Latency-first user reads: `nearest + local + maxStaleness`.
> - RYW across nodes: causal-consistent session.
> - `linearizable`: rare, slow, only when needed.
> - Prefer `secondaryPreferred` to bare `secondary` for failover safety.
> - Tag sets to isolate analytics from OLTP secondaries.
