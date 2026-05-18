# Cache Warm-Up Strategies — Preload, Blue/Green, Replay, Shadow Traffic

## Source / Origin
- Productionised at every CDN (Cloudflare, Fastly, Akamai) and large-scale Memcached deploy (Facebook TAO, Twitter Twemcache).
- Companion docs: `backend-data-prep/caching/03-cache-warmup.md`, `cache-stampede-single-flight.md`, `refresh-ahead-cache.md`.
- Classic interview prompt: "You're deploying a new Redis cluster to replace the old one. How do you cut over without melting the database?"

## Why this question matters in interviews
The cache-warm-up question is the **operational maturity probe**. Anyone can write `cache.get/set`. The senior is the one who pauses and says "wait — what's in the cache right after the cluster spins up? Nothing. What happens when a billion requests hit empty cache? The DB dies." The interviewer wants to see you reason about (a) the cold-cache failure mode, (b) several pre-warming strategies, (c) traffic-shifting techniques during cutover, and (d) which strategy fits which workload. This question shows up at any company that has actually run caches at scale — Stripe, Uber, Discord, Cloudflare. Bombing it screams "I've only run caches in dev."

## Concepts involved

### Syntax to lock in

The four warm-up flavours, with the operating verb in each:

```
1. PRELOAD          — script "for each hot key: read DB, write cache" before serving traffic.
2. BLUE/GREEN       — new cache cluster runs in parallel; gradually shift read traffic to it.
3. REPLAY           — capture production read traffic; replay it against the new cluster.
4. SHADOW TRAFFIC   — fork live requests to both clusters; old one serves users, new one warms.
```

Hot-key preload (the cheap default):
```python
hot_keys = redis.zrevrange("metrics:read_counts", 0, 9999)  # top 10k
for key in hot_keys:
    val = db.read(key)
    new_cache.set(key, val, ttl=300)
```

Shadow-traffic warmup (the expensive but bulletproof default):
```python
def get(key):
    val = old_cache.get(key) or load_and_set(old_cache, key)
    # fire-and-forget mirror to new cluster
    background_executor.submit(lambda: new_cache.get(key) or load_and_set(new_cache, key))
    return val
```

### Edge cases / interview traps

1. **The cold cluster *is* a stampede.** Spinning up an empty cache and switching traffic to it is functionally identical to a global cache flush. Every read becomes a miss; DB takes the full request rate. Don't.
2. **Hot-key preload only covers the head, not the tail.** A typical workload has a Zipfian distribution: the top 1% of keys take 50% of traffic, but the other 99% still hits the DB on first read. Preload helps the headline metric (cache hit rate) but doesn't eliminate the DB spike for tail keys.
3. **Preload must use the same key format as runtime.** Off-by-one in serialisation (e.g., preload stored `user:42` but app reads `users:42`) creates 100% miss rate with a populated cache. Test the *exact* key that production reads.
4. **TTL on preload — start short or start full?** Common mistake: preload with the full 300s TTL right before serving. Then 300s after deploy, every preloaded key expires simultaneously → mass-invalidation stampede. Solution: preload with randomised TTLs (jitter; see `ttl-jitter-design.md`).
5. **Blue/green requires double the cache RAM.** Old cluster keeps serving while new cluster warms. If you can't afford the headroom, you can't blue/green.
6. **Replay traffic must be *recent*.** Last week's access log is useless for a workload that changes daily (e.g., trending content). 24-hour rolling capture is the typical window.
7. **Shadow traffic doubles read load on DB during warmup.** For a few hours, your DB sees `live_reads + warmup_reads`. If you're already at 70% capacity, shadow warmup will spike you over. Throttle shadow reads to a safe fraction.
8. **Stateful caches (sessions, counters) cannot be replayed.** You cannot reconstruct a session counter from a read log. For these, blue/green with explicit migration or live mirroring is required.
9. **Connection-pool warmup.** The cache is empty *and* the connection pool to the cache cluster is empty when the app starts. First few hundred requests pay TCP setup cost. Some teams pre-establish N connections at boot.
10. **Cold-start after deploy ≠ cold-start of cluster.** App restart with shared external cache: cache is warm, your local in-process map is empty. Cluster restart: external cache is empty. Different problems, different fixes.

## Mental Model

### The four strategies on a spectrum

```
   Risk to DB     ◄────────── Cost ──────────►
   ▲
   │
   │  PRELOAD (top-K)             ◄── cheapest, covers head only
   │     │
   │  REPLAY (logged keys)        ◄── 1 hour of disk + a worker
   │     │
   │  SHADOW TRAFFIC              ◄── 2x DB read load during warmup window
   │     │
   │  BLUE/GREEN + gradual cutover◄── 2x cache RAM; safest
   ▼
```

