# Cancellable Promise — wrapper + `AbortController`

> **Difficulty:** Medium-Senior   |   **Time:** ~20 min   |   **Prereqs:** [`04-promises/fetch-with-abort.md`](../04-promises/fetch-with-abort.md), [`04-promises/abortcontroller-fanout.md`](../04-promises/abortcontroller-fanout.md)
>
> **Source:** Domenic Denicola's withdrawn TC39 cancellation proposals, bluebird's `Promise.cancel`. Modern answer: `AbortController` (Node 15+).

---

## 1. Problem statement

**Signature**
```ts
function makeCancellable<T>(p: Promise<T>): {
  promise: Promise<T>;
  cancel(): void;
  isCancelled(): boolean;
};
```

**Input / Output examples**

| Setup                                                | Behaviour                                              |
|------------------------------------------------------|---------------------------------------------------------|
| `{promise, cancel} = makeCancellable(slow); cancel()`| wrapper rejects with CancelError; original still runs  |
| `fetch(url, {signal})` then `controller.abort()`     | actual HTTP request torn down                          |
| Cancel after promise has settled                     | no-op (wrapper already settled)                        |
| Cancel twice                                         | safe (idempotent flag)                                 |
| `signal.aborted` already true when wrapping          | wrapper rejects immediately                            |

**Constraints**
- Native Promises are intentionally **not** cancellable — settlement is monotonic.
- The wrapper **ignores** the original's settlement; it doesn't stop work.
- For real cancellation: `AbortController` — underlying API listens to `signal.aborted`.

---

## 2. Plain-English restatement

You can't cancel a Promise's settlement — once the executor calls `resolve` or `reject`, the state is locked. What you CAN cancel: the **consumer's interest** in the result. Either via a wrapper that flips a flag and rejects when the original settles (work still runs), or via `AbortController` if the underlying API supports it (work actually stops).

---

## 3. Why this matters in interviews

A **conceptual trap question.** Many candidates start writing `promise.cancel()` and get derailed. The senior answer leads with the distinction: cancelling the **work** (AbortController) vs cancelling the **awaiter** (wrapper). Tests: closures over a flag, Promise constructor mechanics, microtask scheduling, the discipline to say "this is a wrapper, the underlying fetch is still running."

---

## 4. Mental model

```
   Wrapper approach (work still runs):
   ┌─────────────────────────────────────────────────────────────┐
   │ original Promise                                            │
   │  ┌────────────────────────────────────┐                     │
   │  │ executor: setTimeout(1000ms)        │ → still runs       │
   │  └────────────────────────────────────┘                     │
   │           ↓ settles at t=1000                                │
   │   wrapper's .then(v => cancelled ? reject(Cancel) : resolve(v))│
   └─────────────────────────────────────────────────────────────┘

   cancel() at t=100:  flips flag.
   At t=1000: original resolves → wrapper sees flag → rejects.
   The 1000ms timer DID fire. Only the wrapper ignored.

   AbortController approach (real cancellation):
   ┌─────────────────────────────────────────────────────────────┐
   │ const ctrl = new AbortController()                          │
   │ fetch(url, { signal: ctrl.signal })                          │
   │   └─ fetch listens to signal; closes socket on abort         │
   │ ctrl.abort()                                                 │
   │   └─ underlying request torn down; no bytes received         │
   └─────────────────────────────────────────────────────────────┘
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. After `cancel()`, does the original Promise's timer/fetch actually stop?
> 2. Why did TC39 drop the cancellable-Promise proposal?
> 3. What's the right tool to actually stop an in-flight `fetch`?

---

## 6. Brute force — walked through

### Wrong attempt 1: "don't call `.then`"
The original still runs and any chained side effects fire. Doesn't help.

### Wrong attempt 2: mutate the Promise's internal state
No API. Promise state is engine-private.

### Wrong attempt 3: `Promise.race` against a cancel-rejected promise
Works for the consumer (race settles first), but original is still running and its `.then` handlers (if any) still fire. Use only if you don't care about side effects.

---

## 7. The unlocking insight

> **Two distinct tools for two distinct goals: (1) wrapper that flips a flag and overrides settlement — the original still runs. (2) `AbortController` + `signal` — the underlying API listens and tears down the work. Modern code uses AbortController; the wrapper is for APIs that don't accept signals.**

Three properties:

1. **Native Promises** are intentionally non-cancellable (monotonic settlement).
2. **Wrapper cancels the awaiter** — flag + override in the wrapper's executor.
3. **AbortController cancels the work** — signal listened to by the underlying API.

---

## 8. Solution (annotated)

```js
class CancelError extends Error {
  constructor() { super('Cancelled'); this.name = 'CancelError'; }
}

function makeCancellable(promise) {
  let cancelled = false;                                            // step 1: closure flag

  const wrapped = new Promise((resolve, reject) => {                 // step 2: outer wrapper
    promise.then(
      (v) => cancelled ? reject(new CancelError()) : resolve(v),     // step 3: gate settlement
      (e) => cancelled ? reject(new CancelError()) : reject(e),
    );
  });

  return {
    promise: wrapped,
    cancel: () => { cancelled = true; },                              // step 4: flip flag
    isCancelled: () => cancelled,
  };
}

// Bridge AbortSignal → wrapper for libs that don't accept signals
function fromSignal(promise, signal) {
  const c = makeCancellable(promise);
  if (signal.aborted) c.cancel();
  else signal.addEventListener('abort', () => c.cancel(), { once: true });
  return c.promise;
}

