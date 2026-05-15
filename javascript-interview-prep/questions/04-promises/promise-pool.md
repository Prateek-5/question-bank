# Implement `promisePool(functions, n)` / `asyncPool(limit, items, iterFn)`

## Source
- LeetCode #2636 "Promise Pool": https://leetcode.com/problems/promise-pool/
- Canonical: every batch-processing backend service, every web scraper, every S3 multi-uploader. Inspired by `p-limit` / `async-pool` / `bluebird.map({ concurrency })`.

## Why this question matters in interviews
**This is the single most-asked promises problem at senior backend interviews.** It tests whether you can think in terms of a *running worker pool* (true concurrency control) vs *fixed chunks* (the naive answer). Real backend code runs into this constantly — fan out 10k S3 uploads, fan out 1k DB updates, scrape 50k URLs without getting rate-limited. The interviewer is grading two things: (1) do you start with the chunk solution and recognize its weakness (latency-bound by the slowest task in each chunk), and (2) can you implement the proper running pool that picks up the next item the instant one finishes. Show both; explain why the running pool is what production code wants.

## Concepts involved

### Syntax to lock in
```js
// LeetCode signature: functions are () => Promise; pool size n; return Promise<void>.
async function promisePool(functions, n) {
  // Running-pool approach.
  let i = 0;
  async function worker() {
    while (i < functions.length) {
      const idx = i++;
      await functions[idx]();
    }
  }
  await Promise.all(Array.from({ length: Math.min(n, functions.length) }, worker));
}
```

### Runtime / engine behavior
- JavaScript is single-threaded. "Concurrency" here means **interleaved async I/O**, not parallel CPU work. The pool limits how many in-flight promises exist at once.
- Each `worker` is itself an async function. Multiple workers running in parallel **share** the index `i` via closure. The `i++` is **safe without locks** because JS is single-threaded — no two workers can read+write `i` simultaneously. (This is a non-obvious win of the JS model. Mention it.)
- The `worker` returns when `i >= functions.length`. `Promise.all` of all workers resolves when every worker has returned — i.e., when all tasks are done.

### Edge cases (interview traps)
1. **`functions` empty** — resolve immediately with no work. `Array.from({ length: 0 })` produces `[]`, `Promise.all([])` resolves with `[]`. Trivially correct.
2. **`n >= functions.length`** — start exactly `functions.length` workers; running more is wasted. Hence `Math.min(n, functions.length)`.
3. **`n === 0` or negative** — what's the contract? Reject? Default to 1? Pick a sensible default and document. Don't silently hang.
4. **A task rejects** — LeetCode's official problem treats rejections as "complete" (`.catch` swallow). Production usually wants fail-fast or `allSettled`-style. Always ask the interviewer "what should happen on reject?" before coding.
5. **Tasks return values** — LeetCode's variant ignores them; production usually wants results **in input order**. Use an `results[idx] = await functions[idx]()` pattern (note `idx`, not `i`, because `i` has moved on).
6. **Synchronous throws in a task** — `await functions[idx]()` converts them to rejections naturally inside an async function. If you call `functions[idx]()` outside an async context, wrap in `try/catch` or `Promise.resolve().then(functions[idx])`.
7. **Order of completion vs order of start** — workers start sequentially in microtask order but finish in arbitrary order. If you care about completion order, capture `idx` from `i++` *before* awaiting.
8. **Memory** — running pool keeps memory O(n), not O(functions.length). The naive chunk approach also uses O(n) but adds latency.

## Brute force approach — chunked (presented first, then critiqued)

```js
async function promisePoolChunked(functions, n) {
  for (let i = 0; i < functions.length; i += n) {
    const chunk = functions.slice(i, i + n);
    await Promise.all(chunk.map((f) => f()));
  }
}
```

Correct but **suboptimal**: every chunk waits for its slowest task before starting the next chunk. If task #2 in chunk 1 takes 10s and tasks #1, #3, #4 take 100ms each, those three workers sit idle for 9.9s. Real workloads are heterogeneous — this leaves throughput on the table. State this clearly and switch to the running pool.

## Optimal approach — running pool

Spawn `min(n, len)` worker coroutines. Each pulls the next index off a shared counter and awaits the corresponding task; loops until exhausted. The instant a task completes, that worker grabs the next one. Steady-state utilization stays at `n`.

## Solution (JavaScript)

```js
/**
 * Run up to `concurrency` async tasks from `tasks` in parallel.
 * Returns results in the SAME order as the input.
 * Fails fast on first rejection (the in-flight tasks finish but no new ones start).
 *
 * @template T
 * @param {number} concurrency
 * @param {Array<() => Promise<T>>} tasks
 * @returns {Promise<T[]>}
 */
async function asyncPool(concurrency, tasks) {
  if (!Number.isInteger(concurrency) || concurrency < 1) {
    throw new TypeError('concurrency must be a positive integer');
  }
  if (tasks.length === 0) return [];

  const results = new Array(tasks.length);
  let nextIndex = 0;
  let failed = false;

  async function worker() {
    while (!failed) {
      const idx = nextIndex++;
      if (idx >= tasks.length) return;
      // Wrap so a sync throw inside the task becomes a rejection.
      results[idx] = await Promise.resolve().then(() => tasks[idx]());
    }
  }

  try {
    await Promise.all(
      Array.from({ length: Math.min(concurrency, tasks.length) }, worker)
    );
    return results;
  } catch (err) {
    failed = true; // stop further worker iterations
    throw err;
  }
}

// ----- LeetCode shape: no results, swallow rejections, return Promise<void> -----
async function promisePool(functions, n) {
  let i = 0;
  async function worker() {
    while (i < functions.length) {
      const idx = i++;
      try { await functions[idx](); } catch { /* swallow per LC spec */ }
    }
  }
  await Promise.all(
    Array.from({ length: Math.min(n, functions.length) }, worker)
  );
}
```

