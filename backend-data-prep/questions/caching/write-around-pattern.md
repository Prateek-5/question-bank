# Write-Around Cache Pattern

## Source / Origin
- Documented in CPU cache literature (Hennessy & Patterson) and revived in distributed-systems caches.
- Used heavily at Facebook for write-heavy, rarely-read data (audit logs, analytic events).
- Companion concept doc: `backend-data-prep/caching/01-caching-strategies.md` — "Write-around" subsection.
- Interview prompt: "You have a workload where writes outpace reads by 100×. Which caching pattern?"

## Why this question matters in interviews
Write-around is the "obvious in retrospect" pattern most candidates forget. They jump between write-through and write-back, missing the third option: don't write to the cache at all. The senior signal is recognizing the read-write asymmetry of the workload (e.g., 99% of audit log entries are never re-read) and selecting write-around accordingly. Combines naturally with TTL and is the de-facto pattern for time-series data.

## Concepts involved

### Syntax to lock in

The minimal write-around:
```
function update(key, value):
    db.write(key, value)            # only the DB; cache untouched
    # no cache.set, no cache.del — but see "with invalidation" below
```

The "write-around with invalidation" (safer):
```
function update(key, value):
    db.write(key, value)
    cache.del(key)                  # ensure the next read picks up new value
```

The reader still uses cache-aside on the read path:
```
function get(key):
    val = cache.get(key)
    if val is None:
        val = db.read(key)
        cache.set(key, val, ttl=300)
    return val
```

