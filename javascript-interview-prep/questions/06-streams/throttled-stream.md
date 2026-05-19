# Throttled stream — rate-limited pipeline

> **Difficulty:** Medium   |   **Time:** ~10 min   |   **Prereqs:** [web-streams-transform.md](./web-streams-transform.md), [`10-machine-coding-patterns/rate-limiter-token-bucket.md`](../10-machine-coding-patterns/rate-limiter-token-bucket.md)
>
> **Source:** Scraping, API ingestion, log shipping. Cloudflare, Stripe, Razorpay.

---

## 1. Problem statement

Stream of items needs to be paced at most N per second before downstream consumer.

**Verification examples**

```js
function throttleStream(intervalMs) {
  let last = 0;
  return new TransformStream({
    async transform(chunk, ctl) {
      const now = Date.now();
      const wait = Math.max(0, last + intervalMs - now);
      if (wait > 0) await new Promise((r) => setTimeout(r, wait));
      last = Date.now();
      ctl.enqueue(chunk);
    },
  });
}

const throttled = source.pipeThrough(throttleStream(100));               // ≤ 10/sec
for await (const ev of throttled) await sendDownstream(ev);
```

**Constraints**
- `async transform` awaits delay before enqueuing.
- Pipeline waits for transform — natural throttling.
- Fixed-interval vs token-bucket — pick policy.
- Thread AbortSignal for cancellation.

---

## 2. Plain-English restatement

Insert a Transform that awaits a delay before each chunk passes through. Pipeline waits for the await; producer naturally throttles.

---

## 3. Why this matters in interviews

Practical: scrape with 100 req/sec limit; log shipper with downstream cap. Tests async transform + composition.

---

## 4. Mental model

```
   Fixed-interval throttle:
     last = 0
     transform(chunk):
       wait = max(0, last + intervalMs - now)
       await delay(wait)
       last = now (after delay)
       enqueue(chunk)
   
   Token bucket:
     bucket = N tokens, refills at R/sec.
     transform(chunk):
       wait until tokens > 0.
       tokens--.
       enqueue.
   
   Fixed-interval: strict pacing, no bursts.
   Token bucket: allows bursts up to N, then steady refill.
   
   Backpressure FREE:
     pipeline awaits async transform.
     producer pauses while transform delays.
     no manual coordination needed.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why does `async transform` naturally throttle?
> 2. Fixed-interval vs token bucket?
> 3. How to abort mid-delay?

---

## 6. Brute force — walked through

### Wrong attempt 1: `setInterval` to emit
Drifts; doesn't tie to chunks.

### Wrong attempt 2: synchronous throttle
Blocks event loop.

### Wrong attempt 3: drop excess chunks
Loses data; throttle should slow, not drop.

---

## 7. The unlocking insight

> **`async transform` awaits delay before enqueue. Pipeline waits → producer throttles naturally. Fixed-interval or token-bucket policy.**

Three properties:

1. **Async transform** awaits.
2. **Pipeline waits** for it → throttle.
3. **Pick policy** — fixed vs burst-tolerant.

---

## 8. Solution (annotated)

```js
function throttleStream(intervalMs) {
  let last = 0;
  return new TransformStream({
    async transform(chunk, ctl) {                                        // step 1: async transform
      const now = Date.now();
      const wait = Math.max(0, last + intervalMs - now);
      if (wait > 0) await new Promise((r) => setTimeout(r, wait));      // step 2: delay
      last = Date.now();                                                 // step 3: after delay (avoid drift)
      ctl.enqueue(chunk);                                                // step 4: enqueue
    },
  });
}

// Token bucket variant (allows bursts)
function tokenBucketStream({ capacity = 5, refillPerSec = 10 } = {}) {
  let tokens = capacity;
  let lastRefill = Date.now();
  return new TransformStream({
    async transform(chunk, ctl) {
      while (true) {
        const now = Date.now();
        const elapsed = (now - lastRefill) / 1000;
        tokens = Math.min(capacity, tokens + elapsed * refillPerSec);
        lastRefill = now;
        if (tokens >= 1) {
          tokens -= 1;
          ctl.enqueue(chunk);
          return;
        }
        const wait = ((1 - tokens) / refillPerSec) * 1000;
        await new Promise((r) => setTimeout(r, wait));
      }
    },
  });
}

// With AbortSignal
function abortableThrottle(intervalMs, signal) {
  let last = 0;
  return new TransformStream({
    async transform(chunk, ctl) {
      const wait = Math.max(0, last + intervalMs - Date.now());
      if (wait > 0) {
        await new Promise((res, rej) => {
          const t = setTimeout(res, wait);
          signal?.addEventListener('abort', () => {
            clearTimeout(t);
            rej(new Error('Aborted'));
          }, { once: true });
        });
      }
      last = Date.now();
      ctl.enqueue(chunk);
    },
  });
}
```

**Try it yourself**

```js
// Scrape with rate limit
const urls = readUrls();
const requests = urls.pipeThrough(throttleStream(100));                  // 10/sec

