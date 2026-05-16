# Redis Patterns

## Intuition first — what Redis actually is

Forget the marketing for a moment. Redis is, at its core, a very fast hash map that lives in RAM, plus a small library of useful data structures (lists, sets, sorted sets, streams) keyed by strings. Everything else — persistence, replication, clustering, Lua, pub/sub — is built on top of that one idea.

**The desk-vs-warehouse analogy.** Disk is a warehouse: huge capacity, but every fetch is a forklift trip. RAM is your desk: tiny by comparison, but everything within arm's reach. A read from RAM is roughly 1000× faster than a read from spinning disk and ~100× faster than SSD. Redis is what happens when you decide to keep your entire working set on the desk.

**Why "single-threaded" is a feature, not a bug.** A single thread executes commands one at a time, in order. That means *no locks*, *no race conditions*, *no atomicity headaches inside a single command*. You pay for it with: no parallelism per shard (so you scale horizontally with Cluster), and any slow command (a giant Lua script, `KEYS *`) blocks everyone else.

**The data-structure-as-metaphor cheatsheet** — internalize these:

| Type | Real-world analogy |
|---|---|
| String | A sticky note: one label, one value |
| Hash | A labelled folder full of forms: object-like fields |
| List | A train of cars: push/pop from either end; a queue or stack |
| Set | A bag of marbles, no duplicates: membership + set algebra |
| Sorted set | A leaderboard: every entry has a score; auto-sorted |
| Stream | A flight recorder: append-only, replayable, with consumer groups |
| Bitmap | A row of light switches: 1 bit per position; pack billions into KB |
| HyperLogLog | A crowd-counter machine: approximate, tiny memory, "how many uniques?" |
| Geospatial | Pins on a map: lat/lng with radius queries |
| Pub/Sub | A loudspeaker in a hallway: broadcasts; anyone not listening misses it |

### Progressive build — from sticky note to event log

1. **Level 0 — just a cache.** `SET user:42 "{...json...}"` with a TTL. You've replaced 90% of round-trips to your slow database. This is where most apps live.
2. **Level 1 — counter & flag.** `INCR pageviews:home`, `SET feature:newui:enabled 1`. Atomic single-key ops; no locks needed.
3. **Level 2 — object updates.** `HSET user:42 last_login 1700000000` to update one field of a stored user without rewriting the whole object.
4. **Level 3 — a queue.** `LPUSH jobs:pending …` from producers; `BRPOP jobs:pending 0` from workers. Blocking pop = built-in semaphore.
5. **Level 4 — a leaderboard / dedup.** `ZADD leaderboard $score $user`; `SADD seen:event123 $userId`.
6. **Level 5 — a rate limiter.** Sliding window via ZSET + Lua; precise and atomic.
7. **Level 6 — durable event bus.** Streams + consumer groups = a "mini Kafka" with replay and ACKs.
8. **Level 7 — distributed coordination.** SETNX + TTL + Lua fenced unlock; or Redlock across nodes. Carefully.

## Why this matters in backend interviews

- **Redis is in every modern backend stack.** Caching, rate limiting, sessions, leaderboards, queues, distributed locks — interviewers expect deep knowledge.
- Senior signal: knowing the **right data structure for the problem**, the persistence trade-offs, and the failure modes.
- Real production debugging: hot keys, memory pressure, replica lag, eviction storms.

## Why interviewers care

- They want to test **pattern-matching skill**: when you hear "leaderboard," do you immediately think ZSET? "Rate limiter" → INCR or sliding ZSET? "Job queue" → List or Stream? Senior engineers don't reach for `SET ... JSON.stringify(...)` for every problem.
- They want to see your **atomicity intuition**: single command = atomic. Multiple commands = need MULTI/EXEC or Lua. Multiple keys across slots in Cluster = impossible without redesign.
- They want **persistence-tradeoff vocabulary**: AOF vs RDB, `fsync always` vs `everysec`, what happens during a fork, why `everysec` can still lose ~1s of writes.
- They want **failure-mode literacy**: what happens when memory fills up? When a replica falls behind? When a Lua script runs forever?
- They want to catch you on **the unsafe defaults**: `SETNX` is not a distributed lock. `MULTI/EXEC` is not a transaction in the ACID sense. `KEYS *` will brick production.

