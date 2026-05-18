# Rate Limiter — Sliding Window Log

## Source / Origin
- Classic precise rate-limiter algorithm; described in Stripe's engineering blog and used widely for API quotas.
- Implementation typically uses a Redis sorted set (ZSET) of request timestamps.
- Companion concept doc: `backend-data-prep/caching/02-redis-patterns.md` — sliding window.
- Interview prompt: "Fix the boundary-burst flaw in fixed window. How precise can you get?"

## Why this question matters in interviews
Sliding window log is the precise-but-expensive answer to "exactly 100 req/min, no more, no less, regardless of when in the window." Interviewers ask it as the natural follow-up to fixed window. The senior signal is being able to (a) describe the ZSET-of-timestamps approach in one breath, (b) compute the memory cost honestly ("one entry per request times window size"), and (c) propose sliding window counter as the cheaper-but-good-enough alternative.

## Concepts involved

### Syntax to lock in

The algorithm:
```
key = "ratelimit:user:42"
now = currentMillis()
windowStart = now - windowMs

# Atomic in Lua:
ZREMRANGEBYSCORE key 0 (windowStart - 1)    # purge expired
count = ZCARD key
if count >= limit:
    reject
ZADD key now now                              # member = score = timestamp
EXPIRE key (windowSec + 1)                    # safety: cleanup if user goes idle
allow
```

The Lua script makes it atomic:
```lua
-- KEYS[1] = ratelimit key
-- ARGV[1] = now (ms), ARGV[2] = window (ms), ARGV[3] = limit
local now = tonumber(ARGV[1])
local windowStart = now - tonumber(ARGV[2])
redis.call('ZREMRANGEBYSCORE', KEYS[1], 0, windowStart - 1)
local count = tonumber(redis.call('ZCARD', KEYS[1]))
if count >= tonumber(ARGV[3]) then
  return 0
end
redis.call('ZADD', KEYS[1], now, now)
redis.call('EXPIRE', KEYS[1], math.ceil(tonumber(ARGV[2]) / 1000) + 1)
return tonumber(ARGV[3]) - count - 1
```

### Edge cases / interview traps
1. **Member uniqueness** — if `member = score = timestamp` and two requests arrive in the same millisecond, the second ZADD updates the score of the existing member (no new entry). Solutions: include a unique suffix (`now + ":" + uuid`) as the member, or use ms+counter.
2. **Memory cost** — one ZSET entry per request × window duration. For 1M users at 100 req/min sustained, that's 100M entries. Roughly 100 bytes/entry in Redis ≈ 10 GB. Often deal-breaker for high-cardinality.
3. **Atomicity** — separate ZREM, ZCARD, ZADD commands have a TOCTOU race. Lua is mandatory.
4. **Score precision** — milliseconds usually sufficient; for very high QPS use microseconds.
5. **Cleanup if user goes inactive** — ZSET keeps growing if you don't EXPIRE. Always set EXPIRE on every operation.
6. **Window boundary** — `> windowStart` vs `>= windowStart`? Off-by-one debates here can change behavior by one request. Document the convention.
7. **Clock skew across app instances** — different servers feeding different `now()` values. Use Redis `TIME` command for a single source.

## Mental Model

### Algorithm visualized

```
ZSET: ratelimit:user:42

Time:    0      5     10     20    45    55    60     65
Entries: ●      ●      ●      ●     ●     ●     ●      ?
                                              ▲
                                              │
                                       window: [now - 60, now]
                                       count visible entries in window

At T=65, window = [5, 65]:
  - entries at 0 → purged (< 5)
  - entries at 5, 10, 20, 45, 55, 60 → count=6
  - if limit=10 → request at T=65 allowed → add to ZSET
  - count now 7
```

### vs Fixed Window — boundary handling

```
FIXED:                       SLIDING LOG:
                                                       
W=[0..60)  W=[60..120)        Window slides with each request.
   ──────  ───────            ──────────────────────────────────
                              At any T, window = [T-60, T]
   100 req  100 req           Request at T=59 + Request at T=61:
   in last  in first          window for the latter = [1, 61]
   second   second              includes nearly all of W1's tail
                                → properly rejected.

   ↑ 200 in 2s                  ↑ exactly 100 in any 60s window.
```

### ZSET memory layout (conceptual)

