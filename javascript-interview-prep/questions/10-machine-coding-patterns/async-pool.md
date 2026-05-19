# Async Pool — limit N concurrent tasks with order preservation

> **Difficulty:** Medium   |   **Time:** ~20 min   |   **Prereqs:** [async-semaphore.md](./async-semaphore.md), [`04-promises/promise-pool.md`](../04-promises/promise-pool.md)
>
> **Source:** `p-limit`, `p-queue`. Stripe, Razorpay, Atlassian, Cloudflare, Booking.

---

## 1. Problem statement

**Signature**
```ts
function asyncPool<I, R>(
  limit: number,
  items: I[],
  worker: (item: I, index: number) => Promise<R>,
  opts?: { stopOnError?: boolean }
): Promise<R[] | { results: R[]; errors: Error[] }>;
```

**Input / Output examples**

| Setup (limit=2, items=[A,B,C,D,E])              | Behaviour                                              |
|--------------------------------------------------|---------------------------------------------------------|
| each worker takes 100ms                          | concurrent ≤ 2; total ~300ms                           |
| `worker(C)` throws, `stopOnError: true`           | reject promise; running tasks complete                |
| `worker(C)` throws, `stopOnError: false`          | returns `{results, errors}` with partial               |
| Empty input                                       | `[]`                                                    |
| `limit > items.length`                            | spawns `items.length` runners (no waste)              |
| `limit <= 0`                                      | throw TypeError                                         |

**Constraints**
- Output order = input order (`results[i]` indexed write).
- Memory O(N) (N runners), not O(M) (M items).
- Decide error policy upfront: fail-fast vs partial-success.

---

## 2. Plain-English restatement

You have M items and a worker that's async. Run at most N workers in flight. Output goes back in the original order. Don't chunk (chunks waste time on stragglers — whole chunk waits for slowest). Use N "runner" loops that pull from a shared cursor and each writes to its index in the output array.

---

## 3. Why this matters in interviews

The canonical async-control-flow question. Web scrapers, fan-out fetchers, image processors, batch ETL. Interviewers grade three things: (1) don't run all M in parallel (memory explosion); (2) don't run sequentially (3 days to finish); (3) errors don't sink the pool. Bombing it means you're going to overload someone's DB in production.

---

## 4. Mental model

```
   N=2 conveyor belts, M=8 packages, write into output rack:

   items:  [A][B][C][D][E][F][G][H]     (input)
                       ↓
   cursor  ─────────────► shared, atomically advances

           belt1 picks: A → C → E → G
           belt2 picks: B → D → F → H

                       ↓
   results: [A'][B'][C'][D'][E'][F'][G'][H']   (in input order via results[i])
```

Each runner: `while (cursor < items.length) { i = cursor++; results[i] = await worker(items[i], i); }`. Memory O(N), not O(M). Output order preserved by indexed write.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. With `limit=3` and 10 items, how many runners are spawned? Why not 10?
> 2. Why does writing to `results[i]` (not `.push`) preserve input order?
> 3. What's wrong with chunking items into groups of N?

---

## 6. Brute force — walked through

### Wrong attempt 1: `Promise.all(items.map(worker))`
No concurrency bound — fires all M. For M=10k, DB connection pool exhausts.

### Wrong attempt 2: chunk into groups of N
Each chunk waits for slowest — stragglers stall the whole batch. Runners keep belts busy continuously.

### Wrong attempt 3: sequential `for...of` with `await`
Concurrency = 1. Slow.

### Wrong attempt 4: push results in completion order
Output order ≠ input order. Caller can't correlate.

---

## 7. The unlocking insight

> **N runner loops sharing a `cursor`. Each runner pulls `i = cursor++`, awaits `worker(items[i], i)`, writes to `results[i]`, repeats until cursor exhausted. Output order preserved by indexed write; memory O(N).**

Three properties:

1. **Shared cursor** — atomic via single-threaded JS.
2. **Indexed write** — `results[i]` preserves input order.
3. **`Promise.all(runners)`** — waits for all runners to drain.

---

## 8. Solution (annotated)

```js
async function asyncPool(limit, items, worker, { stopOnError = true } = {}) {
  if (!Number.isInteger(limit) || limit < 1) {
    throw new TypeError('limit must be >= 1');
  }
  const results = new Array(items.length);
  const errors  = new Array(items.length);
  let cursor = 0;                                                   // step 1: shared cursor
  let aborted = false;

  const n = Math.min(limit, items.length);                          // step 2: don't spawn waste
  const runners = Array.from({ length: n }, async () => {
    while (!aborted && cursor < items.length) {
      const i = cursor++;                                            // step 3: claim slot
      try {
        results[i] = await worker(items[i], i);                      // step 4: indexed write
      } catch (err) {
        errors[i] = err;
        if (stopOnError) { aborted = true; throw err; }              // step 5: fail-fast
      }
    }
  });

  if (stopOnError) await Promise.all(runners);
  else             await Promise.allSettled(runners);

  return stopOnError ? results : { results, errors };
}
```