### Edge cases / interview traps
1. **Stale cache after write (no del)** — pure write-around without invalidation leaves cache holding old value until TTL. Acceptable for "data is rarely re-read soon after write" workloads; broken for read-your-writes.
2. **Read-your-writes inconsistency** — if a user writes data and immediately reads it back, write-around without invalidation serves them the old cached value. Bad UX.
3. **Cache miss rate goes up** — writes don't populate the cache, so subsequent reads always miss the first time. Cold-cache reads dominate latency for write-then-read patterns.
4. **DB write throughput is the bottleneck now** — writes don't get the cache's write-buffering benefit. If you needed write-back's throughput help, write-around is the wrong pick.
5. **Combined with refresh-ahead** — write-around + scheduled refresh-ahead for known-hot keys = best of both worlds (writes don't pollute cache, hot reads stay warm).
6. **CDC-driven invalidation** — replaces explicit `cache.del` with a Debezium pipeline. Decouples write path from cache.
7. **TTL choice is critical** — without write-time invalidation, TTL is your *only* freshness bound.

## Mental Model

### The three write paths side-by-side

```
WRITE-THROUGH:
  Client ──► App ──► Cache.set ─┐
                      DB.write  ├─ both written → return
                                ┘
WRITE-BACK:
  Client ──► App ──► Cache.set (dirty)
                      → return
                      → async: flush to DB

WRITE-AROUND:
  Client ──► App ──► DB.write
                     [cache.del optional]
                     → return
                      
                  cache untouched on write
                  reads still cache-aside
```

### When does write-around win?

```
Read/Write ratio matters.

Workload                           Pattern
─────────                          ────────
Read-heavy, hot keys re-read       Write-through (keep cache fresh)
Write-heavy, hot keys re-read      Write-back (buffer writes)
Write-heavy, rarely re-read soon   Write-around (don't pollute cache)
Read-heavy, mixed updates          Cache-aside (default)
```

### Concrete example — audit log

```
Write rate: 10,000 events/sec
Read rate:  5 events/sec (compliance queries)
Re-read probability of any event within 5 minutes: ~0%

Write-through: caches 10,000 events/sec that nobody will read for hours.
              Cache fills with cold data; LRU evicts what little is hot.
              
Write-back:   Same problem; cache becomes a write-buffer for cold data.

Write-around: Writes go straight to DB. Cache stays small and hot
              (only the few audit events being actively investigated).
              Cache hit rate stays high.
```

## Why interviewers care
- Tests **workload awareness** — do you ask about read/write ratios and re-read probability before picking a pattern?
- Demonstrates understanding that **caches have negative space** — populating with cold data evicts hot data.
- Real-world fit: audit logs, time-series, click streams, write-only analytics ingestion.
- Surfaces the **invalidation question** — write-around with no cache.del has subtle correctness issues.

## Common beginner confusion
- **"Write-around means writes are slower."** No — write-around is roughly the same speed as write-through, sometimes faster (one fewer write).
- **"Write-around skips the cache entirely."** Only on the *write* path. Reads still use cache-aside.
- **"If I'm not writing to cache, why cache at all?"** Because hot data still benefits from being cached when it *is* read. Write-around just doesn't pre-warm the cache with every write.
- **"Write-around guarantees consistency."** No — pure write-around (no `cache.del`) leaves stale cache entries until TTL. You usually want explicit invalidation too.
- **"Write-around is the safe default."** It's the right default *only* for write-heavy/rarely-re-read workloads. For typical CRUD, cache-aside is the default.

## Brute force approach
**"Just cache-aside but skip the cache.set on write."** That *is* write-around. The question is whether you call `cache.del` or leave the stale entry to TTL out.

**"No cache at all."** The baseline — correct, no consistency issues, but reads are always DB-bound. Cache adds value if even 1% of reads are repeats.

## Optimal approach

### When to use write-around
- **Write/read ratio > 10:1**
- **Re-read probability within TTL is low** (audit logs, time-series, click events)
- **Writes don't need to be immediately readable from cache**
- **Cache is RAM-constrained** — don't burn RAM on cold data

### Implementation choices
- **With `cache.del` on write**: defends read-your-writes. Tiny extra cost. Use this by default.
- **Without `cache.del` on write**: pure write-around. Stale until TTL. Only when reads are *guaranteed* to occur >TTL after write.
- **With CDC invalidation**: write-around + Debezium emits invalidations. Decouples app code from cache.

### Hybrid combinations
- **Write-around + refresh-ahead for hot keys**: writes don't pollute cache; hot reads stay proactively warm.
- **Write-around + tiered cache**: L1 (in-process) populated only on read; L2 (Redis) write-through for read-heavy keys.

## Solution

### Plain write-around with invalidation (Node.js + ioredis)

```javascript
const Redis = require('ioredis');
const redis = new Redis();

async function logAuditEvent(eventId, payload) {
  // Write straight to DB
  await db.query(
    'INSERT INTO audit_events (id, payload, ts) VALUES ($1, $2, $3)',
    [eventId, JSON.stringify(payload), Date.now()],
  );
  // Don't populate cache. If a previous version was cached (unusual for audit logs),
  // delete it.
  await redis.del(`audit:${eventId}`);
}

async function getAuditEvent(eventId) {
  const key = `audit:${eventId}`;
  const cached = await redis.get(key);
  if (cached !== null) return JSON.parse(cached);

  const row = await db.query('SELECT * FROM audit_events WHERE id = $1', [eventId]);
  if (row) {
    await redis.set(key, JSON.stringify(row), 'EX', 3600);   // 1h TTL
  }
  return row;
}
```

### Write-around with CDC invalidation

```javascript
// Debezium/CDC consumer (conceptual)
async function onDbChangeEvent(event) {
  if (event.table === 'audit_events' && event.op === 'INSERT') {
    // No cache to invalidate for a new INSERT (key didn't exist).
    // But for UPDATE/DELETE on tables you cache:
    if (event.op === 'UPDATE' || event.op === 'DELETE') {
      const cacheKey = `${event.table}:${event.pk}`;
      await redis.del(cacheKey);
    }
  }
}
```

### Time-series write-around

```javascript
// Metrics: 1M writes/sec, queries are rare and timestamp-range based
async function recordMetric(metricName, value, timestamp = Date.now()) {
  await db.query(
    'INSERT INTO metrics (name, value, ts) VALUES ($1, $2, $3)',
    [metricName, value, timestamp],
  );
  // No cache write. No invalidation — INSERTs don't have an existing cached key.
}

// Reads (rare, expensive aggregation) DO use cache-aside
async function getMetricSeries(metricName, fromTs, toTs) {
  const key = `metric:${metricName}:${fromTs}:${toTs}`;
  const cached = await redis.get(key);
  if (cached !== null) return JSON.parse(cached);

  const rows = await db.query(
    'SELECT * FROM metrics WHERE name=$1 AND ts BETWEEN $2 AND $3',
    [metricName, fromTs, toTs],
  );
  await redis.set(key, JSON.stringify(rows), 'EX', 300);
  return rows;
}
```

## Step-by-step dry run

**Scenario:** audit log; write 1000 events/sec; reads are rare investigations.

### Without write-around (using write-through):

| T | Event | Cache state | DB writes/s |
|---|-------|-------------|-------------|
| 0s | 1000 audit events written | 1000 new keys in cache | 1000 |
| 60s | 60,000 events written | Cache full of cold data; LRU evicting hot items | 1000 |
| 120s | Investigation reads event #42 | Probably evicted → miss → DB read | 1000 |

Cache is harmful: it fills with write-once-read-never data, evicting genuinely hot keys.

### With write-around:

| T | Event | Cache state | DB writes/s |
|---|-------|-------------|-------------|
| 0s | 1000 audit events written | Cache untouched | 1000 |
| 60s | 60,000 events written | Cache still holding genuinely hot keys | 1000 |
| 120s | Investigation reads event #42 | Miss → DB read → cache.set | 1000 |
| 121s | Investigation re-reads event #42 | Hit | 1000 |

**Cache hit rate stays high; investigation reads still benefit on re-access.**

## How to think aloud in the interview

"For this workload — write-heavy, rarely re-read soon — write-around is the right pick. The intuition: caches have finite RAM. If I write-through every audit event, the cache fills up with 60,000 events per minute, most of which nobody will read for hours or days. Meanwhile, the LRU is evicting genuinely hot keys to make room for cold data. The cache becomes a write buffer that hurts read hit rate.

Write-around says: on writes, only touch the DB. Leave the cache alone. Reads still use cache-aside — first read of an audit event misses and populates the cache, and re-reads benefit. The cache stays small and hot.

One subtlety: pure write-around means after a write, any *previously cached* version of the same key is stale until TTL. For new inserts that's a non-issue — nothing was cached before. For updates I'd add `cache.del` on write to invalidate the prior entry. So the writer path is `db.write → cache.del`, and the reader path is normal cache-aside.

The cleaner alternative is CDC-driven invalidation — Debezium reads the DB binlog, emits events, a consumer invalidates the cache. App code stops worrying about cache at all on the write path. Same logical pattern.

Combining write-around with refresh-ahead for known-hot keys is the senior move. Write-around prevents cold-data pollution; refresh-ahead keeps the *known* hot keys warm without going through the write path. Best of both."

## Important takeaways

- **Write-around = skip the cache on write; reads still use cache-aside.**
- **Use when writes outpace reads and re-read probability within TTL is low.**
- **Pair with `cache.del` on UPDATE/DELETE** to invalidate stale entries.
- **Pure write-around (no del) is only safe when reads are guaranteed >TTL after writes.**
- **CDC-driven invalidation decouples write path from cache logic.**
- **Combine with refresh-ahead for known hot keys.**
- **Trap:** picking write-around for general CRUD; forgetting to invalidate on UPDATE.

## Variants

1. **Write-around + del-on-update** — the default safe variant. Handles read-your-writes for updates.
2. **Pure write-around (no del)** — for append-only workloads where keys are unique per write (audit logs, time-series).
3. **Write-around + CDC invalidation** — write path is pure; CDC pipeline handles cache.
4. **Write-around + refresh-ahead** — keeps known hot keys warm without dirtying cache on every write.
5. **Tiered write-around** — write-around on L1, write-through on L2. Hot data gets shared between instances via L2; L1 only caches what each instance actually reads.

## Revision notes

> **write-around — 60 second recap**
> - **Write path: write DB only; skip cache.** Reads still cache-aside.
> - **Use for write-heavy + rarely-re-read workloads** (audit logs, time-series, analytics).
> - **Add `cache.del` on UPDATE/DELETE** to prevent stale reads.
> - **Prevents cold-data pollution of the cache.**
> - **Pair with refresh-ahead for known hot keys** if you want them always-warm.
> - **CDC alternative** decouples write path from cache.
> - **Trap:** using it for read-heavy CRUD; skipping invalidation on UPDATE.
