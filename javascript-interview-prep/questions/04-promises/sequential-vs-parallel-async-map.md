# `asyncMap` — sequential vs parallel vs bounded-parallel

> **Difficulty:** Easy-Medium   |   **Time:** ~10 min   |   **Prereqs:** [promise-all-polyfill.md](./promise-all-polyfill.md), [promise-pool.md](./promise-pool.md)
>
> **Source:** Bread-and-butter senior backend interview question.

---

## 1. Problem statement

**Signatures**
```ts
function asyncMapSeq<T, U>(arr: T[], fn: (x: T, i: number) => Promise<U>): Promise<U[]>;
function asyncMapPar<T, U>(arr: T[], fn: (x: T, i: number) => Promise<U>): Promise<U[]>;
function asyncMapBounded<T, U>(arr: T[], fn: (x: T, i: number) => Promise<U>, concurrency: number): Promise<U[]>;
```

**Input / Output examples**

| Setup                                                    | Sequential time | Parallel time | Bounded(2) time |
|----------------------------------------------------------|------------------|---------------|------------------|
| Three items, latencies [100, 50, 200]                    | ~350 ms (Σ)      | ~200 ms (max) | ~250 ms          |
| `forEach(async fn)`                                       | **doesn't await — returns undefined** | n/a | n/a |
| Order of results                                          | input order      | input order   | input order      |
| One rejects                                              | aborts at throw  | fail-fast     | fail-fast        |

**Constraints**
- All three preserve **input order** in results.
- Sequential: total time = sum of latencies.
- Parallel: total time = max latency; memory = O(N) pending promises.
- Bounded: total time bounded by `ceil(N/k) × per-item-max`; memory = O(k).
- `forEach(async fn)` is **broken** — `forEach` doesn't await.

---

## 2. Plain-English restatement

You have an array of items and an async function to apply to each. There are three valid implementations: **sequential** (wait for each before starting the next), **parallel** (fire all at once, await all), and **bounded parallel** (fire `k` at a time). The interview is testing which one you reach for by default — and whether you know that `forEach(async fn)` is broken.

---

## 3. Why this matters in interviews

This question is a **trap** that interviewers use to separate juniors from seniors. Juniors write `arr.forEach(async ...)` and don't notice it doesn't await. Mids write `for (const x of arr) await fn(x)` everywhere — correct, but unnecessarily slow. Seniors **pick the right pattern based on constraints**: sequential when calls have ordering or rate-limit dependencies, parallel when they're independent, bounded-parallel when memory or downstream load is a concern. The discussion of *which* to use is more important than the code itself.

---

## 4. Mental model

```
   Sequential — wait for each before next
   ──────────────────────────────────────
   t=0 ▶ fn(a) ─── awaits ────▶ result a
                                   ▶ fn(b) ─── awaits ──▶ result b
                                                            ▶ fn(c)
   total time = Σ latencies

   Parallel — fire all, await all
   ──────────────────────────────
   t=0 ▶ fn(a), fn(b), fn(c)   (all running)
                                    └▶ Promise.all
   total time = max(latency)
   memory: O(N) pending promises

   Bounded parallel — k workers, shared cursor
   ───────────────────────────────────────────
   t=0 ▶ worker 1: fn(a) → fn(c) → ...
        ▶ worker 2: fn(b) → fn(d) → ...
   total time ≈ ceil(N/k) × per-item
   memory: O(k)
```

**Default mental discipline:** parallel when items are independent; sequential when ordering matters or downstream is rate-limited; bounded when N is large.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. `await arr.forEach(async (x) => await fn(x))` — does this wait for the async work? What does it return?
> 2. If your downstream API allows 5 concurrent connections, what shape do you reach for?
> 3. With latencies `[100, 50, 200]`, what's the wall time for each variant?

---

## 6. Brute force — walked through

### Wrong attempt 1: `arr.forEach(async fn)`

```js
async function asyncMap(arr, fn) {
  const out = [];
  arr.forEach(async (item) => {
    out.push(await fn(item));    // BUG: forEach doesn't await
  });
  return out;                    // BUG: returns empty array immediately
}
```

**Classic junior bug.** `forEach` doesn't await its callbacks; the outer function returns *before* any of them complete. `out` is empty (or partially filled, depending on timing). Even if you call `forEach((x, i) => out[i] = await fn(x))`, you've created N detached promises with no synchronization. Use `for...of` or `Promise.all + .map`.

### Wrong attempt 2: sequential when independent

```js
async function slowMap(arr, fn) {
  const out = [];
  for (const x of arr) out.push(await fn(x));
  return out;
}

const fetched = await slowMap(urls, fetch);   // 10 URLs × 200ms = 2 SECONDS total
```

Works, but **serializes independent work**. If `urls.length === 10` and each fetch is 200ms, you wait 2 seconds. With parallel, it's 200ms. Junior signal.

