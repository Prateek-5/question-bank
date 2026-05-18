# TTL Jitter — Avoiding Synchronized Expiration Storms

## Source / Origin
- Originated in CDN edge cache design (Akamai, Cloudflare) to prevent "expiration synchronization" at midnight UTC.
- Discussed in Facebook's Memcached at Scale paper as "TTL fuzzing."
- Companion concept doc: `backend-data-prep/caching/01-caching-strategies.md` — "TTL and jitter."
- Interview prompt: "You deploy 100 app instances at noon, each populates the cache with TTL=300; what happens at T+300?"

## Why this question matters in interviews
Jitter is the smallest possible fix that prevents the largest possible disaster. A senior who proactively adds `+ random()` to their TTL signals operational maturity — they've been on-call for a stampede before. Interviewers ask this to verify you (a) recognize the synchronized-expiry failure mode, (b) can quantify the jitter range correctly, and (c) understand why jitter is necessary but not sufficient (single-flight still needed).

## Concepts involved

### Syntax to lock in

```
# Bad
cache.set(key, value, ttl=300)

# Good
cache.set(key, value, ttl=300 + random.randint(0, 30))   # ±10% jitter

# Better (Redis with msec precision)
cache.psetex(key, (300_000 + random.randint(0, 30_000)), value)
```

The jitter range is typically **5–10% of the TTL**, applied as additive randomization. A 300s TTL with 10% jitter gives an actual range of 300–330s.

### Edge cases / interview traps
1. **Subtractive vs additive jitter** — `ttl - random(0, 30)` shifts the *mean* expiry earlier; `ttl + random(0, 30)` keeps the floor at the configured TTL. Most teams use additive to avoid surprising "data expired faster than expected" bugs.
2. **Symmetric jitter** (`ttl ± 15`) is *equivalent* to the cache returning a random value in `[ttl-15, ttl+15]` — fine if your monitoring expects a known floor; bad if downstream assumes "minimum freshness."
3. **Jitter too small** — `300 ± 1` is useless. The expiration cluster is still ~1 second wide. Stampede unchanged.
4. **Jitter too big** — `300 ± 300` means data lifetime is effectively random in [0, 600]. Hot pages refresh at unpredictable cadence; observability gets fuzzy.
5. **Per-key jitter, not per-write** — if you set the same TTL on every write of the same key, every instance still writes the same TTL. Jitter needs to be per-call, not per-key.
6. **Cluster-coordinated TTLs** — if every instance computes jitter from the same hash of the key, you get *deterministic* TTLs — back to synchronized expiry. Use `random()`, not `hash(key)`.
7. **TTL inheritance** — copying a value from one cache to another with `EXPIRE` set to the remaining TTL preserves the synchronized expiry. Jitter on every write.
8. **Negative cache TTL** also needs jitter — non-existent key lookups can stampede too.

## Mental Model

### Without jitter — synchronized expiry

```
T=0   100 instances each populate "trending" with TTL=300
       ──────────────────────────────────────────────────
       inst1   inst2   inst3   ...   inst100
        │        │        │            │
        ▼        ▼        ▼            ▼
       ttl=300s ttl=300s ttl=300s   ttl=300s
        │        │        │            │
       (300s later, all at once)
        ▼        ▼        ▼            ▼
T=300  EXPIRE  EXPIRE  EXPIRE       EXPIRE
T=300.001 1000 concurrent misses → DB ≈ dies
```

### With jitter — spread expiry

```
T=0   100 instances each populate "trending" with TTL=300+rand(0,30)
       ──────────────────────────────────────────────────
       inst1   inst2   inst3   ...   inst100
        │        │        │            │
        ▼        ▼        ▼            ▼
       ttl=305  ttl=312  ttl=298       ttl=327
        │        │        │            │
       Expiries spread over T=300..T=330
        ▼          ▼          ▼          ▼
T=302  EXPIRE 1   T=311 EXPIRE 2  T=325 EXPIRE 3
       At any moment, only a handful expire simultaneously.
       Combined with single-flight, DB sees ~1 query per expiry batch.
```

### Expiration density plot

```
Without jitter:           With 10% jitter:
expiries                  expiries
   │                          │
1000┤▓                     50 ┤▒
    │▓                        │▒▒
    │▓                        │▒▒▒▒▒▒▒▒▒▒▒▒▒▒
    └─┬─────────►            └─┬──────────►
     300s                     300s        330s
   (1000 in 1ms)            (1000 spread over 30s)
```