### Cold-cache failure timeline

```
T=0     New cluster deployed. Cache empty. Read TPS = 50k.
T=0+    Every read → cache miss → DB read.
T=0+    DB sees 50k req/s instead of 5k. Connection pool exhausts.
T=10s   p99 latency goes from 20ms to 8000ms.
T=15s   Upstream services start timing out. Cascade.
T=30s   Incident.

With pre-warming:
T=-3600 (1 hour before cutover) Begin preload of top 10k keys.
T=-300  Begin shadow-traffic mirroring.
T=-60   New cache hit rate observed at 85% (close to old cluster's 90%).
T=0     Flip read traffic. DB extra load: <10% spike. No incident.
```

### Why the head is easy, the tail is hard

```
Zipfian access distribution:
  Rank 1:     ████████████████████  (20% of all reads)
  Rank 2:     ███████████           (11%)
  Rank 3:     ████████              (8%)
  ...
  Rank 100:                  ██     (0.5%)
  Rank 1000:                  ▏     (0.05%)
  Rank 10000+:                ·     ← long tail

Preload top 1000 → covers ~80% of read traffic
Preload top 10000 → covers ~95%
Preload all → impossible at scale
```

The honest answer to "warm everything" is "you can't". You aim for >90% hit-rate-at-cutover and accept the residual spike.

## Why interviewers care

- It tests **operational maturity**, not algorithm cleverness. Senior engineers think about deploy-time failure modes, not just runtime.
- It probes **traffic-shifting reasoning** — gradual cutover, mirroring, fallback paths.
- It naturally pivots to **observability**: how do you *measure* cache hit rate during warmup? How do you decide when to flip?
- It exposes whether you've thought about **cost/risk tradeoffs**. Blue/green is safest but doubles RAM cost. Preload is cheap but covers head only. Replay needs storage. There's no "obvious correct answer" — the trade-offs are the answer.

## Common beginner confusion

- **"Just deploy and let the cache fill organically."** Works at toy scale. Catastrophic at production scale.
- **"Preload everything."** Storage and time forbid it for any cache with >100k keys.
- **"Warm-up only matters for cache deploys."** Also matters for: cache cluster failover, region failover, large invalidations, cache evictions during memory pressure.
- **"If hit rate is 90% I'm fine."** A 10% miss rate at 50k TPS = 5k DB reads/sec. That might *be* your DB capacity. Cache hit rate is a percentage; tail spike is an absolute number.
- **"Pre-warming is a one-time event."** No — every node restart, every cluster reconfiguration, every region failover is a warm-up event. Build the tooling to be repeatable.
- **"Shadow traffic is free."** It doubles DB read load during the window. Free only if your DB has 2x headroom.
- **"Blue/green is overkill."** It's the safest. Use it when DB capacity is tight, traffic is high, or the workload doesn't replay cleanly (sessions, counters).

## Brute force approach

"Deploy the new cluster, switch DNS, hope for the best." Works if your traffic is low or your DB has huge headroom. Otherwise the cache cutover *is* the outage. This is the postmortem-generator approach.

A slightly less bad variant: "Bring it up at 3 AM during low traffic." Buys you a smaller spike but doesn't change the shape of the problem.

## Optimal approach

The realistic production playbook combines several layers:

### Layer 1 — Top-K preload (always do this)

Maintain a counter of "most-read keys over the last hour" in a sorted set. Before cutover, replay the top 10-100k keys into the new cache. Captures ~80-95% of traffic. Cheap. Always do this.

### Layer 2 — Replay recent reads

For 1-24 hours before cutover, log every cache read. Replay that log against the new cluster. Catches "warm" keys that aren't top-K (medium frequency, e.g., user profiles for recently-active users). Adds tail coverage.

### Layer 3 — Shadow traffic

Fork live read requests to both clusters during the cutover window. Old cluster serves users; new cluster warms with live traffic. Tells you the exact hit rate the new cluster will see. Catches edge cases that replay misses (e.g., authentication tokens that change per session).

### Layer 4 — Gradual cutover (blue/green)

Don't flip 0% → 100%. Use a feature flag: 1% → 5% → 25% → 50% → 100% over an hour. Monitor cache hit rate, DB latency, p99 of the read path. Roll back instantly if anything spikes.

### Layer 5 — DB rate-limit guard

Even with all the above, put a circuit breaker between the app and the DB that rejects when DB CPU > X. Better to fail-open with stale data than to take down the DB and lose all reads.

### Decision matrix