### Wrong attempt 3: unbounded parallel on huge arrays

```js
await Promise.all(million_items.map(fetch));   // BUG: 1M concurrent fetches
```

Exhausts the HTTP connection pool, trips API rate limits, OOMs from holding 1M pending promises. Bound the concurrency.

---

## 7. The unlocking insight

> **Pick by constraint: sequential when order matters or downstream is rate-limited; parallel when items are independent and N is bounded; bounded-parallel when N is large or downstream load is a concern. All three preserve input order via indexed write.**

The three shapes:

**Sequential (`for...of` + `await`)**
- Use when: order of side effects matters, or each call depends on the previous result, or downstream can't handle parallel.
- Pattern: `for (let i = 0; i < arr.length; i++) out.push(await fn(arr[i], i));`.
- Time: Σ latencies.
- Memory: O(1) extra.

**Parallel (`Promise.all + arr.map`)**
- Use when: items are independent, N is small, and you accept fail-fast.
- Pattern: `await Promise.all(arr.map((x, i) => fn(x, i)));`.
- Time: max latency.
- Memory: O(N) pending promises.

**Bounded parallel (k workers, shared cursor)**
- Use when: N is large or downstream has concurrency limits.
- Pattern: `k` worker coroutines sharing a cursor. See [promise-pool.md](./promise-pool.md) for the full breakdown.
- Time: bounded by `ceil(N/k) × per-item-max`.
- Memory: O(k).

The key mental discipline: **parallel by default for independent work**, but reach for bounded when downstream load matters.

---

## 8. Solution (annotated)

```js
// Sequential — order of side effects guaranteed
async function asyncMapSeq(arr, fn) {
  const out = [];
  for (let i = 0; i < arr.length; i++) {
    out.push(await fn(arr[i], i));
  }
  return out;
}

// Parallel — fastest for independent work, watch memory
async function asyncMapPar(arr, fn) {
  return Promise.all(arr.map((item, i) => fn(item, i)));
}

// Bounded parallel — k workers + shared cursor
async function asyncMapBounded(arr, fn, concurrency = 5) {
  const results = new Array(arr.length);
  let cursor = 0;

  async function worker() {
    while (cursor < arr.length) {
      const i = cursor++;                  // capture index BEFORE await
      results[i] = await fn(arr[i], i);
    }
  }

  const workers = Array.from(
    { length: Math.min(concurrency, arr.length) },
    worker
  );
  await Promise.all(workers);
  return results;
}
```

**Try it yourself**

```js
const sleep = (ms, v) => new Promise((r) => setTimeout(() => r(v), ms));
const fn = (ms) => sleep(ms, ms);
const items = [100, 50, 200];

console.time('seq');
await asyncMapSeq(items, fn);
console.timeEnd('seq');         // ~350ms (sum)

console.time('par');
await asyncMapPar(items, fn);
console.timeEnd('par');         // ~200ms (max)

console.time('bounded');
await asyncMapBounded(items, fn, 2);
console.timeEnd('bounded');     // ~250ms
```

---

## 9. Step-by-step dry run

Items: `[100, 50, 200]` (ms latencies). `fn = (ms) => sleep(ms, ms)`.

**Sequential trace:**

| Time | Event                                       | `out`           |
|------|---------------------------------------------|------------------|
| 0    | iter 0: `await fn(100)` starts              | `[]`             |
| 100  | result `100`; `out=[100]`; iter 1: `await fn(50)` starts | `[100]` |
| 150  | result `50`; `out=[100, 50]`; iter 2: `await fn(200)` starts | `[100, 50]` |
| 350  | result `200`; `out=[100, 50, 200]`; return | `[100, 50, 200]` |

**Total: ~350ms (Σ).**

**Parallel trace:**

| Time | Event                                        | Pending promises |
|------|----------------------------------------------|-------------------|
| 0    | `arr.map(fn)` fires all three; p1, p2, p3 pending | 3            |
| 50   | p2 settles with 50                            | 2                 |
| 100  | p1 settles with 100                           | 1                 |
| 200  | p3 settles with 200; Promise.all resolves with [100, 50, 200] (input order) | 0 |

**Total: ~200ms (max).**

**Bounded(2) trace:**

| Time | W1 state         | W2 state       | `cursor` | `results`          |
|------|------------------|-----------------|-----------|---------------------|
| 0    | start fn(100)    | start fn(50)   | 2         | `[_, _, _]`         |
| 50   | still running    | done; start fn(200) | 3   | `[_, 50, _]`        |
| 100  | done; cursor>=3, exit | running    | 3         | `[100, 50, _]`      |
| 250  | exited           | done; exit      | 3         | `[100, 50, 200]`    |

**Total: ~250ms.**

---

## 10. Common confusion + traps

1. **`arr.forEach(async fn)`** — doesn't await. The outer function returns before any async work finishes. Classic junior bug.

