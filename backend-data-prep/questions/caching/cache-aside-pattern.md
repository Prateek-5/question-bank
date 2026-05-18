# Cache-Aside (Lazy-Loading) Pattern

## Source / Origin
- Default caching pattern in 90% of production stacks (Facebook's TAO, Instagram, Twitter's early read-path, every Rails/Django/Express app with Redis).
- Companion concept doc: `backend-data-prep/caching/01-caching-strategies.md` — section "Cache-aside".
- Asked in system-design rounds at FAANG-tier and most product cos as the warm-up before the *real* caching question (stampede, hot-key, invalidation).

## Why this question matters in interviews
Cache-aside is the **default** caching pattern. If a candidate cannot describe its read path, write path, failure modes, and the dual-write race in under three minutes, the interviewer will quietly mark them down and move on. It is the entry point to every deeper caching topic — stampede, double-deletion, write-through, refresh-ahead all reference cache-aside as the baseline. As a senior, you're expected to (a) state it precisely, (b) immediately surface its race conditions, and (c) know when *not* to use it.

## Concepts involved

### Syntax to lock in

The canonical read path:
```
function get(key):
    value = cache.get(key)
    if value is not None:
        return value          # cache hit
    value = db.read(key)      # cache miss
    if value is not None:
        cache.set(key, value, ttl=300)
    return value
```

The canonical write path (the controversial one):
```
function update(key, newValue):
    db.write(key, newValue)
    cache.delete(key)         # NOT cache.set(key, newValue)
```

### Why `cache.delete` instead of `cache.set` on write
- `cache.delete` is **idempotent under concurrency**. Two writers racing both delete; final state is "cache empty, DB authoritative."
- `cache.set` on write opens a *double-write race* — see the "double-deletion-problem.md" file in this directory for the timeline.
- Delete also keeps the cache consistent with whatever side-effects/triggers the DB write produced (computed columns, audit rows, etc.).