// Cancellable setTimeout — REAL cancellation, not a wrapper
function delay(ms, { signal } = {}) {
  return new Promise((resolve, reject) => {
    const onAbort = () => { clearTimeout(t); reject(new CancelError()); };
    const t = setTimeout(() => {
      signal?.removeEventListener('abort', onAbort);
      resolve();
    }, ms);
    if (signal?.aborted) onAbort();
    else signal?.addEventListener('abort', onAbort, { once: true });
  });
}
```

**Try it yourself**

```js
// Wrapper approach
const slow = new Promise((r) => setTimeout(() => r('done'), 1000));
const { promise, cancel } = makeCancellable(slow);
promise.then((v) => console.log('got', v), (e) => console.log('rej', e.name));
setTimeout(cancel, 100);
// At t=100: cancelled=true.
// At t=1000: slow resolves 'done'; wrapper sees flag → rejects 'CancelError'.

// AbortController approach (real cancellation)
const ctrl = new AbortController();
delay(1000, { signal: ctrl.signal }).then(() => 'done', (e) => e.name);
setTimeout(() => ctrl.abort(), 100);
// At t=100: timer cleared; rejects immediately. Timer never fires at t=1000.
```

---

## 9. Step-by-step dry run

```
Wrapper approach:
  t=0    new Promise(executor): setTimeout(1000ms) started
         makeCancellable(slow):
           cancelled=false
           wrapped = new Promise(executor2)
             executor2 attaches .then to slow:
               slow.then(v => cancelled ? reject(Cancel) : resolve(v), ...)
           return {promise: wrapped, cancel}

  t=100  cancel() runs → cancelled=true
         (no immediate effect on wrapper or slow)

  t=1000 slow's setTimeout fires → slow resolves with 'done'
         microtask: slow's .then handler runs:
           cancelled === true → reject(new CancelError())
         wrapped rejects.

  Output: rej CancelError. Timer DID run; original DID resolve.

AbortController approach:
  t=0    delay(1000, {signal}):
           setTimeout(1000ms) → t handle
           signal.addEventListener('abort', onAbort, {once:true})

  t=100  ctrl.abort():
           signal.aborted = true; dispatch 'abort' event
           onAbort runs:
             clearTimeout(t)   ← TIMER ACTUALLY CANCELLED
             reject(new CancelError())

  t=1000 (nothing happens — timer was cleared)

  Output: rej CancelError. Underlying work stopped.
```

---

## 10. Common confusion + traps

1. **"I cancelled the Promise"** — no, you cancelled the wrapper; original work still ran.
2. **Cancel twice** — flag should be idempotent; wrapper Promise settles once.
3. **Cancel after settlement** — no-op; wrapper already settled.
4. **`Promise.race` as cancel** — original still running; doesn't stop side effects.
5. **Forgetting to remove abort listener** — memory leak in long-lived signals.
6. **Reusing one AbortController for many ops** — can't cancel one without cancelling all. Use `AbortSignal.any([...])`.
7. **TC39 dropped Promise.cancel** — chaining cancellation propagation is unsolvable cleanly; AbortController is the agreed answer.

---

## 11. Senior follow-ups & variants

### Variant 1 — Promise + AbortSignal combination
Accept a signal in the API; on abort, wrapper rejects AND underlying work signaled to stop. Composes with `fetch`, streams.

### Variant 2 — Cancel with cleanup
`makeCancellable(promise, { onCancel: () => closeSocket() })`. Runs cleanup before rejecting. Bridges to resource management.

### Variant 3 — Hierarchical cancellation (`AbortSignal.any` ES2024)
Parent signal cancels all child signals. Used for "cancel all in-flight requests for this user logout."

### Variant 4 — Race-with-timeout
`Promise.race([promise, delay(ms).then(() => { throw new TimeoutError(); })])`. Combine with cancellation so timeout also stops underlying work.

### Variant 5 — `Promise.withResolvers` (ES2024)
Externalizes resolve/reject without the constructor callback dance. Cleaner for advanced cancellation control.

### Variant 6 — Async iterator cancellation
`for await (const x of iter)` supports `iter.return()` for explicit cleanup — built-in, unlike single Promises.

---

## 12. How to think aloud

> "Native Promises are intentionally not cancellable — settlement is monotonic, executor is in charge. Two flavors of 'cancel': (1) wrapper that ignores the original's settlement (flag + override) — work still runs. (2) AbortController + signal — the work itself listens and tears down. Modern answer in 2026: AbortController. Pass signal into fetch, setTimeout (wrapper), streams. `AbortSignal.any([...signals])` for hierarchical cancellation. Trap: claiming you cancelled when work is still running. Trap: forgetting to remove abort listeners (leak). Trap: reusing one controller for multiple ops. Why TC39 dropped Promise.cancel: chaining cancellation propagation is unsolvable cleanly."

---

## 13. 60-second revision

> - **Native Promises NOT cancellable** — settlement is monotonic.
> - **Wrapper:** closure over `cancelled` flag; wrapper's executor overrides settlement.
> - **AbortController:** the WORK listens to signal and tears down.
> - **Use wrapper** for APIs without signal support; **use AbortController** when supported.
> - **`AbortSignal.any([...signals])`** for hierarchical cancellation (ES2024).
> - **`Promise.withResolvers()`** (ES2024) for cleaner externalized resolve/reject.
> - **Trap:** "I cancelled the Promise" (no — wrapper ignored result; work still ran).
> - **Trap:** abort listener not removed (leak); shared controller cancelling unrelated ops.

---

**Related:** [`04-promises/fetch-with-abort.md`](../04-promises/fetch-with-abort.md) · [`04-promises/abortcontroller-fanout.md`](../04-promises/abortcontroller-fanout.md) · [`04-promises/promise-time-limit.md`](../04-promises/promise-time-limit.md) · [`04-promises/deferred-with-resolvers.md`](../04-promises/deferred-with-resolvers.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
