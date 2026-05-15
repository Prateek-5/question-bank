# Implement a Rate Limiter (Token Bucket)

## Source
- Canonical backend machine-coding / system-design crossover problem (asked at Cloudflare, Stripe, AWS, every API gateway interview).
- Reference: Cloudflare engineering blog, Stripe rate-limiters post, RFC 7234 (caching adjacent).

## Why this question matters in interviews
Rate-limiting is the **#1 backend-flavored machine-coding question** for senior roles. Every API gateway, every webhook delivery system, every public API has one. The interviewer is testing two skills: (1) the algorithm — token bucket vs leaky bucket vs sliding window — and (2) the data structure — per-key state, monotonic time, lazy refill vs background refill. As a backend engineer you've used Redis `INCR` + `EXPIRE` for rate-limiting; in this interview you implement it from scratch in-process. The senior bonus is articulating **why token bucket beats leaky bucket** (allows burst, smoother user experience) and when to choose **sliding window log** (precise but memory-hungry) over **token bucket** (approximate but O(1)).

## Concepts involved

### Syntax to lock in
```js
const limiter = new TokenBucket({ capacity: 10, refillRate: 5 /* per second */ });
limiter.allow('user:42');     // true (consumes 1 token)
limiter.allow('user:42');     // true ... until bucket drained
limiter.allow('user:42');     // false (rejected)
```

Core idea:
- Each key gets a bucket with `capacity` tokens.
- Refill at `refillRate` tokens per second.
- Each request consumes one token.
- If the bucket is empty, reject.
- **Lazy refill**: compute tokens to add based on `now - lastRefillTime` at request time. Avoids a background timer.

### Runtime / engine behavior
- `Date.now()` returns wall-clock ms. **`performance.now()`** is monotonic — preferred for rate-limiting because wall clock can jump backward on NTP sync. For interviews, `Date.now()` is fine; mention the upgrade.
- Per-key state: `{ tokens, lastRefillTime }`. Stored in a `Map<key, bucketState>`.
- Refill arithmetic: `tokensToAdd = (now - lastRefillTime) / 1000 * refillRate`. Cap at `capacity`.
- **Fractional tokens**: keep `tokens` as a float so refills don't lose precision. Only require `tokens >= 1` to allow.
- O(1) per `allow` call. Memory grows with unique keys — needs an LRU or TTL eviction for production.