## Why interviewers care
- It's a **one-line fix** to a class of stampede problems. Candidates who don't reach for it have never been bitten.
- Tests whether you reason about **distributed timing**: many independent caches each running their own TTL clock.
- Combines naturally with **single-flight and refresh-ahead** — jitter alone is necessary but not sufficient.
- Surfaces understanding of **availability vs freshness**: jitter trades a few seconds of staleness for survival.

## Common beginner confusion
- **"Jitter solves stampede."** No — it spreads stampedes out. You still need single-flight to handle the residual concurrency within each smaller expiry batch.
- **"More jitter is better."** Past a point, jitter makes TTL semantics fuzzy. Most ops teams cap it at 10–20%.
- **"Jitter the value, not the TTL."** Wrong — that just changes the data. Jitter the *expiration timestamp*.
- **"I'll jitter in the app layer once."** That works if there's one app instance. With 100 instances, each must independently compute its own jitter.
- **"Jitter is for high-throughput only."** Even a single 100-key warm-up job at deploy time can synchronize expiries. Always jitter.

## Brute force approach
"Use the same TTL everywhere." Standard textbook caching. Works fine until enough instances write the same key with the same TTL at roughly the same time — then they all expire together.

"Vary TTL per key but keep it constant per write." Doesn't help — same key still gets the same TTL from every writer.

## Optimal approach

### Jitter formula
```
actual_ttl = base_ttl + random_uniform(0, base_ttl * jitter_pct)
```
- `base_ttl`: the configured floor (data is guaranteed fresh for at least this long).
- `jitter_pct`: typically 0.05–0.20.
- `random_uniform(0, x)`: a fresh random sample on every `cache.set` call.

### When to use higher jitter (20%)
- Many instances populating the same key.
- Cache writes triggered by external events (webhooks, scheduled jobs) — naturally synchronized.
- Bulk warm-up after deploy.

### When to use lower jitter (5%)
- Single-writer scenarios.
- Long TTLs (an hour or more) where 5% is still tens of minutes of spread.

### Combine with
- **Single-flight** — handles residual stampede within the jitter window.
- **Refresh-ahead** for top hot keys — avoids the miss entirely.
- **Stale-while-revalidate** — serves stale during refresh.

## Solution

### Node.js (ioredis) — simple jitter helper

```javascript
const Redis = require('ioredis');
const redis = new Redis();

function jitteredTtl(baseTtl, jitterPct = 0.1) {
  return Math.floor(baseTtl + Math.random() * baseTtl * jitterPct);
}

async function setWithJitter(key, value, baseTtlSec) {
  const ttl = jitteredTtl(baseTtlSec);
  await redis.set(key, JSON.stringify(value), 'EX', ttl);
}

// Usage
await setWithJitter('trending:home', payload, 300);   // actual TTL: 300-330s
```

### Python — same idea

```python
import random, time

def jittered_ttl(base_ttl: int, jitter_pct: float = 0.1) -> int:
    return base_ttl + random.randint(0, int(base_ttl * jitter_pct))

def cache_set(redis, key, value, base_ttl=300):
    ttl = jittered_ttl(base_ttl)
    redis.setex(key, ttl, value)
```

### Lua-side jitter (atomic with the set)

```lua
-- KEYS[1] = cache key, ARGV[1] = value, ARGV[2] = base_ttl, ARGV[3] = jitter_pct
local base = tonumber(ARGV[2])
local jitter = tonumber(ARGV[3])
math.randomseed(redis.call('TIME')[2])    -- microseconds for entropy
local extra = math.floor(math.random() * base * jitter)
local ttl = base + extra
redis.call('SET', KEYS[1], ARGV[1], 'EX', ttl)
return ttl
```

