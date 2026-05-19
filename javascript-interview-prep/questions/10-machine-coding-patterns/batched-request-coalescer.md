# Batched Request Coalescer — time-window aggregator

> **Difficulty:** Medium-Senior   |   **Time:** ~20 min   |   **Prereqs:** [dataloader-batch-cache.md](./dataloader-batch-cache.md), [debounce.md](./debounce.md)
>
> **Source:** AWS SDK batching, React `unstable_batchedUpdates`, Kafka `linger.ms`. Stripe, Atlassian, AWS, high-fanout backends.

---

## 1. Problem statement

**Signature**
```ts
class BatchCoalescer<I, R> {
  constructor(opts: { maxWaitMs?: number; maxBatchSize?: number; flushFn: (items: I[]) => Promise<R[]> });
  submit(item: I): Promise<R>;
  drain(): Promise<void>;
}
```

**Input / Output examples**

| Setup (maxWaitMs=10, maxBatchSize=3)                 | Behaviour                                              |
|------------------------------------------------------|---------------------------------------------------------|
| Submit A, B, C at t=0, 1, 2                          | size hit at C → flush([A,B,C]) at t=2                  |
| Submit A at t=0, no more                              | timer fires at t=10 → flush([A])                       |
| `flushFn` returns wrong length                       | reject all in batch with length-mismatch error         |
| `drain()` during shutdown                             | flush whatever's buffered, reject new submits          |
| 100 submits rapidly                                   | size-trigger flushes 3 at a time; final batch via timer|

**Constraints**
- Two flush triggers: **time** (maxWaitMs) OR **size** (maxBatchSize), whichever first.
- `flushFn` output length AND order = input items.
- `drain()` for graceful shutdown.
- Size trigger clears the timer to prevent double-flush.

---

## 2. Plain-English restatement

You have many small requests that you'd rather batch into one downstream call. Buffer items; when buffer reaches `maxBatchSize` OR `maxWaitMs` elapses since first submit, flush them all in one batch. Each submission returns a Promise that resolves with that item's result. This is what Kafka's `linger.ms`, SES bulk send, and SQS batching do — trade a few ms of latency for much better throughput.

---

## 3. Why this matters in interviews

DataLoader batches within one microtask; a **time-window coalescer** extends to up to T ms or N items. Probes throughput/latency tradeoff awareness — a linchpin of distributed-systems design.

---

## 4. Mental model

```
   A bus that leaves when full OR after 10 minutes:

   maxWaitMs=10, maxBatchSize=3

   t=0   submit(A) → buffer=[A], schedule timer at t+10
   t=2   submit(B) → buffer=[A, B]
   t=4   submit(C) → buffer=[A, B, C] → SIZE TRIGGER → flush NOW
                     clear timer
                     flushFn([A, B, C]) → resolves A, B, C
   t=20  submit(D) → buffer=[D], schedule timer at t+30
   t=30  TIMER → flush([D]) → resolves D
```

Two knobs: `maxWaitMs` (worst-case added latency) and `maxBatchSize` (max payload per call). Tune per workload.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why does size-trigger need to clear the timer?
> 2. How does `flushFn` map results back to submitters?
> 3. What goes wrong in graceful shutdown without `drain()`?

---

## 6. Brute force — walked through

### Wrong attempt 1: fire one downstream call per submit
1000 small calls instead of 10 big ones. Inefficient.

### Wrong attempt 2: `queueMicrotask` like DataLoader
Batches in one tick — too tight for a time-window aggregator that wants to wait for more arrivals.

### Wrong attempt 3: forget to clear timer on size flush
Double-flush: size triggers, then 10ms later timer fires on an empty buffer (or worse, on new items).

---

## 7. The unlocking insight

> **Buffer items; schedule timer on first submit. Flush when buffer hits `maxBatchSize` OR timer fires. Each submit returns a Promise; on flush, `flushFn(items)` returns aligned results. Size trigger clears timer to prevent double-flush. `drain()` flushes pending on shutdown.**

Three properties:

1. **Two triggers (size OR time)** — either wins.
2. **Output alignment** — `flushFn` returns array in input order.
3. **`drain()` for shutdown** — flushes pending; rejects new submits.

---

