# MongoDB: Shard key design — high cardinality, low monotonicity

## Source / Origin
- Senior Mongo question. Asked at every Mongo-at-scale shop (Atlas customers, ad-tech, IoT).
- Concept reference: `backend-data-prep/nosql/04-mongodb.md` (sharding section), `03-replication-sharding.md`.

## Why this question matters in interviews
Choosing the wrong shard key is **unfixable without re-sharding the whole collection**. A monotonic key like `ObjectId` or `timestamp` puts *all* writes on one shard. A low-cardinality key like `country` creates jumbo chunks. The senior signal: you name the three properties (cardinality, frequency, monotonicity), give the canonical anti-pattern (`_id` as shard key), and propose hashed or compound alternatives.

## Concepts involved

### Syntax to lock in

```javascript
// Enable sharding
sh.enableSharding("shop");

// Create a shard key (must be indexed first)
db.orders.createIndex({ customerId: 1, createdAt: 1 });
sh.shardCollection("shop.orders", { customerId: 1, createdAt: 1 });

// Hashed shard key (avoids monotonic hotspot)
db.events.createIndex({ deviceId: "hashed" });
sh.shardCollection("shop.events", { deviceId: "hashed" });

// View distribution
sh.status();
db.orders.getShardDistribution();
```

### The three properties

| Property | What to want | Anti-example |
|---|---|---|
| **Cardinality** | High — many distinct values | `country` (200 values), `gender` (3) |
| **Frequency** | Even — no value dominates | `userId` where 1 celebrity = 80% writes |
| **Monotonicity** | NOT monotonic — values shouldn't grow over time | `ObjectId`, `createdAt`, autoincrement |

### Edge cases / interview traps

1. **Default `_id` (ObjectId) as shard key** — monotonic; writes pile up on the last chunk's shard. **Worst common choice.** Use `{ _id: "hashed" }` instead.
2. **`createdAt` as shard key** — same problem; useful only with hashed prefix or compound.
3. **`userId` with a celebrity** — high cardinality but skewed frequency. Mitigation: add a random suffix (`userId:bucket0..7`).
4. **Compound shard key** — `{ tenantId: 1, _id: 1 }` keeps a tenant's data co-located but spreads tenants.
5. **Cannot change shard key** before Mongo 4.4; **can refine** after 4.4 (add suffix); only **reshardCollection** in 5.0+.
6. **Targeted vs scatter-gather queries** — queries that include the shard key go to one shard (fast); queries without it hit all shards (slow).
7. **Jumbo chunks** — a chunk that can't be split because all docs share the same shard-key value. Always avoid.
8. **Zone sharding** — pin shard ranges to physical regions (data sovereignty).

## Mental Model

> Imagine 4 warehouses (shards). Shard key = the rule that decides which warehouse each crate goes to.
> - **High cardinality** → many possible labels → can spread evenly.
> - **Even frequency** → no warehouse gets 80% of crates.
> - **Not monotonic** → newest crates don't all pile into Warehouse 4 just because the label increased.

```
   GOOD:  shard key = hash(deviceId)
                ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
   writes  →    │ S1  │ │ S2  │ │ S3  │ │ S4  │     even spread
                └─────┘ └─────┘ └─────┘ └─────┘

   BAD:   shard key = _id (ObjectId, monotonic)
                ┌─────┐ ┌─────┐ ┌─────┐ ┌█████┐
   writes  →    │     │ │     │ │     │ │█HOT█│     all new writes pile up
                └─────┘ └─────┘ └─────┘ └─────┘

   BAD:   shard key = country
                ┌─────┐ ┌─────┐ ┌█████┐ ┌─────┐
   writes  →    │ FR  │ │ UK  │ │█US█ │ │ DE  │     skewed, jumbo chunks
                └─────┘ └─────┘ └─────┘ └─────┘
```

## Why interviewers care

- **Tests irreversibility awareness** — shard key choice is the single most expensive mistake.
- **Tests distribution reasoning** — you can talk about hash vs range, hot keys, query routing.
- **Tests operational maturity** — chunks, migrations, balancer, zones are senior-level vocabulary.

## Common beginner confusion

- "I'll shard by `_id`." Monotonic; hot last shard. Always hash if you do.
- "Higher cardinality = better." Only if frequency is also even. Celebrity `userId` has high cardinality but pathological frequency.
- "Shard everything." Sharding has overhead; collections under ~100 GB usually don't need it.
- "Shard key = primary key." Different — shard key just decides routing; `_id` is still PK.
- "Compound shard key is just a multi-key index." It's also the routing function — leading prefix matters.
- "Hashed shard keys give exact range queries." They don't — range queries become scatter-gather.

## Brute force approach

Pick `_id` as shard key because it's already indexed. Mongo even lets you do it. You will regret it the moment write traffic spikes.

## Optimal approach

Pick from your **most common targeted query**. Examples:
- Per-tenant SaaS: `{ tenantId: 1, _id: 1 }` — keeps a tenant on one shard; spreads tenants.
- IoT events: `{ deviceId: "hashed" }` — random spread; range queries are scatter (acceptable for analytics).
- User-scoped data: `{ userId: "hashed" }` — spreads users; if celebrity is a risk, prefix-bucket the userId.
- Time-series: `{ metadata.sensorId: 1, timestamp: 1 }` — co-locate by sensor; index supports time ranges within.

## Solution (Mongo shell)