```
Workload                          Recommended warm-up
─────────────────────────────────────────────────────────────────
Read-heavy, top-K dominant        Preload + gradual cutover
Read-heavy, long tail             Preload + replay + gradual cutover
Sessions / counters / stateful    Blue/green + explicit migration
First-time deploy (no old cache)  Shadow staging traffic first
Region failover                   Pre-warm replica in advance
Mass invalidation event           Stagger invalidations + refresh-ahead
```

## Solution (preload + shadow + gradual cutover)

### Top-K preload (the always-on baseline)

```python
import time
from concurrent.futures import ThreadPoolExecutor

def preload_top_k(k=10_000, batch_size=100, parallelism=16):
    keys = redis_metrics.zrevrange("read_counts:1h", 0, k - 1)
    pool = ThreadPoolExecutor(max_workers=parallelism)

    def load_batch(batch):
        values = db.multi_read(batch)              # one DB round-trip per batch
        with new_cache.pipeline() as pipe:
            for key, val in zip(batch, values):
                if val is not None:
                    jitter = random.randint(0, 60)
                    pipe.set(key, val, ex=300 + jitter)  # spread TTLs
            pipe.execute()

    batches = [keys[i:i+batch_size] for i in range(0, len(keys), batch_size)]
    for _ in pool.map(load_batch, batches):
        pass
    pool.shutdown(wait=True)
```

### Shadow-traffic mirror

```python
from concurrent.futures import ThreadPoolExecutor

mirror_pool = ThreadPoolExecutor(max_workers=64)
MIRROR_SAMPLE_RATE = 0.5   # mirror 50% to bound DB extra load

def get(key):
    val = old_cache.get(key)
    if val is None:
        val = db.read(key)
        old_cache.set(key, val, ex=300)

    if random.random() < MIRROR_SAMPLE_RATE:
        mirror_pool.submit(_mirror_warm, key)
    return val

def _mirror_warm(key):
    if new_cache.get(key) is None:
        # use the value we already have if possible; otherwise read DB
        v = db.read(key)
        new_cache.set(key, v, ex=300 + random.randint(0, 60))
```

### Gradual read cutover

```python
# Controlled via feature flag / config service
def get_with_cutover(key):
    pct = feature_flag.get("new_cache_read_pct", default=0)
    if random.randint(0, 99) < pct:
        try:
            v = new_cache.get(key)
            if v is not None:
                metrics.incr("new_cache.hit")
                return v
            metrics.incr("new_cache.miss")
        except Exception:
            metrics.incr("new_cache.error")
            # fall through to old cache on error
    return old_cache.get(key) or load_and_set(old_cache, key)
```

Flip the flag in stages: 1, 5, 25, 50, 100. Wait 5-10 minutes between stages, watch `new_cache.hit` ratio + DB latency.

## Step-by-step dry run

Scenario: replace `redis-old` (8GB cluster) with `redis-new` (16GB cluster). Live traffic: 50k read TPS. Old cluster hit rate: 92%. DB capacity: 8k QPS sustained.

```
T = -180 min   Deploy redis-new. Empty. Subscribe metrics.
T = -120 min   Run preload_top_k(50_000). 50k key writes, ~20MB of data.
               Top 50k keys cover ~85% of recent read traffic.
               redis-new hit rate (shadow check): 0% → ~70% as preload completes.
T = -60 min    Enable shadow traffic at 50% sample.
               redis-new warms with live tail keys.
               redis-new hit rate climbs from 70% → 88% over 30 minutes.
T = -10 min    Final check: redis-new hit rate = 88% on shadow.
               Estimated DB extra load at cutover: 50k * (1 - 0.88) = 6k QPS additional.
               Combined: 6k + baseline 4k = 10k QPS. ← above 8k cap! BAD.

               Two options: (a) more preload, (b) gradual cutover.
               Choose (b) since preload top-100k won't help much further.

T = 0 min      Begin cutover. Flag at 1%. New cluster sees 500 TPS;
               DB extra load: 500 * 0.12 = 60 QPS. Trivial.
T = +5 min     Flag → 5%. DB extra: 300 QPS. Fine.
T = +15 min    Flag → 25%. DB extra: 1500 QPS. Combined 5.5k. Fine.
T = +30 min    Flag → 50%. DB extra: 3000 QPS. Combined 7k. Watch closely.
T = +45 min    redis-new hit rate now 91% (more keys warmed from real traffic).
               DB extra: 50% * 50k * 0.09 = 2250 QPS. Combined 6.25k. Better.
T = +60 min    Flag → 100%. redis-new at 92% hit rate. DB at 4k QPS baseline.
               Cutover complete. Decommission redis-old after 1 hour soak.
```

