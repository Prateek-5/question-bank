# Implement `asyncPool(concurrency, tasks)` — bounded concurrency over async work

> **Difficulty:** Medium   |   **Time:** ~30 min   |   **Prereqs:** [promise-all-polyfill.md](./promise-all-polyfill.md), [`concepts/promises.md`](../../concepts/promises.md)
>
> **Source:** <a href="https://leetcode.com/problems/promise-pool/" target="_blank" rel="noopener noreferrer">LeetCode 2636 — Promise Pool</a>; inspired by `p-limit`, `async-pool`, `bluebird.map({ concurrency })`.

---

## 1. Problem statement

**Signature**
```ts
function asyncPool<T>(
  concurrency: number,
  tasks: Array<() => Promise<T>>
): Promise<T[]>;
```

**Input / Output examples**

| Setup                                                                            | Behaviour                                              |
|----------------------------------------------------------------------------------|---------------------------------------------------------|
| `concurrency=2`, four tasks of [100, 400, 100, 100] ms                          | Total ~400 ms (bounded by slowest); results in input order |
| Same tasks, **chunked** approach (n=2)                                          | Total ~500 ms (chunk waits for slowest each round)     |
| `concurrency=1`                                                                  | Strictly sequential                                    |
| `concurrency >= tasks.length`                                                    | All run in parallel                                    |
| `tasks` empty                                                                   | Resolves with `[]` immediately                         |
| `concurrency <= 0`                                                              | Throws `TypeError`                                     |
| One task rejects (default fail-fast)                                            | Outer rejects; in-flight tasks complete but no new ones start |

**Constraints**
- **Running pool**, not chunked — workers grab the next task the instant one finishes.
- Results in **input order**, not completion order.
- JS is single-threaded — `i++` on the shared counter is race-free without locks.
- Decide rejection semantics explicitly (fail-fast / allSettled / swallow).

---

## 2. Plain-English restatement

You're given `N` async tasks and a concurrency budget. Run them so that at any moment at most `concurrency` are in flight. The instant one finishes, start the next waiting task — don't wait for the others in its "chunk" to finish first. Return results in the same order as the input.

This is the universal pattern for "fan out 10k API calls but the API allows 5 concurrent." The naive chunked solution (slice into groups of N, await each chunk) leaves throughput on the table because the chunk waits for its slowest task. The running pool keeps every worker busy.

---

## 3. Why this matters in interviews

**This is the single most-asked promises problem at senior backend interviews.** Real backend code hits this constantly — fan out S3 uploads, fan out DB writes, scrape URLs without getting rate-limited. The interviewer grades two things: (1) do you start with the chunk solution, recognize its weakness, and pivot to a running pool, and (2) can you implement the running pool correctly — shared counter, capture `idx` before `await`, preserve input order. Bonus signal: mention that JS's single-threadedness makes `i++` race-free without locks (most candidates from Java/Go/C++ instinctively reach for synchronization).

---

## 4. Mental model

**N workers sharing a job board.** Each worker walks up to the board, grabs the next ticket (`i++`), goes off to do the work, returns to the board, grabs another. The board's counter increments atomically (single-threaded JS) so no two workers grab the same ticket. When the counter exceeds the task count, workers retire. `Promise.all(workers)` resolves when everyone's retired.

```
   tasks = [A, B, C, D, E, F]   (6 tasks)
   concurrency = 2              (2 workers)

   t=0:   W1 grabs A (idx=0, i→1)        W2 grabs B (idx=1, i→2)
          [W1: A]    [W2: B]
          
   t=A:   W1 grabs C (idx=2, i→3)        W2 still on B
          [W1: C]    [W2: B]
          
   t=C:   W1 grabs D (idx=3, i→4)        W2 still on B
          [W1: D]    [W2: B]
          
   t=B:   W2 grabs E (idx=4, i→5)        W1 still on D
          [W1: D]    [W2: E]
          
   ... eventually all done
   results array (in input order): [A', B', C', D', E', F']
```

**Why the running pool beats chunking**: chunking forces every worker to wait for the slowest task in the current chunk. If one task takes 10s and the others take 100ms, three workers sit idle for 9.9s. The running pool has them picking up new work immediately.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. With 4 tasks of `[100, 400, 100, 100]` ms and `concurrency=2`, what's the **chunked** total time vs the **running pool** total time?
> 2. If you write `results[i++] = await tasks[i]()`, what goes wrong? (Hint: when does `i++` happen vs when does `i` get read?)
> 3. Why is the shared counter `let i = 0` safe in JS without a lock?