```
ratelimit:user:42
  score → member
  ────────────────────
  1700000000123 → 1700000000123
  1700000000456 → 1700000000456
  1700000000789 → 1700000000789
  ...
  1700000060000 → 1700000060000

ZCARD returns count.
ZREMRANGEBYSCORE 0 (now - 60s) purges old entries.
```

## Why interviewers care
- It is the **precise correctness baseline** — every other algorithm trades accuracy for cost.
- Tests **Redis data-structure intuition** — ZSET as a time index is a senior-level move.
- The memory-cost discussion separates candidates who've shipped this from those who've only read about it.
- Stripe famously uses this for billing-API limits; real-world relevance.

## Common beginner confusion
- **"It's just like fixed window."** No — fixed window resets at boundaries; sliding window log is *continuous*.
- **"Use Redis LIST."** LIST doesn't support efficient "remove items older than X" — that's O(N). ZSET ZREMRANGEBYSCORE is O(log N + M).
- **"Member can equal score."** Only if all timestamps are unique. ms collisions happen at high QPS.
- **"EXPIRE isn't needed."** It is — without it, idle users' ZSETs leak forever.
- **"It's too expensive, skip it."** Not always — for low-cardinality (a few hundred limited entities), sliding log is perfectly fine.

## Brute force approach
**SQL window query.** `SELECT COUNT(*) FROM requests WHERE user_id=$1 AND ts > now() - interval '60s'`. Correct, very slow, doesn't scale.

**Redis LIST + LREM.** O(N) cleanup; doesn't scale per request.

**App-memory deque per user.** Fine for one instance; broken across multiple.

## Optimal approach
- Redis ZSET keyed by user.
- Score = member = millisecond timestamp (or with uuid suffix for uniqueness).
- Lua script for atomic purge + count + add.
- EXPIRE on every operation as a safety net.
- Use only when memory budget allows; otherwise fall back to sliding window counter.

When to use:
- **Strict accuracy required** (billing, paid quotas).
- **Low cardinality** (per-tenant, per-API-key, not per-IP for the world).
- **Low/medium request rate per key** (otherwise memory explodes).

When *not* to use:
- High-cardinality, high-rate (use sliding window counter).
- "Approximately fair" is good enough (use fixed window or token bucket).

## Solution

### Node.js + ioredis with Lua

```javascript
const Redis = require('ioredis');
const redis = new Redis();

const LUA = `
  local now = tonumber(ARGV[1])
  local windowMs = tonumber(ARGV[2])
  local limit = tonumber(ARGV[3])
  redis.call('ZREMRANGEBYSCORE', KEYS[1], 0, now - windowMs - 1)
  local count = tonumber(redis.call('ZCARD', KEYS[1]))
  if count >= limit then
    return {0, 0}
  end
  -- unique member to avoid ms collisions
  local member = now .. ':' .. (redis.call('INCR', KEYS[2]) % 1000000)
  redis.call('ZADD', KEYS[1], now, member)
  redis.call('PEXPIRE', KEYS[1], windowMs + 1000)
  return {1, limit - count - 1}
`;

const LIMIT = 100;
const WINDOW_MS = 60_000;

async function checkRateLimit(userId) {
  const now = Date.now();
  const [allowed, remaining] = await redis.eval(
    LUA, 2,
    `ratelimit:user:${userId}`, `ratelimit:counter:${userId}`,
    now, WINDOW_MS, LIMIT,
  );
  return { allowed: allowed === 1, remaining };
}
```

### Express middleware

```javascript
async function slidingWindowLimit(req, res, next) {
  const userId = req.user?.id ?? req.ip;
  const { allowed, remaining } = await checkRateLimit(userId);
  res.set('X-RateLimit-Limit', String(LIMIT));
  res.set('X-RateLimit-Remaining', String(remaining));
  if (!allowed) {
    res.set('Retry-After', '60');
    return res.status(429).json({ error: 'Too Many Requests' });
  }
  next();
}
```

## Step-by-step dry run

**Scenario:** limit=5, window=10s.

