# Rate Limiter — Fixed Window

## Source / Origin
- The simplest rate-limiter algorithm; described in every rate-limiting tutorial since memcached/Redis became commonplace.
- Used by basic API gateways and as the default in many web frameworks (Express `express-rate-limit` with `windowMs`).
- Companion concept doc: `backend-data-prep/caching/02-redis-patterns.md` — rate limiter section.
- Interview prompt: "Design a rate limiter that allows 100 requests per minute per user."

## Why this question matters in interviews
Fixed window is the textbook starting point — every rate limiter question begins here. The senior signal is that within a minute of describing it, you proactively call out its **boundary burst flaw** (200 requests in 2 seconds across a window boundary) and propose sliding window as the fix. Junior candidates stop at "INCR + EXPIRE" and miss the bug.

## Concepts involved

### Syntax to lock in

The minimal Redis-backed fixed window:
```
key = "ratelimit:user:42:" + currentMinute()    # bucket per window
n = INCR key
if n == 1:
    EXPIRE key 60
if n > limit:
    reject
else:
    allow
```

Atomic INCR + EXPIRE in one Lua script:
```lua
-- KEYS[1] = window key, ARGV[1] = limit, ARGV[2] = window_seconds
local current = redis.call('INCR', KEYS[1])
if current == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[2])
end
if current > tonumber(ARGV[1]) then
  return 0  -- rejected
else
  return 1  -- allowed
end
```

### Edge cases / interview traps
1. **Boundary burst flaw** — if limit=100/min and a user makes 100 requests at T=59 and 100 more at T=60, they got 200 requests in 1-2 seconds. The limit is violated *in practice* but satisfied per-window.
2. **EXPIRE without INCR race** — if you INCR then EXPIRE in two separate commands and the process crashes between them, the key has no TTL → leaks forever. Lua makes it atomic.
3. **Bucket key generation** — naive `floor(now() / windowSize)` works but is timezone-sensitive at certain windows. Use UTC timestamps.
4. **Distributed clock skew** — if multiple app instances compute `currentMinute()` from their own clocks, they may write to different bucket keys at the same wall-clock moment. Use Redis `TIME` command or the cluster's wall clock.
5. **Burst at window start** — if you allow 100 per minute, all 100 hitting in the first 100ms is technically allowed. Not always desirable; token bucket smooths this.
6. **Rejection should be cheap** — returning a 429 should not consume the same compute as serving the request. Reject early in middleware.
7. **Counting failed requests** — should failed authentication attempts count toward the limit? Depends on threat model; typically yes for abuse prevention.

## Mental Model

### How fixed window works

```
Window 1 [T=0..60)       Window 2 [T=60..120)       Window 3 [T=120..180)
key="rl:42:0"            key="rl:42:1"               key="rl:42:2"
count=0                   count=0                      count=0

Requests at T=10, T=20 ──► count=1, 2 → allowed
Requests at T=59 (100x) ──► count=3..102 → first 100 allowed, last 2 rejected
                            [reset at T=60]
Requests at T=60 (100x) ──► new window, count=1..100 → allowed
                                      ↑
                                      200 requests in 1-2 seconds!
                                      "boundary burst"
```

### Boundary burst flaw — the diagram

```
Limit: 100 req/min

       Window 1                  │   Window 2
       [T=0..60)                 │   [T=60..120)
       ────────────────────────────────────────────────
                                  │
                                 100 requests
                                 in last second
                                  ┃
                                  ┣── T=59.x
                                  ┃   (counted in W1)
                                  ▼
       boundary  ▲ T=60
                  ┃
                  ┃ 100 requests
                  ┃ in first second
                  ┃
                 (counted in W2)

       Net: 200 requests in <2 seconds. Theoretical limit: 100/min.
```