## Common beginner confusion

- **"MULTI/EXEC is a transaction."** It's atomic (all-or-nothing execution) but not *isolated* in the ACID sense — there's no rollback on logical errors, and reads inside the block see queued, not executed, state. Use `WATCH` for optimistic concurrency, or just write a Lua script.
- **"KEYS \* is fine in prod."** No. `KEYS` scans the entire keyspace in one blocking call. On a 50M-key instance this can lock the server for seconds. Use `SCAN`, which is cursor-based and incremental.
- **"Redis is single-threaded so I can't lose writes."** You absolutely can. With `appendfsync everysec` (the default), up to 1 second of writes are in the OS buffer when the process dies. With `appendfsync no`, you can lose minutes. Single-threaded means atomicity, not durability.
- **"SETNX is a distributed lock."** Only safe if combined with: (a) a TTL to prevent stuck locks if the holder dies, (b) a unique owner-ID so you only release locks you own, (c) Lua for atomic check-and-delete on release, and (d) a fencing token if your downstream allows it. Plain `SETNX` is a foot-gun.
- **"Pub/Sub guarantees delivery."** It's fire-and-forget. Disconnected subscribers miss every message. Use Streams.
- **"Cluster makes everything transparent."** Multi-key commands (`MSET`, transactions, Lua) only work if all keys hash to the *same slot*. Use hashtags `{user:42}:profile` / `{user:42}:settings` to co-locate.
- **"Redis can be a primary database."** Only with very careful AOF + replication + monitoring, and even then it's risky for OLTP workloads. The default mental model: Redis is a high-speed cache that may also persist as a safety net.

## First principles — what makes Redis fast

**Why RAM beats disk by 1000×.** A random read from a spinning disk seeks to a track (~5 ms). A read from RAM is ~100 ns. That's a factor of 50,000. Even SSD at ~100 µs is 1000× slower than RAM. Redis avoids the disk on the read path entirely.

**Why single-threaded simplifies but limits.** A single command-execution thread means no locks anywhere in the codebase, no atomic ops on shared state, no race conditions inside a command. Atomicity is *free*. Cost: one slow command blocks all others on that shard. Modern Redis (6+) added I/O threads for socket read/write parallelism, but command execution is still single-threaded.

**What a slot is in Cluster mode.** Redis Cluster doesn't shard by key; it shards by *slot*. The keyspace is partitioned into 16384 logical slots; each key's slot is `CRC16(key) % 16384`. Each cluster node owns a range of slots. Resharding moves slots (and their keys) between nodes without rewriting client code. The 16384 constant is a balance: small enough to fit in a 2 KB bitmap per cluster gossip message, large enough that even 1000-node clusters get fine-grained distribution.

**Hashtag mechanic.** If a key contains `{…}`, Redis hashes only the substring inside the braces. So `{user:42}:profile` and `{user:42}:settings` hash identically and land on the same slot — making multi-key operations between them legal.

---

## Core concepts

### Data types

#### Mental model — pick the structure that *fits* the access pattern

Redis isn't a "just dump JSON into it" store. The point is that for each data type, the operations you'll perform are O(1) or O(log N), and they map cleanly onto common problems:

