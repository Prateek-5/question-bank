# Redis Patterns

## Why this matters in backend interviews

- **Redis is in every modern backend stack.** Caching, rate limiting, sessions, leaderboards, queues, distributed locks — interviewers expect deep knowledge.
- Senior signal: knowing the **right data structure for the problem**, the persistence trade-offs, and the failure modes.
- Real production debugging: hot keys, memory pressure, replica lag, eviction storms.

---

## Core concepts

### Data types

| Type | When to use |
|---|---|
| **String** | Cache value, counter, flag, JSON blob (small) |
| **Hash** | Object-like (fields per entity); cheap partial updates |
| **List** | Queue, recent activity log (push/pop) |
| **Set** | Unique tags, deduplication, membership |
| **Sorted set (ZSET)** | Leaderboards, time-ordered events, rate limit windows |
| **Stream** | Append-only log with consumer groups (like a mini Kafka) |
| **Bitmap** | Boolean flags at scale (active-user bitmaps) |
| **HyperLogLog** | Approximate distinct count (~1% error, 12 KB) |
| **Geospatial** | Lat/lng with radius queries |
| **Pub/Sub** | Fan-out messaging (no persistence) |

### Persistence

- **RDB**: periodic snapshot, fork & dump. Compact. Risk: data between snapshots can be lost.
- **AOF**: append every write to a log. Configurable fsync (always / every second / never). Bigger files, but more durable.
- **AOF + RDB**: belt + suspenders — most production setups
- **No persistence**: pure cache; OK for ephemeral data

Default config in production: AOF with `appendfsync everysec` + RDB checkpoints.

### Replication

- Async, leader-follower
- Replicas can serve reads (with stale data risk)
- On primary failure: promote a replica (manual or via **Sentinel**)
- **Redis Cluster** for sharding (hash slots: 16384 slots distributed)

### Eviction

When memory limit is reached, pick a policy:
- `noeviction` — refuse writes (safest if Redis is durable store)
- `allkeys-lru` — LRU across all keys (general cache)
- `volatile-lru` — LRU only over keys with TTL
- `allkeys-lfu` — frequency-based
- `volatile-ttl` — closest-to-expiry first

### Atomic operations

All Redis commands on a single key are atomic. For multi-key atomicity:
- `MULTI` / `EXEC` (transaction)
- **Lua scripts** (server-side, atomic across keys on same slot)
- `WATCH` for optimistic concurrency

### Pipeline

Send multiple commands without waiting for individual replies → fewer round trips:
```javascript
const p = redis.pipeline();
for (const id of ids) p.get(`user:${id}`);
const results = await p.exec();
```

10–100x throughput improvement for bulk ops.

### Common misconceptions

- "Redis is durable" — by default no; configure AOF for durability
- "Redis is single-threaded so slow" — actually fast (in-memory + no lock overhead); modern Redis has I/O threads
- "Redis Cluster scales transparently" — multi-key ops require keys on same slot (hashtag `{}`)
- "Pub/Sub is reliable" — no, messages are dropped if no subscriber. Use Streams instead.
- "TTL automatic" — only on keys you explicitly set; no global default

### Interview traps

1. **"Distributed lock with Redis"** — basic `SETNX` is unsafe (no fencing). Mention **Redlock** controversy.
2. **"Rate limiter in Redis"** — must be atomic; use Lua or sorted set.
3. **"Pub/Sub vs Streams"** — Pub/Sub is fire-and-forget; Streams are durable.
4. **"How do you avoid hot keys?"** — sub-shard, replicate values, L1 cache.
5. **"Multi-key transactions in Cluster"** — must use hashtag to co-locate.

---

## Patterns

### 1. Cache-aside (see `01-caching-strategies.md`)
Basic GET/SET with TTL.

### 2. Distributed lock

#### Simple (one node)
```javascript
const ok = await redis.set(`lock:${key}`, owner, 'NX', 'EX', 30);
if (!ok) throw new Error('LOCKED');
try { /* critical section */ }
finally {
  // Release only if we still own it (Lua for atomic check)
  await redis.eval(`
    if redis.call("get", KEYS[1]) == ARGV[1] then
      return redis.call("del", KEYS[1])
    end
    return 0
  `, 1, `lock:${key}`, owner);
}
```

