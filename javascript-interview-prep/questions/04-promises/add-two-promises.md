# Implement `addTwoPromises(p1, p2)` — parallel-await-add

> **Difficulty:** Easy   |   **Time:** ~10 min   |   **Prereqs:** [`concepts/promises.md`](../../concepts/promises.md), [sleep.md](./sleep.md)
>
> **Source:** <a href="https://leetcode.com/problems/add-two-promises/" target="_blank" rel="noopener noreferrer">LeetCode 2723 — Add Two Promises</a>.

---

## 1. Problem statement

**Signature**
```ts
function addTwoPromises(p1: Promise<number>, p2: Promise<number>): Promise<number>;
```

**Input / Output examples**

| Inputs                                                          | Output                                |
|------------------------------------------------------------------|---------------------------------------|
| `Promise.resolve(2), Promise.resolve(3)`                        | resolves with `5`                     |
| `sleep(20, 2), sleep(60, 5)`                                    | resolves with `7` at t≈60 (parallel)  |
| `Promise.reject('boom'), Promise.resolve(5)`                   | rejects with `'boom'`                 |
| `Promise.resolve('5'), Promise.resolve(3)`                     | resolves with `'53'` (string concat)  |

**Constraints**
- Both promises run in **parallel**, not sequentially.
- Reject as soon as either input rejects.
- The async function's return is auto-wrapped in `Promise.resolve`.

---

## 2. Plain-English restatement

You're given two promises that each resolve to a number. Return a new promise that resolves to their sum. The two should be **awaited in parallel** — `Promise.all` + destructure — not chained sequentially.

Looks like a 5-minute warmup, but the interviewer is checking whether you instinctively write `await Promise.all([p1, p2])` vs `await p1; await p2`. The first is what production code should look like.

---

## 3. Why this matters in interviews

The canonical "do you actually understand async/await?" check. Three valid solutions: `await` + add, `Promise.all` + destructure, manual `.then` chaining. A senior candidate knows which is idiomatic and *why* the parallel one is strictly better than sequential awaits. The interviewer is watching for the same mistake juniors make daily in production: `const a = await fetchA(); const b = await fetchB();` instead of `const [a, b] = await Promise.all([fetchA(), fetchB()])`. Sequential awaits **double the wall-clock latency** for no reason — one of the single most common backend perf bugs.

---

## 4. Mental model

The two promises are already running when you receive them. Your job is to wait for both — not to *start* them sequentially. `Promise.all([p1, p2])` is the right primitive: it returns a single promise that fulfills with an array when both fulfill, or rejects on first rejection.

```
   addTwoPromises(p1, p2):
   
   p1 ─running ─────────┐
                        │ both must settle
   p2 ─running ─────────┤
                        ▼
                  Promise.all([p1, p2])
                  resolves with [v1, v2]
                  
                  return v1 + v2
   
   Wall time = max(t1, t2), NOT t1 + t2.
```

**Sequential `await` gives the same timing when inputs are already-running promises** (they run in parallel regardless). But the moment you reach for *factory functions* — `await fetchA(); await fetchB();` — sequential awaits serialize them. Mental discipline is "Promise.all by default."

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. If `p1` takes 20ms and `p2` takes 60ms, when does `addTwoPromises(p1, p2)` resolve?
> 2. If `p1` rejects at t=10 and `p2` would resolve at t=100, when does the function reject, and does `p2`'s work continue?
> 3. If `p1` resolves with `"5"` (string) and `p2` resolves with `3` (number), what's the output? Is that desirable?

---

## 6. Brute force — walked through

### Wrong attempt 1: sequential awaits

```js
async function addTwoPromises(p1, p2) {
  const a = await p1;
  const b = await p2;
  return a + b;
}
```

**Same timing** as the parallel version *when both inputs are already-running promises* — but the moment you replace either input with a factory call, you've doubled the latency. This is the muscle-memory trap. State the distinction:

```js
// SAFE — promises already running
await addTwoPromises(p1, p2);

// DANGEROUS — refactoring into sequential awaits with factory calls would double latency:
async function addAB() {
  const a = await fetchA();   // 200ms
  const b = await fetchB();   // 200ms — starts AFTER a resolves
  return a + b;                // total: 400ms
}
// vs.
async function addABParallel() {
  const [a, b] = await Promise.all([fetchA(), fetchB()]);
  return a + b;                // total: 200ms
}
```