- **String** is the sticky note. Use for: caches, counters (`INCR`), flags, small JSON blobs. Atomic ops: `INCR`, `INCRBYFLOAT`, `APPEND`, `GETSET`.
- **Hash** is the labelled folder. Use for: object-like entities where you frequently update *one field*. `HSET user:42 last_login NOW` doesn't rewrite the whole user; `SET user:42 $bigjson` does.
- **List** is the train of cars. Doubly-linked. `LPUSH`/`RPOP` = FIFO queue; `LPUSH`/`LPOP` = stack; `BRPOP` = blocking pop (consumer waits with no busy loop).
- **Set** is the bag of unique items. `SADD` for membership; `SINTER`, `SUNION`, `SDIFF` for set algebra. Great for "tags," "followers in common," "seen-this-already" dedup.
- **Sorted set (ZSET)** is the leaderboard. Every member has a score; structure auto-sorted. `ZADD` to insert/update, `ZRANGE` / `ZREVRANGE` for top-N, `ZRANGEBYSCORE` for time-window queries, `ZRANK` for "where am I in the ranking?"
- **Stream** is the flight recorder. Append-only log. Each entry gets a monotonically-increasing ID. `XADD` to write; `XREAD` / `XREADGROUP` to consume; ACKs prevent loss. This is Redis's answer to Kafka — durable, replayable, with consumer groups.
- **Bitmap** is the row of light switches. Stored as a string under the hood; each bit is addressable via `SETBIT key offset 1`. 1 billion users in 125 MB. Use for daily-active-user tracking, feature flags per user.
- **HyperLogLog** is the crowd-counter. Probabilistic; ~0.81% standard error; ~12 KB per HLL regardless of cardinality. `PFADD` to add an element, `PFCOUNT` to estimate uniques. Magical for "approximate distinct" without storing the set.
- **Geospatial** is pins on a map. Stored as a ZSET under the hood (lat/lng encoded into a 52-bit geohash score). `GEOADD`, `GEORADIUS` (now `GEOSEARCH`), `GEODIST`.

**Common confusion.** "Why not always use Hash for objects?" Because if you only ever read the whole object back, a String of JSON is simpler and often faster — there's serialization cost, but only one network call and one memory allocation. Use Hash when you do *partial updates* or *partial reads*.

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

#### Mental model — snapshot vs journal

There are two fundamentally different ways to make in-memory data durable:

- **RDB (snapshot)**: every N seconds (or after K writes), Redis `fork()`s a child process which writes the entire current dataset to a `.rdb` file. The child uses copy-on-write to avoid blocking the parent. Restart = load the snapshot in seconds. Cost: anything written *between* snapshots is gone on crash.
- **AOF (append-only file / journal)**: every write command is appended to a log. Restart = replay the log. Cost: log is bigger than RDB; replay is slower than snapshot load; periodic rewrites are needed to compact it.

```
   RDB snapshot timeline:
        T=0:00     T=0:05      T=0:10      T=0:15  ←─crash here
        ●─────────●───────────●───────────●         ← 15s of writes lost
        snap      snap        snap        snap

   AOF journal timeline:
        ►►►►►►►►►►►►►►►►►►►►►►►►►►►►►►►►►►●         ← <=1s lost (everysec)
        each write appended; fsync per policy
```

**The fsync policy is the real durability dial:**
- `appendfsync always` — fsync after every write. Slow, but at most a few writes lost.
- `appendfsync everysec` — fsync once per second. Default. Up to ~1s of writes lost.
- `appendfsync no` — let the OS decide. Fast, but could lose minutes.

**Common confusion.** "AOF means I won't lose any writes." Only true with `appendfsync always`, and even then the write must have returned to the client before fsync completed — there's a small window. For payment-grade durability, never use Redis alone; use a real RDBMS.

#### Walkthrough — what `fork()` does to a 50 GB Redis

1. Background save kicks off. Redis calls `fork()`. The OS creates a child process *sharing* the parent's memory via copy-on-write.
2. The fork itself is nearly instant — only the page table is copied, not the data. But page-table copy on 50 GB can still take a few hundred ms; clients experience a latency blip.
3. While the child writes the snapshot to disk, every write in the parent triggers a page fault → page copy. Memory usage can balloon (worst case 2× RSS).
4. When the child finishes, it exits; the snapshot file is atomically renamed into place.

This is why interviewers ask "what's the operational risk of persistence?" — the answer is the fork-induced memory spike, especially on cloud VMs with overcommit disabled.

- **RDB**: periodic snapshot, fork & dump. Compact. Risk: data between snapshots can be lost.
- **AOF**: append every write to a log. Configurable fsync (always / every second / never). Bigger files, but more durable.
- **AOF + RDB**: belt + suspenders — most production setups
- **No persistence**: pure cache; OK for ephemeral data

