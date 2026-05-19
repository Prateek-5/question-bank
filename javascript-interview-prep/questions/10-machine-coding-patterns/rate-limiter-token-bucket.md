# Rate Limiter — token bucket with lazy refill

> **Difficulty:** Medium-Senior   |   **Time:** ~25 min   |   **Prereqs:** [throttle.md](./throttle.md), [lru-cache.md](./lru-cache.md)
>
> **Source:** Cloudflare engineering blog, Stripe rate-limiters post, AWS API Gateway. Asked at every backend infra interview.

---

## 1. Problem statement

**Signature**
```ts
class TokenBucket {
  constructor(opts: { capacity: number; refillRate: number /* per second */ });
  allow(key: string, cost?: number): boolean;
  retryAfterMs(key: string, cost?: number): number;
}
```

**Input / Output examples**

| Setup (capacity 3, rate 1/sec)         | Behaviour                                              |
|----------------------------------------|---------------------------------------------------------|
| First 3 calls within 50ms              | all allowed (burst)                                    |
| 4th call within same burst             | rejected                                                |
| After 1 second of idle                 | 1 token refilled — next call allowed                   |
| After 5 seconds of idle                | bucket capped at `capacity` (3) — extras don't accumulate |
| `allow('a')` and `allow('b')`          | independent buckets per key                            |
| `retryAfterMs('a')`                    | ms until next token available                          |

