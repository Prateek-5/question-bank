# DynamoDB: Hot partition — write sharding, suffix randomization

## Source / Origin
- "Live debugging" question at Amazon / AWS interviews. Often presented as a war story.
- Concept reference: `backend-data-prep/nosql/05-dynamodb-cassandra.md`.

## Why this question matters in interviews
Hot partition is the #1 production incident in DynamoDB shops. The interviewer hands you a `ProvisionedThroughputExceededException` and asks "what now?". The naive answer ("bump capacity") doesn't work — per-partition limits cap you. Senior signal: you diagnose with CloudWatch Contributor Insights, propose **write sharding (suffix bucketing)**, and discuss the **read amplification cost**.

## Concepts involved

### Syntax to lock in

```javascript
// Random suffix to disperse writes across N buckets
function shardPK(key, n = 10) {
  const suffix = Math.floor(Math.random() * n);
  return `${key}#${suffix}`;
}

// Write
await ddb.put({ TableName: "Events", Item: {
  PK: shardPK("CELEB-USER-1"),    // CELEB-USER-1#0..9
  SK: new Date().toISOString(),
  payload: "..."
}});

// Read: scatter across all N buckets, then merge
async function readAllShards(key, opts) {
  const results = await Promise.all(
    Array.from({ length: 10 }, (_, i) =>
      ddb.query({
        TableName: "Events",
        KeyConditionExpression: "PK = :pk AND SK BETWEEN :a AND :b",
        ExpressionAttributeValues: {
          ":pk": `${key}#${i}`,
          ":a": opts.from,
          ":b": opts.to
        }
      })
    )
  );
  return results.flatMap(r => r.Items).sort((a, b) => a.SK.localeCompare(b.SK));
}
```

### Sharding strategies

| Strategy | When | Read pattern |
|---|---|---|
| **Random suffix (write-sharding)** | Don't care which shard a write lands in | Scatter across all N buckets |
| **Deterministic suffix from payload** | Need to find a specific write later | Single targeted read if you know the suffix mapping |
| **Hash-prefix** | Monotonic ID problem | Same as random suffix |
| **Time-bucketed PK** | High-volume telemetry | Read by day-bucket → naturally bounded |

### Edge cases / interview traps

1. **Adaptive capacity ≠ infinite.** It re-allocates capacity across partitions over **minutes**, not seconds.
2. **Burst capacity ≠ rescue.** 5-min credit; helps spikes, not sustained hot.
3. **Read amplification cost** of write-sharding: every read becomes N parallel queries.
4. **Suffix cardinality vs read cost tradeoff.** 10 buckets ≈ 10× reads; 100 buckets ≈ 100× reads. Pick the lowest N that disperses your write rate.
5. **Hot READ partition (rare)** — same fix; replicate read shards via DAX or GSI.
6. **CloudWatch Contributor Insights** is the diagnostic — top contributor keys = hot PK.
7. **Cold partitions** post-fix — old data sits in shards that have no further writes; that's fine.
8. **Sharded write to GSI** — GSI partition limits apply too; sharding may need to propagate to GSI keys.

## Mental Model

> Hot partition = one queue with all the customers. Write sharding = open N parallel queues with a random doorman. Each writer gets a fast lane; readers visit all N queues and merge.

```
   BEFORE: PK = "CELEB-USER-1"
            ┌──────┐ ┌──────┐ ┌──────┐ ┌█████┐
   →        │      │ │      │ │      │ │█HOT█│   1000 WCU cap → throttle
            └──────┘ └──────┘ └──────┘ └─────┘

   AFTER:  PK = "CELEB-USER-1#" + random(0..9)
            ┌─█──┐ ┌─█──┐ ┌─█──┐ ┌─█──┐ ┌─█──┐ ...   (10 buckets)
   →        │    │ │    │ │    │ │    │ │    │       100 WCU each → safe
            └────┘ └────┘ └────┘ └────┘ └────┘

   READ:    Query(PK#0), Query(PK#1), ..., Query(PK#9)  → merge sorted by SK
```

## Why interviewers care

- Tests **diagnosis-under-fire** — name the metric, name the fix.
- Tests **read-write tradeoff reasoning** — write-sharding shifts cost to reads.
- Tests **knowledge of AWS levers** — adaptive, burst, Contributor Insights, DAX.

## Common beginner confusion

- "On-demand fixes hot partitions." It doesn't; per-partition limits apply.
- "Increase provisioned capacity." Capacity is spread across partitions; one hot partition still caps.
- "DAX caches solve it." Only for reads, and only for repeated keys.
- "Use GSI to spread." GSI has its own partition rules.
- "Re-shard at runtime." Possible but expensive; pre-shard from the start when you know the access pattern.
- "Bigger N is always better." Read cost scales linearly with N.

## Brute force approach

`Increase WCU to 10× and hope`. Doesn't fix per-partition cap. Watch CloudWatch ThrottledWriteRequests stay high. Useless.

## Optimal approach

1. **Identify the hot PK** via Contributor Insights.
2. **Estimate the write rate** for that PK.
3. **Pick N** = ceil(write_rate / 800 WCU). 10 is typical, 100 for extreme.
4. **Migrate writes** to suffixed PK (`PK#bucket`).
5. **Update reads** to scatter-gather across buckets.
6. **Validate** with synthetic load + Contributor Insights post-fix.

## Solution (Node + DynamoDB)

```javascript
// === Diagnostic: show top contributors ===
// AWS Console → CloudWatch → Contributor Insights → "MostAccessedKeys" rule
// Top contributor: PK = "CELEB-USER-1" with 90% of consumed WCU.

// === Step 1: pick N ===
// Sustained write rate for CELEB-USER-1 = 5000 WCU
// 5000 / 800 (safety margin under 1000 cap) = ~7 → round up to 10.

const SHARD_COUNT = 10;
function shardPK(key) {
  return `${key}#${Math.floor(Math.random() * SHARD_COUNT)}`;
}

