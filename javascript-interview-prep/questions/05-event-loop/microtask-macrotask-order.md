# Output Order — `setTimeout` vs `Promise.then` vs `queueMicrotask`

> **Difficulty:** Senior   |   **Time:** ~15 min   |   **Prereqs:** [event-loop-concurrency.md](./event-loop-concurrency.md)
>
> **Source:** Canonical output-prediction puzzle — appears in every senior JS interview.

---

## 1. Problem statement

Predict exact log order for snippets mixing sync, `setTimeout`, `Promise.then`, `queueMicrotask`, `await`, and (in Node) `process.nextTick`/`setImmediate`.

**Verification examples**

| Snippet                                                               | Output                            |
|------------------------------------------------------------------------|-----------------------------------|
| `log(1); setTimeout(()=>log(2),0); Promise.resolve().then(()=>log(3)); log(4)` | `1, 4, 3, 2`                      |
| `log(1); queueMicrotask(()=>log(2)); Promise.resolve().then(()=>log(3))` | `1, 2, 3` (FIFO microtask)        |
| `log(1); setTimeout(()=>log(2),0); process.nextTick(()=>log(3)); Promise.resolve().then(()=>log(4))` | `1, 3, 4, 2` (Node)           |
| `async function f(){log('A'); await null; log('B')} f(); log('C')` | `A, C, B`                         |

**Constraints**
- **Microtasks drain to EMPTY** between every macrotask.
- `await x` ≡ `.then(...)` — continuation is a microtask.
- `process.nextTick` (Node) outranks microtasks.
- Chained `.then`s aren't all enqueued at once.

---

## 2. Plain-English restatement

The interviewer drops a 10-line snippet mixing async APIs. You predict the exact log order. Rules are mechanical: walk top to bottom, queue async callbacks into their right buckets, drain in priority order after sync code, and **drain ALL microtasks before any macrotask**.

---

## 3. Why this matters in interviews

Output prediction gate — fast no-hire if you guess. Tests whether you've internalized the priority rules (not just memorized "Promise wins").

---

## 4. Mental model

```
   Single rule that solves everything:
   Between every two macrotasks, the ENTIRE microtask queue drains to empty.

   Algorithm:
   1. Walk top to bottom. Print every sync log.
   2. Push setTimeout/setImmediate/I/O cb into macrotask queues.
   3. Push .then/queueMicrotask/await-continuation into microtask queue.
   4. Push process.nextTick into nextTick queue (Node).
   5. After sync code: drain nextTick → drain microtask → pick ONE macrotask → goto 4.

   `await x` is sugar:
     await x;
     // code after await
   ≡
     Promise.resolve(x).then(v => /* code after await */);
   The post-await body is a MICROTASK.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Does `setTimeout(0)` ever run before `Promise.resolve().then`? Why/why not?
> 2. Are `queueMicrotask(fn)` and `Promise.resolve().then(fn)` the same priority?
> 3. In `async function f(){log('A'); await x; log('B')}`, what's between A and B in the output?

---

## 6. Brute force — walked through

### Wrong attempt 1: read top to bottom
Wrong for any async involvement.

### Wrong attempt 2: "setTimeout(0) fires soonest because it's 0ms"
Wrong. Microtasks drain first.

### Wrong attempt 3: enqueue all chained `.then`s at once
Wrong. Each `.then` waits for the prior to resolve.

---

## 7. The unlocking insight

> **Walk sync first; drain nextTick (Node) → drain microtasks → run ONE macrotask → repeat. Each chained `.then` waits for the prior promise to resolve, then enqueues its continuation as a NEW microtask. `await x` is `.then` syntactic sugar — continuation is a microtask.**

Three properties:

1. **Microtasks drain to EMPTY** between macrotasks.
2. **Chained `.then`s** are dependent, not co-enqueued.
3. **`await` continuation** is always a microtask.

---

## 8. Solution (annotated)

```js
console.log('1');                                                    // sync

setTimeout(() => console.log('2'), 0);                                // macrotask T

Promise.resolve()
  .then(() => console.log('3'))                                       // microtask M3
  .then(() => console.log('4'));                                      // M4 (chained — enqueued after M3 resolves)

queueMicrotask(() => console.log('5'));                               // microtask M5

(async function () {
  console.log('6');                                                    // sync (inside IIFE)
  await null;                                                          // suspend; continuation M7
  console.log('7');                                                    // microtask M7
})();

console.log('8');                                                      // sync

// Output: 1, 6, 8, 3, 5, 7, 4, 2
//
// 1, 6, 8        — all sync.
// 3              — first .then microtask.
// 5              — queueMicrotask (registered AFTER first .then).
// 7              — await continuation.
// 4              — second .then, enqueued when first .then resolves
//                  (during the drain pass, AFTER 5 and 7).
// 2              — setTimeout(0), only after all microtasks drained.
```

**With `process.nextTick` (Node):**

```js
setTimeout(() => console.log('T'), 0);
Promise.resolve().then(() => console.log('P'));
process.nextTick(() => console.log('N'));
queueMicrotask(() => console.log('Q'));
console.log('S');