(Note: `math.random` in Redis Lua is process-shared; seeding helps but isn't perfect. Prefer client-side jitter for true independence.)

## Step-by-step dry run

Scenario: 100 app instances simultaneously populate `trending:home` at T=0.

**Without jitter** (TTL=300):
| T | Event |
|---|-------|
| 0   | 100 writes, all with EXPIRE = T+300 |
| 0.001 | Redis records expiry at T=300 for all 100 (writes are coalesced — single key, last write wins; TTL is global, not per-writer, but in cache-aside semantics each instance also has a local TTL clock for its own logic) |
| 300 | Redis emits expiry; first read after T=300 is a miss |
| 300 | 1000 req/s hit the cache → 1000 concurrent misses → 1000 DB queries |
| 300.05 | DB saturates, latency spikes from 5ms to 5000ms |
| 300.1 | App pool exhausted, 500s start flowing back to clients |

**With 10% jitter:**
| T | Event |
|---|-------|
| 0   | 100 writes; TTLs in [300, 330] uniformly distributed (assuming each app instance writes its own value, e.g., its own copy in a sharded cache) |
| 300 | Reads start to miss for the first instances; ~3 instances expire/sec |
| 300–330 | 100 instances' caches expire spread over 30s, ~3 misses/sec |
| With single-flight: 1 DB query per expiry; DB sees 100 queries over 30s = manageable |

The 1000:1 reduction in DB load comes from spreading expiries by 30 seconds.

### Subtle correctness note

In a *shared* Redis (not per-instance), only one key exists for `trending:home`, so only one TTL applies — jitter on the shared write doesn't help unless many *keys* share the same TTL. The "100 instances populating with TTL=300" pattern matters most when each instance has its own cache (e.g., L1 in-process caches, or a per-instance Redis), or when many different keys are being warmed up in a synchronized batch.

For the **bulk warm-up case** (e.g., warming 10,000 product keys at deploy), jitter on every write spreads their *future* expiries — avoiding "all 10,000 expire at T+300 and all 10,000 stampede at once."

## How to think aloud in the interview

"Jitter is one of those tiny fixes that prevents a giant class of incidents. The problem: if I deploy 100 app instances and each one warms its in-process cache for the same key with the same TTL of 300 seconds, all 100 entries expire at almost exactly the same instant. The next request after T+300 misses everywhere; 1000 requests per second slam the DB; the DB dies.

The fix is to add a small random amount to every TTL — typically 5 to 10% of the base. So instead of 300 seconds, I use `300 + random(0, 30)`. This spreads the expiries across a 30-second window. With single-flight on top, each expiry is just one DB query, and the DB sees a steady trickle of one query every few seconds instead of a 1000-query spike.

Important detail: the jitter has to be sampled on *every* `cache.set` call, not computed once per key. Otherwise every instance that writes the same key gets the same jittered value, and you're back to synchronized expiries.

Jitter is necessary but not sufficient. You still want single-flight (one loader per key per concurrent burst) and ideally refresh-ahead for the top hot keys. And jitter doesn't help with read-your-writes consistency — that's a different problem solved by versioned keys or pinning reads to primary post-write.

If they push on what 'too much jitter' looks like: more than ~20% makes TTL semantics fuzzy, your monitoring loses a clean expiry signal, and you trade more freshness than you needed to."

## Important takeaways

- **Always jitter your TTL.** Default 10%; adjust by scenario.
- **Sample fresh on every write** — not once per key, not deterministically from the key.
- **Additive is safer than subtractive** — preserves the configured TTL floor.
- **Jitter spreads stampedes; single-flight prevents them.** You need both.
- **Combine with refresh-ahead** for top hot keys.
- **Jitter the negative cache TTL too.**
- **Bulk warm-up always needs jitter** — synchronized writes have synchronized expiries.

## Variants

1. **Multiplicative jitter** — `ttl * uniform(1.0, 1.2)`. Same effect, often cleaner code.
2. **Exponential jitter** — for retry/backoff scenarios; rarely used for cache TTL.
3. **Per-tier jitter** — L1 with 10% jitter, L2 with 5% jitter. Independent expiry clocks.
4. **Hash-based deterministic spread** — TTL = base + (hash(key) % jitter_range). Useful if you need reproducible expiry, but defeats the cross-instance spread.
5. **Adaptive jitter** — increase jitter under high load (measured by miss-rate spikes), decrease in steady state.
6. **Jitter on negative cache TTL** — `30s + random(0, 5)` for "row doesn't exist" entries.

## Revision notes

> **TTL jitter — 60 second recap**
> - **Always add 5–10% random jitter to every TTL.**
> - **Sample on every write**, not per-key.
> - **Use additive** (`ttl + rand(0, ttl*pct)`) to preserve the configured floor.
> - **Necessary but not sufficient** — combine with single-flight and (for hot keys) refresh-ahead.
> - **Bulk warm-up and multi-instance writes are the main offenders** — jitter is mandatory there.
> - **Trap:** deterministic jitter (`hash(key)`), too-small jitter (`±1s`), forgetting to jitter the negative cache TTL.
