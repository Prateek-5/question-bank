# Rate limiter — sliding window counter (Cloudflare-style hybrid)

## Source / Origin
- Cloudflare's blog post "How we built rate limiting capable of scaling to millions of domains" (2017) introduced this hybrid widely.
- `backend-data-prep/caching/03-rate-limiting.md` — concept doc.
- LeetCode #362 "Design Hit Counter" (related), #1396 "Design Underground System" (related ID).
- Classic prompt: *"Implement 'max 100 requests per minute per user'. Don't use fixed windows (they're bursty at boundaries) and don't use exact sliding logs (they're memory-heavy). Sketch the Cloudflare hybrid."*

## Why this question matters in interviews
Rate limiting is the **mandatory system-design subroutine** — appears in API gateway design, abuse prevention, auth flow design. The sliding-window counter is the **Goldilocks algorithm**: fixed window is too inaccurate, sliding log is too expensive, this hybrid is what production systems actually use. The interviewer wants:

1. You **can list four classic rate-limit algorithms** (fixed window, sliding log, sliding counter, token bucket, leaky bucket) and pick between them.
2. You **understand the burst problem** at fixed-window boundaries.
3. You **can write the weighted-counter formula** for sliding window.
4. You **know how to implement it atomically** in Redis (pipeline or Lua).

This is the question that gets followed up with token bucket and leaky bucket — see those companion files.

## Concepts involved

### Syntax to lock in

```
For each user, track:
  current_window_count    (count in the active window)
  previous_window_count   (count in the immediately previous window)
  current_window_start    (epoch second / minute, aligned)

On each request at time t:
  elapsed_in_current = t - current_window_start
  weight             = (window_size - elapsed_in_current) / window_size

  estimated = previous_window_count * weight + current_window_count
                       ^^^^^^^^^^^^^^^^^^^^^^   ^^^^^^^^^^^^^^^^^^^^^^
                       linearly decaying        live counter

  if estimated >= limit:  reject
  else:                   accept, increment current_window_count
```

### Edge cases / interview traps

1. **Clock skew across nodes.** If app servers and Redis disagree by even 1 second, boundaries drift. Always use *server-side* time (Redis `TIME` command in Lua) or accept the drift bound.
2. **First-window cold start.** When `previous_window_count` doesn't exist (first ever request), treat as 0. Some implementations initialize to the limit (conservative); your call.
3. **The weight formula is "fraction of previous window still in the lookback".** At t = boundary+0, weight = 1.0 (all of previous still counts). At t = boundary+window/2, weight = 0.5. At t = boundary+window, weight = 0.0 (previous fully aged out, becomes the new "previous").
4. **Window rotation.** When `t` crosses into the next window, "shift": `previous_window_count := current_window_count; current_window_count := 0; current_window_start := new_aligned_start`.
5. **Burstiness vs accuracy tradeoff.** Fixed window allows 2× burst at boundaries (full quota at 0:59 + full quota at 1:00 = 2× in 1 second). Sliding window counter smooths this to within ~5-10% error of true sliding.
6. **Atomicity** — increment + read must be atomic across processes. Lua script or `EVAL` is the canonical Redis pattern.
7. **TTL on keys** — set to 2× window so they expire after they can no longer be "previous".
8. **Per-user vs per-IP vs per-key** — the design generalises; the choice is product-specific. IP rate limits hit NATted users; per-user requires auth.

## Mental Model

### The burst problem with fixed windows

```
Limit:    100 req/min

Fixed window timeline:
  ─────|─────────────|─────────────|─────
  0:00  0:59 → 1:00  1:59 → 2:00
       ↑           ↑
       100 reqs    100 reqs
       at 0:59     at 1:00      → 200 reqs in 1 second.

That's a 2× burst. Bad for downstream.
```

### Sliding-log accuracy at exorbitant cost

```
Sliding log: store the timestamp of every request.

User makes 100 reqs in last minute:
  redis ZADD user:42:log {ts} {ts}
  redis ZREMRANGEBYSCORE user:42:log -inf (now - 60s)
  redis ZCARD user:42:log → if > 100, reject.

Memory: 100 timestamps per user. 10M users × 100 entries × 8 bytes = 8 GB.
Wall cost: ZRANGEBYSCORE + ZADD per request.

Accurate, expensive.
```

### Sliding-window counter: the hybrid

```
Window = 60s.
previous_window:  [0:00, 1:00)   count_prev
current_window:   [1:00, 2:00)   count_curr   ← we're in here at t=1:20

At t=1:20 (20s into current window):
  elapsed = 20s
  weight  = (60 - 20) / 60 = 2/3
  estimated = count_prev * 2/3 + count_curr

Picture of the lookback window:
                                  t=1:20
  |--prev window--|--current window--|
  0:00         1:00              1:20
       weight=2/3          everything counts

The "2/3 of previous" is the part of [0:20, 1:00) — 40 seconds of the previous
window — that still falls within the 60-second lookback ending at 1:20.

At t=1:30 (30s into current): weight = 0.5
At t=2:00 (boundary): previous becomes 0; counts shift.
```

