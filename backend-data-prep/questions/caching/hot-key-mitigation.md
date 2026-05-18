# Hot key mitigation — local cache, jittered fetch, key sharding, replica reads

## Source / Origin
- Twitter's "Manhattan" paper (2016) discusses hot key handling.
- Facebook's TAO paper covers hot-spot mitigation via local caching and replication.
- `backend-data-prep/caching/01-caching-strategies.md` — "Hot keys" section.
- Classic prompt: *"One product page (a celebrity-endorsed SKU) is getting 50,000 RPS. Redis shard #3 is at 95% CPU. Your other 31 shards are at 5%. Fix this."*

## Why this question matters in interviews
Hot keys are **the asymmetry problem** that breaks every uniformly-sharded system. The interviewer is testing whether you:

1. Recognise that **horizontal scaling fails when one key dominates** — adding shards doesn't help if the hot key is on one shard.
2. Can list **multiple mitigation strategies** — local cache, key sharding, replica reads, jittered fetch — and pick by workload.
3. Know how to **identify hot keys** in production — Redis `MONITOR`, hot-key sampling, CDN access logs.
4. Understand the **CAP-like tradeoffs** of each mitigation (staleness vs throughput vs complexity).

This is a senior-system-design discriminator — the kind of question that appears in staff-level interviews and the failed answers to which become memes in postmortems.

## Concepts involved

### Strategies catalogue (the cheat sheet)

| Mitigation | Throughput multiplier | Staleness | Complexity |
|---|---|---|---|
| **App-local cache (LRU)** | Massive (N app instances × cache hits) | Up to local-TTL | Low |
| **Replica reads** | M× (number of replicas) | Replication lag | Low (built into Redis Cluster) |
| **Key sharding** (split hot key into N copies) | N× | Eventual via merge | Medium |
| **Jittered fetch / single-flight** | Stops stampede | N/A | Low |
| **CDN edge cache** | Massive | TTL/purge propagation | High infra |
| **Promote to in-process constant** | ∞ | Restart-time only | Trivial — but only for truly static data |

### Edge cases / interview traps

