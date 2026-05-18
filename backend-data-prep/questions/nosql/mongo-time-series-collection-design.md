# MongoDB: Time-series collection design — meta + granularity

## Source / Origin
- Mongo 5.0+ specific feature. Asked at IoT, observability, finance interviews.
- Concept reference: `backend-data-prep/nosql/04-mongodb.md` (time-series section).
- Cross-ref: shard key design, observability metrics.

## Why this question matters in interviews
Time-series collections are Mongo's answer to InfluxDB / Timescale. Used right, they reduce storage 10× and accelerate range queries. Used wrong (wrong `metaField`, wrong `granularity`), you get *worse* than a regular collection. Senior signal: you understand the **bucketing model**, choose **metaField** based on access pattern, and know when **time-series collections are wrong** (high-cardinality metaField).

## Concepts involved

### Syntax to lock in

```javascript
db.createCollection("readings", {
  timeseries: {
    timeField:   "ts",            // REQUIRED — the time component of each measurement
    metaField:   "deviceId",       // OPTIONAL but recommended — groups same-source rows
    granularity: "seconds"         // "seconds" | "minutes" | "hours" — bucket size hint
  },
  expireAfterSeconds: 60 * 60 * 24 * 30   // TTL on each measurement; auto-drops old buckets
});

// Insert as if it were a regular collection — Mongo buckets internally
db.readings.insertOne({
  ts: new Date(),
  deviceId: "D-42",
  cpu: 0.87,
  mem: 2.1,
  region: "us-east-1"
});

// Query as normal — Mongo rewrites against the bucket collection
db.readings.find({
  deviceId: "D-42",
  ts: { $gte: ISODate("2026-05-17T00:00:00Z"), $lt: ISODate("2026-05-17T01:00:00Z") }
});
```

### Edge cases / interview traps

1. **No `metaField` = poor compression.** Mongo can't group same-source rows into one bucket.
2. **High-cardinality metaField is wrong.** `metaField: "requestId"` (unique per row) means one bucket per row — defeats the purpose.
3. **Granularity hint vs reality.** `"seconds"` = up to 1h per bucket; `"minutes"` = up to 24h; `"hours"` = up to 30d. Mismatch = wasted scans.
4. **No unique indexes on data fields** (other than the bucket-internal index). Plan dedup at the app layer.
5. **No transactions across TS and regular collections (5.0, fixed in 5.1+).**
6. **Schema-on-write is loose** but you can't change `timeField`/`metaField` after creation.
7. **Updates in place are limited** — recent Mongo versions support targeted updates by `metaField + timeField`; old versions don't.
8. **Sharding** — Mongo 5.1+ supports sharded time-series. Shard key includes `metaField`.

## Mental Model

> Mongo silently maintains a **bucket collection** under the hood. Each bucket holds many measurements with the **same metaField value** within a **bounded time window**. Reads project bucket fields back into row-shaped docs.

```
   Measurements (logical):
     { ts, deviceId, cpu, mem }
     { ts, deviceId, cpu, mem }
     { ts, deviceId, cpu, mem }   ← all deviceId=D-42 within one hour
     ...

   Underlying bucket (physical):
     {
       _id: ...,
       control: { min: {ts:..., cpu:0.2}, max: {ts:..., cpu:0.9}, count: 87 },
       meta:    "D-42",
       data: {
         ts:  [t1, t2, t3, ..., t87],
         cpu: [0.2, 0.3, ..., 0.9],
         mem: [2.0, 2.1, ..., 2.4]
       }
     }
   → columnar layout inside the bucket → great compression and range scan.
```

When you query `find({deviceId:"D-42", ts: range})`, Mongo prunes by bucket metadata (`control.min.ts`/`control.max.ts`/`meta`), opens only the relevant buckets, and reconstitutes rows.

## Why interviewers care

- Tests **awareness of the columnar storage trick** — same data, different layout.
- Tests **metaField choice** — the single most important decision.
- Tests **knowing limits** — no unique indexes on data, limited updates, sharding caveats.

## Common beginner confusion

- "Just put a TTL on a regular collection." Works but no compression win.
- "MetaField = primary key." No — it's a grouping label. Many rows share it.
- "High-cardinality metaField is fine." It defeats bucketing. Each bucket holds one row.
- "I can update any field." Recent versions allow `metaField` + `timeField`-keyed updates only.
- "Granularity = my sample rate." It's a *bucket size hint*; pick based on how often each metaField writes.

## Brute force approach

A regular collection `db.metrics` with index `{deviceId: 1, ts: -1}`. Works; storage ~5–10× larger; range scans visit one doc per measurement.

## Optimal approach

Time-series collection with:
- `timeField`: the measurement timestamp.
- `metaField`: the lowest-cardinality grouping that matches your dominant query — usually deviceId, sensorId, hostname, or `{deviceId, region}`.
- `granularity`: matches average inter-write gap. If a metaField writes every second, `"seconds"`; every minute, `"minutes"`; every hour, `"hours"`.
- TTL via `expireAfterSeconds`.

## Solution (Mongo shell)