---

## 6. Brute force — walked through

### Approach 1: Chunked (the naive answer)

```js
async function promisePoolChunked(tasks, n) {
  const results = [];
  for (let i = 0; i < tasks.length; i += n) {
    const chunk = tasks.slice(i, i + n);
    results.push(...(await Promise.all(chunk.map((f) => f()))));
  }
  return results;
}
```

**Correct but suboptimal.** Every chunk waits for its slowest task before starting the next chunk. If chunk 1 has tasks of duration `[100, 400]` ms, then `[100, 100]` ms in chunk 2, total = 400 + 100 = **500 ms**. The running pool finishes in **400 ms** (worker 2 stays busy with the long task while worker 1 keeps grabbing 100ms tasks). With more skew, the gap widens dramatically.

Present this first in the interview, then critique its latency penalty, then build the running pool.

### Approach 2: Mutate `i` inside await — wrong!

```js
async function broken(tasks, n) {
  let i = 0;
  const results = [];
  while (i < tasks.length) {
    const batch = [];
    for (let k = 0; k < n && i < tasks.length; k++) {
      batch.push(tasks[i]());                   // BUG: i may have moved by the time we read
      i++;
    }
    results.push(...(await Promise.all(batch)));
  }
  return results;
}
```

Subtle bug: `tasks[i]()` reads `i` *after* the increment in some interleaving. Always capture `idx = i++` first, *then* use `idx`.

### Approach 3: Add a mutex for `i++` — unnecessary!

```js
const lock = new Mutex();
async function worker() {
  while (true) {
    const idx = await lock.acquire(() => i++);   // BUG: pointless ceremony
    // ...
  }
}
```

JavaScript is single-threaded. The `i++` is one statement that completes atomically from JS's perspective — no other worker can interleave between the read and the write because there's only one execution thread. The mutex is dead code.

---

## 7. The unlocking insight

> **Spawn `min(concurrency, tasks.length)` worker coroutines. Each runs `while (i < tasks.length) { const idx = i++; results[idx] = await tasks[idx](); }`. Single-threaded JS makes `i++` race-free. `Promise.all` of all workers resolves when everyone's retired.**

The shape is fixed by three observations:

1. **Bounded concurrency** = exactly `N` workers running simultaneously. `Array.from({length: N}, worker)` spawns them.
2. **Shared counter** for next-task assignment — JS is single-threaded, so `let idx = i++` is safe. Mention this in the interview; it's a non-obvious win.
3. **Results in input order** — capture `idx = i++` *before* `await`, write to `results[idx]`. After the await, `i` has moved on; `idx` hasn't.

Two semantic decisions you must make explicit:

| Decision           | Options                                                        | When to pick which                                  |
|--------------------|----------------------------------------------------------------|------------------------------------------------------|
| Rejection policy   | fail-fast (Promise.all) / allSettled / swallow (LC spec)       | Ask the interviewer                                  |
| Sync throws        | Wrap `tasks[idx]()` in `Promise.resolve().then(tasks[idx])` to catch sync throws as rejections | Always (safer)                  |

**Memory:** `O(concurrency + tasks.length)` — the results array holds N entries (regardless of pool size). For huge tasks counts (streaming input), use the async-iterable variant in section 11.

---

## 8. Solution (annotated)

```js
async function asyncPool(concurrency, tasks) {
  if (!Number.isInteger(concurrency) || concurrency < 1) {           // step 1: validate
    throw new TypeError('concurrency must be a positive integer');
  }
  if (tasks.length === 0) return [];                                  // step 2: empty input

  const results = new Array(tasks.length);                            // step 3: input-order results
  let nextIndex = 0;                                                  // step 4: shared counter
  let failed = false;

  async function worker() {                                           // step 5: each worker
    while (!failed) {
      const idx = nextIndex++;                                          //   capture idx BEFORE await
      if (idx >= tasks.length) return;
      results[idx] = await Promise.resolve()                           //   wrap to catch sync throws
        .then(() => tasks[idx]());
    }
  }

  try {
    await Promise.all(                                                  // step 6: spawn min(N, len) workers
      Array.from({ length: Math.min(concurrency, tasks.length) }, worker)
    );
    return results;
  } catch (err) {
    failed = true;                                                      // step 7: stop new tasks on fail
    throw err;
  }
}

// LeetCode shape: swallow rejections, no return values
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

// allSettled flavour — never rejects; per-task status
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

**Try it yourself**

```js
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const tasks = [
  () => sleep(100).then(() => 'a'),
  () => sleep(400).then(() => 'b'),
  () => sleep(100).then(() => 'c'),
  () => sleep(100).then(() => 'd'),
];