#### Redlock (Sentinel/Cluster — controversial)
- Acquire lock on majority of N independent Redis nodes
- Has been criticized (Kleppmann vs antirez debate) — not strict mutual exclusion in all failure modes
- For correctness-critical locks, use ZooKeeper / etcd

### 3. Rate limiter

#### Fixed window (atomic)
```javascript
const k = `rl:${userId}:${Math.floor(Date.now()/60000)}`;
const c = await redis.incr(k);
if (c === 1) await redis.expire(k, 60);
if (c > 100) throw new Error('RATE_LIMIT');
```

#### Sliding window (precise, sorted set)
```javascript
const key = `rl:${userId}`;
const now = Date.now();
const windowMs = 60_000;
const limit = 100;
const lua = `
  local key=KEYS[1] local now=tonumber(ARGV[1])
  local windowMs=tonumber(ARGV[2]) local limit=tonumber(ARGV[3])
  redis.call('ZREMRANGEBYSCORE', key, 0, now-windowMs)
  local c = redis.call('ZCARD', key)
  if c < limit then
    redis.call('ZADD', key, now, now..':'..math.random())
    redis.call('EXPIRE', key, math.ceil(windowMs/1000))
    return 1
  end
  return 0
`;
const allowed = await redis.eval(lua, 1, key, now, windowMs, limit);
```

#### Token bucket (Lua)
Standard pattern: stored as hash `{ tokens, last_refill }`; refill on access.

### 4. Leaderboard

```javascript
await redis.zincrby('leaderboard:global', 10, `user:${userId}`);
const top10 = await redis.zrevrange('leaderboard:global', 0, 9, 'WITHSCORES');
const myRank = await redis.zrevrank('leaderboard:global', `user:${userId}`);
const myScore = await redis.zscore('leaderboard:global', `user:${userId}`);
```

For huge leaderboards, shard by score range or by user-bucket.

### 5. Pub/Sub

```javascript
// Subscriber
redis.subscribe('events');
redis.on('message', (channel, msg) => handle(JSON.parse(msg)));

// Publisher
await redis.publish('events', JSON.stringify({ type: 'OrderPlaced', id }));
```

- Fire-and-forget; offline subscribers miss messages
- Use Streams for durable pub/sub

### 6. Streams (durable log)

```javascript
// Producer
await redis.xadd('orders', '*', 'id', orderId, 'total', total);

// Consumer group
await redis.xgroupCreate('orders', 'order-workers', '0', { MKSTREAM: true });
const msgs = await redis.xreadgroup('GROUP', 'order-workers', 'worker-1',
  'COUNT', 10, 'BLOCK', 5000, 'STREAMS', 'orders', '>');
// Process...
await redis.xack('orders', 'order-workers', msgId);
```

- Consumer groups distribute messages across workers (like Kafka)
- ACKs prevent message loss
- Stream length capped: `XADD orders MAXLEN ~ 100000 …`

### 7. Session store

```javascript
const sessionId = uuid();
await redis.hset(`sess:${sessionId}`, { userId, exp: Date.now()+3600_000 });
await redis.expire(`sess:${sessionId}`, 3600);
```

Sliding session: refresh TTL on access.

### 8. Idempotency / dedup

```javascript
// Check + reserve key in one atomic SETNX
const ok = await redis.set(`idem:${key}`, '1', 'NX', 'EX', 86400);
if (!ok) return cachedResponse(key);
// Process; store response under `idem:${key}:resp`
```

### 9. Counter with rollup

```javascript
// Per-minute counters
const k = `count:${endpoint}:${minute}`;
await redis.incr(k);
await redis.expire(k, 7200);  // 2h retention
```

Roll up to per-hour, per-day via scheduled job.

### 10. Geospatial

```javascript
await redis.geoadd('drivers', lng, lat, driverId);
const near = await redis.georadius('drivers', lng, lat, 2, 'km', 'WITHCOORD', 'COUNT', 10);
```

Use cases: ride-sharing, delivery, store locator.

---

## Real examples

