# Throttled Stream (Rate-Limited Pipeline)

## Source / Origin
- "Cap the throughput" pattern; common in scraping, API ingestion, log shipping.
- Asked at: Cloudflare, Stripe, Razorpay.
- Concept reference: `concepts/streams.md`, sibling `web-streams-transform.md`, `10-machine-coding-patterns/rate-limiter-token-bucket.md`.

## Why this question matters in interviews
"I'm reading 10k items but the downstream API allows 100/sec — slow me down." A throttled stream sits in the middle and gates chunks. Senior bar: you implement via async transform (await delay before enqueue), distinguish fixed-interval from token-bucket throttling, and let backpressure handle the rest.

## Concepts involved

```js
function throttleStream(intervalMs) {
  let last = 0;
  return new TransformStream({
    async transform(chunk, ctl) {
      const now = Date.now();
      const wait = Math.max(0, last + intervalMs - now);
      if (wait > 0) await new Promise(r => setTimeout(r, wait));
      last = Date.now();
      ctl.enqueue(chunk);
    },
  });
}

// Use
const source = ndjsonStream('/events');
const throttled = source.pipeThrough(throttleStream(100));   // ≤ 10/sec
for await (const ev of throttled) await sendDownstream(ev);
```

### Edge cases / traps
1. **Backpressure handles consumer slowness automatically.** Throttle is for *upstream* pacing.
2. **`async transform`** — pipeline waits for it; that's exactly the throttling mechanism.
3. **Burst**: this throttle is strict per-interval; token-bucket allows bursts up to N then refills.
4. **`signal`** — wire AbortController through to bail out of delay.
5. **Drift over many chunks** — base `last = Date.now()` after delay so we don't accumulate drift.
6. **`controller.desiredSize`** can also be honored for backpressure-aware enqueue.

## Mental Model

```
   source ─chunks→ throttle ─[delay]→ downstream
                    │
                    └ await sleep(intervalMs - elapsed)
                      before enqueue
```

Each chunk waits at least `intervalMs` after the previous one was emitted.

## Solution

```js
function throttleByInterval(intervalMs) {
  let lastEmit = 0;
  return new TransformStream({
    async transform(chunk, ctl) {
      const now = Date.now();
      const wait = lastEmit + intervalMs - now;
      if (wait > 0) await new Promise(r => setTimeout(r, wait));
      lastEmit = Date.now();
      ctl.enqueue(chunk);
    },
  });
}

// Token-bucket variant (allows bursts up to capacity)
function tokenBucketStream({ capacity, refillPerSec }) {
  let tokens = capacity;
  let lastRefill = Date.now();
  return new TransformStream({
    async transform(chunk, ctl) {
      while (true) {
        const now = Date.now();
        tokens = Math.min(capacity, tokens + ((now - lastRefill) / 1000) * refillPerSec);
        lastRefill = now;
        if (tokens >= 1) { tokens -= 1; break; }
        await new Promise(r => setTimeout(r, Math.max(10, 1000 / refillPerSec)));
      }
      ctl.enqueue(chunk);
    },
  });
}

// Usage: shipping logs to a 100/s API
const shipped = logStream
  .pipeThrough(tokenBucketStream({ capacity: 100, refillPerSec: 100 }));
for await (const log of shipped) await api.send(log);

// With cancel
const ac = new AbortController();
setTimeout(() => ac.abort(), 60_000);
try {
  for await (const x of throttled) { if (ac.signal.aborted) break; await downstream(x); }
} catch (e) { /* ... */ }
```

## Dry run

`intervalMs=100`, three items arriving immediately:

```
t=0    chunk1 → transform; wait=0; enqueue; lastEmit=0
t=0    chunk2 → transform; wait=100; await 100ms
t=100  enqueue chunk2; lastEmit=100
t=100  chunk3 → wait=100; await 100ms
t=200  enqueue chunk3; lastEmit=200
```

Effective rate: 10/sec. Source paces itself because pipeline awaits in transform (backpressure).

## How to think aloud

> "Async transform in a TransformStream is itself a backpressure mechanism — the pipeline awaits before pulling the next chunk. So a throttle is just `await sleep(intervalMs - elapsed)` before enqueue. For burst-friendly throttling, token bucket — refill N/sec, consume 1 per chunk, await if empty. Wire AbortSignal in for cancel. The source naturally slows down because the pipeline is gating."

## Important takeaways

- **Async `transform` + sleep** = throttle.
- **Backpressure does the rest** — upstream slows automatically.
- **Fixed-interval** = strict pacing; **token bucket** = bursty.
- **`lastEmit = Date.now()` after the wait** to avoid drift.
- **AbortSignal** in sleep for cancellation.

## Variants

- **Throttle by byte count** — track bytes/sec not chunks/sec.
- **Adaptive throttle** — slow on 429, speed up on success.
- **Per-key throttle** — fan-out by key, throttle each lane.
- **Leaky bucket** — smooths bursts to a constant rate.

## Revision notes

```
throttleByInterval(ms):
  async transform(chunk, ctl):
    wait = lastEmit + ms - now
    if wait > 0: await sleep(wait)
    lastEmit = now
    ctl.enqueue(chunk)

tokenBucketStream({capacity, refillPerSec}):
  refill on demand; consume token; sleep if empty

USES:
  - rate-limited API ingestion
  - log shipping
  - polite scraping

BACKPRESSURE: pipeline awaits async transform → source slows automatically
```