console.time('pool');
const results = await asyncPool(2, tasks);
console.timeEnd('pool');                       // ~400 ms
console.log(results);                          // ['a', 'b', 'c', 'd']  (input order)
```

---

## 9. Step-by-step dry run

Input: `concurrency=2`, `tasks = [100ms-'a', 400ms-'b', 100ms-'c', 100ms-'d']`.

Values-first trace:

| Time (ms) | W1 state          | W2 state          | `nextIndex` | `results`                       |
|-----------|-------------------|-------------------|-------------|----------------------------------|
| 0         | start A (idx=0)   | start B (idx=1)   | 2           | `[_, _, _, _]`                  |
| 100       | A done; results[0]='a'; start C (idx=2) | still on B | 3           | `['a', _, _, _]`                |
| 200       | C done; results[2]='c'; start D (idx=3) | still on B | 4           | `['a', _, 'c', _]`              |
| 300       | D done; results[3]='d'; nextIndex>=len; return | still on B | 4    | `['a', _, 'c', 'd']`            |
| 400       | retired           | B done; results[1]='b'; return | 4 | `['a', 'b', 'c', 'd']`         |
| 400       | `Promise.all([W1, W2])` resolves         |             | returns `['a', 'b', 'c', 'd']`  |

**Total wall time: 400 ms** — bound by the single slow task.

**Compare chunked** (concurrency=2):

| Time (ms) | Chunk action                       | Output         |
|-----------|-------------------------------------|----------------|
| 0–400     | chunk [a, b]: waits for slower (b)  | —              |
| 400       | chunk [a, b] done                   | `['a', 'b']`   |
| 400–500   | chunk [c, d]: both finish in 100ms  | —              |
| 500       | chunk [c, d] done                   | `['a', 'b', 'c', 'd']` |

**Total: 500 ms** — 100ms penalty from chunking. With more skew, the gap widens.

---

## 10. Common confusion + traps

1. **Submitting the chunked answer without critiquing it.**
   Always present both. Articulate the latency gap. The interviewer is checking whether you *recognize* the chunk solution's flaw.

2. **Spawning more workers than tasks.**
   `concurrency=10, tasks.length=3` should spawn 3 workers, not 10. Use `Math.min(concurrency, tasks.length)`.

3. **Awaiting `i` instead of `idx`.**
   `results[i++]` reads `i` *after* mutation in some interleavings. Always capture `const idx = i++;` *first*.

4. **Adding a "lock" for `i++`.**
   JS is single-threaded. The increment is atomic. No lock needed. Mention this in the interview — it's a senior signal.

5. **Empty input or `concurrency <= 0`.**
   Empty: return `[]` immediately. `concurrency <= 0`: throw `TypeError`. Don't hang.

6. **Not deciding rejection semantics.**
   Fail-fast (`Promise.all`), allSettled (per-task status), or swallow (LC spec). Ask the interviewer; document the choice.

7. **Sync throws in a task body.**
   `tasks[idx]()` may throw synchronously (not return a Promise). Wrap with `Promise.resolve().then(() => tasks[idx]())` to convert to a rejection.

8. **Memory pinning by holding all promise wrappers.**
   For `tasks.length = 10^6` with `concurrency = 10`, the pool itself only holds 10 in-flight promises. But your `tasks` array of factory functions holds all 10^6 — that's the caller's memory cost. For streaming, see Variant 1.

---

## 11. Senior follow-ups & variants

### Variant 1 — Async-iterable input (streaming, O(concurrency) memory)

For unbounded sources (file lines, paginated API), don't preload all tasks:

```js
async function asyncPoolStream(concurrency, asyncIter, taskFn) {
  const iter = asyncIter[Symbol.asyncIterator]();
  const results = [];
  let idx = 0;
  async function worker() {
    while (true) {
      const myIdx = idx++;
      const { value, done } = await iter.next();
      if (done) return;
      results[myIdx] = await taskFn(value);
    }
  }
  await Promise.all(Array.from({ length: concurrency }, worker));
  return results;
}
```

Memory stays O(concurrency) regardless of source size.

### Variant 2 — Per-task timeout + retry composition

```js
const wrapped = tasks.map((t) => () =>
  retryWithBackoff(({ signal }) => timeLimit(t({ signal }), 5_000), { retries: 3 })
);
await asyncPool(10, wrapped);
```

Pool + per-task timeout + per-task retry. Composes cleanly.

### Variant 3 — Priority pool

Replace the shared counter with a priority queue. Workers pop highest-priority items. Used in job runners (e.g., Bull, Sidekiq-style queues).

```js
class PriorityPool {
  constructor(concurrency) {
    this.heap = new MinHeap();
    this.workers = concurrency;
  }
  add(task, priority) {
    this.heap.push({ task, priority });
    this._tick();
  }
  // ... workers pull from heap ...
}
```

### Variant 4 — Cancellation via AbortSignal

```js
async function asyncPool(concurrency, tasks, { signal } = {}) {
  // ... same shape, plus:
  async function worker() {
    while (!failed && !signal?.aborted) {
      const idx = nextIndex++;
      if (idx >= tasks.length) return;
      results[idx] = await tasks[idx]({ signal });
    }
  }
}
```

Caller can abort the whole pool. Each task receives the signal so it can cancel its own work.

### Variant 5 — Dynamic concurrency

Expose `setConcurrency(k)`. Increasing spawns more workers; decreasing lets idle workers exit. Used in autotuning systems (e.g., bandwidth-adaptive uploaders).

```js
function createPool(initialConcurrency) {
  let concurrency = initialConcurrency;
  let workersAlive = 0;
  async function spawnWorker() { workersAlive++; /* ... worker loop ... */ workersAlive--; }
  return {
    submit(task) { /* enqueue; spawn if workersAlive < concurrency */ },
    setConcurrency(k) {
      concurrency = k;
      while (workersAlive < concurrency) spawnWorker();
      // shrinking happens naturally — workers see `workersAlive > concurrency` and exit
    },
  };
}
```

### Variant 6 — `Promise.allSettled` style — never rejects

Already shown in section 8 as `asyncPoolSettled`. Each task returns `{ status, value | reason }`. Useful when you want to process all results regardless of partial failures.

---

## 12. How to think aloud in the interview

> "I'll present two approaches. First, the chunked solution: slice into groups of N, await each chunk. It's correct but the chunk waits for its slowest task — leaves throughput on the table. Better: a running pool. Spawn `min(N, tasks.length)` worker coroutines. Each loops: grab `idx = i++`, await `tasks[idx]()`, write `results[idx]`. JS is single-threaded so `i++` is race-free — no lock needed. Workers retire when `idx >= len`. `Promise.all(workers)` resolves when everyone's retired. Two policy decisions: fail-fast vs allSettled vs swallow, and whether to wrap each task in `Promise.resolve().then(...)` to catch sync throws. For streaming input, swap the array for an async-iterable so memory stays O(concurrency). Composes with retry, per-attempt timeout, AbortSignal cancellation."

---

## 13. 60-second revision

> - **Running pool > chunked.** Workers grab next task the instant one finishes.
> - **Spawn `min(N, tasks.length)`** worker coroutines. Shared `let i = 0` counter.
> - **Capture `idx = i++` before `await`.** Then `results[idx] = await tasks[idx]()`.
> - **JS is single-threaded** — `i++` is race-free, no lock needed. **State this aloud.**
> - **Preserve input order** via `results[idx]`.
> - **Empty input** → `[]` immediately. **`concurrency <= 0`** → throw.
> - **Rejection policy** is a design decision: fail-fast / allSettled / swallow.
> - **Sync throws** → wrap `tasks[idx]()` with `Promise.resolve().then(...)`.
> - **Family:** rate limiter, paginated consumer, bulk uploader, scraper, fanout-to-N-replicas.
> - **Trap:** chunked answer with no critique; using `i` instead of `idx`; adding a needless lock.

---

**Related:** [promise-all-polyfill.md](./promise-all-polyfill.md) · [retry-with-backoff.md](./retry-with-backoff.md) · [promise-time-limit.md](./promise-time-limit.md) · [abortcontroller-fanout.md](./abortcontroller-fanout.md) · [`10-machine-coding-patterns/async-semaphore.md`](../10-machine-coding-patterns/async-semaphore.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