// Output: S, N, P, Q, T
// Sync first → drain NT (N) → drain MQ (P, then Q in registration order) → macrotask (T).
```

**Try it yourself**

```js
async function fetchAndLog() {
  console.log('start');
  await Promise.resolve();
  console.log('after await 1');
  await Promise.resolve();
  console.log('after await 2');
}
fetchAndLog();
console.log('end');

// Output: start, end, after await 1, after await 2
// Each await suspends → next continuation runs as separate microtask.
```

---

## 9. Step-by-step dry run

```
Queues: MQ (microtask), NT (nextTick, Node), Macro

t=0:
  log '1'                            output: 1
  setTimeout(cb_T, 0)                 Macro=[cb_T]
  Promise.resolve().then(cb_3)        MQ=[cb_3]
  .then(cb_4)                         cb_4 NOT enqueued yet — chained, depends on cb_3
  queueMicrotask(cb_5)                MQ=[cb_3, cb_5]
  IIFE: log '6'                       output: 1, 6
        await null suspends; continuation = cb_7
                                       MQ=[cb_3, cb_5, cb_7]
  log '8'                              output: 1, 6, 8

Sync done. Drain microtasks:
  pop cb_3 → log '3' → returns; previous promise resolves; cb_4 enqueued
                                       MQ=[cb_5, cb_7, cb_4]
                                       output: 1, 6, 8, 3
  pop cb_5 → log '5'                  output: ..., 5
  pop cb_7 → log '7' (await resume)   output: ..., 7
  pop cb_4 → log '4'                  output: ..., 4

MQ empty. Pick next macrotask:
  run cb_T → log '2'                   output: 1, 6, 8, 3, 5, 7, 4, 2
```

---

## 10. Common confusion + traps

1. **`setTimeout(0)` before `Promise.then`** — never; MQ drains first.
2. **`queueMicrotask` != `.then`** — they ARE the same priority (FIFO).
3. **All chained `.then`s enqueued at once** — no, each waits for the prior's resolution.
4. **`process.nextTick` is a microtask** — no, separate higher-priority queue.
5. **`async` function runs entirely later** — runs sync up to first `await`.
6. **`await null` is a no-op** — still enqueues a microtask continuation.
7. **`MutationObserver`** — also microtask priority (browser).

---

## 11. Senior follow-ups & variants

### Variant 1 — With `try/finally` and rejections
`.catch` and `.finally` are microtasks. `finally` returns the original value (or rejection) unchanged.

### Variant 2 — `Promise.all` ordering
`await Promise.all([a, b])` resolves after BOTH settle; each settle still creates own microtask.

### Variant 3 — `requestAnimationFrame` (browser)
Third queue, serviced once per repaint, after microtasks but before next macrotask.

### Variant 4 — `MessageChannel` (browser/Node)
Macrotask (not microtask) — fastest yield primitive in cooperative schedulers.

### Variant 5 — Top-level await (ESM)
Module body becomes async; `import`-ers wait.

---

## 12. How to think aloud

> "Walk top to bottom. Print sync logs. Push setTimeout/setImmediate to macrotask queue; .then/queueMicrotask/await-continuation to microtask queue; process.nextTick to NT queue (Node). After sync done: drain NT → drain MQ → run ONE macrotask → re-drain NT + MQ. Chained .then's aren't co-enqueued — each waits for prior to resolve. `await x` ≡ `.then(...)` — continuation is microtask. Trap: assuming setTimeout(0) beats Promise.then. Trap: treating queueMicrotask as a different priority. Trap: forgetting sync prefix of async fn."

---

## 13. 60-second revision

> - **Microtasks drain to EMPTY between every macrotask.**
> - **Priority:** sync → `process.nextTick` (Node) → microtasks → one macrotask.
> - **`await x` ≡ `.then(...)`** — post-await is microtask.
> - **`setTimeout(0)` ALWAYS loses to `Promise.then`.**
> - **Chained `.then`s** depend; each enqueues NEW microtask when prior resolves.
> - **`queueMicrotask` == `.then`** priority.
> - **`process.nextTick`** > microtasks (Node).
> - **Trap:** `setTimeout(0)` "soonest"; chained then co-enqueue; async fn entirely later.

---

**Related:** [event-loop-concurrency.md](./event-loop-concurrency.md) · [predict-mixed-async-output.md](./predict-mixed-async-output.md) · [nexttick-vs-setimmediate.md](./nexttick-vs-setimmediate.md) · [queuemicrotask-deep-dive.md](./queuemicrotask-deep-dive.md)

**Concept primer:** [`concepts/event-loop.md`](../../concepts/event-loop.md), [`concepts/promises.md`](../../concepts/promises.md)
