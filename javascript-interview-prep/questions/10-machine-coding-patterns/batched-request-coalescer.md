# Batched Request Coalescer (Time-Window Aggregator)

## Source / Origin
- AWS SDK's `aws-sdk-v3` batching; React's `unstable_batchedUpdates`; GraphQL DataLoader; Kafka's `linger.ms`.
- Asked at: Stripe, Atlassian, AWS, anywhere with high-fanout downstream calls.
- Concept reference: `concepts/event-loop.md`, sibling `dataloader-batch-cache.md`.

## Why this question matters in interviews
DataLoader batches within a *single microtask tick* (same event-loop turn). A *time-window coalescer* extends that: collect requests for up to `T` ms or `N` items, whichever comes first, then dispatch one batch. This is the pattern behind Kafka's `linger.ms`, SQS batch sending, Slack's typing-indicator aggregation, observability flush windows. Senior bar: you can articulate the latency-vs-throughput tradeoff this knob represents.

## Concepts involved

### Syntax to lock in
```js
class BatchCoalescer {
  constructor({ maxWaitMs = 10, maxBatchSize = 100, flushFn }) {
    this.maxWaitMs = maxWaitMs;
    this.maxBatchSize = maxBatchSize;
    this.flushFn = flushFn;          // async (items: T[]) => R[]  (output aligned to input)
    this.buffer = [];
    this.timer = null;
  }

  submit(item) {
    return new Promise((resolve, reject) => {
      this.buffer.push({ item, resolve, reject });
      if (this.buffer.length >= this.maxBatchSize) {
        this._flush();
      } else if (!this.timer) {
        this.timer = setTimeout(() => this._flush(), this.maxWaitMs);
      }
    });
  }

  async _flush() {
    if (this.timer) { clearTimeout(this.timer); this.timer = null; }
    const batch = this.buffer.splice(0, this.buffer.length);
    if (batch.length === 0) return;
    try {
      const results = await this.flushFn(batch.map(b => b.item));
      if (results.length !== batch.length) throw new Error('flushFn length mismatch');
      batch.forEach((b, i) => results[i] instanceof Error ? b.reject(results[i]) : b.resolve(results[i]));
    } catch (err) {
      batch.forEach(b => b.reject(err));
    }
  }
}
```

### Edge cases / interview traps
1. **Two flush triggers; either fires once.** Size-trigger short-circuits the timer; the size path must clear the timer. The timer path must avoid double-flush if a concurrent size-trigger fired between scheduling and firing.
2. **Output alignment.** Like DataLoader, `flushFn` returns array in same order; throw on length mismatch.
3. **Last-item starvation.** If the timer hasn't fired and the process is shutting down, in-flight items are lost. Expose `drain()` for graceful shutdown.
4. **Backpressure.** If `flushFn` is slow and submissions keep arriving, you build up unbounded latency. Decide: drop, reject, or block.
5. **maxWaitMs = 0 vs microtask.** A timer with `0ms` waits until next macrotask — strictly later than `queueMicrotask`. Use `queueMicrotask` for DataLoader-style same-tick batching; use timer for time-window batching.
6. **Per-batch error vs per-item error.** Decide and document.
7. **Drift over many cycles.** `setTimeout` is not monotonic-precise; over hours, batches may skew. Re-schedule from the *first* submit, not from the previous flush time.

## Mental Model

A **bus that leaves either when full or after 10 minutes**:

```
   t=0   submit(A) → buffer=[A], scheduled flush at t=10
   t=2   submit(B) → buffer=[A,B]
   t=4   submit(C) → buffer=[A,B,C]
   t=10  TIMER → flush([A,B,C])   ← time trigger wins
   
   Alternate scenario:
   t=0   submit(A)  scheduled flush at t=10
   t=1   submit(B), submit(C), ... submit(100)
                 → buffer hits maxBatchSize → flush NOW
                 → clear timer; flushFn([A..100th])
```