Default config in production: AOF with `appendfsync everysec` + RDB checkpoints.

### Replication

#### Mental model — async write fan-out

A Redis primary doesn't wait for replicas. It writes locally, returns OK to the client, *then* fans out the write to replicas via a replication stream. This is what "async" means and why **reading from replicas can return stale data**. The gap (lag) is normally microseconds but can grow if the replica is overloaded or the network is slow.

**Cluster mode** layers on top: 16384 hash slots distributed across N primaries, each with M replicas. Slots are the unit of resharding — when you add a node, slots (and their keys) are migrated.

```
   Cluster slot map (toy example, 3 primaries, 16384 slots):

      Node A  ──  slots [0     .. 5460  ]
      Node B  ──  slots [5461  .. 10921 ]
      Node C  ──  slots [10922 .. 16383 ]

   Client computes:  slot = CRC16(key) % 16384
                    then routes directly to the owning primary.
```

**Common confusion.** "If I read from a replica I get eventual consistency." Yes, but worse — under failover you can read a value that was *committed on the primary* but never made it to the replica, then never see it again if a different replica is promoted. Redis replication is not RAFT.

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

#### Mental model — single-threaded gives you atomicity for free, but only per command

Because exactly one command executes at any instant on a given Redis instance, every individual command is *automatically* atomic. `INCR` is atomic. `LPUSH` is atomic. `ZADD` is atomic. No locks, no races.

The complication appears when you need *multiple* commands to behave as one logical unit:

- **MULTI/EXEC**: queues commands, then executes them as a single atomic block. But it's *not* a transaction in the SQL sense — no rollback on logical error, no isolation in the snapshot sense.
- **Lua script**: the script runs in a single, uninterrupted call. While it executes, *nothing else runs on the shard*. Full atomicity, including conditional logic.
- **WATCH**: optimistic CAS. You declare interest in some keys; if any of them change before your EXEC, the EXEC aborts.

**Common confusion.** "MULTI/EXEC rolls back if a command fails." False. If a queued command has a syntax error, EXEC aborts the whole transaction. But if a runtime error occurs (e.g., `INCR` on a non-integer), the other commands still execute. Redis prioritizes simplicity over rollback semantics.

All Redis commands on a single key are atomic. For multi-key atomicity:
- `MULTI` / `EXEC` (transaction)
- **Lua scripts** (server-side, atomic across keys on same slot)
- `WATCH` for optimistic concurrency

### Pipeline

#### Mental model — batch the round trips, not the work

Without pipelining, a sequence of N commands takes N round-trip times (RTT). With pipelining, all N commands go in one packet and all N replies come back in one packet — total cost ≈ 1 RTT + N × server-time. Over the wire it's a *huge* difference.

```
   Without pipeline (4 commands):

      client  ──cmd1──▶  server
              ◀──rep1──
              ──cmd2──▶
              ◀──rep2──
              ──cmd3──▶
              ◀──rep3──
              ──cmd4──▶
              ◀──rep4──            total = 4 × RTT

   With pipeline:

      client  ──cmd1,cmd2,cmd3,cmd4──▶  server
              ◀──rep1,rep2,rep3,rep4──   total ≈ 1 × RTT
```

**Common confusion.** "Pipeline is the same as MULTI/EXEC." No — pipelining is purely a *network optimization*; commands still execute one at a time and can be interleaved with other clients' commands. MULTI/EXEC adds atomicity (no interleaving).

Send multiple commands without waiting for individual replies → fewer round trips:
```javascript
const p = redis.pipeline();
for (const id of ids) p.get(`user:${id}`);
const results = await p.exec();
```