### Rate-limit middleware (Express)
```javascript
async function rateLimit(req, res, next) {
  const key = `rl:${req.ip}:${Math.floor(Date.now()/60000)}`;
  const count = await redis.incr(key);
  if (count === 1) await redis.expire(key, 60);
  if (count > 100) return res.status(429).send('Too Many Requests');
  next();
}
```

### Distributed worker queue (Redis Streams)
```javascript
// Each worker
while (true) {
  const messages = await redis.xreadgroup('GROUP', 'workers', `worker-${id}`,
    'BLOCK', 5000, 'COUNT', 10, 'STREAMS', 'jobs', '>');
  for (const [stream, entries] of messages || []) {
    for (const [msgId, fields] of entries) {
      try {
        await process(fields);
        await redis.xack('jobs', 'workers', msgId);
      } catch (e) {
        // pending entry stays; re-claim via XPENDING / XCLAIM
      }
    }
  }
}
```

### Top-N feed cache (sorted set)
```javascript
// Push new post to top of user's feed (capped at 1000)
await redis.zadd(`feed:${userId}`, postTimestamp, postId);
await redis.zremrangebyrank(`feed:${userId}`, 0, -1001);  // keep 1000

const feedPage = await redis.zrevrange(`feed:${userId}`, 0, 49);
```

### Online users count (HyperLogLog)
```javascript
await redis.pfadd('users:online:today', userId);
const approx = await redis.pfcount('users:online:today');
```

### Notification dedup (Set)
```javascript
const added = await redis.sadd(`notified:${userId}`, eventId);
if (added) await sendNotification(...);
```

### Cluster + multi-key (hashtag)
```javascript
// Both keys land on the same slot
await redis.mset(`{user:42}:profile`, ..., `{user:42}:settings`, ...);
```

---

## Common interview questions

1. Redis data types — what are they and when used?
2. How do you build a rate limiter in Redis?
3. How do you implement distributed locks in Redis?
4. Pub/Sub vs Streams.
5. Redis persistence (RDB, AOF).
6. What is Redis Cluster? Hash slots? Hashtags?
7. How does Redis handle eviction?
8. What is a hot key in Redis? Mitigation?
9. How would you implement a leaderboard?
10. Redis transactions — MULTI/EXEC vs Lua.
11. When to use Redis vs Memcached?
12. How does Redis Sentinel work?

---

## Detailed answers

### 1. Data types
String, Hash, List, Set, Sorted set, Stream, Bitmap, HyperLogLog, Geospatial. Each maps to a problem pattern; choose by access shape.

### 2. Rate limiter
Fixed window: `INCR` + `EXPIRE` — fast, slight edge inaccuracy. Sliding window: sorted set with timestamps + Lua atomic. Token bucket: hash with tokens + refill via Lua.

### 3. Distributed lock
`SET NX EX` for basic; release with Lua to check owner. For correctness-sensitive, use ZooKeeper/etcd. **Redlock** is controversial — discuss honestly.

### 4. Pub/Sub vs Streams
- Pub/Sub: in-memory broadcast, dropped if no subscriber, no replay
- Streams: durable, consumer groups, replay, ACKs, capped length
Use Streams for anything resembling event processing.

### 5. Persistence
RDB: periodic snapshot, fast restart, possible data loss between snapshots. AOF: every write logged, configurable fsync, slower but more durable. Combine both in prod.

### 6. Cluster
16384 hash slots; each node owns a slot range. Key → slot via CRC16. To co-locate keys (for multi-key commands), use hashtags: `{user:42}:profile`.

### 7. Eviction
Picks based on `maxmemory-policy`. Common: `allkeys-lru` for cache, `volatile-lru` if you have a mix of TTL and persistent data, `noeviction` if Redis is durable source.

### 8. Hot key
A single key receiving disproportionate traffic. Mitigate: L1 in-process cache (avoid round trip), sub-shard the key (`leaderboard:0..9`), CDN for cacheable responses, dedicated replica.

### 9. Leaderboard
Sorted set; `ZINCRBY` for score updates, `ZRANGEBYSCORE` / `ZREVRANK` for queries. For massive scale: shard by user-bucket; merge top-N from each shard.