## Why interviewers care
- Establishes the **rate-limiter algorithm baseline** — every other algorithm is "fixes the boundary burst" or "smooths the rate."
- Tests **atomicity reasoning** — INCR + EXPIRE in one Lua block; common Redis gotcha.
- Surfaces **time-windowing reasoning** — what is a "window" exactly?
- Junior candidates leave it there; seniors immediately call out the flaw.

## Common beginner confusion
- **"Fixed window enforces the rate."** Only on average over windows. Not within a window.
- **"I'll just use shorter windows."** Shrinks the burst window but doesn't eliminate it. Also more keys, more memory.
- **"EXPIRE handles cleanup."** Only if you set it after INCR. Without the `if current == 1` guard, you reset the TTL on every request — keys never expire.
- **"INCR then EXPIRE is atomic."** Two separate commands; a crash between them leaks the key. Use Lua or check `if current == 1`.
- **"Fixed window is fine for most APIs."** Only if you don't care about burst behavior at window boundaries. Many real systems do.

## Brute force approach
**Counter per user in memory.** Works for one app instance; breaks instantly with multiple instances (each enforces its own limit; net rate is N × intended limit).

**SQL `SELECT COUNT(*) FROM requests WHERE user_id=$1 AND ts > now() - interval '1 minute'`** then INSERT. Correct, slow, doesn't scale past low QPS.

**"Just use AWS WAF / Cloudflare rate limiting."** Valid in production; useless answer in an interview testing your understanding.

## Optimal approach
- Use Redis as the shared counter store.
- Bucket key per (user, window): `ratelimit:{user}:{window_id}`.
- Use Lua for atomic INCR + EXPIRE-on-first-increment.
- Reject as early in middleware as possible.
- Return `Retry-After` and rate-limit headers on rejection.

When fixed window is acceptable:
- Internal APIs where boundary bursts are tolerable.
- Coarse-grained limits where the burst is small relative to the limit.
- Prototypes / starting point.

When to switch algorithms:
- User-visible API with strict SLA → sliding window log or sliding window counter.
- Need to smooth out traffic (not just reject) → token bucket.
- Need to enforce throughput rather than rate → leaky bucket.

## Solution

### Node.js + ioredis with Lua atomicity

```javascript
const Redis = require('ioredis');
const redis = new Redis();

const LUA = `
  local current = redis.call('INCR', KEYS[1])
  if current == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[2])
  end
  if current > tonumber(ARGV[1]) then
    return 0
  else
    return current
  end
`;

const LIMIT = 100;
const WINDOW_SEC = 60;

async function checkRateLimit(userId) {
  const window = Math.floor(Date.now() / 1000 / WINDOW_SEC);
  const key = `ratelimit:user:${userId}:${window}`;
  const result = await redis.eval(LUA, 1, key, LIMIT, WINDOW_SEC);
  return result !== 0;  // 0 = rejected
}

// Express middleware
function rateLimitMiddleware(req, res, next) {
  const userId = req.user?.id ?? req.ip;
  checkRateLimit(userId).then((allowed) => {
    if (!allowed) {
      res.set('Retry-After', String(WINDOW_SEC));
      res.set('X-RateLimit-Limit', String(LIMIT));
      res.set('X-RateLimit-Remaining', '0');
      return res.status(429).json({ error: 'Too Many Requests' });
    }
    next();
  });
}
```

### Variant: per-IP + per-user composite

```javascript
async function checkComposite(ip, userId) {
  const [allowedIP, allowedUser] = await Promise.all([
    checkRateLimit(`ip:${ip}`, 1000, 60),        // 1000/min per IP
    checkRateLimit(`user:${userId}`, 100, 60),   // 100/min per user
  ]);
  return allowedIP && allowedUser;
}
```

## Step-by-step dry run

**Scenario:** limit=100/min, user 42.