### Edge cases / interview traps
1. **The "delete-before-write" inversion** — junior candidates often delete *before* writing the DB. Race: T1 deletes, T2 reads (miss), T2 reads stale DB row, T2 repopulates cache with stale value, T1 finally writes DB. Cache is now permanently stale.
2. **Cache miss + slow DB** — every miss adds one DB round-trip. If your DB is the bottleneck, a cold cache after deploy can take the DB down. See `cache-warm-up-strategies.md`.
3. **Negative caching** — `db.read(key) == None` (the row doesn't exist). If you don't cache the negative result, a malicious client can hammer non-existent keys and bypass the cache entirely. Cache `None` with a *short* TTL (30s) or use a Bloom filter.
4. **TTL without jitter** — synchronized expiry across many app instances → stampede. See `ttl-jitter-design.md`.
5. **Read-your-writes inconsistency** — User saves their profile, then refreshes the page. Their app instance reads from cache (the deleted cache repopulates on a stale replica read) — they see the old value. Fix: pin user's reads to primary for N seconds post-write.
6. **Cache and DB drift on delete failure** — if `db.write` succeeds but `cache.delete` fails (network blip), cache is stale until TTL. Always have a TTL as the safety net.

## Mental Model

```
                    ┌──────────────┐
       READ ──────► │   CACHE      │
                    │  (Redis)     │
                    └─────┬────────┘
                          │ miss
                          ▼
                    ┌──────────────┐
                    │   DATABASE   │
                    └──────────────┘
                          │
                          ▼
                    populate cache, return value


       WRITE ──────► DB.write(newValue)
                          │
                          ▼
                    cache.delete(key)
                    (next read repopulates)
```

The defining property: **the application owns the cache logic**. The cache itself is dumb — just a fast key-value store. This makes cache-aside flexible (you choose what/when/how to cache) but also unsafe by default (you must get the write-path race right).

## Why interviewers care
- It is the **most common** pattern in production. A candidate who can't sketch it is not a senior backend engineer.
- The write-path question (`delete` vs `set`, order vs DB write) reveals whether you've shipped this in anger.
- It is the springboard to *every* other caching pattern in this drill bank.

## Common beginner confusion
- **"I'll write to cache and DB in parallel."** Race condition guaranteed. Sequence them and delete the cache, don't set it.
- **"TTL guarantees freshness."** TTL bounds staleness; it doesn't eliminate it. A 5-minute TTL means readers see up-to-5-min-old data.
- **"If cache is down, just bypass it."** OK in theory, but a 100% DB load when cache fails will take your DB down. You need a circuit breaker and graceful degradation budget.
- **"Cache the entire response object."** Sometimes right, sometimes wrong. If the object is 10MB and you read 5 fields, you're burning network + JSON.parse. Cache at the access-pattern granularity.

## Brute force approach
"On every read, hit the DB; on every write, hit the DB." This is no cache at all — the baseline. It's correct but doesn't scale.

A naive cache: "On read, check cache, fall back to DB. On write, write DB and *set* the new value into cache." This breaks under concurrency (see double-deletion problem). It also doesn't handle the case where the write succeeds but cache write fails — now cache has the old value while DB has the new one.

## Optimal approach
- **Read path**: cache.get → on miss → db.read → cache.set with TTL + jitter → return.
- **Write path**: db.write → cache.delete. Never `cache.set` on write.
- **Negative caching**: store sentinel for "row doesn't exist" with short TTL.
- **Single-flight**: on miss, only one request goes to DB; concurrent missers wait (see `cache-stampede-single-flight.md`).
- **TTL with jitter**: `ttl = base + random(0, base * 0.1)` to avoid synchronized expiry.
- **Versioned keys** for global invalidation: `user:42:v7` — bumping the version effectively invalidates all consumers without a delete loop.

## Solution

```javascript
// Node.js, ioredis
const Redis = require('ioredis');
const redis = new Redis();

const TTL_SECONDS = 300;
const JITTER_PCT = 0.1;

function jitteredTtl(base) {
  return Math.floor(base + Math.random() * base * JITTER_PCT);
}

async function getUser(userId) {
  const key = `user:${userId}`;
  const cached = await redis.get(key);
  if (cached !== null) {
    if (cached === '__NULL__') return null;          // negative cache hit
    return JSON.parse(cached);
  }

  // miss — go to DB
  const row = await db.query('SELECT * FROM users WHERE id = $1', [userId]);
  const value = row ?? null;

  // populate cache (negative or positive)
  const payload = value === null ? '__NULL__' : JSON.stringify(value);
  const ttl = value === null ? 30 : jitteredTtl(TTL_SECONDS);
  await redis.set(key, payload, 'EX', ttl);

  return value;
}

async function updateUser(userId, patch) {
  // 1. write DB first (source of truth)
  await db.query(
    'UPDATE users SET name = $1, email = $2 WHERE id = $3',
    [patch.name, patch.email, userId]
  );
  // 2. invalidate cache
  await redis.del(`user:${userId}`);
}
```

## Step-by-step dry run

Scenario: `getUser(42)` called twice with an update in between.

| T  | Actor | Action | Cache state | DB state |
|----|-------|--------|-------------|----------|
| 0  | App A | `getUser(42)` — cache.get → null | `{}` | `{42: {name:"Old"}}` |
| 1  | App A | db.read → `{name:"Old"}` | `{}` | `{42: {name:"Old"}}` |
| 2  | App A | cache.set `user:42` TTL=312s | `{user:42: "Old"}` | `{42: {name:"Old"}}` |
| 3  | App A | returns `{name:"Old"}` | — | — |
| 4  | App B | `updateUser(42, {name:"New"})` — db.write | `{user:42: "Old"}` | `{42: {name:"New"}}` |
| 5  | App B | cache.del `user:42` | `{}` | `{42: {name:"New"}}` |
| 6  | App C | `getUser(42)` — cache.get → null | `{}` | `{42: {name:"New"}}` |
| 7  | App C | db.read → `{name:"New"}` | `{}` | `{42: {name:"New"}}` |
| 8  | App C | cache.set | `{user:42: "New"}` | `{42: {name:"New"}}` |

No stale read. Now contrast with the broken version (cache.set on write, see `double-deletion-problem.md`).

## How to think aloud in the interview

"OK, so the read path is straightforward — check cache, on miss go to DB, populate cache with a TTL, return. The interesting part is the write path. My first instinct, and probably most candidates', is to `cache.set(key, newValue)` on update. That's wrong, and here's why: imagine two writers updating the same key concurrently. Writer A writes DB then sets cache; Writer B writes DB then sets cache — but the network reorders the cache.set calls so B's DB write lands first but A's cache.set lands second. Now cache has A's value but DB has B's. The cache is permanently inconsistent until TTL.

So instead I delete the cache on write. Delete is idempotent — two concurrent deletes leave the cache empty either way, and the next read repopulates from DB which has the latest. The TTL is my safety net: even if a delete fails due to a network blip, staleness is bounded.

Two more things I'd flag. First, negative caching: if I don't cache `None`, an attacker can hammer non-existent keys and every request is a DB hit. I'll cache nulls with a short TTL, say 30 seconds. Second, TTL jitter: if I deploy 100 instances and they all populate the same hot key with TTL=300, they all expire at roughly the same second and stampede the DB. I add 10% random jitter to the TTL.

If you push me on read-your-writes — user updates their profile, refreshes, sees old data — I'd pin reads to the primary DB for N seconds after a write for that user, or use a versioned key like `user:42:v7` and bump the version on write."

## Important takeaways

- **Read path: cache → miss → DB → set cache → return.** Memorize.
- **Write path: DB write → cache delete.** Never set on write.
- **Always TTL.** Even when you also invalidate explicitly — TTL is the safety net for missed invalidations.
- **Always jitter the TTL.** 5–10% random skew breaks synchronized expiry.
- **Cache nulls.** Otherwise you're vulnerable to "cache penetration" attacks.
- **Application owns the cache logic** — that's the defining trait. Contrast with read-through (cache owns it).

## Variants

1. **Cache-aside with single-flight** — on miss, only one request goes to DB; others wait. See `cache-stampede-single-flight.md`.
2. **Cache-aside + refresh-ahead** — proactively refresh before TTL expiry for hot keys. See `refresh-ahead-cache.md`.
3. **Cache-aside with versioned keys** — `user:42:v7`; bump the version (a separate small key) to invalidate all readers without scanning.
4. **Stale-while-revalidate** — serve the stale value to the requester, refresh in background. Lower p99 at the cost of bounded staleness.
5. **Read-through** — same read path but the cache library does the DB fetch on miss. Application code becomes pure `cache.get(key)`.
6. **Cache-aside with CDC invalidation** — instead of `cache.del` in app code, a Debezium/CDC pipeline watches the DB and emits invalidations. Decouples invalidation from app logic.

## Revision notes

> **cache-aside — 60 second recap**
> - **Read:** cache.get → miss → db.read → cache.set(TTL+jitter) → return.
> - **Write:** db.write → cache.del. NEVER cache.set on write.
> - **Why delete not set:** dual-write race; delete is idempotent under concurrency.
> - **TTL is your safety net** for missed invalidations.
> - **Cache nulls** to prevent penetration attacks.
> - **Jitter the TTL** to prevent synchronized expiry storms.
> - Application owns the cache logic — that's the whole point.
> - **Trap:** delete-before-write; set-on-write; no TTL; no jitter; no negative caching.