### `allSettled` flavour (no fail-fast)

```js
async function asyncPoolSettled(concurrency, tasks) {
  const results = new Array(tasks.length);
  let i = 0;
  async function worker() {
    while (i < tasks.length) {
      const idx = i++;
      try { results[idx] = { status: 'fulfilled', value: await tasks[idx]() }; }
      catch (reason) { results[idx] = { status: 'rejected', reason }; }
    }
  }
  await Promise.all(
    Array.from({ length: Math.min(concurrency, tasks.length) }, worker)
  );
  return results;
}
```

## Step-by-step dry run

Input:
```js
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const tasks = [
  () => sleep(100).then(() => 'a'),  // 100ms
  () => sleep(400).then(() => 'b'),  // 400ms
  () => sleep(100).then(() => 'c'),  // 100ms
  () => sleep(100).then(() => 'd'),  // 100ms
];
asyncPool(2, tasks).then(console.log);
```

Trace (running pool, concurrency = 2):
- `t=0`: workers W1, W2 spawn. W1 takes idx=0 (task 'a', 100ms). W2 takes idx=1 (task 'b', 400ms). `nextIndex = 2`.
- `t=100`: W1 finishes 'a', `results[0]='a'`. W1 loops, takes idx=2 ('c', 100ms). `nextIndex = 3`.
- `t=200`: W1 finishes 'c', `results[2]='c'`. W1 loops, takes idx=3 ('d', 100ms). `nextIndex = 4`.
- `t=300`: W1 finishes 'd', `results[3]='d'`. W1 loops; `idx=4 >= 4`, W1 returns.
- `t=400`: W2 finishes 'b', `results[1]='b'`. W2 loops; W2 returns.
- `Promise.all([W1, W2])` resolves. Returns `['a', 'b', 'c', 'd']`.

Total wall time: **400ms** (bound by the single slow task).

Compare to **chunked(n=2)**:
- `t=0–400`: chunk ['a','b'] — finishes at t=400 (waiting on 'b').
- `t=400–500`: chunk ['c','d'] — finishes at t=500.
- Total: **500ms**. That extra 100ms is the chunked penalty. With more skew, the gap widens dramatically.

## Important takeaways

**Syntax to memorize**
- `Array.from({ length: k }, worker)` to spawn `k` workers.
- Shared `nextIndex` counter via closure — single-threaded JS makes `i++` race-free.
- Capture `idx = i++` **before** awaiting, then use `idx` for `results[idx]`.

**Patterns to reuse**
- Same skeleton powers: rate-limited batch processors, paginated API consumers, bulk upload helpers, web scrapers, fan-out DB writes.
- Wrap with `pRetry`-style retry around `tasks[idx]()` to add resilience.

**Common mistakes**
- Submitting the chunked answer and not mentioning the running-pool improvement.
- Forgetting `Math.min(n, len)` and spawning more workers than needed.
- Awaiting `i` instead of `idx` for results — `i` mutates and you'll overwrite or misalign.
- Forgetting that JS is single-threaded — adding a "lock" for `i++` (real submissions have this — it's wasted code).
- Failing to handle empty input or `concurrency <= 0`.
- Not deciding the rejection semantics up front (fail-fast vs allSettled vs swallow).

**Related questions**
- `Promise.all` polyfill (different — fans out all at once, no limit).
- Token-bucket rate limiter (concurrency over time, not in-flight count).
- Worker queue with backpressure (producer waits for room).

## Variants

1. **Streaming generator-input** — accept an async iterable of tasks (so memory stays O(concurrency), not O(tasks)). Pull via `for await`. Pattern for "process every line of a 10GB file with concurrency 32".

2. **Per-task timeout + retry** — wrap each `tasks[idx]()` with `timeLimit` + `pRetry`. Composable.

3. **Priority pool** — replace shared index with a priority queue; workers pop highest-priority items. Used in job runners.

4. **Cancellation** — accept `AbortSignal`; on abort, set `failed = true` and abort each in-flight task's signal.

5. **Dynamic concurrency** — expose `setConcurrency(k)` that spawns more workers if k goes up, lets idle workers exit if k goes down. Used in autotuning systems.

## Revision notes

> **promisePool / asyncPool — 60 second recap**
> - **Running pool** beats **chunked**: workers grab next index the instant one finishes; steady-state utilization stays at `n`.
> - Spawn `min(n, tasks.length)` worker coroutines. Each: `while (i < tasks.length) { const idx = i++; await tasks[idx](); }`.
> - JS is single-threaded — `i++` is race-free, no lock needed. **State this in the interview.**
> - Preserve input order with `results[idx]` (capture `idx` *before* the await).
> - Decide rejection semantics: fail-fast (Promise.all behaviour) vs allSettled vs swallow (LC spec).
> - Empty array → resolve `[]` immediately. `n === 0` → throw/reject.
> - Family: rate limiter, paginated consumer, bulk uploader, scraper — all the same skeleton.
> - **Trap:** writing the chunked solution and not articulating the latency penalty. Show both, explain the gap.