### Wrong attempt 2: wrap return in `Promise.resolve`

```js
async function addTwoPromises(p1, p2) {
  const [a, b] = await Promise.all([p1, p2]);
  return Promise.resolve(a + b);   // BUG: redundant double-wrap
}
```

An `async` function's return value is **auto-wrapped** in `Promise.resolve`. Returning a Promise from `async` is fine — the engine flattens it — but `Promise.resolve(a + b)` is noise.

### Wrong attempt 3: manual `.then` chaining

```js
function addTwoPromises(p1, p2) {
  return p1.then((a) => p2.then((b) => a + b));   // nested
}
```

Works but nested. The outer `.then` returns the inner promise; chaining waits for it. Less readable than `Promise.all` + destructure.

---

## 7. The unlocking insight

> **`Promise.all([p1, p2])` is the right primitive for "wait for both, in parallel." Async functions auto-wrap returns in `Promise.resolve`; don't double-wrap.**

Three properties:

1. **`Promise.all` does not start promises** — they're already running. It just waits for both to settle.
2. **Fail-fast.** If `p1` rejects, `Promise.all` rejects immediately with that reason. `p2` continues running but its result is discarded.
3. **Auto-wrap.** `async function f() { return 5; }` returns `Promise.resolve(5)`. `return new Promise(...)` works too — the engine flattens.

The interview check: do you write `await Promise.all([p1, p2])` instinctively, or fall into the sequential-await habit?

---

## 8. Solution (annotated)

```js
async function addTwoPromises(p1, p2) {
  const [a, b] = await Promise.all([p1, p2]);   // step 1: wait for both in parallel
  return a + b;                                   // step 2: auto-wrapped in Promise.resolve
}

// Equivalent without async/await
function addTwoPromisesThen(p1, p2) {
  return Promise.all([p1, p2]).then(([a, b]) => a + b);
}
```

**Try it yourself**

```js
const sleep = (ms, v) => new Promise((r) => setTimeout(() => r(v), ms));

const sum = await addTwoPromises(sleep(20, 2), sleep(60, 5));
console.log(sum);   // 7 at t≈60ms (NOT t=80ms — parallel)

// Fail-fast
try {
  await addTwoPromises(Promise.reject(new Error('boom')), sleep(1000, 5));
} catch (e) {
  console.log(e.message);   // 'boom' — p2 still runs but its 5 is discarded
}

// String coercion
await addTwoPromises(Promise.resolve('5'), Promise.resolve(3));   // '53'
```

---

## 9. Step-by-step dry run

Input:

```js
const p1 = new Promise((r) => setTimeout(() => r(2), 20));
const p2 = new Promise((r) => setTimeout(() => r(5), 60));
addTwoPromises(p1, p2).then(console.log);
```

Values-first trace:

| Time (ms) | Event                                                | State                    |
|-----------|-------------------------------------------------------|---------------------------|
| 0         | `p1`, `p2` constructed; both timers scheduled         | both pending             |
| 0         | `addTwoPromises(p1, p2)` invoked; hits `await Promise.all`; suspends | pending           |
| 20        | `p1` resolves with `2`; Promise.all internal counter 1/2 | partial                |
| 60        | `p2` resolves with `5`; counter 2/2; Promise.all resolves `[2, 5]` | settled         |
| 60+µ      | async fn resumes; destructures; returns `7`           | function's promise resolves |
| 60+2µ     | `.then(console.log)` fires → prints `7`              |                          |

**Total wall time: ~60ms** (max of the two), not ~80ms (sum). That's the parallelism win.

Rejection trace:

```js
addTwoPromises(Promise.reject(new Error('boom')), sleep(1000, 5))
  .catch((e) => console.log(e.message));
```