| T (s) | Action  | ZSET before                  | After purge (≤ T-10) | Count | Decision | ZSET after        |
|-------|---------|-------------------------------|----------------------|-------|----------|--------------------|
| 0     | req 1   | {}                             | {}                    | 0     | allow    | {0}                 |
| 1     | req 2   | {0}                            | {0}                   | 1     | allow    | {0, 1}              |
| 3     | req 3   | {0, 1}                         | {0, 1}                | 2     | allow    | {0, 1, 3}           |
| 5     | req 4   | {0, 1, 3}                      | {0, 1, 3}             | 3     | allow    | {0, 1, 3, 5}        |
| 8     | req 5   | {0, 1, 3, 5}                   | {0, 1, 3, 5}          | 4     | allow    | {0, 1, 3, 5, 8}     |
| 9     | req 6   | {0, 1, 3, 5, 8}                | {0, 1, 3, 5, 8}       | 5     | **reject** | unchanged         |
| 10.5  | req 7   | {0, 1, 3, 5, 8}                | {1, 3, 5, 8}          | 4     | allow    | {1, 3, 5, 8, 10.5}  |
| 11.5  | req 8   | {1, 3, 5, 8, 10.5}             | {3, 5, 8, 10.5}       | 4     | allow    | {3, 5, 8, 10.5, 11.5} |

**Boundary burst test:** if 5 requests at T=9 (all in [0..10)) and 5 more at T=10 (window now [0..10] but T=10 is at edge):
- At T=10 the request's window is [0..10]; entry at T=0 boundary is purged if `< now - windowMs`, otherwise kept.
- If 5 are at T=9.x and the user tries 5 more at T=10.x: window for T=10.1 is [0.1, 10.1], so the T=0 entry is purged, but T=9.x are still in window → count=5 → reject.

**No boundary burst** — the limit is enforced continuously.

## How to think aloud in the interview

"Sliding window log is the algorithm I'd reach for when I need strict accuracy — billing, paid quotas, anywhere the limit really means 'no more than 100 in any rolling 60-second period.'

The implementation is a Redis sorted set keyed by user, where each request adds an entry with score and member equal to the request's millisecond timestamp. On every request, I run a Lua script that does three things atomically: purge entries older than `now - windowMs`, count remaining entries, and either reject or add the new entry. The atomicity is critical — without Lua, ZCARD and ZADD race with each other.

The trade-off is memory. Each request occupies a ZSET entry — roughly 100 bytes in Redis. At 100 req/min sustained per user × 1M users, that's 10GB of Redis. Often too much. So I reserve sliding window log for limited cardinality — per-tenant quotas, per-API-key billing — and switch to sliding window counter for the high-cardinality cases like per-user-per-endpoint.

A couple of subtleties. Members must be unique. If two requests arrive in the same millisecond and I use the timestamp as both score and member, the second ZADD just updates the existing entry, not adding a new one — silent under-counting. I add a small uniqueness suffix to the member. And I always EXPIRE the ZSET on every operation so idle users' keys age out.

What I love about this algorithm is it's literally counting requests in a rolling window — no boundary burst, no approximation. The math is exact. The cost is per-request storage."

## Important takeaways

- **ZSET of (timestamp, timestamp+suffix) per user.**
- **Lua-atomic purge + count + add.**
- **Memory cost = requests × window size × users.** Often the dealbreaker.
- **No boundary burst:** continuous rolling window.
- **EXPIRE on every op** to clean up idle users.
- **Use for low-cardinality strict limits** (billing, API keys).
- **Switch to sliding window counter for high-cardinality.**

## Variants

1. **Sliding window log with sampling** — keep only every Nth request to reduce memory at the cost of accuracy.
2. **Distributed sliding log** — shard by user across Redis Cluster; user's ZSET lives on one slot.
3. **Sliding log with per-endpoint scoping** — ZSET per (user, endpoint).
4. **Soft-limit / hard-limit mode** — at 80% emit warning header; at 100% reject.
5. **Sliding log over multiple windows** — count entries in last 1m, 5m, 1h with separate operations.
6. **Sliding log + concurrency limit** — count *in-flight* requests instead of completed ones (different semantics, similar mechanics).

## Revision notes

> **sliding window log — 60 second recap**
> - **Data structure:** Redis ZSET per key; member = score = unique timestamp.
> - **Atomic op:** Lua: ZREMRANGEBYSCORE → ZCARD → (if under limit) ZADD + EXPIRE.
> - **Pro:** exact; no boundary burst.
> - **Con:** memory = O(requests × users); expensive for high cardinality.
> - **Use:** billing, paid quotas, low-cardinality strict limits.
> - **Switch to sliding window counter** for high-cardinality.
> - **Trap:** non-unique members under ms collisions; non-atomic op sequence; no EXPIRE.