## 8. Solution (annotated)

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
      this.buffer.push({ item, resolve, reject });                    // step 1: buffer
      if (this.buffer.length >= this.maxBatchSize) {
        this._flush();                                                 // step 2a: size trigger
      } else if (!this.timer) {
        this.timer = setTimeout(() => this._flush(), this.maxWaitMs);  // step 2b: time trigger
      }
    });
  }

  async _flush() {
    if (this.timer) { clearTimeout(this.timer); this.timer = null; }  // step 3: clear timer
    const batch = this.buffer.splice(0, this.buffer.length);
    if (batch.length === 0) return;

    try {
      const results = await this.flushFn(batch.map((b) => b.item));
      if (results.length !== batch.length) {
        throw new Error('flushFn length mismatch');
      }
      batch.forEach((b, i) =>                                          // step 4: route by index
        results[i] instanceof Error ? b.reject(results[i]) : b.resolve(results[i]),
      );
    } catch (err) {
      batch.forEach((b) => b.reject(err));                              // batch-level error
    }
  }

  async drain() {                                                       // step 5: graceful shutdown
    this.draining = true;
    await this._flush();
  }
}
```

**Try it yourself**

```js
const emailCoalescer = new BatchCoalescer({
  maxWaitMs: 100,
  maxBatchSize: 50,
  flushFn: async (emails) => ses.sendBulk({ recipients: emails }),
});

await Promise.all([
  emailCoalescer.submit({ to: 'a@x.com', body: 'hi' }),
  emailCoalescer.submit({ to: 'b@x.com', body: 'hi' }),
]);
// Both sent in one SES bulk call after ~100ms (or sooner if 50 queued).

// Shutdown
process.on('SIGTERM', async () => {
  await emailCoalescer.drain();
  process.exit(0);
});
```

---

## 9. Step-by-step dry run

```
maxWaitMs=10, maxBatchSize=3:

t=0   submit(A) → buffer=[A], timer=t+10
t=1   submit(B) → buffer=[A, B]
t=2   submit(C) → buffer=[A, B, C] → size===max → _flush() NOW
                  clear timer
                  flushFn([A,B,C]) → resolves all three

t=20  submit(D) → buffer=[D], timer=t+30

t=30  TIMER → _flush()
              flushFn([D]) → resolves D

Two flushes total: one size-triggered (3 items), one time-triggered (1 item).

Failure mode:
  submit(E) → buffer=[E], timer=t+10
  t=10 timer → flushFn throws
              batch.forEach(b => b.reject(err)) → E's promise rejects
```

---

## 10. Common confusion + traps

1. **Forget to clear timer on size flush** — double-flush.
2. **`flushFn` returns wrong-length array** — caller mapping breaks; throw loudly.
3. **`queueMicrotask` instead of `setTimeout`** — too tight a window; loses batching opportunity.
4. **Drain not implemented** — shutdown loses in-flight items.
5. **Larger batch = always better** — wrong; bigger batch = more latency. Tune per SLO.
6. **Per-item error semantics unclear** — pick: batch-level fail-all vs per-item `Error` slot in output.
7. **`setTimeout` drift** — over hours, batches may skew; re-schedule from first submit, not previous flush.

---

## 11. Senior follow-ups & variants

### Variant 1 — Microtask coalescer (DataLoader-style)
`queueMicrotask` instead of `setTimeout`. Single-tick batching.

### Variant 2 — Per-key batching
Bucket items by key (e.g., shard ID); flush each bucket independently.

### Variant 3 — Backpressure-aware
Bound buffer size; reject `submit` when full instead of unbounded growth.

### Variant 4 — Adaptive `maxWaitMs`
Shrink window under heavy load; expand when idle.

### Variant 5 — Async iterable input
Flush whenever source yields slower than timer.

### Variant 6 — Pair with retry / circuit breaker
Wrap `flushFn` so batch failure → retry batch; circuit breaker for downstream protection.

---

## 12. How to think aloud

> "Buffer + two triggers: size or time, whichever first. Schedule timer on first submit; size trigger clears the timer to prevent double-flush. Each `submit` returns a promise; `_flush` calls `flushFn(items)` and routes results back by index (output length+order must match). `drain()` for graceful shutdown — flush whatever's buffered, reject new submits. Trade-off: bigger window = better throughput, worse latency. 10ms for autocomplete fanout, 200ms for SES batch, 1s for analytics. Trap: forget to clear timer on size trigger (double-flush); no drain (lose items on shutdown); larger-is-better fallacy."

---

## 13. 60-second revision

> - **Buffer + two triggers** (size OR time).
> - **Size trigger clears timer** to prevent double-flush.
> - **`flushFn` output:** same length AND order as input items.
> - **`drain()`** mandatory for graceful shutdown.
> - **Knobs:** `maxWaitMs` (latency cap), `maxBatchSize` (payload cap).
> - **Per-item error:** `Error` in output slot. **Batch error:** reject all.
> - **Variants:** microtask (DataLoader), per-key, backpressure, adaptive.
> - **Trap:** missed timer clear; bad alignment; no drain; "bigger always better."

---

**Related:** [dataloader-batch-cache.md](./dataloader-batch-cache.md) · [debounce.md](./debounce.md) · [throttle.md](./throttle.md) · [request-deduplication.md](./request-deduplication.md)

**Concept primer:** [`concepts/event-loop.md`](../../concepts/event-loop.md)