| Time | Event                                          | State        |
|------|------------------------------------------------|---------------|
| 0    | `Promise.all` sees `p1` already rejected       | rejecting    |
| 0+µ  | `Promise.all` rejects with `Error('boom')`     | rejected     |
| 0+µ  | async fn's `await` throws; function rejects    | rejected     |
| 0+2µ | `.catch` fires → prints `'boom'`              | done         |
| 1000 | `p2`'s timer fires, resolves with `5`; ignored | (discarded)  |

`p2` keeps running — `Promise.all` doesn't cancel siblings. For true cancellation, wrap with AbortController.

---

## 10. Common confusion + traps

1. **Sequential awaits with factory functions.**
   ```js
   const a = await fetchA();   // 200ms
   const b = await fetchB();   // another 200ms — sequential!
   ```
   Doubles latency. Switch to `Promise.all`.

2. **Wrapping return in `Promise.resolve`.**
   `async` auto-wraps. `return Promise.resolve(x)` is noise.

3. **Forgetting `Promise.all` is fail-fast.**
   If you need all results regardless of rejections, use `Promise.allSettled`. If you need the first success, use `Promise.any`.

4. **Mutating shared state inside the awaited promises.**
   Order of resolution is unpredictable. Don't rely on which finishes first.

5. **String coercion bites.**
   `"5" + 3 === "53"`. If the contract is numeric, validate types or coerce explicitly with `Number()`.

6. **`p1 === p2` works.**
   Same promise passed twice — Promise.all destructures both positions with the same value.

7. **Awaiting non-thenables.**
   `await 5` is legal — wraps in `Promise.resolve(5)`, costs one microtask hop.

---

## 11. Senior follow-ups & variants

### Variant 1 — Sum N promises

```js
async function sumPromises(arr) {
  return (await Promise.all(arr)).reduce((s, x) => s + x, 0);
}
```

Scales the pattern. Same parallelism guarantee.

### Variant 2 — Partial failure tolerance

```js
async function sumWithFailureTolerance(arr) {
  const settled = await Promise.allSettled(arr);
  return settled.reduce((s, r) => s + (r.status === 'fulfilled' ? r.value : 0), 0);
}
```

Treat rejections as zero. Use case: aggregate scores across services where some may be down.

### Variant 3 — Type-strict variant

```js
async function addTwoPromisesStrict(p1, p2) {
  const [a, b] = await Promise.all([p1, p2]);
  if (!Number.isFinite(a) || !Number.isFinite(b)) {
    throw new TypeError('both inputs must resolve to finite numbers');
  }
  return a + b;
}
```

Defensive coding posture; prevents string-coercion surprises.

### Variant 4 — Concurrent with timeout

```js
async function addTwoPromisesWithTimeout(p1, p2, ms) {
  return Promise.race([
    addTwoPromises(p1, p2),
    new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), ms)),
  ]);
}
```

Compose with race for deadline enforcement.

---

## 12. How to think aloud in the interview

> "`const [a, b] = await Promise.all([p1, p2]); return a + b;`. One line, parallel by construction. Promise.all is fail-fast — first reject wins; siblings keep running but results discarded. Async function auto-wraps the return in `Promise.resolve` — no need for explicit wrapping. The mental discipline is `Promise.all` by default for independent waits — sequential awaits serialize *factory calls*, which doubles latency. For partial-failure tolerance, swap to `allSettled` + filter. For first-success-wins, `any`. For deadline, race with a setTimeout-rejecter."

---

## 13. 60-second revision

> - **`const [a, b] = await Promise.all([p1, p2]); return a + b;`** — one line.
> - `Promise.all` is **fail-fast**; siblings keep running but results discarded.
> - `async` return is **auto-wrapped** in `Promise.resolve`. Don't double-wrap.
> - **Parallel by construction.** Sequential awaits would serialize factory calls (doubles latency).
> - **Family:** `Promise.all` (all-or-first-reject), `allSettled` (wait-all), `race` (first-either), `any` (first-fulfill).
> - **Trap:** sequential awaits with factory functions; wrapping return in `Promise.resolve`.

---

**Related:** [promise-all-polyfill.md](./promise-all-polyfill.md) · [sequential-vs-parallel-async-map.md](./sequential-vs-parallel-async-map.md) · [sleep.md](./sleep.md) · [promise-allsettled-polyfill.md](./promise-allsettled-polyfill.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