```javascript
// === Case 1: per-tenant SaaS (compound) ===
db.documents.createIndex({ tenantId: 1, _id: 1 });
sh.shardCollection("app.documents", { tenantId: 1, _id: 1 });
// Queries:
//   db.documents.find({ tenantId: "T-9" })            → targeted (one shard)
//   db.documents.find({ _id: ... })                   → scatter (no shard key)
//   db.documents.find({ tenantId: "T-9", _id: ... })  → targeted

// === Case 2: IoT events (hashed) ===
db.events.createIndex({ deviceId: "hashed" });
sh.shardCollection("iot.events", { deviceId: "hashed" });
// Queries:
//   db.events.find({ deviceId: "D-1" })                   → targeted
//   db.events.find({ ts: { $gt: t } })                    → scatter-gather
//   db.events.find({ deviceId: "D-1", ts: { $gt: t } })   → targeted, then range within

// === Case 3: celebrity-safe userId ===
function bucketedId(userId) {
  const suffix = murmur3(userId) % 16;     // 16 buckets
  return `${userId}#${suffix}`;
}
db.activity.createIndex({ bucketedKey: "hashed" });
sh.shardCollection("app.activity", { bucketedKey: "hashed" });
// Write: bucketedKey = bucketedId(userId)
// Read: bucketedKey IN [`${userId}#0`, ..., `${userId}#15`]  → scatters across 16, never one celeb shard

// === Refining a shard key (Mongo 4.4+) ===
sh.refineCollectionShardKey("shop.orders", { customerId: 1, _id: 1 });
// adds suffix, doesn't move data; future inserts split chunks more finely.

// === Resharding (Mongo 5.0+) ===
db.adminCommand({ reshardCollection: "shop.orders", key: { customerId: "hashed" } });
// expensive — rewrites the whole collection in the background.

// === Zone sharding (data sovereignty) ===
sh.addShardTag("shard0001", "EU");
sh.addShardTag("shard0002", "EU");
sh.addShardTag("shard0003", "US");
sh.addTagRange("app.users", { region: "EU", _id: MinKey }, { region: "EU", _id: MaxKey }, "EU");
```

## Step-by-step dry run

```
Scenario: 4 shards (S1..S4). Insert 1M user-activity events.

ANTI-PATTERN: shard key = { createdAt: 1 }
  Every new doc has ts >= last doc's ts.
  All writes hit the last chunk on S4.
  S4 CPU 90%, S1..S3 idle.
  Eventually S4 chunk splits; balancer migrates; brief relief; pattern resumes.

FIX A: shard key = { createdAt: "hashed" }
  Hash spreads writes across all 4 shards by hash mod 4.
  Range query "events in last hour" → scatter-gather (visit all 4).
  OK for low-frequency analytics; bad for hot-path scrolls.

FIX B: shard key = { deviceId: 1, createdAt: 1 }
  Co-locates a device's history; spreads devices.
  "events for device D last hour" → targeted (1 shard, range within).
  "all events last hour" → still scatter, but each shard answers locally.

CELEBRITY: one deviceId = 80% writes
  Even FIX B has a hot shard for that device.
  FIX C: pre-shard the device → shard key = { deviceBucket: 1, createdAt: 1 }
         deviceBucket = `${deviceId}#${hash(ts) % 8}`
         8 chunks spread across 8 shards; reads merge from 8 buckets.
```

## How to think aloud in the interview

> "Three properties: cardinality, frequency, monotonicity. The shard key needs all three right or you get a hot shard or jumbo chunks.
>
> Default ObjectId is monotonic — terrible shard key for writes; hashed _id fixes the monotonicity but loses range query locality. So I pick based on the most common targeted query. For per-tenant SaaS, `{tenantId, _id}` co-locates a tenant; for IoT, `{deviceId hashed}` spreads writes; for celebrities I bucketize with a random suffix.
>
> The big trap is that pre-4.4 you cannot change a shard key. 4.4 lets you refine (add a suffix), 5.0 lets you reshard (background rewrite, expensive). So I treat this as an architectural decision and over-document it.
>
> I always check `sh.getShardDistribution()` after seeding 10% of expected traffic — if any shard owns >40% of the chunks I redesign before going to prod."

## Important takeaways

- **High cardinality, even frequency, not monotonic.** Three properties — pick a key that satisfies all.
- **`_id` (ObjectId) is monotonic.** Use `{ _id: "hashed" }` only.
- **Hashed = even writes, scatter reads.** Range = co-located, hot tail.
- **Compound `{tenantId, _id}`** balances both for multi-tenant.
- **Celebrity = bucket-suffix.** 8–16 buckets is usually enough.
- **Cannot change pre-4.4. Refine 4.4+. Reshard 5.0+ (expensive).**
- **Verify distribution early** with `sh.getShardDistribution()`.

## Variants

1. **Time-series collections** — Mongo 5.0+ does the bucketing for you on `metaField + timeField`.
2. **Zone sharding** — pin ranges to geographic shards for data sovereignty.
3. **Refining shard key** — 4.4+; adds suffix without rewriting data.
4. **Reshard** — 5.0+; full background rewrite.
5. **Hashed `_id` with TTL** — works for short-lived events; expiry doesn't fight monotonicity.
6. **Pre-split chunks** — for bulk loads, pre-create chunk boundaries to avoid balancer churn.
7. **Compound hashed** (5.0+) — `{tenantId: 1, _id: "hashed"}` co-locates tenant but hashes within.

## Revision notes

> **shard key design — 60s recap**
> - Three properties: high cardinality, even frequency, NOT monotonic.
> - `_id` (ObjectId) is monotonic → hot last shard → use `{_id: "hashed"}`.
> - Compound `{tenantId, _id}` for multi-tenant SaaS.
> - Hashed for even spread; range for co-location.
> - Celebrity → bucket-suffix shard key (`userId#0..7`).
> - Pre-4.4: cannot change. 4.4: refine. 5.0: reshard (expensive).
> - Always verify `sh.getShardDistribution()` after 10% load.
> - Targeted query = includes shard key; scatter-gather = doesn't.