**Try it yourself**

```js
const urls = ['/a', '/b', '/c', '/d', '/e'];
const results = await asyncPool(2, urls, (url) => fetch(url).then(r => r.json()));
// In-flight count ≤ 2; results in input order.

// Partial-success mode
const { results: r, errors: e } = await asyncPool(2, urls, fetchSafely, { stopOnError: false });
// Returns whatever succeeded; errors array indexed by item position.
```

---

## 9. Step-by-step dry run

```
limit=2, items=[A,B,C,D,E], worker takes ~80-120ms per item.

t=0   cursor=0. spawn 2 runners.
      R1: i=0 (cursor=1), start worker(A)
      R2: i=1 (cursor=2), start worker(B)

t=80  worker(A) resolves → results[0]=A'.
      R1: cursor<5? yes. i=2 (cursor=3), start worker(C).

t=100 worker(B) resolves → results[1]=B'.
      R2: i=3 (cursor=4), start worker(D).

t=180 worker(C) resolves → results[2]=C'.
      R1: i=4 (cursor=5), start worker(E).

t=200 worker(D) resolves → results[3]=D'.
      R2: cursor<5? cursor=5 → false. Loop exits.

t=260 worker(E) resolves → results[4]=E'.
      R1: cursor<5? false. Loop exits.

await Promise.all(runners) → resolved with [undefined, undefined].
return results = [A', B', C', D', E'].

Output is in INPUT order, written via results[i] index, not push order.
```

Failure dry run (`stopOnError: true`, worker(C) throws):

```
t=180 worker(C) throws. errors[2] = err. aborted=true. R1 throws.
      Promise.all sees the rejection → rejects overall.
      R2 still running worker(D) — it checks `aborted` next iter but worker(D) finishes.
      Final: pool rejects with the err from C.
```

---

## 10. Common confusion + traps

1. **`Promise.all(items.map(worker))`** — no bound.
2. **Chunking** — stragglers stall.
3. **Sequential `for await`** — concurrency 1.
4. **Push results in completion order** — wrong output ordering.
5. **`limit > items.length`** without `Math.min` — spawns idle runners.
6. **`limit <= 0`** — silently no-op or hang; throw TypeError.
7. **`stopOnError` ambiguity** — pick a default and document; fail-fast is most common.

---

## 11. Senior follow-ups & variants

### Variant 1 — Async iterable input
`for await (const item of source)` inside a single producer; N consumers race for `source.next()`. Streams paginated APIs.

### Variant 2 — AbortSignal
Thread signal into worker + check `signal.aborted` at top of runner loop. On abort, runners exit cleanly.

### Variant 3 — Per-item timeout
Wrap worker in `Promise.race([worker(...), delay(ms).then(() => { throw new TimeoutError(); })])`.

### Variant 4 — Backpressure on results
Gate `cursor++` on downstream consumption. Becomes producer-consumer with bounded buffer.

### Variant 5 — Priority queue input
Items sorted by priority; pull highest-priority first. Use heap (see [min-heap-priority-queue.md](./min-heap-priority-queue.md)).

### Variant 6 — Semaphore-based alternative
```js
const sem = new Semaphore(limit);
return Promise.all(items.map((item, i) => sem.run(() => worker(item, i))));
```
Same result, slightly more allocations.

---

## 12. How to think aloud

> "N runner loops sharing a cursor. Each runner: `while (cursor < items.length) { i = cursor++; results[i] = await worker(items[i], i); }`. Memory O(N), not O(M). Output order preserved by writing to `results[i]`. For errors I'd ask: fail-fast or partial? Default fail-fast — `Promise.all(runners)`. Partial: return `{results, errors}` via `Promise.allSettled`. Don't chunk — chunks waste time on stragglers. Trap: `Promise.all(items.map(worker))` no bound. Trap: push results in completion order — wrong ordering. Trap: spawning `limit` runners when `limit > items.length`."

---

## 13. 60-second revision

> - **N runners** + shared `cursor` + indexed `results[i]` write.
> - **`while (cursor < items.length)`** drains the queue.
> - **Output order = input order** via `results[i]`.
> - **Memory O(N)** (runners), not O(M) (items).
> - **`stopOnError=true`** (default) → `Promise.all`; `false` → `Promise.allSettled` + `{results, errors}`.
> - **Spawn `Math.min(limit, items.length)`** runners.
> - **Alt:** `Semaphore + items.map(sem.run(worker))`.
> - **Trap:** `Promise.all(map)`; chunking; push (loses order); spawning over `items.length`.

---

**Related:** [async-semaphore.md](./async-semaphore.md) · [`04-promises/promise-pool.md`](../04-promises/promise-pool.md) · [`04-promises/sequential-vs-parallel-async-map.md`](../04-promises/sequential-vs-parallel-async-map.md) · [batched-request-coalescer.md](./batched-request-coalescer.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