Two knobs: `maxWaitMs` (max latency you'll add) and `maxBatchSize` (max payload per call). Tune them per workload.

## Why interviewers care

- **Throughput/latency tradeoff awareness.** A linchpin of distributed-systems design.
- **Real-world parallels.** Kafka `linger.ms`, SQS `WaitTimeSeconds`, SES batch send. Senior candidates recognize all of these.
- **Lifecycle reasoning.** Graceful drain, error semantics, output alignment.

## Common beginner confusion

- **"Just use DataLoader."** DataLoader batches in one tick; if you want time-window batching, you need a timer-driven coalescer.
- **"`setTimeout(0)` is the same as `queueMicrotask`."** No — different priority queue; you'll batch across more interleaving than you want.
- **"Drain isn't needed."** It is. Shutdown loses in-flight items without it.
- **"Larger batch = always better."** No — larger batch = more latency. The sweet spot depends on downstream limits and SLO.

## Brute force approach

```js
// fire one downstream call per submission
async function submit(item) {
  return downstream.call([item]);     // 1000 small calls instead of 10 big ones
}
```

## Optimal approach

Buffer in a queue. Schedule a timer on first submit. Flush when either the timer fires or `buffer.length >= maxBatchSize`. Use `Promise` per submission to deliver results back to callers in original order.

## Solution (JavaScript)

```js
class BatchCoalescer {
  constructor({ maxWaitMs = 10, maxBatchSize = 100, flushFn }) {
    this.maxWaitMs = maxWaitMs;
    this.maxBatchSize = maxBatchSize;
    this.flushFn = flushFn;
    this.buffer = [];
    this.timer = null;
    this.draining = false;
  }
  submit(item) {
    if (this.draining) return Promise.reject(new Error('Coalescer draining'));
    return new Promise((resolve, reject) => {
      this.buffer.push({ item, resolve, reject });
      if (this.buffer.length >= this.maxBatchSize) this._flush();
      else if (!this.timer) this.timer = setTimeout(() => this._flush(), this.maxWaitMs);
    });
  }
  async _flush() {
    if (this.timer) { clearTimeout(this.timer); this.timer = null; }
    const batch = this.buffer.splice(0, this.buffer.length);
    if (batch.length === 0) return;
    try {
      const results = await this.flushFn(batch.map(b => b.item));
      if (results.length !== batch.length) throw new Error('flushFn length mismatch');
      batch.forEach((b, i) => results[i] instanceof Error ? b.reject(results[i]) : b.resolve(results[i]));
    } catch (err) {
      batch.forEach(b => b.reject(err));
    }
  }
  async drain() {
    this.draining = true;
    await this._flush();
  }
}

// Usage: batch SES emails — up to 50 recipients or 100ms latency
const emailCoalescer = new BatchCoalescer({
  maxWaitMs: 100,
  maxBatchSize: 50,
  flushFn: (emails) => ses.sendBulk({ recipients: emails }),
});
await emailCoalescer.submit({ to: 'a@x.com', body: 'hi' });
```

## Step-by-step dry run

`maxWaitMs=10, maxBatchSize=3`, three rapid submits followed by a lone one:

```
t=0   submit(A) → buffer=[A]; timer=t+10
t=1   submit(B) → buffer=[A,B]
t=2   submit(C) → buffer=[A,B,C] → size==3 → _flush() NOW
                 clear timer; flushFn([A,B,C]); resolve A, B, C
t=20  submit(D) → buffer=[D]; timer=t+30
t=30  TIMER → _flush() → flushFn([D]); resolve D
```

Two flushes: one size-triggered with 3 items, one time-triggered with 1.

## How to think aloud in the interview

> "Time-window batching: buffer items, dispatch when either `maxBatchSize` is hit or `maxWaitMs` elapsed since first submit. Each submit returns a Promise; on flush, I call `flushFn(items)` and route results back by index. Size-trigger clears the timer. I'd expose `drain()` for graceful shutdown — flush pending immediately. Tradeoffs: bigger window = better throughput, worse latency. I'd pick 10ms for an autocomplete fanout, 200ms for SES batches, 1s for analytics ingestion."

## Important takeaways

- **Two triggers** (time OR size), either wins.
- **Output alignment.** `flushFn` returns array in input order.
- **`drain()` is mandatory** for non-toy use.
- **Knobs translate to SLO.** `maxWaitMs` is the worst-case extra latency you commit to.
- **Pair with retry/circuit-breaker** around `flushFn` — batches can fail wholesale.

## Variants

- **Microtask coalescer** (`queueMicrotask`-based) — DataLoader. Use when "same tick" is the right window.
- **Per-key batching** — bucket items by a key (e.g., shard) and flush each bucket independently.
- **Backpressure-aware** — bound buffer size; reject `submit` when full.
- **Adaptive `maxWaitMs`** — shrink window under heavy load, expand when idle.
- **Async iterable input** — flush whenever the source yields slower than the timer.

## Revision notes

```
BatchCoalescer({maxWaitMs, maxBatchSize, flushFn}):
  submit(item): push to buffer; size==max → flush; else schedule timer
  _flush(): clear timer; batch=splice; flushFn(items); route results by index
  drain(): set draining=true; flush remaining
  
  two triggers (size, time); either wins
  output aligned to input
  drain on shutdown
  tradeoff: latency vs throughput
  variants: per-key, adaptive, microtask (DataLoader), backpressure
```