The formula is linear approximation: it assumes events were spread uniformly within the previous window. Worst-case error is bounded by ~7% (Cloudflare's analysis).

## Why interviewers care

- Rate limiting is **every production system's safety belt**. Knowing it cold signals operational maturity.
- The algorithm choice (fixed/log/counter/token/leaky) is a **classic systems tradeoff conversation** — accuracy vs memory vs latency.
- Implementing it atomically in Redis is the **Redis Lua scripting** initiation — a senior pattern worth several follow-up questions.
- The hybrid is **what real products run** (Cloudflare, Stripe). Naming it specifically is a signal you've read the production literature.

## Common beginner confusion

- *"Sliding window = sliding log."* They're different. Sliding log stores timestamps; sliding counter stores two integers + a window start.
- *"Use `INCR` + `EXPIRE`."* That's fixed window — the simplest algorithm, with the 2× burst problem.
- *"`INCR` is atomic; that's enough."* INCR is atomic but the *check + decision* needs to be atomic too. Use Lua or `INCR` + check on the returned value.
- *"Just block IPs that send too many requests."* Naive — NAT, mobile carriers, corporate proxies. Use auth-based limits where possible.
- *"Token bucket and sliding window are the same."* Different shapes. Token bucket allows controlled bursts; sliding window strictly caps over a rolling period.

## Brute force approach

**Fixed window with `INCR` + `EXPIRE`:**

```
key = "rate:" + user_id + ":" + current_minute
n = redis.INCR(key)
if n == 1: redis.EXPIRE(key, 60)
if n > limit: reject
```

Works; simple; has the 2× burst boundary problem. Often acceptable for non-critical paths.

**Sliding log with sorted sets:**

```
redis.ZREMRANGEBYSCORE(key, 0, now - window_ms)
redis.ZADD(key, now, now)
if redis.ZCARD(key) > limit: reject
```

Exact accuracy; per-request O(log n) + O(k) for trim. Memory proportional to request volume — expensive.

## Optimal approach

The Cloudflare hybrid:

1. Store **previous-window count, current-window count, current-window-start**.
2. On each request, compute weighted estimate.
3. Increment current-window count if accepted.
4. On window boundary, rotate.

Atomic implementation via Redis Lua. Memory: ~3 integers per user. Accuracy: within ~5-7% of true sliding. Wall cost: one Redis round-trip.

## Solution (Redis Lua + Node)

### Lua script

```lua
-- KEYS[1]: hash key like "rate:{user_id}"
-- ARGV[1]: limit
-- ARGV[2]: window seconds
-- ARGV[3]: current timestamp in seconds
-- Returns: {allowed (1/0), estimated_count, retry_after_seconds}

local key       = KEYS[1]
local limit     = tonumber(ARGV[1])
local window    = tonumber(ARGV[2])
local now       = tonumber(ARGV[3])

local bucket    = math.floor(now / window)
local elapsed   = now - (bucket * window)
local weight    = (window - elapsed) / window

-- Fetch state
local data = redis.call('HMGET', key, 'cur', 'prev', 'bucket')
local cur  = tonumber(data[1]) or 0
local prev = tonumber(data[2]) or 0
local b    = tonumber(data[3]) or bucket

-- Rotate windows if we've moved on
if b < bucket then
  if b == bucket - 1 then
    prev = cur                 -- last window becomes previous
  else
    prev = 0                   -- gap > 1 window; previous decayed away
  end
  cur = 0
  b   = bucket
end

local estimated = prev * weight + cur

if estimated >= limit then
  -- Compute retry-after: time until estimated drops below limit
  -- (linear: need weight to drop enough to push prev*weight below limit-cur)
  local needed_drop = estimated - limit + 1
  local retry_after = math.ceil((needed_drop / prev) * window)
  return {0, math.floor(estimated), retry_after}
end

-- Accept; increment and persist
cur = cur + 1
redis.call('HMSET', key, 'cur', cur, 'prev', prev, 'bucket', b)
redis.call('EXPIRE', key, window * 2)        -- TTL = 2 windows
return {1, math.floor(prev * weight + cur), 0}
```

### Node client

```javascript
const Redis = require('ioredis');
const fs = require('fs');
const redis = new Redis();

const script = fs.readFileSync('./sliding_window.lua', 'utf8');
const sha = await redis.script('LOAD', script);

async function checkLimit(userId, limit = 100, windowSec = 60) {
  const key = `rate:{${userId}}`;
  const now = Math.floor(Date.now() / 1000);
  const [allowed, estimated, retryAfter] = await redis.evalsha(
    sha, 1, key, limit, windowSec, now,
  );
  return {
    allowed: allowed === 1,
    estimated,
    retryAfter,
  };
}

// Express middleware
app.use(async (req, res, next) => {
  const { allowed, estimated, retryAfter } = await checkLimit(req.user.id);
  res.set({
    'X-RateLimit-Limit': 100,
    'X-RateLimit-Remaining': Math.max(0, 100 - estimated),
  });
  if (!allowed) {
    res.set('Retry-After', retryAfter);
    return res.status(429).json({ error: 'rate_limited', retryAfter });
  }
  next();
});
```

The `{userId}` curly braces are Redis Cluster hashtags — ensure the key hashes to the same slot as any related keys for the user.

## Step-by-step dry run

Limit = 10 req/min. User makes a steady 8 req/min.

```
At minute 1 (bucket = 1): user makes 8 requests.
  After last:  cur=8, prev=0, bucket=1.

At minute 2 (bucket=2), t=2:00 (elapsed=0, weight=1.0):
  rotate: prev=8, cur=0, bucket=2.
  Request arrives: estimated = 8 * 1.0 + 0 = 8 → accept. cur=1.

At minute 2, t=2:30 (elapsed=30, weight=0.5):
  estimated = 8 * 0.5 + 1 = 5 → accept. cur=2.
  ... user makes 5 more requests in next 30 seconds ...
  At t=2:59, cur=7. estimated = 8 * 0.017 + 7 ≈ 7.14 → accept. cur=8.

At minute 3 (bucket=3), t=3:00:
  rotate: prev=8 (was cur), cur=0.

Burst test:
  At t=2:55 (still in minute 2): elapsed=55, weight=5/60≈0.083.
  Suppose cur=10 already. estimated = 8*0.083 + 10 = 10.66 → reject (>10).

  Compare with fixed window at t=1:59 + t=2:00:
  Fixed window allows 10 in [1:00, 2:00) PLUS 10 in [2:00, 3:00). Could push 20 in 1s.
  Sliding window counter caps it: at t=2:00 elapsed=0, weight=1, estimated=prev*1+0=10
  → next request rejected. Burst contained.
```

## How to think aloud in the interview

> "Four algorithms to choose from: fixed window, sliding log, sliding-window counter, token bucket. Fixed window with `INCR`+`EXPIRE` is the simplest but allows a 2× burst at the boundary — full quota at 0:59, full quota at 1:00. Sliding log stores every timestamp; exact accuracy but memory-heavy (100 8-byte entries per user). The sweet spot is the Cloudflare-style sliding-window counter: store two counters and a window start, compute a weighted estimate.
>
> Formula: `estimated = previous_count * (window - elapsed) / window + current_count`. The first term is the part of the previous window still in our lookback, prorated linearly under the assumption that requests were uniform within that window. Error is bounded ~7% — good enough.
>
> Implementation: a Lua script in Redis, atomic by definition. Fetch the hash with cur/prev/bucket, rotate if we've crossed the boundary, compute estimate, accept-and-increment or reject. TTL the hash at 2× window so stale keys expire.
>
> For Redis Cluster, use a hashtag in the key (`rate:{user_id}`) so all per-user state lives on one shard. For multi-shard load distribution, accept that rate limiting is inherently per-key — not the parallelism problem.
>
> If the workload tolerates controlled bursts, I'd switch to token bucket. If it requires perfectly smooth output rate, leaky bucket. For 'cap at N over rolling W' which is the most common ask, sliding window counter is the right default."

## Important takeaways

- **Sliding window counter** is the production default: ~7% error, O(1) memory per user, single Redis round-trip.
- **Fixed window** = 2× burst at boundary; cheap and simple; fine for noncritical paths.
- **Sliding log** = exact but memory-heavy; for low-volume / high-accuracy needs.
- **Lua script** for atomicity — increment + decision in one round-trip.
- **TTL = 2× window** so old state expires after it can't matter.
- **Use a hashtag** for Redis Cluster co-location.
- **Return `Retry-After`** header for clients to back off intelligently.
- **Per-user keying** dominates per-IP; auth-based limits avoid NAT problems.

## Variants

1. **Per-endpoint limits** — key = `rate:{user_id}:endpoint`. Lower limits on expensive endpoints.
2. **Tiered limits** — free tier 100/min, paid tier 1000/min. Look up tier first.
3. **Multi-window** — 10/sec AND 100/min AND 1000/hour. Run three counters; reject if any exceeds.
4. **Token bucket** — see `rate-limiter-token-bucket.md`.
5. **Leaky bucket** — see `rate-limiter-leaky-bucket.md`.
6. **Distributed counter with sharded keys** — for *very* hot keys, shard the counter into N pieces and sum.
7. **GCRA (Generic Cell Rate Algorithm)** — telco-style; more rigorous than token bucket but functionally similar.

## Revision notes

> **sliding window counter — 60 second recap**
> - **Hybrid of fixed and sliding**: two counters + window start, weighted estimate.
> - **Formula:** `prev * (W - elapsed) / W + cur >= limit ?`.
> - ~7% error vs true sliding; O(1) memory per user.
> - **Atomic Lua script** in Redis — fetch, rotate, compute, decide, write.
> - **TTL = 2 × window** so state expires.
> - Use Redis Cluster **hashtag** `rate:{user_id}` for slot co-location.
> - Return `Retry-After` header on 429.
> - Alternatives: fixed (bursty), sliding log (memory-heavy), token bucket (allows bursts), leaky bucket (smoothing).