### 10. Transactions
- `MULTI/EXEC`: queue commands; executed atomically. `WATCH` for optimistic concurrency.
- Lua: atomic script execution; can have conditional logic; more flexible.
Lua is the modern choice for non-trivial atomic ops.

### 11. Redis vs Memcached
Redis: richer data structures, persistence, replication, scripting, streams, pub/sub. Memcached: pure KV, multi-threaded, slightly simpler/faster for plain ops. Pick Redis by default unless minimal needs.

### 12. Sentinel
Cluster of Sentinel processes monitor Redis primary + replicas. On primary failure, vote to promote a replica. Update DNS or notify apps. Provides automatic failover without manual ops.

---

## Practical coding examples

### Connection pool (Node ioredis)
```javascript
const Redis = require('ioredis');
const redis = new Redis.Cluster([
  { host: 'r1', port: 6379 },
  { host: 'r2', port: 6379 }
], { redisOptions: { maxRetriesPerRequest: 3 } });
```

### Pipeline + batch
```javascript
const p = redis.pipeline();
for (const id of ids) p.hgetall(`user:${id}`);
const results = await p.exec();
```

### Atomic counter with cap
```lua
-- KEYS[1] = counter, ARGV[1] = cap
local v = redis.call("INCR", KEYS[1])
if v == 1 then redis.call("EXPIRE", KEYS[1], 3600) end
if v > tonumber(ARGV[1]) then return 0 end
return v
```

### Streams: claim stuck messages
```javascript
const pending = await redis.xpending('jobs', 'workers');
// Re-claim ones older than 30s by some worker
const claimed = await redis.xclaim('jobs', 'workers', `worker-${id}`, 30000, ...msgIds);
```

### Bitmap: daily active users
```javascript
await redis.setbit(`active:${date}`, userId, 1);
const dau = await redis.bitcount(`active:${date}`);

// Last-7-day actives (union of 7 bitmaps)
await redis.bitop('OR', 'active:last7', ...sevenDateKeys);
const wau = await redis.bitcount('active:last7');
```

---

## Common mistakes

- Using Pub/Sub when you needed Streams (lost messages)
- Long-running Lua scripts blocking the single-threaded server
- Mass `KEYS *` scans (use `SCAN`!)
- Storing huge values (Redis is memory; >1 MB items slow everything)
- No memory limit + no eviction policy → OOM crash
- Single Redis as durable store without AOF + replication
- Not testing failover with Sentinel/Cluster
- Hot key without mitigation

---

## Senior engineer discussion points

- **Redis modules**: RediSearch (full-text), RedisJSON, RedisGraph, RedisBloom — extends data model
- **Redis Stack / Enterprise** vs OSS — feature differences
- **KeyDB / Dragonfly / Garnet** — Redis-compatible alternatives with multi-threaded performance
- **Hot key detection** via `MONITOR` (debug only) or sampling
- **Memory fragmentation** — `MEMORY DOCTOR`; defragmentation with `activedefrag`
- **Persistence trade-off** — AOF rewrites can be expensive; tune `auto-aof-rewrite-percentage`
- **Replication lag impact** — if you read from replica, expect stale data
- **Redis as primary store** — risky; need careful persistence + replication; not recommended for OLTP
- **Memcached resurgence** at giant scale (Facebook, Twitter) for sheer simplicity / multi-threading
- **Cluster pain points** — multi-key ops need same-slot keys; cross-slot transactions impossible

---

## Revision notes

- Data types: String / Hash / List / Set / ZSET / Stream / Bitmap / HLL / Geo
- Persistence: RDB (snapshot) + AOF (log); use both
- Eviction: `allkeys-lru` for cache, `noeviction` for durable store
- Cluster: 16384 hash slots; `{tag}` for co-location
- Single-threaded → long Lua scripts block everything
- Pub/Sub = ephemeral; Streams = durable + consumer groups
- Rate limiter: fixed window (`INCR+EXPIRE`) or sliding (ZSET + Lua)
- Distributed lock: `SET NX EX` + Lua release; Redlock for cluster (controversial)
- Hot key: L1 + sub-shard + CDN
- Pipeline for bulk ops; `SCAN` not `KEYS`
- Memcached: pure KV, multi-threaded; Redis: rich features