### Edge cases (these are the interview traps)
1. **Token bucket vs leaky bucket** — **token bucket allows bursts** up to `capacity`, then sustains `refillRate`. **Leaky bucket** processes at fixed rate (no bursts) and drops overflow. Token bucket is what most APIs want.
2. **Refill timing** — lazy (compute on request) vs eager (background `setInterval`). Lazy is simpler, O(1) per call, no timer leaks. Always go lazy in an interview.
3. **First request** — initialize bucket to `capacity` (full) so a new user can immediately spend. Some implementations start at 0; state your choice.
4. **`Date.now()` jumping backward** — if `now < lastRefillTime`, treat the delta as 0 (don't add negative tokens). Or use `performance.now()`.
5. **Multi-key memory leak** — `Map<key, bucket>` grows unbounded with new users. Wrap with LRU or evict buckets that have been full for > N seconds.
6. **Multiple cost per request** — `allow(key, cost=1)` lets premium endpoints consume more tokens.
7. **Distributed rate limiting** — out of scope for an in-process interview, but mention Redis `INCR` + `EXPIRE` or `CL.THROTTLE` for the system-design follow-up.
8. **Token vs request units** — clarify with interviewer: "tokens per second" vs "requests per second" — usually 1 token = 1 request.

## Brute force approach
**Fixed window counter**: `counter[key][windowId]++`, reject if > limit. Simple but has the **boundary burst** problem: a user can do `limit` requests in the last ms of window N and another `limit` in the first ms of window N+1, doubling the effective limit briefly. Mention as a known weakness, then move to token bucket.

## Optimal approach
**Token bucket with lazy refill.** Per key, store `{ tokens, lastRefillTime }`. On each request:
1. Compute elapsed time since last refill.
2. Add `elapsed * refillRate` tokens, capped at `capacity`.
3. Update `lastRefillTime = now`.
4. If `tokens >= 1`, decrement and allow. Else reject.

O(1) per request, no background timer, naturally smooths over bursty workloads.

## Solution (JavaScript)

```js
/**
 * Token bucket rate limiter, lazy refill.
 * Use per-API-key or per-IP for incoming requests.
 */
class TokenBucket {
  /**
   * @param {{ capacity: number, refillRate: number }} opts
   * @param opts.capacity   max tokens (= max burst size)
   * @param opts.refillRate tokens added per second
   */
  constructor({ capacity, refillRate }) {
    if (capacity <= 0) throw new Error('capacity must be > 0');
    if (refillRate <= 0) throw new Error('refillRate must be > 0');
    this.capacity = capacity;
    this.refillRate = refillRate;
    this.buckets = new Map();   // key → { tokens, lastRefillTime }
  }

  _refill(bucket, now) {
    const elapsedSec = Math.max(0, (now - bucket.lastRefillTime) / 1000);
    bucket.tokens = Math.min(this.capacity, bucket.tokens + elapsedSec * this.refillRate);
    bucket.lastRefillTime = now;
  }

  /**
   * @param {string} key
   * @param {number} [cost=1]  tokens this request consumes
   * @returns {boolean} true if allowed, false if rate-limited
   */
  allow(key, cost = 1) {
    const now = Date.now();
    let bucket = this.buckets.get(key);
    if (!bucket) {
      bucket = { tokens: this.capacity, lastRefillTime: now };
      this.buckets.set(key, bucket);
    } else {
      this._refill(bucket, now);
    }

    if (bucket.tokens >= cost) {
      bucket.tokens -= cost;
      return true;
    }
    return false;
  }

  /**
   * Optional: return ms until enough tokens are available (useful for Retry-After).
   */
  retryAfterMs(key, cost = 1) {
    const bucket = this.buckets.get(key);
    if (!bucket || bucket.tokens >= cost) return 0;
    const deficit = cost - bucket.tokens;
    return Math.ceil((deficit / this.refillRate) * 1000);
  }
}
```

## Step-by-step dry run

Input:
```js
const limiter = new TokenBucket({ capacity: 3, refillRate: 1 });  // 3-burst, 1/sec sustained
// Simulate calls at specific timestamps (ms).
```

| time (ms) | call                   | refill calc                                   | tokens after | result |
|-----------|------------------------|-----------------------------------------------|--------------|--------|
| 0         | `allow('u1')`          | First call → init to capacity (3).            | 2            | true   |
| 100       | `allow('u1')`          | elapsed 0.1s → +0.1 token, cap 3 → ~2.1. Consume → 1.1. | 1.1          | true   |
| 200       | `allow('u1')`          | elapsed 0.1s → +0.1 → 1.2. Consume → 0.2.     | 0.2          | true   |
| 300       | `allow('u1')`          | elapsed 0.1s → +0.1 → 0.3. Consume needs 1 → no. | 0.3          | **false** |
| 1500      | `allow('u1')`          | elapsed 1.2s → +1.2 → 1.5. Consume → 0.5.     | 0.5          | true   |
| 5000      | `allow('u1')`          | elapsed 3.5s → +3.5 → 4.0, capped at 3.       | 2            | true   |

Key observations from the trace:
- The bucket starts full → first burst of 3 succeeds immediately. That's the **burst tolerance**.
- Continuous fast calls drain the bucket; at t=300 the request is rejected.
- At t=5000 the bucket has had plenty of time to refill, but is **capped at capacity 3** — refill rate doesn't accumulate beyond capacity. That's the "smoothing" property.
- Fractional tokens (e.g., 1.1, 0.5) let the math stay clean. We only allow when `tokens >= cost`.

If we'd used leaky bucket instead, at t=0 we could only do 1 request (rate=1/sec), no burst. Token bucket is friendlier for occasional spikes.

## Important takeaways

**Algorithm comparison — say this in the interview**
- **Token bucket**: bucket fills at `refillRate`; each request consumes 1. **Allows bursts** up to capacity. Most APIs want this.
- **Leaky bucket**: requests added to a queue draining at fixed rate. **Smooths output** to constant rate. No bursts.
- **Fixed window counter**: count requests per N-second window. Simple but has **boundary burst** issue.
- **Sliding window log**: store timestamps of all requests in last N seconds; reject if count > limit. **Precise but memory-heavy** (O(limit) per key).
- **Sliding window counter**: weighted combination of current and previous window. Good compromise.

**Syntax to memorize**
- Per-key state: `{ tokens: number, lastRefillTime: number }`.
- Lazy refill: `tokens = min(capacity, tokens + elapsedSec * refillRate)` on every request.
- Fractional tokens; only allow when `tokens >= cost`.

**Patterns to reuse**
- "Lazy state update on read" appears in: TTL caches (lazy expire), CRDTs, lock-free counters.
- Per-key bucket pattern shows up in: per-user quotas, per-tenant throttling, per-endpoint limits.
- The `retryAfterMs` calculation is what populates the HTTP `Retry-After` header — production-grade detail.

**Common mistakes**
- Using a background `setInterval` to refill → timer leaks per key, breaks at scale, harder to reason about.
- Treating tokens as integers and losing precision on refill → user can't make 1 request per 0.9 seconds even if refill rate allows.
- Forgetting to cap at `capacity` → tokens grow unbounded, defeating the limiter.
- Allowing `Date.now()` clock jumps to add huge token deltas → use `Math.max(0, ...)` or `performance.now()`.
- Not evicting unused buckets → memory leak under high-cardinality keys.

**Related questions**
- Sliding window log / counter — see Variants.
- Distributed rate limiter — Redis `INCR` + Lua script, or Cloudflare's "memcache + token" hybrid.
- Concurrency limiter — bounded queue + semaphore (different problem: limits **in-flight**, not **rate**).
- Promise pool — similar in spirit (bounded concurrency for async tasks).

## Variants

1. **Leaky bucket** — queue requests; drain at constant rate; drop or block on overflow. Better when downstream can't tolerate bursts at all.

2. **Sliding window log** — store last N timestamps per key in a deque; reject if length > limit; pop expired timestamps lazily. **Most accurate**, O(limit) memory per key. Use when precision matters more than memory.

3. **Sliding window counter** — `current_count * (elapsed_in_current_window / window_size) + previous_count * remainder`. Single counter per window, very memory-efficient, ~98% accurate.

4. **Distributed token bucket** — Redis Lua script atomically reads tokens, refills, decrements. Or `CL.THROTTLE` from RedisBloom. System-design follow-up.

5. **Tiered rate limits** — per-second + per-minute + per-day all on same key. N nested buckets; reject if any rejects.

6. **Cost-aware limiter** — `allow(key, cost)` where heavy endpoints cost more tokens. Already supported in the snippet above.

## Revision notes

> **Token bucket rate limiter — 60 second recap**
> - Per key: `{ tokens, lastRefillTime }` in a Map.
> - Lazy refill: on each call, `tokens = min(capacity, tokens + elapsed * rate)`.
> - If `tokens >= cost`, decrement and allow; else reject.
> - **Bursts up to capacity, sustained `refillRate`/sec.**
> - **vs leaky bucket**: leaky = constant drain, no bursts. **vs sliding window**: precise but O(limit) memory.
> - **Trap:** background timer for refill — leaks at scale. Always lazy.
> - **Trap 2:** integer tokens lose precision. Use floats.
> - **Trap 3:** unbounded `Map` of keys — pair with LRU/TTL eviction in production.
