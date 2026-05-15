# Output Order: setTimeout vs Promise.then vs queueMicrotask

## Source
- Canonical output-prediction question: appears in nearly every senior JS interview.
- Reference: https://nodejs.org/en/learn/asynchronous-work/event-loop-timers-and-nexttick

## Why this question matters in interviews
Pure output prediction. The interviewer drops a 10-line snippet mixing sync logs, `setTimeout`, `Promise.then`, `queueMicrotask`, and `await`, then asks you to predict the exact order. Getting this wrong is a fast no-hire signal because the rules are mechanical, not creative: **microtasks (Promise jobs + queueMicrotask) drain to empty between every macrotask**. Once you internalize that one rule plus "`await` is sugar for `.then`", these snippets become trivial. Senior backend interviews use this to gate the rest of the round.

## Concepts involved

### The one rule that solves everything
> **Between every two macrotasks, the entire microtask queue is drained to empty.**

A macrotask is: a `setTimeout` callback, a `setInterval` callback, a `setImmediate` callback, an I/O callback, a `'message'` event handler, etc. Each one is a discrete unit picked from a phase queue.

A microtask is: a `.then` / `.catch` / `.finally` callback, a `queueMicrotask` callback, code after an `await`, a `MutationObserver` callback (browser).

`process.nextTick` is **higher priority than microtasks** but runs in the same interleave slot (drain to empty between callbacks). It's Node-specific.

### Syntax to know
```js
queueMicrotask(() => console.log('mt'));     // explicit microtask
Promise.resolve().then(() => console.log()); // implicit microtask
process.nextTick(() => console.log());       // Node only, before microtasks

setTimeout(() => console.log('mt'), 0);      // macrotask (timers phase)
setImmediate(() => console.log());           // Node only, macrotask (check)
```

### `await` mechanics
```js
async function f() {
  console.log('A');
  await Promise.resolve();   // suspends; rest is wrapped in a .then
  console.log('B');          // microtask
}
f();
console.log('C');
// Output: A, C, B
```
`await x` is equivalent to `Promise.resolve(x).then(v => /* code after await uses v */)`. The continuation after `await` is a microtask.