```javascript
// === Create the collection ===
db.createCollection("readings", {
  timeseries: {
    timeField:   "ts",
    metaField:   "deviceId",
    granularity: "seconds"
  },
  expireAfterSeconds: 60 * 60 * 24 * 30    // 30-day retention
});

// === Insert ===
db.readings.insertMany([
  { ts: new Date("2026-05-17T12:00:00Z"), deviceId: "D-42", cpu: 0.81, mem: 2.0 },
  { ts: new Date("2026-05-17T12:00:01Z"), deviceId: "D-42", cpu: 0.83, mem: 2.0 },
  { ts: new Date("2026-05-17T12:00:00Z"), deviceId: "D-99", cpu: 0.10, mem: 1.1 }
]);

// === Range query per device ===
db.readings.find({
  deviceId: "D-42",
  ts: { $gte: ISODate("2026-05-17T12:00:00Z"), $lt: ISODate("2026-05-17T13:00:00Z") }
}).sort({ ts: 1 });

// === Aggregation: 1-minute downsampling ===
db.readings.aggregate([
  { $match: { deviceId: "D-42", ts: { $gte: hourAgo() } } },
  { $group: {
      _id: {
        deviceId: "$deviceId",
        minute: { $dateTrunc: { date: "$ts", unit: "minute" } }
      },
      avgCpu: { $avg: "$cpu" },
      maxCpu: { $max: "$cpu" }
  }},
  { $sort: { "_id.minute": 1 } }
]);

// === $densify + $fill for gap-free time buckets ===
db.readings.aggregate([
  { $match: { deviceId: "D-42", ts: { $gte: hourAgo() } } },
  { $densify: { field: "ts", range: { step: 1, unit: "minute", bounds: "full" } } },
  { $fill:    { sortBy: { ts: 1 }, output: { cpu: { method: "linear" } } } }
]);

// === Sharded (5.1+) ===
sh.shardCollection("metrics.readings", { deviceId: 1, ts: 1 });

// === Compound metaField (object) ===
db.createCollection("ops", {
  timeseries: {
    timeField: "ts",
    metaField: "tags",      // tags is an object: { host, region, service }
    granularity: "minutes"
  }
});
// Query: { "tags.host": "h-1", "tags.region": "us-east-1", ts: {...} }
```

## Step-by-step dry run

```
Workload: 1K IoT devices, each writing one row/second.

Regular collection (baseline):
  86.4M docs/day, ~10 GB/day raw.
  Range scan "D-42 last hour" = 3600 docs read.

Time-series with metaField=deviceId, granularity=seconds:
  Mongo packs ~1000 rows per bucket (one bucket per device per ~16min window).
  1K devices × 86 buckets/day = 86K bucket docs/day, ~1 GB/day after columnar compression.
  Range scan "D-42 last hour" = ~4 bucket docs read, prune internal arrays by ts range.
  10× storage win, 100× scan win.

Wrong metaField=requestId (high cardinality):
  Each row gets its own bucket → 86.4M buckets/day → WORSE than regular.

Wrong granularity=hours when writes are per second:
  Bucket too large; control.min/max ranges span all rows in the bucket;
  range queries can't prune internal arrays effectively.
  Some storage win, no scan win.
```

## How to think aloud in the interview

> "Time-series collections in Mongo 5.0+ are a columnar bucketing layer hidden behind a row-shaped API. Inserts look normal; under the hood Mongo packs same-`metaField` rows within a time window into one bucket doc, columnar within. Compression is 5–10× and range scans prune by bucket metadata.
>
> Choosing `metaField` is the whole game. It must be **low cardinality relative to row count** — typically deviceId, hostname, sensorId. The mistake is picking something unique per row (requestId, traceId), which defeats bucketing.
>
> `granularity` is a *bucket size hint*. Seconds = up to 1h per bucket. Minutes = up to 24h. Hours = up to 30d. Match it to your average inter-write interval per metaField.
>
> Limitations: no unique indexes on measurements, limited update semantics, sharding only since 5.1. TTL via `expireAfterSeconds` cleans up old buckets automatically — that's the only retention I need."

## Important takeaways

- **Time-series = columnar buckets under a row API.** Hidden bucket collection.
- **metaField choice is critical.** Low cardinality, matches dominant access pattern.
- **granularity hint matches inter-write interval.** Seconds / minutes / hours.
- **TTL via `expireAfterSeconds`.** Automatic retention.
- **Wrong metaField (high cardinality) is worse than no time-series.**
- **Limited mutability.** Recent versions allow targeted updates only.
- **Sharding from 5.1+.** Shard key includes metaField.
- **`$densify` + `$fill`** for gap-free time bucket aggregations.

## Variants

1. **Compound metaField** (object) — `metaField: "tags"` with `{host, region, service}` inside.
2. **Compressed JSON ingestion** — use a $merge from staging to TS collection nightly.
3. **Combined with change streams** — emit downsampled views post-insert.
4. **Hot-tier + cold-tier** — recent in TS, archived to S3 via Atlas Online Archive.
5. **High-cardinality fallback** — for unique IDs, fall back to regular collection + manual bucketing.
6. **Continuous aggregations** — schedule `$out`/`$merge` to materialize 1-min / 5-min rollups.

## Revision notes

> **time-series collection — 60s recap**
> - Mongo 5.0+. Columnar bucket layer hidden behind row API.
> - `timeField` required; `metaField` strongly recommended; `granularity` hint.
> - metaField = LOW cardinality (deviceId, hostname, sensorId). High cardinality kills it.
> - granularity matches inter-write interval per metaField.
> - TTL via `expireAfterSeconds` auto-drops old buckets.
> - 5–10× storage win, prune by bucket metadata for range scans.
> - No unique indexes on measurements; limited updates.
> - Sharding 5.1+; shard key must include metaField.
> - `$densify` + `$fill` for gap-free time buckets.
