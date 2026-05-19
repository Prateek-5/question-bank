# Build `withCancel(work)` — a closure-based cancellation token

> **Difficulty:** Medium-Hard   |   **Time:** ~25 min   |   **Prereqs:** [allow-one-function-call.md](./allow-one-function-call.md), [`04-promises/abortcontroller-fanout.md`](../04-promises/abortcontroller-fanout.md), [`concepts/closures.md`](../../concepts/closures.md)
>
> **Source:** Cancellable async patterns (pre-AbortController era and as a complement to it). Asked at Stripe, Atlassian, Razorpay.

---

## 1. Problem statement

**Signature**
```ts
function withCancel<T>(work: (signal?: AbortSignal) => Promise<T>): {
  promise: Promise<T>;
  cancel(reason?: any): void;
  cancelled: boolean;
};
```

**Input / Output examples**

| Setup                                          | Sequence                              | Outcome                                       |
|------------------------------------------------|----------------------------------------|------------------------------------------------|
| `const {promise, cancel} = withCancel(fetchSomething)` | `setTimeout(cancel, 1000); await promise` | rejects with `{message:'Cancelled', cancelled:true}` |
| Work completes before cancel                   | `await promise; cancel();`            | resolves with result; cancel is a no-op       |
| `cancel()` called twice                        | `cancel(); cancel();`                  | idempotent — second call no-ops               |
| Real interruption (with AbortController combo) | `cancel('timeout')` while fetch is in-flight | underlying fetch socket aborts immediately |

**Constraints**
- The wrapper produces a `{ promise, cancel }` 2-tuple.
- `cancel()` must be **idempotent**.
- The closure flag handles "discard result if cancelled"; combining with `AbortController` provides **real** interruption.

---

## 2. Plain-English restatement