**Constraints**
- Per-key state `{ tokens, lastRefillTime }`.
- **Lazy refill:** compute tokens on each call, no background timer.
- Cap at `capacity` (refill doesn't accumulate forever).
- Fractional tokens for precision.

---

## 2. Plain-English restatement

Each user has a bucket holding up to N tokens. Each request consumes 1 token. The bucket refills at a fixed rate. When the bucket is empty, requests are rejected. Bursts up to `capacity` are allowed; sustained rate is capped at `refillRate`. Implement the refill **lazily** — compute it on demand from elapsed time, never via a background timer.

---

## 3. Why this matters in interviews

The **#1 backend-flavored machine-coding question** at senior level. Every API gateway, webhook delivery, public API has one. Probes two skills: (1) algorithm choice — token bucket vs leaky bucket vs sliding window; (2) data structure — per-key state, monotonic time, lazy refill. Senior bonus: articulate **why token bucket beats leaky bucket** (allows bursts → smoother UX), when **sliding window log** beats token bucket (precise but memory-heavy), and how Redis-based distributed limiters work.

---

## 4. Mental model

```
   capacity = 3, refillRate = 1 token/sec

   bucket: [● ● ●]   3 tokens at t=0

   allow():
     refill_now()         add (now - lastRefillTime)*rate, cap at capacity
     if tokens >= 1:
       tokens -= 1
       return true
     return false

   Timeline:
   t=0    allow() → [● ●_]  (2 left)
   t=100  allow() → [●_ _] +0.1 refill (2.1) → 1.1
   t=200  allow() → 1.2 → 0.2
   t=300  allow() → 0.3 < 1 → REJECT
   t=1500 allow() → +1.2 refill (1.5) → 0.5 → ALLOWED
   t=5000 allow() → +3.5 refill, capped at 3 → 2 → ALLOWED

   Lazy refill: no setInterval; math happens on each call.
```

**Comparison:**
- **Token bucket:** bursts up to capacity, smooth thereafter. Friendliest UX.
- **Leaky bucket:** constant drain rate, no bursts. Smooths downstream load.
- **Fixed window:** count per N-sec window — boundary burst doubles effective limit.
- **Sliding window log:** timestamps in deque — precise, O(limit) memory.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. With capacity=3 and rate=1/sec, how many requests can a brand-new user make in the first 100ms?
> 2. Why use lazy refill instead of `setInterval` to refill every second?
> 3. After 10 seconds of idle, how many tokens does the bucket hold? Why isn't it 10?

---

## 6. Brute force — walked through

### Wrong attempt 1: fixed window counter
```js
counter[key][windowId]++;
if (counter[key][windowId] > limit) reject();
```
Has the **boundary burst** problem: a user can do `limit` requests at end of window N and another `limit` at start of N+1, effectively 2× the limit briefly.

### Wrong attempt 2: background `setInterval` to refill
Per-key timer leaks at scale (millions of users). Memory churn. Always lazy.

### Wrong attempt 3: integer tokens
Loses precision: if rate=1/sec, a user can't get 1 token per 0.9 sec elapsed. Use floats.

---

## 7. The unlocking insight

> **Lazy refill: on each `allow` call, compute `tokens += elapsedSec * rate`, cap at capacity, then check if ≥ cost. Per-key state in a `Map<key, {tokens, lastRefillTime}>`.**

Three properties:

1. **Lazy refill** — no timers, O(1) per request.
2. **Cap at capacity** — `Math.min(capacity, tokens + elapsed * rate)`.
3. **Fractional tokens** — float arithmetic so refill granularity is exact.

---

## 8. Solution (annotated)

```js
class TokenBucket {
  constructor({ capacity, refillRate }) {
    if (capacity <= 0) throw new Error('capacity must be > 0');
    if (refillRate <= 0) throw new Error('refillRate must be > 0');
    this.capacity = capacity;
    this.refillRate = refillRate;                                    // tokens / second
    this.buckets = new Map();                                         // step 1: per-key state
  }

  _refill(bucket, now) {                                              // step 2: lazy refill
    const elapsedSec = Math.max(0, (now - bucket.lastRefillTime) / 1000);
    bucket.tokens = Math.min(this.capacity, bucket.tokens + elapsedSec * this.refillRate);
    bucket.lastRefillTime = now;
  }

  allow(key, cost = 1) {
    const now = Date.now();
    let bucket = this.buckets.get(key);
    if (!bucket) {                                                     // step 3: new user → full bucket
      bucket = { tokens: this.capacity, lastRefillTime: now };
      this.buckets.set(key, bucket);
    } else {
      this._refill(bucket, now);
    }

    if (bucket.tokens >= cost) {                                       // step 4: consume + allow
      bucket.tokens -= cost;
      return true;
    }
    return false;                                                       // step 5: reject
  }

  retryAfterMs(key, cost = 1) {                                         // for HTTP Retry-After
    const bucket = this.buckets.get(key);
    if (!bucket || bucket.tokens >= cost) return 0;
    const deficit = cost - bucket.tokens;
    return Math.ceil((deficit / this.refillRate) * 1000);
  }
}
```

**Try it yourself**

```js
const limiter = new TokenBucket({ capacity: 3, refillRate: 1 });

console.log(limiter.allow('u1'));  // true (3 → 2)
console.log(limiter.allow('u1'));  // true (2 → 1)
console.log(limiter.allow('u1'));  // true (1 → 0)
console.log(limiter.allow('u1'));  // false (0 → reject)

await new Promise(r => setTimeout(r, 1000));
console.log(limiter.allow('u1'));  // true (refilled to ~1)
console.log(limiter.retryAfterMs('u1', 2));  // ~1000ms (need 1 more token)
```

---

## 9. Step-by-step dry run

```
capacity=3, refillRate=1/sec

t=0    allow('u1'):
       no bucket → init {tokens: 3, lastRefillTime: 0}
       tokens=3 >= 1 → consume → tokens=2 → ALLOW

t=100  allow('u1'):
       refill: elapsedSec=0.1, +0.1 tokens → 2.1 (≤3) → tokens=2.1
       lastRefillTime=100
       tokens=2.1 >= 1 → consume → tokens=1.1 → ALLOW

t=200  allow('u1'):
       refill: elapsedSec=0.1, +0.1 → 1.2
       consume → 0.2 → ALLOW

t=300  allow('u1'):
       refill: elapsedSec=0.1, +0.1 → 0.3
       0.3 < 1 → REJECT
       lastRefillTime=300 (still updated)

t=1500 allow('u1'):
       refill: elapsedSec=1.2, +1.2 → 1.5
       consume → 0.5 → ALLOW

t=5000 allow('u1'):
       refill: elapsedSec=3.5, +3.5 → 4.0
       CAPPED at capacity=3 → tokens=3
       consume → 2 → ALLOW
```

Cap-at-capacity is what makes this a token bucket vs an unbounded counter — idle time never accumulates beyond burst tolerance.

---

## 10. Common confusion + traps

1. **Background `setInterval` refill** — per-key timer leaks; doesn't scale.
2. **Integer tokens** — precision loss.
3. **No cap at capacity** — idle users accumulate huge token reserves.
4. **`Date.now()` jumping backward** (NTP sync) — `Math.max(0, ...)` guards; `performance.now()` is monotonic.
5. **Unbounded `Map<key, bucket>`** — production needs LRU/TTL eviction.
6. **First request: 0 tokens or full?** — init to `capacity` (full); state the choice.
7. **Confusing token bucket with leaky bucket** — token = bursts allowed; leaky = constant drain.

---

## 11. Senior follow-ups & variants

### Variant 1 — Leaky bucket
Queue requests; drain at constant rate; drop overflow. Better when downstream can't tolerate bursts.

### Variant 2 — Sliding window log
Deque of timestamps per key; reject if `length > limit`. Pop expired timestamps lazily. **Most accurate**, O(limit) memory per key.

### Variant 3 — Sliding window counter
`current_count * (elapsed/window) + previous_count * remainder`. Single counter per window, ~98% accurate, very memory-light.

### Variant 4 — Distributed token bucket
Redis Lua script atomically reads/refills/decrements. Or `CL.THROTTLE` from RedisBloom. Single-node → cluster.

### Variant 5 — Tiered limits
Per-second + per-minute + per-day on same key. N nested buckets; reject if any rejects.

### Variant 6 — Cost-aware
`allow(key, cost)` where heavy endpoints consume more. Already in the snippet.

---

## 12. How to think aloud

> "Token bucket with lazy refill. Per key: `{tokens, lastRefillTime}` in a Map. On each `allow`: compute elapsed time, add `elapsed * rate` tokens (capped at capacity), then if `tokens >= cost` decrement and allow, else reject. O(1), no timers. Capacity is the burst size; refillRate is the sustained rate. Float tokens for precision. First request initializes to full bucket. Production needs LRU/TTL on the Map to avoid unbounded growth across users. Senior follow-ups: leaky bucket (no bursts, constant drain), sliding window log (precise, memory-heavy), distributed via Redis Lua. Trap: background timer per key leaks at scale. Trap: integer tokens lose precision."

---

## 13. 60-second revision

> - **Token bucket, lazy refill.**
> - **Per key:** `{tokens, lastRefillTime}` in a Map.
> - **On call:** `tokens = min(capacity, tokens + elapsed*rate)`; if `>= cost`, decrement and allow.
> - **Bursts** up to capacity; sustained rate = refillRate.
> - **Fractional tokens** for precision; `Math.max(0, elapsed)` for clock skew.
> - **`retryAfterMs(key)`** = `(cost - tokens) / rate * 1000`.
> - **vs leaky bucket:** leaky = constant drain, no bursts.
> - **vs sliding window:** window precise but O(limit) memory.
> - **Distributed:** Redis Lua, `CL.THROTTLE`.
> - **Trap:** background timer; integer tokens; unbounded Map.

---

**Related:** [throttle.md](./throttle.md) · [debounce.md](./debounce.md) · [batched-request-coalescer.md](./batched-request-coalescer.md) · [`04-promises/promise-pool.md`](../04-promises/promise-pool.md)

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md)