1. **Local cache freshness.** TTL too long → users see stale; too short → defeats the purpose. Pair with cache-bust via pub/sub or short TTL + revalidation.
2. **Key sharding correctness.** "Top trending video views" might shard to 10 counter keys; the read path must SUM them. Writes pick a shard uniformly.
3. **Replica read consistency.** Reads from a replica can be stale by replication lag (10ms-1s). Fine for product info; bad for "did this user just log in".
4. **Hot-key identification.** Redis 4.0+ `--hotkeys` flag; sampling-based, may miss true hottest. Or analyze SLOWLOG / MONITOR output (don't run MONITOR in prod long-term).
5. **Stampede on local cache expiry.** Each app instance independently expires its local copy; they each fetch the upstream. Use jittered TTL.
6. **Probabilistic early refresh** — pair local cache with the XFetch algorithm from the stampede question.
7. **The "celebrity user" problem.** Some keys are hot because of one user; some because of fan-in (popular product). Strategies differ.
8. **Operational visibility.** `INFO commandstats`, `redis-cli --latency-history`, `CLIENT LIST` to spot the hot client.

## Mental Model

### Why one hot key breaks uniform sharding

```
Cluster of 32 Redis shards. Uniform hashing assumes uniform load.

  Reality of the trending product:
                                              50k RPS
                                                 │
                                                 ▼
  shard1 shard2 shard3 ... shard32        ┌──────────┐
  [5%]   [5%]   [95%]    [5%]              │ shard 3  │
                                            │  ALL hot │
                                            │  key reqs│
                                            │ go here  │
                                            └──────────┘

Adding shard 33 doesn't help — the key still hashes to one shard.
You need to BREAK the assumption that "one key = one shard".
```

### The four core moves

```
1. LOCAL CACHE
       ┌─app─┐    ┌─app─┐    ┌─app─┐
       │ LRU │    │ LRU │    │ LRU │     ← absorbs reads
       │ TTL │    │ TTL │    │ TTL │
       └──┬──┘    └──┬──┘    └──┬──┘
          └───────┬──┴──┬────────┘
                  ▼     ▼
              Redis hot shard (now sees miss only)

2. REPLICA READS
       app ─► reads from any replica
                 │
                 ▼
       [primary] ◄─ replicates ─► [r1] [r2] [r3]
                                 (reads sharded across replicas)

3. KEY SHARDING
       hot_key → split into hot_key:0, hot_key:1, ..., hot_key:9
       Write: pick random shard. INCR hot_key:rand(10).
       Read:  read all 10 shards, SUM them.
       Now load is across 10 cluster shards instead of 1.

4. JITTERED FETCH / SINGLE-FLIGHT
       Same idea as the stampede problem, applied per app instance:
       only one request to Redis per N concurrent local misses.
```

### Combined production pattern

```
Reader path:
  1. App's local LRU (1ms hit). Hit? return.
  2. Miss → in-process single-flight (dedupe concurrent fetches).
  3. Fetch from Redis replica (5ms hit, lag-tolerant data).
  4. Populate local LRU with jittered TTL (60s ± 10s).

Writer path:
  1. Write to Redis primary.
  2. Publish "invalidate <key>" via pub/sub.
  3. All app instances subscribed → drop key from local LRU.

Result: Redis primary sees N writes/s; Redis replicas see ~N misses/s; the
       50k RPS read storm is absorbed by app-local caches.
```

## Why interviewers care

- Hot keys are a real ops headache. Senior candidates have a war story.
- The problem **isn't solvable by adding more nodes** — it forces multi-layer thinking.
- Key sharding is the **clever counterintuitive trick** that signals real Redis expertise.
- Replica reads tie into **CAP / consistency** discussions naturally.

## Common beginner confusion

- *"Add more Redis shards."* Doesn't help — the key still maps to one shard. Resharding only spreads *different* hot keys across shards.
- *"Use Redis Cluster."* You're already on Cluster; the issue is *intra*-cluster skew.
- *"Use a CDN."* Works for static GETs but cart, prices, inventory are dynamic. CDN as one *layer* of mitigation, not the answer.
- *"Cache it in the database."* That just moves the hot read to the DB — worse than Redis.
- *"Local cache is unsafe."* It's safe when paired with reasonable TTL or explicit invalidation. The naive worry blocks an obvious win.

## Brute force approach

Vertically scale the hot shard's Redis box. Bigger CPU. Helps the short term. Doesn't help when the key gets hotter. And costs money that scales linearly with traffic.

Pre-emptively distribute everything via consistent hashing and hope. Doesn't help — consistent hashing still maps one key to one node.

## Optimal approach

**Layered defense.**

1. **App-local LRU cache** as the first line. Absorbs most reads.
2. **Replica reads** for non-write-critical data.
3. **Key sharding** for hot counters / append-only data.
4. **Single-flight** dedupes concurrent misses per instance.
5. **CDN edge cache** for purely public data.

Layers compose. A 50k-RPS hot key + 100 app instances + 100ms local TTL + 5 replicas = 50k / 100 / (50 misses per second) / 5 replicas = ~100 RPS per Redis replica. Each layer brings the load down by orders of magnitude.

## Solution (Node + Redis)

### Local cache with single-flight and jittered TTL

```javascript
const Redis = require('ioredis');
const LRU = require('lru-cache');

const redis = new Redis();
const local = new LRU({ max: 10000 });
const inflight = new Map();

const BASE_TTL_MS = 60_000;
const JITTER_MS   = 10_000;

function jitteredTTL() {
  return BASE_TTL_MS + Math.random() * JITTER_MS;
}

async function getHotKey(key) {
  // 1. Local cache
  const cached = local.get(key);
  if (cached && cached.expiresAt > Date.now()) return cached.value;

  // 2. In-process single-flight
  if (inflight.has(key)) return inflight.get(key);

  const promise = (async () => {
    try {
      // 3. Redis (or DB)
      const raw = await redis.get(key);
      const value = raw ? JSON.parse(raw) : null;
      // 4. Populate local with jittered TTL
      local.set(key, { value, expiresAt: Date.now() + jitteredTTL() });
      return value;
    } finally {
      inflight.delete(key);
    }
  })();
  inflight.set(key, promise);
  return promise;
}

// Write path with pub/sub invalidation
async function setHotKey(key, value) {
  await redis.set(key, JSON.stringify(value));
  await redis.publish('cache:invalidate', key);
}

// Subscribe to invalidations
const sub = new Redis();
sub.subscribe('cache:invalidate');
sub.on('message', (chan, key) => {
  local.delete(key);
});
```

### Key sharding for hot counters

```javascript
// Hot key: "views:product:42" getting 50k INCR/s.
// Shard into 32 counter keys; aggregate on read.

const SHARDS = 32;
function shardOf(key) {
  return `${key}:${Math.floor(Math.random() * SHARDS)}`;
}

async function incrHot(key) {
  await redis.incr(shardOf(key));
}

async function readHot(key) {
  const keys = Array.from({ length: SHARDS }, (_, i) => `${key}:${i}`);
  const vals = await redis.mget(keys);
  return vals.reduce((sum, v) => sum + (parseInt(v) || 0), 0);
}
```

Writes distribute across 32 shards (each shard might land on a different Redis Cluster node thanks to varied keys). Reads pay 32 GETs (one MGET round-trip), which is fine for low-frequency read paths.

### Replica reads (ioredis)

```javascript
const cluster = new Redis.Cluster([{ host: 'r1' }, { host: 'r2' }, { host: 'r3' }], {
  scaleReads: 'slave',   // route reads to replicas
});
// Now GETs hit replicas; SETs hit the primary.
```

For per-call routing:

```javascript
await cluster.get('hot:key', 'READONLY');  // explicit replica read
await cluster.set('hot:key', 'val');       // primary
```

## Step-by-step dry run

**Scenario: 50k RPS on `product:viral`, 100 app instances, each instance ~500 RPS.**

```
Step 1: install app-local cache (LRU, jittered 60-70s TTL).
  - first request per instance: miss → Redis fetch → local set.
  - next ~30k requests in that 60s window: local hit.
  - per instance: ~1 miss per 60s window for this key.
  - across 100 instances: 100 / 60 = ~1.7 RPS to Redis. Down from 50k.

Step 2: in-process single-flight dedupes concurrent misses on local TTL expiry.
  - without it, on TTL expiry there could be 50+ concurrent misses on one instance.
  - with it: 1 outbound fetch dedupes all 50.

Step 3: enable replica reads in cluster client.
  - even the 1.7 RPS spreads across 5 replicas = 0.34 RPS each.

Step 4: pub/sub invalidation when product data changes.
  - 'cache:invalidate' message → all app instances drop the key from local LRU.
  - next request per instance fetches fresh; no stale data window beyond pub/sub latency.

Final result:
  Redis primary: handles writes + ~1.7 RPS reads (negligible).
  Redis replicas: 0.34 RPS each.
  App memory: 1 cache entry per hot key (~KB).
  Stale window: ≤ pub/sub propagation (~10ms) on writes.
```

**Scenario: hot counter `views:product:42` at 50k INCR/s.**

```
Without sharding: 50k INCRs to one Redis shard → 95% CPU.
With 32-way sharding:
  Each INCR picks shards 0..31 uniformly.
  Per shard: 50k / 32 ≈ 1560 INCRs/s.
  Reads: aggregate 32 keys (MGET) — usually low-frequency on counters.

For Redis Cluster: the 32 keys distribute across the cluster (different slots).
  Now hot work spreads across many cluster nodes.
```

## How to think aloud in the interview

> "Hot keys break the assumption that uniform hashing gives uniform load. Adding shards doesn't help — the celebrity product is one key, hashes to one shard, that shard saturates. So the fixes have to break that one-key-one-shard assumption.
>
> Layer 1: **app-local cache**. 100 app instances × a 60s TTL means Redis sees ~2 reads/s instead of 50k. Massive win. Pair with jittered TTL so all instances don't expire at the same instant — and in-process single-flight to dedupe concurrent misses within an instance.
>
> Layer 2: **replica reads**. Already-replicated data; turn on `scaleReads: 'slave'` in the client. The miss path spreads across replicas.
>
> Layer 3: for hot *counters* — append-only data like view counts — **shard the key**. `views:product:42` becomes `views:product:42:0` through `views:product:42:31`. Writes pick a shard at random; reads aggregate. The 32 keys hash differently, so cluster load redistributes.
>
> Layer 4: **invalidation via pub/sub**. When the underlying product data changes, publish to a channel; all app instances drop the key from local LRU. Keeps staleness ≤ pub/sub propagation.
>
> Layer 5: for purely public, static-ish data, **CDN edge cache** in front of Redis. Different operational layer; high-impact when applicable.
>
> Identification: Redis 4.0+'s `--hotkeys` flag samples requests. Otherwise tail SLOWLOG, examine `INFO commandstats`, or instrument the app with per-key metrics. Sometimes the hottest key is a surprise — a single user's session or a logging key.
>
> Tradeoffs by layer: local cache adds TTL-bounded staleness; replica reads add replication-lag staleness; key sharding adds read-side aggregation cost; CDN adds purge-propagation delay. Pick the staleness you can tolerate."

## Important takeaways

- **Adding shards doesn't fix hot keys** — one key still hashes to one shard.
- **Local cache + jittered TTL + single-flight** absorbs reads at the app tier — the biggest single win.
- **Replica reads** spread reads across N replicas; bounded by replication lag.
- **Key sharding** is the trick for hot counters: split into N keys, sum on read.
- **Pub/sub invalidation** keeps local caches fresh on writes.
- **CDN edge cache** is the strongest layer for static-public data.
- **Layers compose** — combine 2-3 for orders-of-magnitude relief.
- **Identification first**: `--hotkeys`, SLOWLOG, per-key app metrics.

## Variants

1. **Hot user (celebrity Twitter user)** — fan-out at write time vs fan-in at read time. Twitter's solution: hybrid.
2. **Cold shard recovery** — once you've sharded a hot key, undo when traffic normalises.
3. **CRDT counters** for distributed shard aggregation.
4. **Tiered cache** — app local + Redis local replica + Redis primary. Three layers.
5. **Read-through cache** with `getOrSet(key, loader)` API hiding the layers.
6. **EdgeKV / Cloudflare Workers** for compute-at-edge with hot key.
7. **Bloom-filter prefetch** to predict hot keys before they go hot.

## Revision notes

> **hot-key mitigation — 60 second recap**
> - **Adding shards doesn't help** — one key → one shard.
> - **Layer 1: app-local LRU** with jittered TTL + single-flight (kills 99% of load).
> - **Layer 2: replica reads** (scaleReads: 'slave' / READONLY).
> - **Layer 3: key sharding** for hot counters (split into N, sum on read).
> - **Layer 4: pub/sub invalidation** to keep local caches fresh.
> - **Layer 5: CDN edge** for static-public.
> - Stale window of each: TTL / replication lag / aggregation skew / purge delay.
> - Identify: `--hotkeys`, SLOWLOG, per-key metrics.
> - Twitter "hot user" = read-time fan-in instead of write-time fan-out.