### Edge cases (interview traps)
1. **`setTimeout(fn, 0)` runs AFTER `Promise.resolve().then(fn)`** even though both look "immediate". Microtasks drain before the next macrotask.
2. **`queueMicrotask` and `.then` have the same priority** (both microtasks) — resolve in registration order.
3. **`process.nextTick` runs BEFORE microtasks** — including before `Promise.resolve().then`.
4. **Microtask scheduled from inside a microtask** runs in the same drain pass, before the next macrotask. (Same for nextTick — that's why recursive nextTick starves the loop.)
5. **`await` inside a for-loop** does NOT batch — each iteration's continuation is a separate microtask. For sequential ops, this is fine; for parallel, use `Promise.all`.
6. **Top-level await (ESM)** — the entire module body becomes async; `import` waits.
7. **Synchronous resolve doesn't make `.then` synchronous** — `new Promise(r => r(1)).then(...)` still schedules the `.then` as a microtask.
8. **Throwing in a `.then`** schedules a rejected promise; the next `.catch` is also a microtask.

## Brute force approach
"I'll just read top to bottom." Wrong for any async involvement. You must separate sync (runs immediately), microtasks (drain before next macrotask), and macrotasks (one per loop iteration).

## Optimal approach
Mental algorithm:
1. Walk the code; print every sync log.
2. As you encounter `setTimeout` / `setImmediate` / `fs.x`, add to the appropriate macrotask queue. **Don't fire yet.**
3. As you encounter `.then` / `queueMicrotask` / `process.nextTick`, add to the corresponding queue. **Don't fire yet.**
4. After sync code finishes: drain nextTick → drain microtask → pick ONE macrotask → repeat from step 3.

This algorithm produces the correct output every time.

## Solution (JavaScript)

```js
// The canonical snippet. Predict the exact output.
console.log('1');

setTimeout(() => console.log('2'), 0);

Promise.resolve()
  .then(() => console.log('3'))
  .then(() => console.log('4'));

queueMicrotask(() => console.log('5'));

(async function () {
  console.log('6');
  await null;                  // suspends here
  console.log('7');
})();

console.log('8');
```

```js
// Expected output:
// 1
// 6      ← async fn runs sync up to the await
// 8
// 3      ← first .then microtask
// 5      ← queueMicrotask (registered after the first .then)
// 7      ← await continuation microtask
// 4      ← second .then chained, scheduled when 3 resolves
// 2      ← setTimeout(0) macrotask, after ALL microtasks drained
```

## Step-by-step dry run

Tracking three queues: **MQ** (microtask), **Macro** (timers/check/etc), and the **Call Stack**.

| Step | Action | Output | MQ (front→back) | Macro |
|------|--------|--------|-----------------|-------|
| 1 | `console.log('1')` | `1` | — | — |
| 2 | `setTimeout(cbT, 0)` registered | — | — | `[cbT]` |
| 3 | `Promise.resolve().then(cb3)` registers cb3 as microtask | — | `[cb3]` | `[cbT]` |
| 4 | `.then(cb4)` chains to the promise returned by step 3 — cb4 is NOT scheduled yet; it's pending until cb3 resolves | — | `[cb3]` | `[cbT]` |
| 5 | `queueMicrotask(cb5)` | — | `[cb3, cb5]` | `[cbT]` |
| 6 | async IIFE runs: `console.log('6')`, then `await null` — wraps continuation `cb7` and schedules via microtask. async fn returns. | `6` | `[cb3, cb5, cb7]` | `[cbT]` |
| 7 | `console.log('8')` | `8` | `[cb3, cb5, cb7]` | `[cbT]` |
| 8 | Sync done. Drain microtasks. Pop cb3 → log `3`. cb3 returns undefined → the chained promise from step 3 resolves → cb4 (registered in step 4) is enqueued. | `3` | `[cb5, cb7, cb4]` | `[cbT]` |
| 9 | Drain continues. Pop cb5 → log `5`. | `5` | `[cb7, cb4]` | `[cbT]` |
| 10 | Pop cb7 → log `7`. (The await resumes the async fn; it returns.) | `7` | `[cb4]` | `[cbT]` |
| 11 | Pop cb4 → log `4`. | `4` | — | `[cbT]` |
| 12 | MQ empty. Pick next macrotask → cbT → log `2`. | `2` | — | — |

Final output: `1, 6, 8, 3, 5, 7, 4, 2`.

### Now add `process.nextTick` (Node)

```js
setTimeout(() => console.log('T'), 0);
Promise.resolve().then(() => console.log('P'));
process.nextTick(() => console.log('N'));
queueMicrotask(() => console.log('Q'));
console.log('S');
```

Trace:

| Step | NT | MQ | Macro | Output |
|------|----|----|----|--------|
| Sync logs `S` | `[N]` | `[P, Q]` | `[T]` | `S` |
| Drain NT first → `N` | — | `[P, Q]` | `[T]` | `N` |
| Drain MQ → `P`, `Q` | — | — | `[T]` | `P`, `Q` |
| Next macrotask → `T` | — | — | — | `T` |

Output: `S, N, P, Q, T`.

### With Node's `setImmediate`

```js
setImmediate(() => console.log('I'));
setTimeout(() => console.log('T'), 0);
Promise.resolve().then(() => console.log('P'));
```

From main module, `I` vs `T` order is **non-deterministic** (depends on whether the loop reaches timers before the 0ms deadline expires). But `P` always wins because it's a microtask.

Output is either `P, T, I` or `P, I, T`.

## Important takeaways

**The hierarchy (memorize, in order)**
1. Sync code on stack.
2. `process.nextTick` queue (Node).
3. Microtask queue (Promise jobs, `queueMicrotask`).
4. One macrotask from the next phase / task queue.
5. Goto 2 (drain 2 + 3 between every macrotask).

**`await` rule**
- `await x` = `.then(v => /* rest */)`. The body before await is sync; after await is a microtask.

**Common mistakes**
- Predicting `setTimeout(0)` before `Promise.then`. **Wrong** — microtasks drain first.
- Treating `queueMicrotask` differently from `.then` — they're the same priority.
- Forgetting that **chained** `.then`s create dependent microtasks — they're not all enqueued at once. The second `.then` waits for the first to resolve.
- Treating `process.nextTick` as a microtask — it has higher priority.
- Forgetting that the sync prefix of an async function runs synchronously.

**Where this shows up at work**
- "Why is this log out of order?" debugging.
- React's `useEffect` cleanup ordering, batched state updates.
- Tracing distributed traces / OpenTelemetry context propagation through async callbacks.
- Avoiding deadlocks with sync logic that assumes a microtask has drained.

## Variants

1. **With `try/finally` and rejections** — `Promise.reject().catch(...).finally(...)`. Predict ordering when `.then` throws mid-chain.

2. **Mixed `async/await` + `Promise.all`** — show that `await Promise.all([a, b])` resolves after all of them settle, but each settle still creates its own microtask.

3. **`MutationObserver` (browser)** — same microtask priority as Promise jobs. Used to demonstrate that microtasks are NOT just a Promise concept.

4. **`requestAnimationFrame`** — a third queue serviced once per browser repaint. Sits between macrotasks and the next paint, after all microtasks.

## Revision notes

> **microtask-macrotask-order — 60 second recap**
> - **Rule:** microtasks drain to EMPTY between every two macrotasks.
> - Sync > `process.nextTick` > microtasks (Promise, `queueMicrotask`) > one macrotask > repeat.
> - `await x` ≡ `.then(...)` — the post-await code is a microtask.
> - `setTimeout(0)` ALWAYS loses to `Promise.resolve().then`.
> - Chained `.then`s aren't all enqueued at once — each one waits for the prior to resolve.
> - `process.nextTick` (Node only) outranks Promise microtasks.
> - **Trap:** treating `queueMicrotask` differently from `.then` — both are microtasks.
> - **Trap:** infinite microtask chain blocks ALL macrotasks (including I/O).
> - Predict by walking sync logs first, then draining MQ, then ONE macrotask, then drain MQ again.
