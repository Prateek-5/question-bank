# `asyncMap` — sequential vs parallel implementations

## Source
- Bread-and-butter senior backend interview question — every Node.js role tests it.
- Real bug source: misusing `for...of await` when parallel is meant, or `Promise.all` when sequential is required.
- Variants on BFE.dev and the Effective TypeScript section on `Promise.all`.

## Why this question matters in interviews
This question is a **trap** that interviewers use to separate juniors from seniors. Juniors write `arr.forEach(async ...)` and don't notice it doesn't await. Mids write `for (const x of arr) await fn(x)` everywhere — correct, but unnecessarily slow. Seniors **pick the right pattern based on constraints**: sequential when calls have ordering or rate-limit dependencies, parallel when they're independent, bounded-parallel when memory or downstream load is a concern. The discussion of *which* to use is more important than the code itself.

## Concepts involved

### Syntax to lock in
```js
// SEQUENTIAL — wait for each before next
async function asyncMapSeq(arr, fn) {
  const out = [];
  for (const item of arr) {
    out.push(await fn(item));
  }
  return out;
}

// PARALLEL — fire all, await all
async function asyncMapPar(arr, fn) {
  return Promise.all(arr.map(fn));
}
```

### Runtime / engine behavior
- **Sequential**: each `await` yields control to the event loop, but the next iteration only starts after the current promise settles. Total time ≈ sum of latencies.
- **Parallel**: `arr.map(fn)` fires all `fn(item)` calls immediately, creating N pending promises. `Promise.all` aggregates. Total time ≈ max of latencies.
- **`forEach(async ...)` is the bug** — `forEach` doesn't await the async callbacks; the outer function returns before any of them complete. Returns `undefined` regardless.
- Parallel allocates **all N promise objects at once** — if N is huge (e.g., 100k DB rows), this can OOM or hammer the downstream.

### Edge cases (interview traps)
1. **Order preservation** — both versions preserve input order. `Promise.all` resolves with results indexed by input position.
2. **Fail-fast** — `Promise.all` rejects on the first rejection. Sequential aborts at the first throw (the `await` re-throws). For "best effort", use `Promise.allSettled`.
3. **Memory pressure** — parallel loads all results in memory simultaneously. Sequential lets each result be discarded if not retained.
4. **Rate limits / connection pools** — parallel fires N HTTP requests at once; you'll exhaust the keep-alive pool or trip API rate limits. Use **bounded parallel** (concurrency limit).
5. **Side effects** — sequential guarantees ordering of side effects (writes to a file in order). Parallel does not.
6. **Errors mid-batch** — sequential stops; parallel keeps running pending tasks but won't return their results. For cleanup, attach `.catch` to each or use `allSettled`.
7. **`forEach` returning `undefined`** — common bug. Use `for...of` for sequential.

## Brute force approach
**For sequential**, brute force *is* the answer — `for...of` + `await`. No clever tricks needed.

**For parallel**, brute force `for...of` with `await` is the **wrong** answer when calls are independent. The naive parallel attempt of `arr.forEach(async fn)` is also wrong because `forEach` ignores promises.

## Optimal approach
- **Sequential** when: order matters, throttling required, downstream can't handle parallel.
- **Parallel** when: items are independent, N is bounded, and you accept fail-fast (or use `allSettled`).
- **Bounded parallel** when: N is large or downstream load is a concern. Implement with a counter + worker loop, or use `p-limit`-style helper.

## Solution (JavaScript)

```js
// Sequential
async function asyncMapSeq(arr, fn) {
  const out = [];
  for (let i = 0; i < arr.length; i++) {
    out.push(await fn(arr[i], i));
  }
  return out;
}

// Parallel
async function asyncMapPar(arr, fn) {
  return Promise.all(arr.map((item, i) => fn(item, i)));
}

// Bounded parallel (concurrency-limited)
async function asyncMapBounded(arr, fn, concurrency = 5) {
  const results = new Array(arr.length);
  let cursor = 0;

  async function worker() {
    while (cursor < arr.length) {
      const i = cursor++;
      results[i] = await fn(arr[i], i);
    }
  }

  const workers = Array.from({ length: Math.min(concurrency, arr.length) }, worker);
  await Promise.all(workers);
  return results;
}
```