for await (const url of requests) {
  const res = await fetch(url);
  await processResponse(res);
}

// Combine with concurrency
const results = urls
  .pipeThrough(throttleStream(100))                                       // 10/sec emit
  .pipeThrough(asyncMap(fetch, { concurrency: 5 }));                      // 5 concurrent

// Node.js Transform equivalent
const { Transform } = require('node:stream');
class NodeThrottle extends Transform {
  constructor(intervalMs) {
    super({ objectMode: true });
    this.intervalMs = intervalMs;
    this.last = 0;
  }
  async _transform(chunk, enc, cb) {
    const wait = Math.max(0, this.last + this.intervalMs - Date.now());
    if (wait > 0) await new Promise((r) => setTimeout(r, wait));
    this.last = Date.now();
    this.push(chunk);
    cb();
  }
}
```

---

## 9. Step-by-step dry run

```
throttleStream(100ms), 5 chunks arrive immediately:

t=0    chunk1 arrives → transform.
       wait = max(0, 0 + 100 - 0) = 0.
       await (no delay). last=0. enqueue chunk1.
t=0    chunk2 arrives → transform.
       wait = max(0, 0 + 100 - 0) = 100.
       await 100ms. PAUSE pipeline (producer paused).
t=100  resume. last=100. enqueue chunk2.
t=100  chunk3 arrives → transform.
       wait = max(0, 100 + 100 - 100) = 100.
       await 100ms.
t=200  last=200. enqueue chunk3.
t=200  chunk4 → wait 100ms.
t=300  enqueue chunk4.
t=300  chunk5 → wait 100ms.
t=400  enqueue chunk5.

5 chunks over 400ms = exactly 1 per 100ms after first.

Token bucket variant:
  capacity 5, refill 10/sec.
  Burst: first 5 chunks pass instantly (tokens drain).
  6th chunk waits for refill (100ms for 1 token).
  Continues at steady rate.
```

---

## 10. Common confusion + traps

1. **`setInterval` instead** — drifts; doesn't tie to data.
2. **Drop chunks** — should slow, not drop.
3. **`last = now` before delay** — drift accumulates.
4. **No AbortSignal** — can't cancel mid-delay.
5. **Throttle producer instead of transform** — same effect; transform is cleaner.
6. **Mix sync/async transforms** — keep async for await semantics.
7. **`signal.aborted` only at start** — must reject mid-delay too.

---

## 11. Senior follow-ups & variants

### Variant 1 — Token bucket
Allows bursts up to capacity, then steady refill.

### Variant 2 — Per-key throttle
Map<key, lastTime> for different keys at independent rates.

### Variant 3 — Async map with concurrency
Throttle + parallel — best of both.

### Variant 4 — Drop policy
Burst-with-drop instead of delay (lossy).

### Variant 5 — Node Transform equivalent
`async _transform` + `cb()` after delay.

---

## 12. How to think aloud

> "Throttle stream: insert a TransformStream whose `async transform` awaits a delay before enqueuing. Pipeline naturally waits for the async transform → producer pauses while we sleep → no manual coordination needed. Fixed-interval (strict pacing): `wait = max(0, last + intervalMs - now)`. Token bucket (allows bursts): maintain `tokens`, refill at rate, consume 1 per chunk, wait for refill when 0. Set `last = Date.now()` AFTER the delay to avoid drift accumulation. Thread AbortSignal: wrap the `setTimeout` with abort listener that `clearTimeout` and rejects. Node `Transform` version: `async _transform(chunk, enc, cb)` + `cb()` after delay. Trap: setInterval (drifts; loses chunk binding); dropping chunks (should slow, not lose); `last = now` before delay (drift); ignoring signal."

---

## 13. 60-second revision

> - **`async transform`** awaits delay → pipeline waits → throttle.
> - **Fixed-interval:** `wait = max(0, last + interval - now)`.
> - **Token bucket:** capacity + refill; allows bursts.
> - **`last = Date.now()` AFTER delay** — avoid drift.
> - **AbortSignal** wraps setTimeout for cancel.
> - **Node Transform:** `async _transform` + `cb()`.
> - **Combine with concurrency** for parallel-but-paced.
> - **Trap:** setInterval; drop chunks; pre-delay timestamp; ignore signal.

---

**Related:** [web-streams-transform.md](./web-streams-transform.md) · [backpressure-demo.md](./backpressure-demo.md) · [`10-machine-coding-patterns/rate-limiter-token-bucket.md`](../10-machine-coding-patterns/rate-limiter-token-bucket.md) · [`10-machine-coding-patterns/throttle.md`](../10-machine-coding-patterns/throttle.md)

**Concept primer:** [`concepts/streams.md`](../../concepts/streams.md)