Wrap an async work function so that the caller gets back two things: the result-bearing promise *and* a `cancel()` function. Calling `cancel()` flips a private flag inside the wrapper; when the work finishes (or while it's running), the wrapper checks the flag and rejects with a "Cancelled" error instead of resolving normally.

This is the closure-based cousin of `AbortController`. Modern code uses `AbortSignal`; the closure variant is what you reach for in internal APIs where you want cancellation without the standard ceremony, or as a complement that adds "post-await discard" semantics on top of a signal-driven fetch.

---

## 3. Why this matters in interviews

Senior interviewers ask `withCancel` to test three things at once. **First**, can you encapsulate mutable state across two cooperating closures (the work-runner reads the flag; the cancel-fn writes it)? **Second**, do you understand that the closure flag is *cooperative* — it doesn't interrupt the in-flight work, only changes what happens after `await`? **Third**, can you combine your closure version with `AbortController` for actual interruption? Getting all three signals senior FP + async lifecycle fluency.

---

## 4. Mental model

A **shared flag in a private cubby**, accessible only via two doors. One door is the worker (reads the flag after each yield point and bails out if set). The other door is the cancel button (writes the flag). The cubby itself is invisible to everyone except those two doors.

```
   ┌──────────────────────────────────────┐
   │ cubby (closure):                     │
   │   cancelled: false                   │
   │                                       │
   │   ┌───────────────────────────────┐   │
   │   │ async worker closure          │   │
   │   │   await work()                │   │
   │   │   if (cancelled) throw        │   │
   │   │   return result               │   │
   │   └───────────────────────────────┘   │
   │                                       │
   │   ┌───────────────────────────────┐   │
   │   │ cancel closure                │   │
   │   │   cancelled = true            │   │
   │   │   (idempotent)                │   │
   │   └───────────────────────────────┘   │
   └──────────────────────────────────────┘

   Two closures, one shared LE. The flag is unreachable externally.
```

For **real** interruption (kill the underlying fetch), combine with `AbortController`:

```
   ┌──────────────────────────────────────┐
   │ ac = new AbortController()           │
   │ cancelled: false                     │
   │                                       │
   │   work(ac.signal)  ──► fetch obeys signal
   │                                       │
   │   cancel() → cancelled=true + ac.abort()
   │                                       │
   │   await catches AbortError → throws Cancelled
   └──────────────────────────────────────┘
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. If `cancel()` is called *after* `work()` has already resolved, what does `await promise` produce — the original result, or a Cancelled error?
> 2. Does setting `cancelled = true` interrupt an in-flight `fetch`? Why not?
> 3. How would you make `cancel()` idempotent — and why does it matter?

---

## 6. Brute force — walked through

### Wrong attempt 1: outer-scope flag

```js
let cancelled = false;
const work = async () => {
  const r = await fetch(url);
  if (cancelled) throw new Error('Cancelled');
  return r;
};
const p = work();
setTimeout(() => { cancelled = true; }, 1000);
```

Works mechanically — but `cancelled` is exposed in the calling scope. Two concurrent jobs trip over each other. Reject as a non-encapsulating solution.

### Wrong attempt 2: flag mutation from outside

```js
function withCancel(work) {
  return {
    promise: (async () => await work())(),
    cancelled: false,   // returned as a property
  };
}
const wrapped = withCancel(fetchThing);
wrapped.cancelled = true;
```

Cancellation is now anyone's-business. There's no way for the inner work runner to *see* the property mutation unless it polls it — and you've lost any privacy. The closure version puts the flag *inside* the closure where only the two intended functions can touch it.

### Wrong attempt 3: assume cancel interrupts the fetch

```js
function withCancel(work) {
  let cancelled = false;
  const promise = work();   // no signal threading
  return { promise, cancel: () => { cancelled = true; } };
}
```

`cancelled = true` only matters at the *check point* after `await`. The underlying fetch continues to completion — bytes still flow, the response still arrives, you just throw away the result. For real interruption, thread an `AbortSignal` through.

---

## 7. The unlocking insight

> **Closure-based cancellation is *cooperative*: the flag is checked at well-defined yield points, and a `true` flag means "discard the result." For *interrupting* the in-flight work itself, combine the closure flag with `AbortController.signal` threaded into the work function.**

The pattern has two intentional invariants:

1. **Two closures share one LE.** The work runner reads `cancelled` after `await`; the cancel function writes it. Both close over the same slot. Outside the factory, nothing reaches `cancelled`.
2. **Cancel after resolve is a no-op cancel + a thrown-away result.** If the work has *already* finished when `cancel()` fires, the flag flips but no one will check it. If the work hadn't finished, the flag will be true when the post-await check runs, and the wrapper throws.

The third invariant is **idempotency**. `cancel()` should be safe to call any number of times. The simplest way: bail early if `cancelled` is already true:

```js
cancel: () => { if (cancelled) return; cancelled = true; }
```

The senior twist: **combine with AbortController for interruption**. The closure flag handles "throw Cancelled instead of returning the result"; the signal handles "kill the fetch socket." Together they give you both behaviours — the closure version's clean throw shape *and* the standard's resource cleanup.

---

## 8. Solution (annotated)

```js
// ── Pure closure (cooperative cancel) ────────────────────────────
function withCancel(workFn) {
  let cancelled = false;                            // step 1: shared private slot

  const promise = (async () => {                    // step 2: async IIFE — starts work immediately
    const result = await workFn();                  // step 3: yield point — cancellation can race here
    if (cancelled) {                                 // step 4: post-await check
      const err = new Error('Cancelled');
      err.cancelled = true;
      throw err;
    }
    return result;
  })();

  return {
    promise,
    cancel: () => {                                  // step 5: writes the flag; idempotent via prior check
      if (cancelled) return;
      cancelled = true;
    },
    get cancelled() { return cancelled; },           // step 6: read-only getter for inspection
  };
}

// ── Closure + AbortController (real interruption) ────────────────
function withCancelAndAbort(workFn) {
  const ac = new AbortController();                  // step 1: signal for the inner work
  let cancelled = false;

  const promise = (async () => {
    try {
      const result = await workFn(ac.signal);        // step 2: work receives the signal
      if (cancelled) {                                // step 3: post-await closure check
        const err = new Error('Cancelled');
        err.cancelled = true;
        throw err;
      }
      return result;
    } catch (err) {
      if (err.name === 'AbortError') {                // step 4: translate AbortError to Cancelled
        const e = new Error('Cancelled');
        e.cancelled = true;
        throw e;
      }
      throw err;
    }
  })();

  return {
    promise,
    cancel: (reason = 'user-cancel') => {
      if (cancelled) return;                          // idempotent
      cancelled = true;
      ac.abort(reason);                                // real interruption: fetch socket aborts
    },
    signal: ac.signal,
    get cancelled() { return cancelled; },
  };
}
```

**Try it yourself**

```js
// Pure closure — cooperative cancel
const { promise, cancel } = withCancel(async () => {
  await new Promise((r) => setTimeout(r, 2000));
  return 'result';
});
setTimeout(() => cancel(), 1000);
try { await promise; } catch (e) { console.log(e.cancelled, e.message); }
// → true, Cancelled
// (the inner setTimeout still ran for full 2s; we just discarded the result)

// Closure + AbortController — real interruption
const { promise: p, cancel: c } = withCancelAndAbort((signal) =>
  fetch('/api/slow', { signal }).then((r) => r.json())
);
setTimeout(() => c('timeout'), 1000);
try { await p; } catch (e) { console.log(e.cancelled); }   // true
// Underlying fetch's TCP connection was actually aborted at t=1000
```

---

## 9. Step-by-step dry run

Input:

```js
const { promise, cancel } = withCancelAndAbort((signal) =>
  fetch('/slow', { signal }).then((r) => r.json())
);
setTimeout(() => cancel('timeout'), 2000);
try { await promise; } catch (e) { /* handle */ }
```

Values-first trace:

| Time | Action                              | `cancelled` | `ac.signal.aborted` | Outcome                         |
|------|-------------------------------------|-------------|---------------------|----------------------------------|
| 0    | `withCancelAndAbort` runs           | `false`     | `false`             | `fetch('/slow', {signal})` starts |
| 0    | async IIFE awaiting fetch           | `false`     | `false`             | pending                          |
| 2000 | `cancel('timeout')` fires           | `false → true` | `false → true`  | `ac.abort('timeout')` propagates  |
| 2000 | fetch rejects with `AbortError`     | `true`      | `true`              | inner catch translates to `Cancelled` |
| 2001 | outer `await promise` throws        | `true`      | `true`              | `e.cancelled === true`            |

If `cancel()` had been called at t=2000 *after* fetch already resolved at t=1500:

| Time | Action                | `cancelled` | Outcome                              |
|------|------------------------|-------------|---------------------------------------|
| 0    | fetch starts          | `false`     | pending                               |
| 1500 | fetch resolves        | `false`     | result captured by await              |
| 1500 | post-await check       | `false`     | returns result (no throw)             |
| 1500+ | promise resolved      | `false`     | caller's await receives result        |
| 2000 | `cancel('timeout')`    | `false → true` | flag flips, ac.abort fires, but no one is checking |
| 2000 | (no further effect)   | `true`      | result was already delivered          |

---

## 10. Common confusion + traps

1. **Cancel interrupts the running fetch.**
   It doesn't, unless you pass an `AbortSignal` to `fetch`. The closure flag is cooperative — it only matters at the post-await check.

2. **Setting `cancelled = true` from outside the closure works.**
   No — the flag is a binding inside the closure. You can only mutate it through the `cancel` function returned by the factory.

3. **Cancel after resolve causes a weird error.**
   It doesn't. The flag flips, but no one checks it any more. Cancel becomes a no-op.

4. **Multiple cancels do extra work.**
   With the idempotent guard (`if (cancelled) return`), the second call is a no-op. Without it, you might call `ac.abort()` twice, which is harmless but ugly. Always guard.

5. **The closure leaks `cancelled` forever.**
   `cancelled` lives until the promise settles. After settlement, if no one holds the wrapper object, the closure becomes unreachable and is GC'd. Tiny: one boolean. The risk is bigger if `workFn` captured a 10 MB blob — then it's pinned until settle.

6. **`AbortError` needs translation.**
   Fetch with an aborted signal rejects with an Error whose `name === 'AbortError'`. The wrapper should translate that to its own `Cancelled` error so callers have one shape to catch.

7. **Closure vs raw AbortController for public APIs.**
   For public/library APIs, prefer raw `AbortSignal` — it's the standard. The closure version is best as an *internal* primitive or a complement that adds "throw Cancelled on post-await."

---

## 11. Senior follow-ups & variants

### Variant 1 — Resettable (re-arm the cancellation)

```js
function withCancel(workFn) {
  let cancelled = false;
  const promise = /* ... */;
  return {
    promise,
    cancel: () => { if (!cancelled) cancelled = true; },
    reset: () => { cancelled = false; },        // re-arm for next use
  };
}
```

Re-arming makes the wrapper reusable across multiple work cycles. Rare for cancellation but useful for "retry" patterns.

### Variant 2 — Timeout-driven auto-cancel

```js
function withTimeout(workFn, ms) {
  const wrapper = withCancelAndAbort(workFn);
  const timer = setTimeout(() => wrapper.cancel('timeout'), ms);
  wrapper.promise.finally(() => clearTimeout(timer));
  return wrapper;
}
```

Auto-cancel after `ms`. Common in HTTP clients and circuit breakers.

### Variant 3 — Cancellation chain (parent → children)

```js
function withCancelChain(parent) {
  const children = new Set();
  parent.signal?.addEventListener('abort', () => {
    for (const c of children) c.cancel('parent-cancelled');
  });
  return {
    addChild(workFn) {
      const c = withCancelAndAbort(workFn);
      children.add(c);
      c.promise.finally(() => children.delete(c));
      return c;
    },
  };
}
```

Cancelling the parent cancels all in-flight children. Same shape as structured concurrency / `TaskGroup`.

### Variant 4 — Tag/reason tracking

```js
cancel: (reason = 'user-cancel') => {
  if (cancelled) return;
  cancelled = true;
  cancelReason = reason;
  ac.abort(reason);
}
```

`Cancelled` error carries the reason; useful for telemetry ("cancelled because: timeout" vs "user-cancel" vs "shutdown").

### Variant 5 — Generation counter for race-free refreshes

```js
let gen = 0;
function reload() {
  const myGen = ++gen;
  return workFn().then((data) => {
    if (myGen !== gen) return;   // stale — newer reload has started
    apply(data);
  });
}
```

A relative of the cancellation pattern — instead of a boolean, use a monotonically increasing counter. Old async tasks check their generation and bail out if a newer one has started.

---

## 12. How to think aloud in the interview

> "Closure-based cancellation: two closures share a private `cancelled` flag. The work runner reads it after each `await`; the cancel function writes it. Cancel is cooperative — it doesn't interrupt the fetch, it just makes the wrapper throw Cancelled instead of returning the result. For real interruption, combine with `AbortController`: thread `ac.signal` into the work function (so fetch can abort), and have `cancel()` flip the flag *and* call `ac.abort()`. Always idempotent — guard with `if (cancelled) return`. Translate AbortError to the wrapper's Cancelled shape so callers have one error to catch. For public APIs I'd prefer raw `AbortSignal`; the closure version is best as an internal primitive."

---

## 13. 60-second revision

> - **Pattern:** factory closure captures `let cancelled = false`; returns `{ promise, cancel }`. Work runner checks `cancelled` after `await`; throw `Cancelled` if set.
> - **Cooperative**: doesn't interrupt in-flight work — only changes the post-await outcome.
> - **Combine with AbortController**: closure flag for "throw Cancelled"; `ac.signal` threaded into work for **real** interruption.
> - **Idempotent**: `if (cancelled) return` at the top of cancel.
> - **Cancel after resolve**: no-op (no one to check the flag).
> - **Translate AbortError → Cancelled** so callers have one error shape.
> - **Family:** AbortController, structured concurrency (`TaskGroup`), generation counters, timeout-driven cancellation.
> - **Trap:** thinking the closure flag interrupts the fetch; not threading the signal; forgetting idempotency guard.

---

**Related:** [allow-one-function-call.md](./allow-one-function-call.md) · [setinterval-stale-closure.md](./setinterval-stale-closure.md) · [`04-promises/abortcontroller-fanout.md`](../04-promises/abortcontroller-fanout.md) · [`04-promises/structured-concurrency-primitive.md`](../04-promises/structured-concurrency-primitive.md)

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md), [`concepts/promises.md`](../../concepts/promises.md)