2. **Sequential when parallel is wanted.** Slow. Junior signal — interviewer expects you to spot the parallelism opportunity.

3. **Unbounded parallel on huge arrays.** OOM, connection pool exhaustion, rate-limit breach. Senior anti-pattern. Add bounded concurrency.

4. **`Promise.all` when you need partial results.** First reject loses everyone's results. Use `Promise.allSettled` and filter.

5. **Mutating shared state inside parallel `fn`.** Order of side effects is non-deterministic. Don't rely on it.

6. **Capturing `cursor` inside the await.** `results[cursor++]` reads `cursor` *after* the increment. Always `const i = cursor++;` first.

7. **Not preserving input order in bounded.** `results.push(...)` gives completion order. Use indexed write into pre-allocated array.

8. **`for await...of` confusion.** That's for async iterables — different concept. For an array of promises, use `for...of` with `await`.

---

## 11. Senior follow-ups & variants

### Variant 1 — Per-item timeout

```js
const timeLimit = (p, ms) => Promise.race([
  p,
  new Promise((_, rej) => setTimeout(() => rej(new Error('item timeout')), ms)),
]);

async function asyncMapWithTimeout(arr, fn, perItemMs) {
  return Promise.all(arr.map((x, i) => timeLimit(fn(x, i), perItemMs)));
}
```

Compose with `timeLimit`. Per-item deadline.

### Variant 2 — Bounded + per-item retry

```js
async function asyncMapResilient(arr, fn, { concurrency = 5, retries = 3 } = {}) {
  return asyncMapBounded(
    arr,
    (x, i) => retryWithBackoff(() => fn(x, i), { retries }),
    concurrency,
  );
}
```

Combine bounded concurrency with per-item retry. Production shape for fan-out to flaky downstream.

### Variant 3 — Streaming async map

For unbounded input (e.g., paginated API), use an async generator:

```js
async function* asyncMapStream(asyncSource, fn, concurrency) {
  // Pull from source, fan-out via cursor + workers, yield results
}
```

Memory bounded by `concurrency` regardless of source size.

### Variant 4 — AbortSignal-aware

```js
async function asyncMapBoundedCancellable(arr, fn, concurrency, signal) {
  // ... worker loop ...
  async function worker() {
    while (cursor < arr.length) {
      if (signal?.aborted) throw signal.reason;
      const i = cursor++;
      results[i] = await fn(arr[i], i, { signal });
    }
  }
}
```

External cancellation cleans up in-flight work.

### Variant 5 — Streaming results (out of order)

When you want results as soon as they arrive (not in input order):

```js
async function* asyncMapAsTheyArrive(arr, fn) {
  const pending = arr.map((x, i) => fn(x, i).then((v) => ({ i, v })));
  while (pending.length) {
    const { i, v } = await Promise.race(pending);
    pending.splice(pending.findIndex((p) => p === /* matching */), 1);
    yield { index: i, value: v };
  }
}
```

Different semantics from `Promise.all`. Useful for "first response to stream UI."

---

## 12. How to think aloud in the interview

> "Three valid shapes. **Sequential**: `for...of` + `await`. Use when order of side effects matters or downstream is rate-limited. Time = sum. **Parallel**: `Promise.all(arr.map(fn))`. Use when items are independent and N is bounded. Time = max. Watch for unbounded N — OOM and rate-limit breach. **Bounded parallel**: `k` workers + shared cursor. Use when N is large or downstream needs concurrency control. Time = roughly N/k. **The classic junior bug**: `arr.forEach(async fn)` — forEach doesn't await. **The default mental discipline**: parallel for independent work; bounded when downstream load matters. All three preserve input order via indexed write or input-order iteration."

---

## 13. 60-second revision

> - **Sequential:** `for...of` + `await`. Time = Σ. Memory O(1). Use for order, rate limits.
> - **Parallel:** `Promise.all(arr.map(fn))`. Time = max. Memory O(N) pending. Use for independent, small N.
> - **Bounded:** k workers + shared cursor. Time ≈ N/k × per-item. Memory O(k). Use for large N or rate limits.
> - **`forEach(async fn)` is broken** — doesn't await.
> - **All preserve input order** via indexed write or input-order iteration.
> - **Capture `idx = cursor++` BEFORE `await`** in bounded.
> - **Fail-fast:** `Promise.all` rejects on first; for partial-success, use `Promise.allSettled` and filter.
> - **Family:** `asyncFilter`, `asyncReduce`, `priority-async-queue`.
> - **Trap:** `forEach(async)`, sequential by default, unbounded parallel on huge arrays.

---

**Related:** [promise-all-polyfill.md](./promise-all-polyfill.md) · [promise-pool.md](./promise-pool.md) · [async-filter.md](./async-filter.md) · [async-reduce.md](./async-reduce.md) · [retry-with-backoff.md](./retry-with-backoff.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
