# Rate limiter — leaky bucket (queue-based smoothing)

## Source / Origin
- Original concept from ATM/Frame Relay traffic shaping; RFC 2697 is the classical reference.
- Used in Nginx's `limit_req` module, RabbitMQ flow control, and many message brokers.
- `backend-data-prep/caching/03-rate-limiting.md`.
- Classic prompt: *"Downstream service can only handle 100 requests per second. Implement a leaky-bucket smoother. Don't drop requests; queue them."*

## Why this question matters in interviews
Leaky bucket is the **output-smoothing algorithm** — used when the downstream cannot tolerate bursts, regardless of what input looks like. Token bucket controls *what enters*; leaky bucket controls *what leaves*. The interviewer is testing whether you:

1. Understand the **conceptual flip**: bucket fills at a variable rate, drains at a *fixed* rate.
2. Can design **a FIFO queue with bounded depth** that drops or rejects on overflow.
3. Recognise when this is the right tool — protecting a downstream that can't burst-absorb.
4. Can implement it without a background thread (the "lazy leak" trick mirrors lazy refill in token bucket).

It rounds out the rate-limiter trio (sliding window, token bucket, leaky bucket). Knowing all three by name and use-case is the senior signal.

## Concepts involved

### Syntax to lock in

```
parameters:
  rate         leak rate in items per second (fixed output rate)
  capacity     max items in the queue/bucket

state per key:
  level        current "fluid level" (or queue length)
  last_leak_ts when level was last updated

on each arrival at time t:
  elapsed = t - last_leak_ts
  level   = max(0, level - elapsed * rate)
  last_leak_ts = t
  if level < capacity:
    level += 1                          # admit
    accept
  else:
    reject
```

In the **queueing variant**, you also schedule each admitted request to be processed at `last_leak_ts + level/rate` so output really leaks at a steady rate. In the **counter variant**, you accept/reject immediately and downstream pacing is separate.

### Edge cases / interview traps

1. **Lazy leak**, mirroring lazy refill in token bucket. No background drainer; compute level at arrival from elapsed × rate.
2. **Leaky bucket vs token bucket — flipped semantics.** Tokens replenish, items drain. Tokens enable; level forbids.
3. **Queueing variant** has unbounded latency for the last-admitted item: latency ≈ level/rate. Cap the level to bound max latency.
4. **Counter variant** acts identically to GCRA — admission rate is limited but no actual queue is maintained.
5. **Atomic update.** Same as token bucket: arrival check + level update must be atomic. Lua in Redis.
6. **Floating-point level** — items aren't necessarily integer-counted; a request might be size 5. Use floats internally.
7. **Reject vs delay decision.** Real systems pick one. Nginx `limit_req` rejects (`burst=N nodelay`) or delays (`burst=N delay`). Document which you're doing.
8. **Backpressure to clients.** If you queue, return `429` with `Retry-After`; clients shouldn't keep submitting if you're already saturated.

## Mental Model

### The leaky bucket picture

```
            input (bursty, e.g. 200 req/s briefly)
                 │
                 ▼
        ┌────────────────┐
        │                │  ← capacity (max queue)
        │   ░░░░░░░░░░   │
        │   ░░░░░░░░░░   │
        │   ░░░░░░░░░░   │
        │       ▼        │
        └────────┬───────┘
                 │
                 ▼  drips at a fixed rate (e.g. 100 req/s)
            downstream

Input rate < drip rate: bucket drains; arrivals pass through immediately.
Input rate > drip rate: bucket fills; eventually overflows; later arrivals dropped.
```

### Leaky bucket vs token bucket — the inversion

```
TOKEN BUCKET (admit if tokens available)
   ┌──────────────┐
   │  tokens=50   │ ← refill at rate
   └──────────────┘
   On arrival: take token. Limit on input.
   Bursts ARE allowed up to capacity.

LEAKY BUCKET (admit if level < capacity)
   ┌──────────────┐
   │  level=10    │ ← drains at rate
   └──────────────┘
   On arrival: add level. Limit on level → limit on output rate.
   Output ALWAYS leaks at constant rate.

Both have a 2-parameter signature; semantics differ.
```

### Smoothing in timeline

```
Input arrivals (burst):
  ↓↓↓↓↓↓↓↓↓↓                                 ↓↓↓↓↓
  0  1  2  3  4  5  6  7  8  9  10 ... 60s

Leaky bucket output (100 req/s steady, rate=100):
  ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓
  every 10ms — perfectly smooth.

Input that exceeds rate over time:
  capacity fills, then drops.
```

## Why interviewers care

