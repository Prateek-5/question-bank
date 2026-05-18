# Rate limiter — token bucket (Redis + Lua atomic implementation)

## Source / Origin
- Original concept from network traffic shaping (RFC 2697 — Single Rate Three Color Marker, related GCRA work).
- Stripe and AWS API Gateway both publicly describe token-bucket-shaped limits.
- `backend-data-prep/caching/03-rate-limiting.md` — concept doc.
- Classic prompt: *"Allow bursts of up to 50 requests but a steady rate of 10 per second. Implement this with Redis."*

## Why this question matters in interviews
Token bucket is the **"controlled burst" algorithm** — the one to reach for when fixed-rate caps feel wrong. AWS, GitHub, and Stripe all describe their public API limits in token-bucket terms ("10 requests per second sustained, 100 burst"). The interviewer wants:

1. You **know token bucket allows configured bursts**, in contrast to sliding-window-counter (strict cap) and leaky-bucket (smoothing).
2. You **can implement it atomically** with Redis + Lua — no race conditions across processes.
3. You understand the **lazy-refill trick** (don't run a background filler thread; refill on demand using elapsed time × refill rate).
4. You can compute **`Retry-After`** accurately — when will enough tokens be available for the next request?

This is the natural follow-up to the sliding-window-counter question.

## Concepts involved

### Syntax to lock in

```
bucket parameters:
  capacity         maximum tokens (the "burst")
  refill_rate      tokens per second (the "steady rate")

state per user:
  tokens           current token count, 0 ≤ tokens ≤ capacity
  last_refill_ts   when tokens were last computed

on each request at time t:
  elapsed   = t - last_refill_ts
  tokens   := min(capacity, tokens + elapsed * refill_rate)
  last_refill_ts := t
  if tokens >= cost:
    tokens -= cost
    accept
  else:
    retry_after = (cost - tokens) / refill_rate
    reject(retry_after)
```

### Edge cases / interview traps

1. **Lazy refill, not active.** Don't run a background thread filling tokens at refill_rate. Compute refill on demand: tokens added = elapsed * rate, capped at capacity. Saves N CPUs.
2. **Float vs integer tokens.** Use floats internally; rounding errors with integer tokens cause off-by-one over thousands of requests. If Redis requires strings, scale up (tokens × 1000) and operate on integers.
3. **Cost != 1.** Real APIs charge different requests different token amounts: "list" = 1 token, "write" = 5, "search" = 10. Implementation must support `cost` argument.
4. **Empty bucket on first request.** Initialize to `capacity` (allow full burst on first arrival) or `0` (force ramp-up). Most APIs use `capacity` — friendly to legitimate new users.
5. **Concurrent refills.** Two requests in flight at the same time can both compute `elapsed` and double-refill if not atomic. **Use Lua.**
6. **`Retry-After` accuracy.** It's not `1 / refill_rate`; it's `(cost - tokens) / refill_rate`. If the user requested cost=5 and has 1 token, they need `4 / rate` seconds.
7. **Clock skew.** Use Redis's `TIME` command inside Lua for a single authoritative clock.
8. **TTL the key.** Set TTL ≥ `capacity / refill_rate` so the bucket doesn't expire mid-fill, but does eventually clean up inactive users.

## Mental Model

### The bucket-and-faucet picture

```
                refill at 10 tokens/sec
                       │
                       ▼
              ┌─────────────────┐
              │       50        │ ← capacity (max burst)
              │     │ │ │       │
              │     ▼ ▼ ▼       │
              │  ░░░░░░░░░░░    │ ← current tokens
              │  ░░░░░░░░░░░    │
              └────────┬────────┘
                       │
                       ▼ pay 1 token per request
                  ┌─────────┐
                  │ request │
                  └─────────┘

If tokens >= cost: accept and deduct.
If tokens < cost:  reject with Retry-After.
```

### Token bucket vs sliding window counter vs leaky bucket

```
Sliding-window counter:
  "max 100 in any 60s window"
  Strict cap. No burst tolerance.

Token bucket (cap=100, refill=10/s):
  Starts with 100 tokens.
  Burst: can drain all 100 in 1 second.
  Then capped at 10/s for the next minute.
  Bursts ARE allowed, controlled by capacity.

Leaky bucket (rate=10/s, queue=100):
  Output is smooth at 10/s regardless of input.
  Bursts buffered up to queue size, then dropped.
  Input can be bursty; output never is.

Use cases:
  Sliding counter:  abuse prevention, hard caps.
  Token bucket:     API limits with friendly burst allowance.
  Leaky bucket:     downstream protection — must smooth output.
```

### Refill-on-demand timeline

```
t=0  user starts with tokens=50, last_refill=0
t=1  request arrives. elapsed=1, refill=1*10=10 → tokens=min(50,50+10)=50.
     Already at cap; no actual add. cost=1 → tokens=49. accept.

t=1.1 request. elapsed=0.1, refill=1 → tokens=50. cost=1 → 49. accept.
        (so far: 2 requests, tokens stay at 49 because refill keeps up.)

User now bursts 60 requests at t=10..t=10.1 (essentially simultaneously).
  Request #1:  elapsed=8.9, refill=89→capped at 50. cost=1, tokens=49.
  Request #2:  elapsed=~0, refill=~0. tokens=48.
  ...
  Request #50: tokens=0.
  Request #51: tokens=0, cost=1. retry_after = 1/10 = 0.1s. reject.

User waits 0.5s and retries:
  elapsed=0.5, refill=5, tokens=5. cost=1 → 4. accept.

Burst absorbed; then back to the steady-state rate.
```

## Why interviewers care

- Token bucket is **the most-deployed real-world rate-limit algorithm** at API gateways. Real product knowledge.
- The lazy-refill trick is a **classic resource-saving pattern** that interviewers love hearing about.
- Atomic Redis Lua implementation is the **canonical "distributed coordination" example** outside locks.
- It contrasts naturally with sliding window and leaky bucket — the rate-limit family conversation.

## Common beginner confusion

- *"Tokens are filled by a background thread."* Don't. Lazy compute on demand from elapsed time × rate.
- *"Bucket and window are the same."* No. Window = strict cap over rolling period. Bucket = burst + steady-rate.
- *"Increment a counter."* That gives you fixed window. Different algorithm.
- *"`Retry-After` is `1 / refill_rate`."* Only when cost=1 and tokens=0. Generally `(cost - tokens) / refill_rate`.
- *"Use Redis `INCR`."* Won't work — token bucket needs read-modify-write of a float, not simple increment. Use HMGET + Lua.

## Brute force approach

Background thread refilling tokens at `refill_rate`. For 10M users, 10M timer callbacks per second. Won't scale. Lazy refill is the standard.

Naive non-atomic Redis: GET tokens, compute new value, SET tokens. Two concurrent requests both read the same value, both write — lost-update race. Always Lua.

## Optimal approach

1. **Lua script** does fetch → refill → check → deduct → store in one atomic operation.
2. State: hash with `tokens` (float) and `last_refill_ts` (seconds since epoch).
3. Use Redis `TIME` inside Lua for the clock — avoids client-side clock skew.
4. Return `(allowed, tokens_remaining, retry_after)` from the script.

## Solution (Redis Lua + Node)

### Lua script

```lua
-- KEYS[1]: hash key, e.g. "tb:{user_id}"
-- ARGV[1]: capacity  (max tokens)
-- ARGV[2]: refill_rate (tokens per second, may be fractional)
-- ARGV[3]: cost  (tokens this request consumes)
-- Returns: {allowed (1/0), tokens_remaining_int, retry_after_ms_int}

local key       = KEYS[1]
local capacity  = tonumber(ARGV[1])
local rate      = tonumber(ARGV[2])
local cost      = tonumber(ARGV[3])

-- Redis-side clock: returns {seconds, microseconds}
local time      = redis.call('TIME')
local now       = tonumber(time[1]) + tonumber(time[2]) / 1e6

local state     = redis.call('HMGET', key, 'tokens', 'ts')
local tokens    = tonumber(state[1])
local last_ts   = tonumber(state[2])

if tokens == nil then
  tokens   = capacity      -- friendly initial state: full bucket
  last_ts  = now
end

-- Lazy refill
local elapsed = math.max(0, now - last_ts)
tokens = math.min(capacity, tokens + elapsed * rate)

local allowed = 0
local retry_after_ms = 0
if tokens >= cost then
  tokens  = tokens - cost
  allowed = 1
else
  local deficit  = cost - tokens
  retry_after_ms = math.ceil((deficit / rate) * 1000)
end

redis.call('HMSET', key, 'tokens', tokens, 'ts', now)
-- TTL big enough for inactive cleanup; small enough to free memory
local ttl = math.ceil(capacity / rate) + 60
redis.call('EXPIRE', key, ttl)

return {allowed, math.floor(tokens), retry_after_ms}
```

### Node wrapper

```javascript
const Redis = require('ioredis');
const fs = require('fs');
const redis = new Redis();

const lua = fs.readFileSync('./token_bucket.lua', 'utf8');
const sha = await redis.script('LOAD', lua);

async function take(userId, { capacity = 100, refillRate = 10, cost = 1 } = {}) {
  const key = `tb:{${userId}}`;
  const [allowed, remaining, retryAfterMs] = await redis.evalsha(
    sha, 1, key, capacity, refillRate, cost,
  );
  return { allowed: allowed === 1, remaining, retryAfterMs };
}

// Express middleware
app.use(async (req, res, next) => {
  const cost = req.path.startsWith('/search') ? 5 : 1;
  const { allowed, remaining, retryAfterMs } = await take(req.user.id, {
    capacity: 100, refillRate: 10, cost,
  });
  res.set({
    'X-RateLimit-Limit': 100,
    'X-RateLimit-Remaining': remaining,
  });
  if (!allowed) {
    res.set('Retry-After', Math.ceil(retryAfterMs / 1000));
    return res.status(429).json({ error: 'rate_limited', retryAfterMs });
  }
  next();
});
```

The hashtag `{userId}` ensures Redis Cluster routes the key consistently.

### EVALSHA + NOSCRIPT fallback

```javascript
async function take(userId, opts) {
  try {
    return await redis.evalsha(sha, 1, key, ...args);
  } catch (e) {
    if (e.message.startsWith('NOSCRIPT')) {
      // Redis restarted; re-load the script and retry once
      sha = await redis.script('LOAD', lua);
      return await redis.evalsha(sha, 1, key, ...args);
    }
    throw e;
  }
}
```

## Step-by-step dry run

Bucket: capacity=10, refill_rate=2/sec. User starts empty (initial=10).

```
t=0.0  initial:   tokens=10, ts=0.0
       req cost=1: elapsed=0, refill=0, tokens=10 → 9. accept.
t=0.1  req cost=1: elapsed=0.1, refill=0.2 → tokens=9.2 → 8.2. accept.
t=0.2  req cost=1: tokens=8.4 → 7.4. accept.
       ...
       (10 requests fired rapidly drain to tokens=~0)
t=0.5  req cost=1: tokens ≈ 0.0. retry_after = 1/2 = 500ms. reject.
t=1.0  req cost=1: elapsed=0.5 (from last refill), refill=1.0. tokens=1.0 → 0. accept.
t=1.5  req cost=1: tokens=1.0 → 0. accept. (steady state at refill rate.)
t=10.0 (idle for 8.5s)
       req cost=1: elapsed=8.5, refill=17 → capped to 10. tokens=10 → 9. accept.
t=10.1 req cost=5: tokens=9.2-5 = 4.2. accept.
t=10.2 req cost=5: tokens=4.4. cost=5 > 4.4 → reject.
       retry_after = (5 - 4.4) / 2 = 0.3s.
```

The "fill while idle" effect — tokens cap at capacity even after long idle — is the burst allowance. Useful for users who batch their work.

## How to think aloud in the interview

> "Token bucket allows controlled bursts on top of a steady rate. Parameters: `capacity` is the max burst; `refill_rate` is tokens-per-second sustained. State per user is `tokens` (float) and `last_refill_ts`. Each request: compute `elapsed = now - last_refill_ts`, add `elapsed * rate` to tokens capped at capacity, then either deduct `cost` and accept or reject with a `Retry-After`.
>
> Two implementation choices to flag. First, **lazy refill** — don't run a background timer adding tokens; compute the refill at request time. With 10M users this saves 10M background timers. Second, **atomicity** — fetch + refill + decide + store must be atomic across processes. Lua script in Redis is the canonical way; `EVALSHA` for hot path with `NOSCRIPT` fallback.
>
> `Retry-After` accuracy matters: if cost is 5 and tokens is 1, the client must wait `(5 - 1) / refill_rate` seconds — not just `1/refill_rate`. Otherwise clients hammer back too soon.
>
> Compared to sliding-window counter: counter is strict cap over rolling window; bucket allows bursts within capacity. Compared to leaky bucket: leaky smooths output unconditionally; bucket is input-controlling, not output-shaping.
>
> Cost-per-request lets you charge expensive operations more — listing maybe 1 token, full-text search 10. Easier than maintaining multiple buckets.
>
> Redis Cluster: hashtag the user id so per-user state co-locates. For genuinely hot keys (rare), shard the bucket into N pieces."

## Important takeaways

- **Lazy refill** — compute on demand from elapsed time × rate. No background threads.
- **Atomic Lua script** in Redis — single round-trip, no race conditions.
- **Float tokens internally** (or scale to integer); avoids long-run drift.
- **`Retry-After` = `(cost - tokens) / refill_rate`** — not `1 / rate`.
- **Capacity = burst size**, **rate = steady throughput** — two knobs, separate concerns.
- **Cost per request** generalises to "expensive ops cost more tokens."
- **Initial state = capacity** (friendly) or 0 (strict); pick deliberately.
- **TTL the key** to free memory for inactive users.

## Variants

1. **Per-endpoint token cost** — same bucket, different costs per route.
2. **Hierarchical buckets** — per-user bucket + global bucket; reject if either exhausted.
3. **Tier-based parameters** — free tier (cap=10, rate=1), paid tier (cap=100, rate=10).
4. **GCRA** — Generic Cell Rate Algorithm. Equivalent to token bucket but expressed as "earliest next request time"; one float of state instead of two.
5. **Sharded token bucket** — split into N sub-buckets for very hot keys; client picks a shard.
6. **Token bucket with debit** — allow negative tokens up to a debt cap, then reject. Useful for absorbing brief overshoots.
7. **Refill schedules with non-uniform rate** — e.g. higher rate during business hours.

## Revision notes

> **token bucket — 60 second recap**
> - Two knobs: **capacity** (burst) + **refill_rate** (steady rate).
> - **Lazy refill** — compute on demand from elapsed × rate.
> - State: `tokens` (float) + `last_refill_ts`.
> - **Atomic Lua script** — fetch, refill, deduct or reject, persist.
> - **`Retry-After` = `(cost - tokens) / rate`** — not `1/rate`.
> - **Cost** parameter for differential pricing per endpoint.
> - Allows bursts (vs sliding-window counter); allows bursty input (vs leaky bucket).
> - TTL the key; hashtag for Cluster co-location.
> - GCRA = single-float equivalent.
