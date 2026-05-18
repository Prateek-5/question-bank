# Cassandra: Time-series rotation — bucketed tables, TTL, TWCS

## Source / Origin
- Asked at IoT, telemetry, observability shops using Cassandra.
- Concept reference: `backend-data-prep/nosql/05-dynamodb-cassandra.md`.

## Why this question matters in interviews
Time-series in Cassandra is **the textbook unbounded-partition trap**. A naive design (`PRIMARY KEY (device_id, ts)`) grows partitions forever, blowing past the 100 MB / 100K-row soft limits in weeks. Senior signal: you bucket by time, pick the right window size, use `TimeWindowCompactionStrategy`, and pair with TTL for retention.

## Concepts involved

### Syntax to lock in

```sql
-- Bucketed time-series table
CREATE TABLE readings (
  device_id  uuid,
  bucket     date,        -- 1-day bucket
  ts         timestamp,
  value      double,
  PRIMARY KEY ((device_id, bucket), ts)
) WITH CLUSTERING ORDER BY (ts DESC)
  AND default_time_to_live = 2592000               -- 30 days
  AND gc_grace_seconds = 86400                      -- 1 day (whole-bucket drop)
  AND compaction = {
    'class':                 'TimeWindowCompactionStrategy',
    'compaction_window_unit':'DAYS',
    'compaction_window_size':'1'
  };

-- Insert
INSERT INTO readings (device_id, bucket, ts, value)
VALUES (?, ?, ?, ?) USING TTL 2592000;

-- Read latest day for a device
SELECT * FROM readings
WHERE device_id = ? AND bucket = ?
ORDER BY ts DESC LIMIT 100;

-- Read range across buckets (multi-query)
-- for day in [start..end]: query each bucket separately, merge in app
```

### Bucket window sizing

| Write rate per device | Window | Rows/partition (target ≤ 100K) |
|---|---|---|
| 1 / hour | 30 days | ~720 |
| 1 / minute | 1 day | 1440 |
| 1 / second | 1 hour | 3600 |
| 100 / second | 1 hour | 360K  (too big — go 10-min) |

Pick the window so `rows_per_window × estimated_row_size < 100 MB` and `rows_per_window < 100K`.

### Edge cases / interview traps

1. **Unbucketed PK = unbounded partition.** Worst time-series design.
2. **Bucket too small** = many partitions; cross-bucket range queries pay coordinator overhead.
3. **Bucket too large** = jumbo partitions.
4. **TWCS + TTL** is the magic combo: SSTable per window; expire whole SSTable when bucket TTL passes; **zero per-row tombstone reads**.
5. **gc_grace_seconds = TTL bucket length or less** for whole-bucket expiry. Default 10 days defeats the win.
6. **`UNLOGGED BATCH` across buckets** — OK if same partition; cross-partition batches are expensive.
7. **Read across N buckets** — fan-out in app; coordinator doesn't auto-merge across PKs.
8. **Schema for ad-hoc queries** — Cassandra doesn't do them; pre-compute or use Spark/Trino.

## Mental Model

> Time-series in Cassandra = **rotating logs on disk**. Each day's partition is a separate log file; old logs expire and drop as whole units; new writes append to today's log. TWCS sizes each SSTable to one window so compaction is trivial.

```
   Time axis →
   |  bucket=2026-05-15  |  bucket=2026-05-16  |  bucket=2026-05-17  |
   |  SSTable_day15      |  SSTable_day16      |  SSTable_day17      |  (TWCS)
   |  TTL expires day45  |  TTL expires day46  |  TTL expires day47  |

   On expiry: SSTable dropped as a unit → no per-row tombstone reads.
```

## Why interviewers care

- Tests **partition-bounding instinct** — the #1 time-series mistake.
- Tests **operational fluency** — TWCS + TTL combo isn't beginner-obvious.
- Tests **read-fan-out tradeoff** — bucket size affects multi-day queries.

## Common beginner confusion

- "Just use TTL." TTL alone causes tombstone explosions without bucketing.
- "Use STCS for time-series." Defeats whole-SSTable expiry.
- "Bucket by month for simplicity." 30× the rows per partition — explodes.
- "Cassandra handles range queries across buckets." No; you must query each bucket and merge in app.
- "Set gc_grace_seconds to default 10 days." For TWCS-with-TTL, set it to ≤ bucket length so whole SSTables can drop.

## Brute force approach

`PRIMARY KEY (device_id, ts)` with TTL only. Partitions grow until they break Cassandra; tombstones accumulate as TTL expires individual rows. Worst common design.

## Optimal approach

1. Estimate write rate per device.
2. Pick bucket window so rows/window < 100K and partition size < 100 MB.
3. Add `bucket` to the partition key: `PRIMARY KEY ((device_id, bucket), ts)`.
4. Use TWCS with the same window unit.
5. Set TTL via `default_time_to_live`.
6. Set `gc_grace_seconds ≤ bucket window` to allow whole-SSTable drops.
7. App-side: when reading a time range, query each bucket in the range, merge.

## Solution (CQL + Node fanout)

```sql
-- === Table ===
CREATE TABLE readings (
  device_id  uuid,
  bucket     date,
  ts         timestamp,
  value      double,
  PRIMARY KEY ((device_id, bucket), ts)
) WITH CLUSTERING ORDER BY (ts DESC)
  AND default_time_to_live = 2592000
  AND gc_grace_seconds = 86400
  AND compaction = {
    'class': 'TimeWindowCompactionStrategy',
    'compaction_window_unit': 'DAYS',
    'compaction_window_size': '1'
  };
```