| T (s) | Action               | Bucket key            | INCR result | Allowed? |
|-------|----------------------|-----------------------|-------------|----------|
| 0.5   | req 1 (window 0)     | rl:user:42:0          | 1 → set TTL=60 | yes  |
| 30    | req 50               | rl:user:42:0          | 50          | yes      |
| 59.5  | req 100              | rl:user:42:0          | 100         | yes      |
| 59.7  | req 101              | rl:user:42:0          | 101         | **no**   |
| 60.1  | req 102 (window 1)   | rl:user:42:1          | 1 → set TTL=60 | yes  |
| 60.3  | req 103              | rl:user:42:1          | 2           | yes      |
| ...   | bursts to 100 in 1s   | rl:user:42:1          | up to 100   | all yes  |

**Net during [T=59, T=61]:** ~100 requests in W0 + ~100 requests in W1 = ~200 requests in 2 seconds. **Boundary burst.**

The user is *theoretically* limited to 100/min but *practically* sent 200 in 2 seconds — a 2× violation across the window boundary.

## How to think aloud in the interview

"Fixed window is the simplest rate limiter and the one I'd reach for first to discuss the problem before improving it. The implementation is one Redis key per user per window: I compute a window ID by dividing the current time by the window size, append it to a key like `ratelimit:user:42:window-2024-01-15T14:32`, and INCR. If the result is 1, I set EXPIRE — that's the first hit in this window. If the result exceeds the limit, I reject. INCR and EXPIRE need to be in a Lua script for atomicity; otherwise a crash between them leaves a leaked key.

The flaw I want to flag immediately is the boundary burst. If my limit is 100 per minute and a user sends 100 requests at second 59 and another 100 at second 60, they got 200 requests in two seconds, even though both windows individually respected the limit. Whether that matters depends on the use case — for protecting against bots it might be fine; for protecting an expensive downstream API, it's a 2× violation that defeats the purpose.

The next algorithm up is sliding window log — store every request's timestamp in a Redis ZSET, count entries in the last 60 seconds on every check. Precise but expensive (one ZSET entry per request). After that, sliding window counter — a hybrid that weights the previous window by elapsed fraction. Cloudflare uses this. Almost as cheap as fixed window, almost as accurate as sliding log.

For traffic *shaping* — smoothing rather than rejecting — I'd use token bucket. For enforcing throughput — outbound rate to a downstream — leaky bucket.

So fixed window is the right starting point but I'd never ship it as the primary mechanism for user-facing rate limits."

## Important takeaways

- **One Redis key per (user, window).**
- **INCR + EXPIRE in Lua for atomicity** (or guard with `if INCR result == 1`).
- **Boundary burst flaw:** 2× limit across window boundaries.
- **Use only for coarse-grained, burst-tolerant limits.**
- **Always emit `Retry-After` and `X-RateLimit-*` headers** on rejection.
- **Composite limits:** check per-IP + per-user simultaneously.
- **Reject in middleware before doing real work.**

## Variants

1. **Fixed window per (user, endpoint)** — finer-grained; `ratelimit:42:GET-/api/x:window`.
2. **Composite limits (IP + user + endpoint)** — multi-key Lua check.
3. **Tiered limits** — anonymous users get 10/min, free users 100/min, paid users 1000/min.
4. **Soft-reject vs hard-reject** — over limit but under threshold serves a slow response; far over rejects.
5. **Per-resource bucket** — `ratelimit:resource:product-42` for protecting a single hot resource.
6. **Quota with daily/monthly windows** — same algorithm at different time scales.

## Revision notes

> **rate limiter, fixed window — 60 second recap**
> - **Key:** `ratelimit:{user}:{window_id}`; INCR + first-increment EXPIRE.
> - **Lua for atomicity.**
> - **Flaw:** boundary burst — 2× limit possible across window edges.
> - **Use for:** coarse limits, internal APIs, prototypes.
> - **Avoid for:** strict user-facing SLA, expensive downstream protection.
> - **Emit Retry-After and X-RateLimit-* headers.**
> - **Next algorithm up:** sliding window log (precise, expensive) or sliding window counter (Cloudflare-style hybrid).
> - **Trap:** non-atomic INCR + EXPIRE; missing the boundary burst.