// === Step 2: write with sharded PK ===
async function writeEvent(userId, event) {
  await ddb.put({
    TableName: "Events",
    Item: {
      PK: shardPK(userId),
      SK: event.ts + "#" + event.id,
      payload: event.payload
    }
  });
}

// === Step 3: scatter-gather read ===
async function readEvents(userId, fromTs, toTs, limit = 50) {
  const buckets = await Promise.all(
    Array.from({ length: SHARD_COUNT }, (_, i) =>
      ddb.query({
        TableName: "Events",
        KeyConditionExpression: "PK = :pk AND SK BETWEEN :a AND :b",
        ExpressionAttributeValues: {
          ":pk": `${userId}#${i}`,
          ":a": fromTs,
          ":b": toTs
        },
        Limit: limit
      })
    )
  );
  // K-way merge by SK
  const merged = buckets.flatMap(b => b.Items)
                        .sort((x, y) => x.SK.localeCompare(y.SK));
  return merged.slice(0, limit);
}

// === Step 4: deterministic suffix (if you need to look up a specific item) ===
function deterministicShardPK(userId, eventId) {
  const h = hashStr(eventId) % SHARD_COUNT;
  return `${userId}#${h}`;
}
// Now a point-lookup can compute the bucket without scatter.
```

### Migration plan for live tables

```javascript
// Dual-write phase
async function writeEvent(userId, event) {
  await Promise.all([
    ddb.put({ TableName: "Events", Item: { PK: userId, SK: ..., ... } }),       // old
    ddb.put({ TableName: "Events", Item: { PK: shardPK(userId), SK: ..., ... } }) // new
  ]);
}

// Backfill in batches (read old PK rows, re-PUT with sharded PK)
// Cutover reads
// Stop dual-write
```

## Step-by-step dry run

```
Diagnosis:
  CloudWatch ThrottledRequests > 0 for 30 min.
  Contributor Insights top key: PK = "CHANNEL-NEWS" at 4500 WCU consumed.
  ProvisionedWCU = 10000 globally, but per-partition cap = 1000.

Action:
  N = ceil(4500 / 800) = 6 → use 10 buckets.
  Roll out dual-write to PK = "CHANNEL-NEWS#0..9".

After 10-bucket sharding:
  Each bucket consumed ~450 WCU → well under 1000 cap.
  Total writes spread; no throttling.

Read pattern:
  Before: 1 Query for "feed for CHANNEL-NEWS".
  After:  10 parallel Queries, merge by SK, take top-N.
  Latency: dominated by slowest query (~p99 of single shard, not 10×).
  Cost:    10× RCU but each query smaller, so net ~3× depending on result merge.

Choice of N=10:
  N=5  → 900 WCU/bucket → too close to cap.
  N=10 → 450 WCU/bucket → safe with headroom.
  N=100→ 45 WCU/bucket → safe but 100× read cost. Overkill.
```

## How to think aloud in the interview

> "Three steps: diagnose, shard, validate. Diagnose with Contributor Insights — find the top contributor PK. If one PK is more than ~30% of consumed capacity, that's the hot partition.
>
> Bumping global capacity doesn't help — per-partition cap is 1000 WCU regardless. So I write-shard the hot PK with a random suffix: `PK#bucket0..9`. Writes scatter. Reads do scatter-gather across all N buckets.
>
> Picking N: roughly write_rate / 800 (leaving headroom under 1000). 10 is the typical sweet spot; 100 only for extreme hotspots. Each additional bucket scales reads linearly, so I pick the smallest N that disperses.
>
> If I need to find a specific item later, I use a *deterministic* suffix derived from a known key (hash of eventId mod N) instead of random — that way point-lookups stay targeted.
>
> Migration is dual-write, backfill, cutover. Never a flag-day flip; always a graceful migration."

## Important takeaways

- **Per-partition: 1000 WCU / 3000 RCU.** Hard cap.
- **Diagnose with Contributor Insights.** Top contributor keys.
- **Write-shard with suffix.** `PK#bucket(0..N)`.
- **N = ceil(write_rate / 800).** Round up; 10 is typical.
- **Read amplification = N.** Pick smallest viable N.
- **Deterministic suffix** if you need point-lookups; random for write-only fanout.
- **Migration = dual-write + backfill + cutover.**
- **Adaptive/burst capacity ≠ rescue** from sustained hot partition.

## Variants

1. **Time-bucketed PK** — `PK = entity#yyyy-mm-dd`; naturally bounds per-day writes.
2. **Hot read partition** — same fix; or front with DAX.
3. **Hot GSI partition** — apply sharding to GSI PK attributes.
4. **Auto-shard discovery** — use a `shardCount` config row in DDB; readers consult it before scatter.
5. **Combination with random + time** — `PK = entity#yyyy-mm#bucket(0..n)` for very high volume.
6. **Reverse migration** — when hot key cools, you may want to consolidate; rarely worth it.

## Revision notes

> **hot partition fix — 60s recap**
> - Per-partition cap: 1000 WCU / 3000 RCU. Bumping global capacity doesn't help.
> - Diagnose: CloudWatch Contributor Insights → top contributors by PK.
> - Fix: write-shard PK with suffix `key#bucket(0..N)`.
> - N = ceil(write_rate / 800). Usually 10.
> - Read = scatter-gather N parallel Queries + K-way merge by SK.
> - Deterministic suffix (hash) if you need point-lookups.
> - Migration: dual-write → backfill → cutover.
> - Adaptive capacity = minutes. Burst = 5 min credit. Neither saves sustained hot.