```javascript
// === Write ===
async function writeReading(deviceId, ts, value) {
  const bucket = ts.toISOString().slice(0, 10);    // "YYYY-MM-DD"
  await client.execute(
    "INSERT INTO readings (device_id, bucket, ts, value) VALUES (?, ?, ?, ?)",
    [deviceId, bucket, ts, value],
    { prepare: true }
  );
}

// === Read latest N values for a device ===
async function recentReadings(deviceId, limit = 100) {
  const today = new Date().toISOString().slice(0, 10);
  return client.execute(
    "SELECT * FROM readings WHERE device_id = ? AND bucket = ? LIMIT ?",
    [deviceId, today, limit],
    { prepare: true }
  );
}

// === Read time range (potentially across buckets) ===
async function rangeReadings(deviceId, fromTs, toTs) {
  const buckets = enumerateBuckets(fromTs, toTs);   // ["2026-05-15", "2026-05-16", "2026-05-17"]
  const results = await Promise.all(
    buckets.map(b =>
      client.execute(
        "SELECT * FROM readings WHERE device_id=? AND bucket=? AND ts>=? AND ts<=?",
        [deviceId, b, fromTs, toTs],
        { prepare: true }
      )
    )
  );
  return results.flatMap(r => r.rows).sort((a, b) => a.ts - b.ts);
}

function enumerateBuckets(from, to) {
  const out = [];
  for (let d = new Date(from); d <= to; d.setDate(d.getDate() + 1)) {
    out.push(d.toISOString().slice(0, 10));
  }
  return out;
}
```

### TWCS internals (why it matches the pattern)

```
TWCS groups writes by time window (the compaction_window_size).
Each window's SSTable is compacted internally; no cross-window merges.
When all rows in a window are TTL-expired AND gc_grace passed,
the SSTable drops as a unit — zero per-row tombstone walks at read time.

Read path:
  recent reads hit the current window's SSTable + maybe the previous.
  range queries hit a small set of SSTables (one per day in the range).
```

## Step-by-step dry run

```
Setup: 10K devices, 1 reading/second each → 10K writes/sec, 864M rows/day total.

Naive design: PK=device_id only.
  Per-device partition grows by 86,400 rows/day.
  Day 2: 172K rows → exceeds 100K soft limit.
  Day 30: 2.6M rows → operations alarms blare; reads slow 10×.

Bucketed design: PK=((device_id, day), ts), TWCS 1-day, TTL 30 days.
  Per-(device, day) partition: 86,400 rows ≤ 100K. Safe.
  Day 31: yesterday's bucket reaches TTL → 30-day-old SSTable drops as a unit.
  Read path:
    - "last hour for device X" → 1 bucket query → 1 SSTable hit.
    - "last 24 hours for device X" → 1–2 bucket queries.
    - "last 7 days" → 7 parallel queries, app-side merge.
```

## How to think aloud in the interview

> "Time-series in Cassandra needs bounded partitions. Naive `PRIMARY KEY (device_id, ts)` grows forever and crashes into the 100 MB / 100K-row soft limits within weeks at any real volume.
>
> I add a `bucket` column to the partition key. Size the bucket so each `(device, bucket)` partition holds well under 100K rows. For 1 reading per second, a 1-hour bucket gives 3600 rows; for IoT averages of 1 per minute, a 1-day bucket gives 1440 — pick one and stick to it.
>
> Pair with TimeWindowCompactionStrategy and a matching TTL. TWCS keeps one SSTable per window; when all rows in a window expire, the whole SSTable drops — no per-row tombstone reads. This is the only way to do high-write-rate time-series in Cassandra without tombstone hell.
>
> Important: set `gc_grace_seconds` ≤ bucket window. Default 10 days defeats the whole-SSTable expiry win.
>
> Read time ranges fan out in the app: enumerate buckets in the range, query each, merge. The coordinator doesn't auto-fan-out across partition keys."

## Important takeaways

- **Bucket by time** in the partition key: `((device_id, bucket), ts)`.
- **Bucket size** so partition < 100 MB and < 100K rows.
- **TWCS + TTL** = whole-SSTable drops, zero per-row tombstone reads.
- **`gc_grace_seconds` ≤ bucket window.** Default defeats the pattern.
- **Range reads = app-side fanout.** Coordinator doesn't merge across PKs.
- **`CLUSTERING ORDER BY ts DESC`** for newest-first reads.

## Variants

1. **Compound bucket** — `((device_id, year_month, day), ts)` for queries spanning multiple granularities.
2. **Multi-resolution rollups** — separate tables for 1-min, 1-hour, 1-day averages; written by streaming pipelines.
3. **Materialized views** — pre-compute alt access (e.g., by region) — risky in production.
4. **Append-only audit** — same shape, infinite TTL; partitions bounded by bucket size.
5. **Hot bucket on celebrities** — bucket suffix for devices with extreme rate.
6. **Cross-DC time-series** — `NetworkTopologyStrategy` with local quorum per DC.

## Revision notes

> **time-series in cassandra — 60s recap**
> - Bucket the PK: `((device_id, bucket), ts)`.
> - Bucket size keeps partition < 100 MB and < 100K rows.
> - TimeWindowCompactionStrategy (TWCS) with matching window.
> - default_time_to_live for retention.
> - `gc_grace_seconds` ≤ bucket window for whole-SSTable expiry.
> - Range reads = app-side fanout across buckets, merge.
> - CLUSTERING ORDER BY ts DESC for latest-first.
> - Hot devices → bucket suffix.