- Leaky bucket protects **downstream services that genuinely can't burst-absorb**: database connection pools, payment processors, third-party APIs with strict QPS.
- It's the natural answer to **"smooth my request stream"** — distinct from "cap my request rate."
- The lazy-leak trick is the same "compute on demand" pattern as token bucket — proves you generalise the technique.
- It pairs naturally with **queuing theory** (M/M/1, Little's Law) for capacity planning conversations.

## Common beginner confusion

- *"Leaky bucket and token bucket are the same."* Different. Leaky controls output rate; token controls input rate.
- *"Leaky bucket = FIFO queue."* The queueing variant uses a FIFO, but the counter variant only tracks level. Both qualify as "leaky bucket".
- *"Just throttle with `setInterval`."* That's a leak loop in app code; doesn't survive process restarts and doesn't coordinate across instances.
- *"Drop is the same as reject."* Subtle distinction: drop = silent (used in network shaping); reject = with response code/Retry-After (used in API shaping). Pick deliberately.
- *"Capacity = throughput."* Capacity is the *burst absorption*; throughput is the leak rate. Independent dimensions.

## Brute force approach

Background goroutine/thread firing every `1/rate` to dequeue one item. Works for single-process but doesn't scale across N app instances (each runs its own drain timer, total output rate becomes N × rate). And it wastes CPU on idle keys.

Lazy-leak in Redis Lua is the production pattern.

## Optimal approach

**Counter variant (admission control only):**

1. State: `level` (float) + `last_leak_ts`.
2. On arrival: compute lazy leak, check `level < capacity`, increment level, accept; else reject.
3. Atomic in Lua.

**Queueing variant (true smoothing):**

1. State: `last_admitted_at` + queue.
2. On arrival: compute scheduled emission time = `max(now, last_admitted_at + 1/rate)`.
3. If `scheduled - now > max_latency`: reject. Else: store scheduled time, wait until then, emit.
4. The "queue" can be virtual — you don't actually buffer the request, you just compute its emission time and `setTimeout`.

## Solution (Redis Lua + Node)

### Counter variant — Lua script

```lua
-- KEYS[1]: hash key, e.g. "lb:{user_id}"
-- ARGV[1]: capacity
-- ARGV[2]: leak rate (items per second)
-- ARGV[3]: cost (items this request adds)
-- Returns: {allowed (1/0), level_after, retry_after_ms}

local key       = KEYS[1]
local capacity  = tonumber(ARGV[1])
local rate      = tonumber(ARGV[2])
local cost      = tonumber(ARGV[3])

local time      = redis.call('TIME')
local now       = tonumber(time[1]) + tonumber(time[2]) / 1e6

local state     = redis.call('HMGET', key, 'level', 'ts')
local level     = tonumber(state[1]) or 0
local last_ts   = tonumber(state[2]) or now

-- Lazy leak
local elapsed = math.max(0, now - last_ts)
level = math.max(0, level - elapsed * rate)

local allowed = 0
local retry_after_ms = 0
if level + cost <= capacity then
  level   = level + cost
  allowed = 1
else
  -- need (level + cost - capacity) units to drain
  local overflow = level + cost - capacity
  retry_after_ms = math.ceil((overflow / rate) * 1000)
end

redis.call('HMSET', key, 'level', level, 'ts', now)
local ttl = math.ceil(capacity / rate) + 60
redis.call('EXPIRE', key, ttl)

return {allowed, level, retry_after_ms}
```

### Queueing variant — virtual queue with scheduled emission

```javascript
// last_emit_at + 1/rate = next available emission slot
// state: { lastEmitAt }  per key
// admitted requests resolve their promise after a setTimeout to the slot

const Redis = require('ioredis');
const redis = new Redis();

const LUA_SCHEDULE = `
  local key = KEYS[1]
  local rate = tonumber(ARGV[1])       -- items/sec
  local max_latency_ms = tonumber(ARGV[2])
  local time = redis.call('TIME')
  local now_ms = tonumber(time[1]) * 1000 + tonumber(time[2]) / 1000
  local last = tonumber(redis.call('GET', key)) or now_ms
  local interval_ms = 1000.0 / rate
  local next_slot = math.max(now_ms, last + interval_ms)
  local wait = next_slot - now_ms
  if wait > max_latency_ms then
    return {-1, wait}
  end
  redis.call('SET', key, next_slot, 'EX', 60)
  return {1, wait}
`;

const sha = await redis.script('LOAD', LUA_SCHEDULE);

async function leakyAdmit(key, rate, maxLatencyMs) {
  const [allowed, waitMs] = await redis.evalsha(sha, 1, key, rate, maxLatencyMs);
  if (allowed === -1) return { allowed: false, waitMs };
  if (waitMs > 0) await new Promise(r => setTimeout(r, waitMs));
  return { allowed: true, waitMs };
}

// Usage
app.use(async (req, res, next) => {
  const { allowed, waitMs } = await leakyAdmit(`lb:{${req.user.id}}`, 100, 500);
  if (!allowed) {
    res.set('Retry-After', Math.ceil(waitMs / 1000));
    return res.status(429).json({ error: 'queue_full' });
  }
  res.set('X-RateLimit-Delay-Ms', waitMs);
  next();
});
```

The queueing variant emits at a fixed pace by computing each request's emission timestamp; the application `await`s until that time, then proceeds.

## Step-by-step dry run

**Counter variant.** capacity=10, rate=2/s.

```
t=0.0   level=0, ts=0. req cost=1. elapsed=0, leak=0. level=0+1=1 ≤ 10. accept.
t=0.1   elapsed=0.1, leak=0.2. level=max(0,1-0.2)=0.8. req cost=1. level=1.8. accept.
t=0.2   elapsed=0.1, leak=0.2. level=1.6. req cost=1. level=2.6. accept.
...
(burst of 10 requests in 0.1 sec each — accept all, level rises faster than it leaks)

After 10 quick requests at near-zero intervals:
  level ≈ 9.5 → next request: 9.5 + 1 = 10.5 > capacity 10 → reject.
  retry_after_ms = (10.5 - 10) / 2 * 1000 = 250 ms.

t=5.0  idle. elapsed=4.8, leak=9.6. level=max(0, 9.5-9.6)=0. accept next request.
```

**Queueing variant.** rate=2/s (one item every 500ms). max_latency=2s.

```
t=0     req#1 arrives. last=now=0, next_slot=max(0, 0+500)=500ms? 
        First request: last starts as now → next_slot=now → wait=0. accept immediately.
        Set last=500.
t=100ms req#2. next_slot=max(100, 500)=500. wait=400ms. accept (latency 400ms ≤ 2000).
        Set last=1000.
t=120ms req#3. next_slot=max(120, 1000)=1000. wait=880ms. accept (≤ 2000).
        Set last=1500.
t=140ms req#4. next_slot=max(140, 1500)=1500. wait=1360ms. accept.
        Set last=2000.
t=160ms req#5. next_slot=max(160, 2000)=2000. wait=1840ms. accept.
        Set last=2500.
t=180ms req#6. next_slot=2500. wait=2320ms > 2000. REJECT.

Output emissions land at exactly 0, 500, 1000, 1500, 2000, 2500 ms.
Smooth output regardless of burst input.
```

## How to think aloud in the interview

> "Leaky bucket controls *output* rate; it's the right tool when downstream genuinely can't burst-absorb — say, a third-party payment API with a strict 100 QPS limit or a database connection pool of fixed size.
>
> Two flavours. The **counter variant** is essentially 'admit if level < capacity', leaking lazily at `rate * elapsed`. Similar shape to token bucket but inverted: instead of subtracting tokens, you add level; instead of capacity meaning burst headroom, capacity means queue depth.
>
> The **queueing variant** actually paces output: each admitted request is assigned a scheduled emission time at `max(now, last_emit + 1/rate)`. The application `setTimeout`s until that time then proceeds. This gives you genuinely smooth output. The tradeoff is added latency — if you'd admit a request and emit 800ms later, the client waits 800ms.
>
> Bound the latency: reject when `scheduled - now > max_latency`. Otherwise queue depth grows unboundedly under sustained overload — bad for tail latency, bad for memory.
>
> Implementation: lazy leak (no background drainer), Lua script for atomicity in Redis, hashtag for Cluster co-location. Same pattern as token bucket.
>
> Vs token bucket: bucket allows bursts up to capacity then steady-rate. Vs sliding window: counter is a strict cap over a rolling window. Leaky bucket protects downstream pace specifically."

## Important takeaways

- **Output-rate smoother**, in contrast to token bucket (input-rate limiter) and sliding-window (rolling cap).
- **Lazy leak** — compute level on demand from elapsed × rate.
- **Counter variant** = admission control; **queueing variant** = paced emission with scheduled delay.
- **Atomic Lua** in Redis — fetch, leak, check, update.
- **Bound latency** by rejecting when scheduled wait exceeds max_latency.
- **Use when downstream is the bottleneck** — payment APIs, DB connection pools, brokers.
- **Float level**; cost may not be 1.
- Same `Retry-After` semantics as token bucket.

## Variants

1. **Nginx `limit_req`** — counter variant with optional `delay` mode (paces requests up to burst capacity).
2. **GCRA** — Generic Cell Rate Algorithm; mathematically equivalent to leaky bucket, expressed as TAT (theoretical arrival time).
3. **Priority leaky buckets** — multiple input queues, different priorities, merged drain.
4. **Hierarchical leak** — per-user bucket feeding into a global bucket.
5. **Drop tail vs drop head** — when overflowing, drop the newest or the oldest request. Typically drop newest (lowest expected service).
6. **Weighted leaky bucket** — different request types have different "size" added to level; matches token bucket cost concept.
7. **Backpressure to upstream** — instead of dropping, return `429` so upstream slows naturally.

## Revision notes

> **leaky bucket — 60 second recap**
> - **Output-rate smoother** (vs token bucket's input rate, vs sliding window's rolling cap).
> - Two flavours: **counter** (admission only) and **queueing** (paced emission).
> - State: `level` (float) + `last_leak_ts`. Lazy leak from elapsed × rate.
> - **Atomic Lua script** in Redis.
> - **Bound latency** — reject when scheduled wait > max_latency.
> - Used in Nginx `limit_req`, RabbitMQ flow control, payment-API protection.
> - GCRA is the math-friendly equivalent.
> - `Retry-After` = (overflow / rate) seconds.