The bounded version spins `concurrency` workers, each pulling the next index off a shared `cursor`. When `cursor` reaches `arr.length`, workers exit naturally. Order-preserving via positional `results[i]` write.

## Step-by-step dry run

Setup:
```js
const sleepReturn = (ms, val) => new Promise(r => setTimeout(() => r(val), ms));
const items = [100, 50, 200];
const fn = (ms) => sleepReturn(ms, ms);
```

**Sequential** (`asyncMapSeq(items, fn)`):
- t=0: start. iter 0: `await fn(100)` → blocks until t=100.
- t=100: `out=[100]`. iter 1: `await fn(50)` → blocks until t=150.
- t=150: `out=[100,50]`. iter 2: `await fn(200)` → blocks until t=350.
- t=350: return `[100, 50, 200]`. **Total time ≈ 350ms (sum)**.

**Parallel** (`asyncMapPar(items, fn)`):
- t=0: `arr.map(fn)` fires three promises: p1=fn(100), p2=fn(50), p3=fn(200). All running.
- t=50: p2 settles with 50.
- t=100: p1 settles with 100.
- t=200: p3 settles. `Promise.all` resolves with `[100, 50, 200]` (input order).
- **Total time ≈ 200ms (max)**.

**Bounded parallel** (`asyncMapBounded(items, fn, 2)`):
- t=0: 2 workers start. W1 picks i=0 (fn(100)). W2 picks i=1 (fn(50)).
- t=50: W2 done with results[1]=50. W2 picks i=2 (fn(200)).
- t=100: W1 done with results[0]=100. cursor=3, W1 exits.
- t=250: W2 done with results[2]=200. exits.
- Return `[100, 50, 200]`. **Total time ≈ 250ms**.

## Important takeaways

**Syntax to memorize**
- Sequential: `for...of` with `await` (NOT `forEach`).
- Parallel: `Promise.all(arr.map(fn))`.
- Bounded: cursor + workers pattern, `Promise.all(workers)` at the end.

**Patterns to reuse**
- "Cursor + N workers" is the universal **concurrency-limited pipeline** — same shape used in `priority-async-queue.md`, web crawlers, file batch uploaders.
- `Promise.all + .map` is the simplest "fan-out / fan-in" idiom.

**Common mistakes**
- `arr.forEach(async fn)` — `forEach` doesn't await. Returns undefined; race conditions galore.
- Sequential when parallel is wanted — slow. Junior signal.
- Parallel with no concurrency cap on huge arrays — OOM or rate-limit breach. Senior anti-pattern.
- `Promise.all` when you need partial results — use `allSettled` and inspect each.
- Mutating shared state inside parallel `fn` — race conditions. Order of side effects is non-deterministic.

**Related questions**
- `asyncFilter`, `asyncReduce` (same family)
- `priority-async-queue.md` (concurrency-limited with priorities)
- `Promise.all` vs `Promise.allSettled` semantics

## Variants

1. **Async map with timeout per item** — wrap each `fn(item)` in `Promise.race([fn(item), timeout])`. Discuss what timeout means: skip, throw, default value.
2. **Bounded parallel with retries** — combine `asyncMapBounded` with `retry-with-backoff.md`.
3. **Streaming async map** — yield results as they complete (not in order). Use `for await...of` over a generator that yields settled promises. Different semantics from `Promise.all`.
4. **AbortController-aware** — accept a signal, abort in-flight tasks if signal is aborted. See `fetch-with-abort.md`.

## Revision notes

> **asyncMap — 60 second recap**
> - **Sequential**: `for...of` + `await`. Time = Σ latencies. Order of side effects guaranteed.
> - **Parallel**: `Promise.all(arr.map(fn))`. Time = max latency. Memory = O(N) pending promises.
> - **Bounded**: cursor + N workers + `Promise.all(workers)`. Best of both worlds.
> - **forEach(async ...) is the bug** — doesn't await.
> - Pick based on: ordering needs, rate limits, memory, fail-fast tolerance.
> - **Trap:** parallel-by-default on large arrays exhausts pools and rate limits.