The gradual cutover converted a guaranteed-fatal 10k QPS spike into a smooth progression that never exceeded the DB cap.

## How to think aloud in the interview

> "Cache warm-up is a deploy-time concern, and the failure mode is: cold cache + live traffic → DB sees the full request rate. So the question is how to fill the new cluster *before* it serves traffic, or how to ease into serving without overloading the DB.
>
> Four strategies in order of cost and coverage:
>
> 1. **Top-K preload** — counter of hottest keys; replay them into the new cache before cutover. Catches ~80-95% of traffic for the cost of one batch job. Always do this.
> 2. **Replay** — log live read traffic for the last hour; replay it. Adds the tail. Useful when the head/tail split is shallow.
> 3. **Shadow traffic** — fork live requests to both clusters; old one serves, new one warms organically. Most accurate hit-rate prediction, but doubles read load on DB during the window.
> 4. **Blue/green with gradual cutover** — 1% → 5% → 25% → 50% → 100% via feature flag. Lets you measure the new cluster's hit rate at low traffic and abort if it's bad.
>
> Production playbook: combine #1 and #4 always, add #3 for high-stakes cutovers, use #2 when the tail matters.
>
> Two traps to flag:
> - **TTL synchronization** — if you preload everything with the same TTL, you get a mass-invalidation stampede 300 seconds later. Add jitter.
> - **Shadow traffic doubles DB load** during the window. Sample at 50% or less if your DB is near capacity.
>
> And a meta-point: warm-up is not a one-time event. Every region failover, every node replacement, every memory eviction is a warm-up. Build the tooling to be repeatable, not a deploy-script special case."

## Important takeaways

- **Empty cache + live traffic = DB-killer.** Pre-warming is non-optional at scale.
- **Top-K preload** covers head of Zipfian distribution cheaply. Always do this.
- **Replay** of recent read logs covers the tail.
- **Shadow traffic** gives the most accurate "what will the hit rate be?" preview.
- **Gradual cutover (blue/green)** converts a discontinuous spike into a smooth ramp.
- **TTL jitter** during preload prevents mass-invalidation stampede later.
- **Shadow doubles DB load during the warmup window** — sample or throttle.
- **Stateful caches (sessions, counters)** cannot be replayed — blue/green with explicit migration.
- **Connection pool warmup** matters separately from cache warmup — pre-establish connections at boot.
- **Warm-up is a recurring operational event**, not a one-time deploy task.

## Variants

1. **Predictive pre-warm** — ML model predicts what keys will be hot in the next hour; pre-warm those. Used at Netflix CDN, Cloudflare. Overkill for most.
2. **Region-aware pre-warm** — when standing up a cache cluster in a new region, replicate the *existing* region's cache contents via a one-time scan. Skips DB entirely.
3. **Refresh-ahead as warm-up** — the always-on warm-up; hot keys get proactively refreshed before TTL. See `refresh-ahead-cache.md`.
4. **In-process warm-up** — pre-fill the app's in-memory LRU at boot from disk-cached snapshots. Common for sidecars and embedded caches.
5. **Cold-start guard** — a circuit breaker on the DB that rejects requests when CPU > threshold, returning 503 instead of melting. Defence in depth.
6. **TTL-aware partial cutover** — promote keys to the new cluster only as their TTL expires; the rest stay on the old cluster. Used by some CDN migrations.
7. **MySQL specifics** — InnoDB has its own buffer pool warm-up (`innodb_buffer_pool_dump_at_shutdown` + `_load_at_startup`). Mention this if asked about DB-side warm-up.

## Revision notes

> **cache warm-up — 60 second recap**
> - **Problem:** new/cold cluster + live traffic → DB sees full request rate → cascade.
> - **Strategy 1: top-K preload** — cheap, covers ~85% of traffic via head of Zipf.
> - **Strategy 2: replay** — log live reads, replay against new cluster — adds tail.
> - **Strategy 3: shadow traffic** — mirror live reads; new cluster warms organically; doubles DB load briefly.
> - **Strategy 4: blue/green + gradual cutover** — 1→5→25→50→100% via flag; smooth ramp.
> - **Trap 1:** TTL synchronisation after preload → mass-invalidation. Add jitter.
> - **Trap 2:** shadow doubles DB load during window. Sample/throttle.
> - **Trap 3:** sessions/counters can't be replayed → blue/green or live migration.
> - Real stack: preload + gradual cutover always; add shadow for high-stakes; add replay for tail-heavy.
> - **Warm-up is recurring** (failovers, evictions), not a one-off deploy step.
