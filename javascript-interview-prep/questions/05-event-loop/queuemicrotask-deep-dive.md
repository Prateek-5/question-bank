# `queueMicrotask` — when (and why) to use it over `Promise.resolve().then()`

## Source
- WHATWG HTML spec: https://html.spec.whatwg.org/multipage/webappapis.html#microtask-queuing
- MDN: https://developer.mozilla.org/en-US/docs/Web/API/queueMicrotask
- Node.js docs: https://nodejs.org/api/globals.html#queuemicrotaskcallback
- v8.dev microtask post: https://v8.dev/features/promise-combinators (background reading)

## Why this question matters in interviews
Mid-level engineers say "queueMicrotask is the same as `Promise.resolve().then` — pick whichever." Senior engineers know the **three concrete differences**: allocation cost, exception semantics, and intent. This question is a fast-paced 3-minute litmus test that an interviewer uses to gauge how deeply you've read the spec vs. how much you've cargo-culted. Real backend uses: schedulers (React/Vue use queueMicrotask under the hood), batched-update libraries, observer notifiers, and any spot where you want "run after the current sync work, but before I/O."

## Concepts involved

### Syntax to lock in
```js
queueMicrotask(() => {
  // Runs after current sync code, before next macrotask / phase.
});

// "Equivalent" using Promise:
Promise.resolve().then(() => {
  // Same scheduling tier.
});
```

### Three real differences (the senior answer)

#### 1. **Allocation cost**
- `Promise.resolve().then(fn)` allocates: a Promise, an array of reactions, a microtask record, and a continuation closure.
- `queueMicrotask(fn)` allocates: a microtask record. Period.
- In hot paths (e.g., scheduler firing thousands of times per second), the savings matter. React's scheduler does this measurement live.

#### 2. **Exception semantics** (the gotcha)
- `Promise.resolve().then(fn)`: if `fn` throws, the **rejection is swallowed** by the unhandled promise rejection mechanism. You get an `unhandledRejection` event eventually, but the error is wrapped in a Promise. Stack traces are mangled.
- `queueMicrotask(fn)`: if `fn` throws, Node emits an `uncaughtException` (and the browser emits `error` on `window`). The error is propagated as if from sync code. **No promise wrapping.**

Demonstration:
```js
queueMicrotask(() => { throw new Error('a'); });          // -> uncaughtException
Promise.resolve().then(() => { throw new Error('b'); });  // -> unhandledRejection
```

This matters because:
- `uncaughtException` is the *correct* failure mode for "this should never fail." It triggers process supervisors (pm2, systemd) to restart.
- `unhandledRejection` is treated more leniently by Node (process *can* be kept alive in old versions, though Node 16+ exits by default).

#### 3. **Intent / API surface**
- `queueMicrotask` says "defer this." There is no return value, no chaining, no promise to await.
- `Promise.resolve().then` looks like you're computing a value. Other engineers reading the code may try to `await` the result, leading to confusion.

### Edge cases
1. **Both tiers are identical for scheduling** — both go to the microtask queue. Order is FIFO; no priority between them.
2. **Inside browsers**, `MutationObserver` callbacks are also microtasks. `queueMicrotask` joined them in 2019 (Chrome 71+).
3. **`MessageChannel` is NOT a microtask** — it's a macrotask (task in HTML spec). Often confused. See the separate question in this bucket.
4. **Microtasks queued from microtasks** drain in the *same* flush. You can infinite-loop the microtask queue and starve macrotasks. (Try `function loop() { queueMicrotask(loop); } loop();` — your timer callbacks never fire.)
5. **Inside a microtask**, `process.nextTick` still wins. nextTick is drained before microtask continuation in Node.
6. **`Promise.resolve(thenable)`** is *different* from `Promise.resolve(value)` — if you pass a thenable, the runtime calls `.then` and may insert **extra microtask hops**. This is a footgun. `queueMicrotask` avoids it.

## Brute force approach
"Just use whichever; they're the same." This is a junior answer. The interviewer is testing whether you know the *cheaper* option, the *exception-safe* option, and the *intent-clearer* option.

## Optimal approach
Default to `queueMicrotask` for fire-and-forget scheduling. Reserve `Promise.resolve().then` for when you legitimately need a Promise (chaining, awaiting). The rule of thumb: **if you don't use the returned Promise, use `queueMicrotask`**.

## Solution (JavaScript)

A real scheduler-style use case:

```js
/**
 * Batched flush — collect updates synchronously, fire one callback per microtask.
 * Used by React, Vue, MobX, and most reactive libs.
 */
function createBatcher(flushFn) {
  let scheduled = false;
  const queue = [];

  return function enqueue(item) {
    queue.push(item);
    if (scheduled) return;
    scheduled = true;
    // queueMicrotask: 1 allocation, exceptions propagate as uncaughtException.
    queueMicrotask(() => {
      scheduled = false;
      const batch = queue.splice(0);
      flushFn(batch);
    });
  };
}

const batcher = createBatcher((batch) => {
  console.log('flush', batch);
});

batcher('a');
batcher('b');
batcher('c');
// After current sync work, logs: flush [ 'a', 'b', 'c' ]
```

Contrast with the Promise version:

```js
function createBatcherPromise(flushFn) {
  let scheduled = false;
  const queue = [];
  return function enqueue(item) {
    queue.push(item);
    if (scheduled) return;
    scheduled = true;
    Promise.resolve().then(() => {  // allocates a Promise + then-record per flush
      scheduled = false;
      const batch = queue.splice(0);
      flushFn(batch);                // if this throws → unhandledRejection (swallowed)
    });
  };
}
```

For a UI lib that flushes 10,000 times in a benchmark, the GC pressure from the Promise version is measurable. React's scheduler specifically benchmarked this and prefers `MessageChannel` or `queueMicrotask`.

## Step-by-step dry run

```js
console.log('1');
queueMicrotask(() => {
  console.log('2');
  queueMicrotask(() => console.log('3'));         // queues onto same flush
  Promise.resolve().then(() => console.log('4')); // also same microtask tier
});
Promise.resolve().then(() => console.log('5'));
queueMicrotask(() => console.log('6'));
console.log('7');
```

Trace:
- Sync: log `1`, queue mt-A (logs 2), queue mt-B (logs 5), queue mt-C (logs 6), log `7`.
- Output so far: `1`, `7`.
- Microtask queue: `[A, B, C]`.
- Drain A: log `2`. Inside A, queue mt-D (logs 3) and mt-E (logs 4). Queue is now `[B, C, D, E]`.
- Drain B: log `5`.
- Drain C: log `6`.
- Drain D: log `3`.
- Drain E: log `4`.

**Output**: `1 7 2 5 6 3 4`.

The key insight: microtasks queued *during* a microtask drain go to the **same flush**, after the currently-queued ones.

## Important takeaways

**Syntax to memorize**
- `queueMicrotask(fn)` — no return, no args, exceptions propagate.
- `Promise.resolve().then(fn)` — returns a Promise, exceptions caught as rejections.

**Patterns to reuse**
- Batched flush pattern (`scheduled` flag + `queueMicrotask`) for reactive libs.
- Defer "end of current tick" notifications without polluting the Promise graph.
- Yield to the next phase without a full macrotask (use `setImmediate` for macrotask yield).

**Common mistakes**
- Believing they're "completely identical." They're not — exception path differs.
- Using `Promise.resolve().then` in a hot loop and creating GC pressure.
- Expecting `queueMicrotask` to fire on the next macrotask. It fires *before* the next macrotask, at the next microtask checkpoint.
- Infinite microtask recursion. `queueMicrotask` can starve I/O just like `nextTick` (though Node tries to mitigate after Node 11).

**Related questions**
- `process.nextTick` vs microtask priority
- `MessageChannel` for cross-realm task scheduling
- React Scheduler internals
- Mixed-async output prediction

## Variants

1. **"Implement queueMicrotask as a polyfill for old browsers"** — typical answer: `Promise.resolve().then(fn)`. Bonus: discuss the exception-semantics mismatch you can't fix without engine help.
2. **"How would you build a Promise from scratch without using `then`?"** — you'd need a microtask-scheduling primitive, which is exactly `queueMicrotask`.
3. **"Microtask vs nextTick — which should I use?"** — nextTick is Node-only and **higher priority**. Use nextTick for "before any I/O." Use microtask for "after current sync." If you're writing cross-platform code, microtask.
4. **"What did Node 11 change about microtask processing?"** — pre-11, microtasks drained only between phases; post-11, after every individual callback within a phase. Aligns with browser semantics.

## Revision notes

> **queueMicrotask vs Promise.then — 60 second recap**
> - Same scheduling tier (microtask queue, FIFO).
> - `queueMicrotask`: **no Promise allocation**, exceptions become `uncaughtException`.
> - `Promise.resolve().then`: allocates Promise + reactions, exceptions become `unhandledRejection`.
> - Default to `queueMicrotask` for fire-and-forget; use Promise when you need to chain/await.
> - React/Vue/MobX schedulers use it for batched flushes.
> - Microtasks queued during a flush drain in the **same** flush — can starve macrotasks.
> - **Trap:** assuming "they're identical." They're not on the exception path.