Step-by-step:
1. `redis.pipeline()` creates a local buffer; subsequent `p.get(...)` calls don't go to the network — they're queued in the client.
2. `p.exec()` sends the entire buffer in one socket write. Server reads them, executes each (potentially interleaved with other clients' commands), writes all replies in one socket write.
3. Client returns the array of results. If you had 100 GETs over a 1 ms RTT network, you went from 100 ms total to ~1 ms.

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

#### Mental model — the three pieces of a safe lock

A correct distributed lock requires three properties simultaneously:

1. **Mutual exclusion** — at most one holder at a time. Provided by `SETNX` (set if not exists).
2. **Liveness on holder failure** — if the holder dies mid-critical-section, the lock must eventually release itself. Provided by `EX` (TTL).
3. **Safe release** — the holder must not accidentally release someone else's lock if its TTL expired but it's still running. Provided by storing a unique `owner` token and checking it before delete (Lua, atomic).

The remaining gap is **fencing**: even with all three above, a process that froze (GC pause, OS swap) past the TTL could resume, think it still holds the lock, and clobber the new holder's work downstream. Fencing tokens — monotonically-increasing IDs — solve this when your protected resource can validate them.

```
   Fencing-token timeline (the classic Kleppmann diagram):

   Client A   |══════ holds lock, token=33 ═══X (GC pause!)══════════════►
                                                                  writes "X" with token 33
                                                                  to storage
   Lock TTL   ──────────────────────expires─────────────────────────────
   Client B   ───────────────────────────|═════ holds lock, token=34 ══►
                                          writes "Y" with token 34
                                          to storage

   Storage rejects token=33 because it already saw 34 ✓
```

Without fencing, A's late write would silently overwrite B's. Pure Redlock does *not* give you a fencing token (without external bookkeeping); that's the core of the Kleppmann critique.

**Common confusion.** "If I just use `SET NX EX` I'm safe." Only safe for *advisory* coordination (e.g., singleton periodic job). Not safe for protecting writes to a downstream system where correctness depends on at-most-one-writer.

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

Step-by-step:
1. `SET lock:foo owner NX EX 30` — atomically: "set this key to `owner` only if it doesn't exist, with a 30s TTL." Returns OK if we got the lock, nil otherwise.
2. If we got the lock, we do our work. If anything throws, the `finally` runs.
3. Release time. We can't just `DEL lock:foo` — by the time we get here, our TTL might have expired and someone else might hold the lock. Deleting it would corrupt their critical section.
4. Lua script atomically: read the current value, compare to *our* `owner` token, only delete if they match. This is the safe-release property.
5. If TTL expired (we're slow), the script returns 0; we just move on. The new holder is unaffected.

#### Redlock (Sentinel/Cluster — controversial)
- Acquire lock on majority of N independent Redis nodes
- Has been criticized (Kleppmann vs antirez debate) — not strict mutual exclusion in all failure modes
- For correctness-critical locks, use ZooKeeper / etcd

### 3. Rate limiter

#### Mental model — three flavors, three tradeoffs

- **Fixed window**: count requests inside calendar minute. Simple, fast, but allows a *burst at the boundary* — a user can fire 100 requests at 12:00:59 and 100 more at 12:01:00, effectively 200 in 1 second.
- **Sliding window** (ZSET): store each request's timestamp; on each new request, drop entries older than the window and count what's left. Exact and burst-free; costs more memory (one ZSET entry per request).
- **Token bucket**: tokens accrue at a fixed rate up to a cap; each request consumes one. Supports controlled bursts. The "API throttling" textbook algorithm.

```
   Fixed window flaw (boundary burst):

      ───────|───────────────|───────────────|────
            12:00          12:01          12:02
            ▲ 100 reqs at 12:00:59 ── allowed (window 1 count = 100)
            ▲ 100 reqs at 12:01:00 ── allowed (window 2 count = 100)
                  effective: 200 req in 1 second
```

**Common confusion.** "Fixed window is fine for most use cases." For abuse prevention it usually isn't — the boundary burst is exactly what attackers exploit. Sliding window is the senior default; fixed window only when you genuinely don't care about precision.

#### Fixed window (atomic)
```javascript
const k = `rl:${userId}:${Math.floor(Date.now()/60000)}`;
const c = await redis.incr(k);
if (c === 1) await redis.expire(k, 60);
if (c > 100) throw new Error('RATE_LIMIT');
```

Step-by-step:
1. Build a key that *includes the current minute* — e.g., `rl:user42:28333333`. The key itself rolls over each minute.
2. `INCR` atomically increments and returns the new count. If this is the first request in this minute, `INCR` creates the key with value 1.
3. On the first request only (`c === 1`), set a TTL of 60s so the key auto-expires after its window.
4. If the count exceeds the limit, reject. Otherwise allow.

Edge case: there's a tiny race where `INCR` succeeds but the server dies before `EXPIRE` runs — the key would live forever (until eviction). Lua-ify both ops for absolute safety.

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

Step-by-step (sliding window Lua):
1. `ZREMRANGEBYSCORE key 0 now-windowMs` — drop all entries whose timestamp is older than the window. The sorted set now contains only "still relevant" requests.
2. `ZCARD key` — how many are left? That's the precise count of requests in the last `windowMs`.
3. If under limit, `ZADD now <unique>` adds this request. The score is `now`, the member is `now:<random>` to avoid ZADD's update-if-exists behavior collapsing same-timestamp entries.
4. Set/refresh TTL on the key itself so a quiet user doesn't waste memory forever.
5. Return 1 (allow) or 0 (deny). The whole script runs atomically on the server.

#### Token bucket (Lua)
Standard pattern: stored as hash `{ tokens, last_refill }`; refill on access.

Mental model: imagine a bucket holding up to `cap` tokens. Tokens trickle in at `rate` per second. Each request grabs one token; if the bucket is empty, the request is denied. On each request, the algorithm computes "how many tokens have accrued since last_refill?" and adds them (capped at `cap`).

### 4. Leaderboard

#### Mental model — the ZSET is *built* for this

A ZSET is a sorted set where every member has a numeric score. Internally it's a skip list + hash table, giving O(log N) inserts/updates and O(log N + K) range queries. That is exactly what a leaderboard needs: "give me top 10" (range), "what's my rank" (rank lookup), "increment my score" (atomic update).

```javascript
await redis.zincrby('leaderboard:global', 10, `user:${userId}`);
const top10 = await redis.zrevrange('leaderboard:global', 0, 9, 'WITHSCORES');
const myRank = await redis.zrevrank('leaderboard:global', `user:${userId}`);
const myScore = await redis.zscore('leaderboard:global', `user:${userId}`);
```

Step-by-step:
1. `ZINCRBY` adds 10 to user's score atomically. If the user wasn't in the set, they're inserted at score 10.
2. `ZREVRANGE 0 9` fetches the highest-scored 10 members (REV = descending). `WITHSCORES` returns interleaved member-score pairs.
3. `ZREVRANK` returns 0-indexed rank. User at top = rank 0.
4. `ZSCORE` returns the raw score.

**Common confusion.** "Won't a 100-million-user leaderboard be slow?" `ZINCRBY` is O(log N) — for 100M users, that's ~27 ops. Fine. The pathology is *querying ranks deep in the list* for many users at once, or storing huge top-N pages. Pagination + caching of the top hundred handles most real apps.

For huge leaderboards, shard by score range or by user-bucket.

### 5. Pub/Sub

#### Mental model — a loudspeaker in a hallway

Pub/Sub is the simplest possible message bus: a publisher shouts a message on a channel; everyone currently listening hears it. Anyone *not* listening — disconnected, slow, asleep — misses it forever. No queues, no buffering, no replay.

This makes it perfect for "live notifications" where loss is acceptable (typing indicators, presence updates, ephemeral cache invalidations). It's wrong for anything where you'd say "I don't want to lose this message."

```javascript
// Subscriber
redis.subscribe('events');
redis.on('message', (channel, msg) => handle(JSON.parse(msg)));

// Publisher
await redis.publish('events', JSON.stringify({ type: 'OrderPlaced', id }));
```

Step-by-step:
1. The subscriber tells Redis "I care about channel `events`." Its connection is now in subscriber mode (can't issue arbitrary commands).
2. The publisher fires `PUBLISH events <json>`. Redis iterates all current subscribers of that channel and writes the message to their sockets.
3. If the subscriber is slow to read, messages buffer in its output buffer (configurable per-class) — if it overflows, the subscriber is *disconnected* by Redis. This is the dropped-message scenario.
4. If the subscriber was offline at publish time, it never gets the message.

**Common confusion.** "Pub/Sub is reliable in Cluster." Even worse — Pub/Sub in Cluster mode either uses sharded pub/sub (Redis 7+) where the channel is hash-slotted, or broadcasts across all nodes (older versions, expensive). Either way, no persistence.

- Fire-and-forget; offline subscribers miss messages
- Use Streams for durable pub/sub

### 6. Streams (durable log)

#### Mental model — a mini Kafka inside Redis

A Stream is an append-only log of entries, each with a monotonically increasing ID (`<ms>-<seq>`). Producers `XADD`; consumers `XREAD` or `XREADGROUP`. Unlike Pub/Sub, entries are persisted (subject to your AOF/RDB settings) and replayable.

Consumer groups are the magic. Within a group, each message is delivered to exactly one consumer. If that consumer dies before ACKing, the message stays in the "pending entries list" (PEL) and can be re-claimed by another consumer via `XCLAIM`.

```
   Stream conceptual layout:

      XADD entries:    [id1] [id2] [id3] [id4] [id5] ...
                         │     │     │     │     │
       group="workers"   ▼     ▼     ▼     ▼     ▼
         consumer-1     ACK   PEL  ACK    │     │
         consumer-2                       ACK    │
         consumer-3                              ACK

   PEL = pending entries list (delivered but not yet ACK'd)
```

**Common confusion.** "Streams are unbounded — won't they fill memory?" Yes, unless you cap them. `XADD orders MAXLEN ~ 100000 *` keeps roughly the last 100k entries (`~` = approximate trimming, much cheaper than exact).

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

Step-by-step:
1. Producer: `XADD orders * id 123 total 99.50`. The `*` tells Redis to auto-generate the ID. Field/value pairs follow.
2. Consumer group is created once with starting position `0` (read from beginning) or `$` (only new entries from now).
3. `XREADGROUP GROUP order-workers worker-1 COUNT 10 BLOCK 5000 STREAMS orders >`: "as `worker-1` in group `order-workers`, give me up to 10 *new* (`>`) entries; if none available, wait up to 5s."
4. Process the entries.
5. `XACK orders order-workers <msgId>` removes from PEL — Redis now knows you've fully handled this entry.
6. If `worker-1` crashes between read and ack, the entries stay in PEL. A janitor can `XPENDING` to find stuck entries and `XCLAIM` to reassign them to a different worker.

- Consumer groups distribute messages across workers (like Kafka)
- ACKs prevent message loss
- Stream length capped: `XADD orders MAXLEN ~ 100000 …`

### 7. Session store

#### Mental model — TTL as the session timer

Sessions are the textbook Redis use case: short-lived, key-value, accessed by every request. A Hash is perfect because you can update one field (`last_active`) without rewriting the whole session. TTL gives you free expiration — no janitor job needed.

```javascript
const sessionId = uuid();
await redis.hset(`sess:${sessionId}`, { userId, exp: Date.now()+3600_000 });
await redis.expire(`sess:${sessionId}`, 3600);
```

Step-by-step:
1. Generate a cryptographically random session ID (uuid v4 or crypto.randomBytes).
2. Store session fields in a Hash. Cheap partial updates later: `HSET sess:xxx last_seen NOW`.
3. Set a 1-hour TTL. After 1h of inactivity, Redis silently deletes the key — session expires.
4. **Sliding session**: on each authenticated request, call `EXPIRE sess:xxx 3600` again to push the deadline. The session never expires while the user is active.

**Common confusion.** "If Redis loses my sessions on restart, users get logged out." True with no persistence. AOF with `everysec` reduces but doesn't eliminate the risk. For "never log out" durability, store sessions in a real DB and use Redis as a *cache* in front of it.

Sliding session: refresh TTL on access.

### 8. Idempotency / dedup

#### Mental model — "have I seen this request before?"

When a client retries a request (mobile network blip, gateway timeout), you want the *second* attempt to return the *first* attempt's result, not re-execute the side effects. Pattern: client sends an `Idempotency-Key` header; server uses Redis SETNX to claim the key. If claimed first → execute and store response. If already claimed → return stored response.

```javascript
// Check + reserve key in one atomic SETNX
const ok = await redis.set(`idem:${key}`, '1', 'NX', 'EX', 86400);
if (!ok) return cachedResponse(key);
// Process; store response under `idem:${key}:resp`
```

Step-by-step:
1. Client sends `POST /charge` with header `Idempotency-Key: abc-123`.
2. Server calls `SET idem:abc-123 1 NX EX 86400`. NX = only if not exists.
3. If `ok` → we're the first to see this key. Process the charge. Store the response somewhere keyed by the idempotency key, with the same TTL.
4. If `ok` is nil → another request with the same key already arrived. Return the stored response.
5. Edge case: race between two retries — the second one might arrive *before* the first stored its response. Handle with a "pending" state and a poll/wait, or accept the rare double-execute.

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

Step-by-step:
1. Without the hashtag, `user:42:profile` and `user:42:settings` would hash to two different slots (CRC16 of the full key). `MSET` across slots is rejected by Cluster.
2. With `{user:42}`, Redis hashes only the substring inside the braces — same for both keys → same slot.
3. They now live on the same primary node; multi-key operations (MSET, transactions, Lua KEYS[]) work normally.

---

## Interview storytelling — designing real systems

### "Design a rate limiter for our public API"

- Start with requirements: per-user? per-IP? per-endpoint? what's the limit (e.g., 100 req/min)? sliding or fixed?
- Pick the data structure. Sliding window with ZSET + Lua is the senior default — precise, atomic, distributed.
- Mention the failure modes: if Redis is down, do you fail open (allow all) or closed (deny all)? For abuse prevention, fail open; for paid quota enforcement, fail closed (with circuit breakers so a single Redis blip doesn't take down the API).
- Sharding: rate-limit keys are naturally well-distributed (one per user) — Cluster scales linearly. Only hot accounts need sub-sharding.
- Mention Lua for atomicity, and the cost: a slow script blocks the shard. Keep scripts under 5 ms.

### "Design a leaderboard for 50M users"

- ZSET. `ZINCRBY` for updates, `ZREVRANGE 0 99` for top-100 in O(log N + 100).
- For per-user rank lookups (`ZREVRANK`), still O(log N) — fine.
- Memory: ~64 bytes per ZSET entry × 50M = ~3 GB. Fits on a single Redis node.
- Hot spots: top-100 page is read by every user — cache that page in app memory with a 1-second refresh.
- Resets / seasons: use one ZSET per season (`leaderboard:season42`); old seasons can be moved to cold storage.

### "Design a session store for 10M concurrent sessions"

- Hash per session, 1-hour TTL, sliding refresh on each authenticated call.
- Memory: ~500 bytes × 10M = 5 GB. Single replicated Redis is fine; for multi-region, partition by user ID with Cluster.
- Durability: AOF `everysec` + replica. Acceptable loss = a few seconds of new logins (users just re-auth).
- Security: store *only* a session ID in the cookie; never user data. The session payload lives server-side in Redis.

### "Design a job queue with at-least-once delivery"

- Redis Streams with a consumer group. Producers `XADD jobs * …`; workers `XREADGROUP` then `XACK`.
- If a worker dies mid-job, the entry stays in the PEL (pending entries list). A janitor `XPENDING` + `XCLAIM` moves it to a healthy worker.
- For "exactly-once" semantics you need an *idempotency key per job* — Redis Streams gives you "at-least-once" delivery, the rest is on your job handler.
- Capacity: cap stream length with `MAXLEN ~ N` so memory doesn't grow unboundedly.

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

Mental model for the slot mechanism: think of slots as 16384 small buckets. Every key goes into exactly one bucket via `CRC16(key) % 16384`. Each Cluster node owns some range of buckets. When you add a node, you move *buckets* between nodes — clients learn the new mapping via redirection (`MOVED` / `ASK`) and gossip.

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
