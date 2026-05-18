# Read-Through Cache

## Source / Origin
- Classic pattern from in-process object caches (EhCache, Caffeine, Hibernate's 2nd-level cache) and provider-managed caches (AWS DAX for DynamoDB, Spring Cache abstraction).
- Companion concept doc: `backend-data-prep/caching/01-caching-strategies.md` — "Read-through" section.
- Common interview probe: "What's the difference between cache-aside and read-through?" Most candidates can't articulate it cleanly.

## Why this question matters in interviews
Read-through is the **inversion of cache-aside**: in cache-aside, the application owns the read logic; in read-through, the cache library owns it. Interviewers ask this to test whether you understand who owns invalidation and miss-handling. The senior signal is being able to (a) name the pattern precisely, (b) recognize when your stack already uses it (Hibernate, DataLoader, Spring `@Cacheable`), and (c) explain why it doesn't eliminate the same race conditions as cache-aside — only relocates them.

## Concepts involved

### Syntax to lock in

```
// Application code — pure
value = cache.get(key)
return value
```

The cache library implements the miss path internally:
```
class ReadThroughCache:
    def get(self, key):
        if self.store.has(key):
            return self.store.get(key)
        value = self.loader(key)        # the registered DB-fetch function
        if value is not None:
            self.store.set(key, value, ttl=self.ttl)
        return value
```

The application registers a **loader function** once at boot:
```
cache = ReadThroughCache(loader=lambda k: db.query("SELECT * FROM users WHERE id=$1", k))
```

### Edge cases / interview traps
1. **Loader exception handling** — what if the loader throws? Most libraries propagate the exception; some cache the exception briefly to avoid hammering the DB. Know which behavior you want.
2. **Negative results** — does the loader return `None` for a missing row? Does the cache store the `None` or treat it as "not loaded"? Behavior varies by library. Caffeine has `loadAll` returning a `Map` where missing keys = absent; you must opt in to cache nulls.
3. **Concurrent misses for the same key** — without single-flight, N concurrent gets all call the loader N times. Good libraries (Caffeine, DataLoader) deduplicate; Redis-as-read-through generally doesn't unless you add it.
4. **Write path is still your problem** — read-through only handles reads. Writes still need explicit invalidation. Confusing this with write-through is a common mistake.
5. **TTL semantics** — most read-through libraries support `expireAfterWrite` (TTL from population) and `expireAfterAccess` (TTL from last read). Picking the wrong one causes either stale data or premature eviction of hot keys.
6. **Loader latency = user latency** — the first reader of a key waits for the full DB round-trip. For a cold key with a 200ms DB query, that reader sees 200ms. Refresh-ahead avoids this for known-hot keys.

## Mental Model

```
                  Application
                       │
                       │ get(key)
                       ▼
              ┌────────────────────┐
              │  Cache (with       │
              │  registered loader)│
              └─────┬──────────────┘
                    │ on miss, cache itself calls:
                    ▼
              loader(key)  ──► DB
                    │
                    ▼
            cache.set(key, value, TTL)
                    │
                    ▼
            return value to app
```

Contrast with cache-aside:

```
CACHE-ASIDE                       READ-THROUGH
───────────                       ─────────────
App calls cache.get               App calls cache.get
App handles miss                  Cache handles miss
App calls db.read                 Cache calls loader (registered)
App calls cache.set               Cache sets internally
App returns value                 Cache returns value
                                  
"App owns the orchestration."     "Cache owns the orchestration."
```

The behavior is identical from the app's perspective on a hit; on a miss, only the *code location* of the DB fetch differs. The invalidation problem is the same.

## Why interviewers care
- Tests **layering / abstraction reasoning**: who owns the cache logic, and what are the consequences of moving it?
- Read-through is the model behind **ORM 2nd-level caches, DataLoader, Spring `@Cacheable`, AWS DAX**. Candidates who don't recognize they've used it can't reason about its quirks.
- It's the cleanest setup for **library-level optimizations** (single-flight, bulk loading, refresh-ahead) since the cache controls the miss path.

## Common beginner confusion
- **"Read-through means writes also go through the cache."** No — that's write-through. Read-through only governs the read path.
- **"Read-through is faster than cache-aside."** No, the hit and miss paths cost the same. The difference is code locality, not performance.
- **"Read-through avoids stampedes."** Only if the library implements single-flight. A naive read-through cache hit by N concurrent misses still triggers N loader calls.
- **"DAX is just Redis for DynamoDB."** Closer to a read-through *and* write-through cache; with item-level TTL and write propagation. Don't conflate it with plain Redis.
- **"DataLoader is for caching."** It's primarily for *batching* (collect requests in the current tick, fire one DB query). Caching is a secondary feature with per-request scope by default.

## Brute force approach
"Every read does cache.get; on miss, the app calls db.read; on success, app calls cache.set." That's cache-aside, scattered across every read site in the codebase. The brute-force argument against it: copy-pasting that block 200 times leads to drift — one place forgets the TTL, another forgets the negative caching. Read-through centralizes it.

The brute-force argument *for* it: explicit beats implicit. If reading a user does something subtle (e.g., merges columns from two tables), you don't want a generic loader hiding the join.

## Optimal approach
- **Use read-through when reads are uniform** — single-row lookups by key, same DB query for every miss. The loader is a one-liner.
- **Use cache-aside when reads are heterogeneous** — joins, filtering, dynamic projections. Pushing all that into a loader is awkward.
- **Add single-flight inside the loader** — N concurrent misses for the same key fire one DB call. (Caffeine and DataLoader do this for you.)
- **Combine with refresh-ahead** for hot keys — proactively refresh before TTL expiry so no reader sees the miss latency.
- **Negative caching** — explicitly decide loader return semantics for "not found."
- **Bulk-loading** — for N keys, issue one batched query (DataLoader pattern) instead of N round-trips.

## Solution

### Read-through with single-flight (Node.js)

```javascript
const Redis = require('ioredis');
const redis = new Redis();

class ReadThroughCache {
  constructor({ loader, ttl = 300, namespace = 'rt' }) {
    this.loader = loader;
    this.ttl = ttl;
    this.namespace = namespace;
    this.inflight = new Map();   // key → Promise (single-flight)
  }

  fullKey(key) {
    return `${this.namespace}:${key}`;
  }

  async get(key) {
    const fk = this.fullKey(key);
    const cached = await redis.get(fk);
    if (cached !== null) {
      if (cached === '__NULL__') return null;
      return JSON.parse(cached);
    }
    // single-flight: only one loader call per key in-flight
    if (this.inflight.has(key)) {
      return this.inflight.get(key);
    }
    const promise = this.loadAndStore(key, fk);
    this.inflight.set(key, promise);
    try {
      return await promise;
    } finally {
      this.inflight.delete(key);
    }
  }

  async loadAndStore(key, fk) {
    const value = await this.loader(key);
    const payload = value === null ? '__NULL__' : JSON.stringify(value);
    const ttl = value === null ? 30 : this.ttl;
    // jittered TTL
    const jitterTtl = Math.floor(ttl + Math.random() * ttl * 0.1);
    await redis.set(fk, payload, 'EX', jitterTtl);
    return value;
  }

  async invalidate(key) {
    await redis.del(this.fullKey(key));
  }
}

// Usage
const userCache = new ReadThroughCache({
  namespace: 'user',
  loader: async (id) => {
    const row = await db.query('SELECT * FROM users WHERE id=$1', [id]);
    return row ?? null;
  },
  ttl: 300,
});

const user = await userCache.get(42);
```

### Bulk-loading variant (DataLoader-style, per-request)

```javascript
class BatchedReadThrough {
  constructor({ batchLoader, maxBatch = 100 }) {
    this.batchLoader = batchLoader;
    this.queue = [];
    this.scheduled = false;
  }

  async get(key) {
    return new Promise((resolve, reject) => {
      this.queue.push({ key, resolve, reject });
      if (!this.scheduled) {
        this.scheduled = true;
        process.nextTick(() => this.flush());
      }
    });
  }

  async flush() {
    const batch = this.queue.splice(0);
    this.scheduled = false;
    const keys = batch.map((b) => b.key);
    try {
      const results = await this.batchLoader(keys);  // one DB call
      batch.forEach((b, i) => b.resolve(results[i]));
    } catch (err) {
      batch.forEach((b) => b.reject(err));
    }
  }
}
```

## Step-by-step dry run

Scenario: 5 concurrent calls to `userCache.get(42)` on a cold cache.

| T (ms) | Caller | Action | Cache | inflight Map |
|--------|--------|--------|-------|--------------|
| 0  | C1 | `.get(42)` → miss → no inflight → start loader | empty | `{42: P}` |
| 1  | C2 | `.get(42)` → miss → inflight has 42 → await P | empty | `{42: P}` |
| 2  | C3 | `.get(42)` → miss → inflight has 42 → await P | empty | `{42: P}` |
| 3  | C4 | `.get(42)` → miss → inflight has 42 → await P | empty | `{42: P}` |
| 4  | C5 | `.get(42)` → miss → inflight has 42 → await P | empty | `{42: P}` |
| 50 | — | loader returns `{name:"A"}` | `{user:42:"A"}` | `{}` |
| 50 | C1-5 | all resolve with `{name:"A"}` | `{user:42:"A"}` | `{}` |
| 60 | C6 | `.get(42)` → hit | `{user:42:"A"}` | `{}` |

**One DB call for five concurrent misses.** Without the inflight map: 5 DB calls, every one of them returning the same row, all racing to populate the cache.

## How to think aloud in the interview

"Read-through is cache-aside but with the orchestration pushed inside the cache library. The application just calls `cache.get(key)`; if it's a miss, the library calls a registered loader function, populates the cache, returns the value. From the app's perspective the call is identical to a hit.

What does that buy you? Two things. First, centralization — every cached read goes through one code path, so you can't accidentally forget the TTL or the negative caching in one place. Second, library-level optimizations: single-flight (one loader call per key for N concurrent misses), bulk loading (collect keys in the current tick, batch them), and refresh-ahead (proactively refresh before expiry).

What does it not buy you? Anything on the write path. You still have to invalidate the cache on writes explicitly. And it doesn't solve stampedes unless you add single-flight inside the loader — a naive implementation will still fire N loader calls for N concurrent misses.

In practice, read-through is the pattern behind Spring's `@Cacheable`, Hibernate's second-level cache, AWS DAX for DynamoDB, and Facebook's DataLoader for GraphQL. If your reads are uniform — same query, different ID — read-through wins on cleanliness. If your reads are heterogeneous — joins, projections, dynamic SQL — cache-aside stays explicit and that's a feature."

## Important takeaways

- **Read-through = cache library handles the miss path.** App code is pure `cache.get(key)`.
- **It's structurally equivalent to cache-aside** — only differs in where the loader lives.
- **Single-flight is the killer feature** — but you have to add it (or use a library that does).
- **It only governs reads.** Writes still need explicit invalidation.
- **Bulk-loading variants (DataLoader) reduce N round-trips to 1.**
- **Recognize where you're already using it:** ORM 2nd-level caches, AWS DAX, Spring Cache, DataLoader.

## Variants

1. **Read-through + write-through** — cache library handles both. AWS DAX is the canonical example.
2. **Read-through with refresh-ahead** — proactively refresh before TTL expiry. See `refresh-ahead-cache.md`.
3. **Bulk read-through (DataLoader)** — batch concurrent misses into a single DB call. Per-request scope by default.
4. **Read-through with stale-while-revalidate** — serve stale on miss, refresh in background. Lower p99 at the cost of bounded staleness.
5. **Tiered read-through** — L1 (in-process Caffeine) → L2 (Redis) → DB. Each tier has its own loader pointing at the next tier.
6. **Read-through with negative TTL** — explicitly cache "not found" with shorter TTL than positive results.

## Revision notes

> **read-through — 60 second recap**
> - **App calls `cache.get(key)`; cache library calls loader on miss.**
> - Functionally equivalent to cache-aside; differs in *where* loader code lives.
> - Centralizes the read path — no scattered cache logic.
> - **Single-flight inside the loader** is the key optimization — one DB call per key per concurrent burst.
> - **Bulk-loading variant** (DataLoader) batches concurrent misses.
> - **Only handles reads.** Writes still need explicit invalidation.
> - Examples: Spring `@Cacheable`, Hibernate L2, AWS DAX, DataLoader.
> - **Trap:** confusing with write-through; assuming it solves stampedes automatically.
