# Closure with Cancel Token — Stateful Async Cancellation

## Source / Origin
- Cancellable async patterns (pre-AbortController era and as a complement to it).
- Asked at: Stripe, Atlassian, Razorpay.
- Concept reference: `concepts/closures.md`, sibling `04-promises/abortcontroller-fanout.md`.

## Why this question matters in interviews
You need an async operation that you can cancel from outside. The modern way is `AbortController` + signal; the *closure-based* way is to return a cancel function from a factory that captures shared mutable state. Senior bar: you can build both, see they're isomorphic, and pick the right one for an internal API (closure: cheap, no deps) vs a public API (AbortSignal: standard).

## Concepts involved

### Syntax to lock in
```js
function withCancel(asyncWork) {
  let cancelled = false;
  const promise = (async () => {
    const result = await asyncWork();
    if (cancelled) throw new Error('Cancelled');
    return result;
  })();
  return { promise, cancel: () => { cancelled = true; } };
}

const { promise, cancel } = withCancel(() => fetchSomething());
setTimeout(cancel, 1000);
try { const r = await promise; } catch (e) { /* cancelled */ }
```

### Edge cases / interview traps
1. **Closure captures shared `cancelled` flag.** Both the work-runner and the cancel-fn close over the same slot.
2. **Cancel is cooperative.** Setting `cancelled = true` doesn't interrupt the in-flight `asyncWork`; it just causes a post-await throw.
3. **For real interruption, use `AbortController`** and pass the signal to fetch/timer.
4. **Cancel after resolve** — the result is discarded; caller sees `'Cancelled'` error. Decide: silently ignore vs surface.
5. **Idempotent cancel** — multiple cancel calls should be safe.
6. **Memory** — closure keeps `cancelled` alive until the promise settles; not a leak unless you keep many around.
7. **Composition with AbortController** — wrap both: closure flag for in-process discard; signal for actual fetch abort.

## Mental Model

A **shared flag in a private cubby**, accessible only via two closures:

```
   ┌──────────────────────────────────────┐
   │ cubby: cancelled = false             │
   │                                       │
   │   ┌───────────────────────────────┐   │
   │   │ promise runner closure        │   │
   │   │   reads cubby.cancelled       │   │
   │   └───────────────────────────────┘   │
   │                                       │
   │   ┌───────────────────────────────┐   │
   │   │ cancel closure                │   │
   │   │   writes cubby.cancelled=true │   │
   │   └───────────────────────────────┘   │
   └──────────────────────────────────────┘
```

The two closures share the lexical environment of `withCancel`. From outside, neither the flag nor the cubby is reachable.

## Why interviewers care

- **Closure-as-state pattern** — foundational JS idiom.
- **Async lifecycle reasoning** — what does "cancel" mean during/after await?
- **API design** — token + work + cancel as a 3-tuple.

## Common beginner confusion

- **"Cancel interrupts the running fetch."** It doesn't unless you pass a signal to `fetch`.
- **"Closure is overkill for this."** It's the simplest primitive; AbortController is the standardized version of the same idea.
- **"Set `cancelled=true` outside the closure works."** No — the flag is captured by reference inside; you need a setter that's also inside.
- **"Multiple cancels duplicate work."** Set to true is idempotent.

## Brute force approach

```js
// Outer flag — pollutes the calling scope
let cancelled = false;
const work = async () => {
  const r = await fetch(url);
  if (cancelled) throw new Error('Cancelled');
  return r;
};
const p = work();
setTimeout(() => cancelled = true, 1000);
```

Works, but `cancelled` is global to the scope; can't have two independent jobs.

## Optimal approach

A factory closure that encapsulates the flag and exposes `{ promise, cancel }`. Composes with AbortController for real interruption.

## Solution (JavaScript)

```js
// 1. Closure-only (cooperative)
function withCancel(workFn) {
  let cancelled = false;
  const promise = (async () => {
    const result = await workFn();
    if (cancelled) throw Object.assign(new Error('Cancelled'), { cancelled: true });
    return result;
  })();
  return {
    promise,
    cancel: () => { cancelled = true; },
    get cancelled() { return cancelled; },
  };
}

// 2. Combined: closure flag + AbortController for interruptibility
function withCancelAndAbort(workFn) {
  const ac = new AbortController();
  let cancelled = false;
  const promise = (async () => {
    try {
      const result = await workFn(ac.signal);
      if (cancelled) throw new Error('Cancelled');
      return result;
    } catch (err) {
      if (err.name === 'AbortError') throw Object.assign(new Error('Cancelled'), { cancelled: true });
      throw err;
    }
  })();
  return {
    promise,
    cancel: (reason = 'user-cancel') => {
      if (cancelled) return;        // idempotent
      cancelled = true;
      ac.abort(reason);
    },
    signal: ac.signal,
    get cancelled() { return cancelled; },
  };
}

// Usage
const { promise, cancel } = withCancelAndAbort((signal) =>
  fetch('/api/slow', { signal }).then(r => r.json())
);
setTimeout(() => cancel('timeout'), 5_000);
try {
  const data = await promise;
} catch (e) {
  if (e.cancelled) console.log('cancelled');
  else throw e;
}
```

## Step-by-step dry run

```
t=0   withCancelAndAbort(workFn) called
       enter scope: cancelled=false; ac=new AbortController
       async IIFE starts: invokes workFn(ac.signal); workFn returns a fetch promise
       return { promise, cancel }

t=2s  user calls cancel('timeout')
       cancel closure: reads `cancelled` → false; sets cancelled=true
       calls ac.abort('timeout')
       → fetch internal AbortSignal fires; underlying request aborts
       → fetch rejects with AbortError

t=2s+ async IIFE: catch block runs
       err.name === 'AbortError' → throw Cancelled error
       outer promise rejects

       await promise → catch → e.cancelled is true → handle as cancellation
```

## How to think aloud in the interview

> "Closure captures a mutable `cancelled` flag in the factory's lexical env. The work-runner reads it post-await; the cancel function sets it. That's cooperative — doesn't interrupt in-flight work. To actually interrupt, combine with AbortController: the closure flag handles 'don't return result if we cancelled,' the signal handles 'kill the fetch socket.' Cancel must be idempotent. For public APIs I'd prefer raw AbortSignal — standardized."

## Important takeaways

- **Closure captures shared `cancelled`.**
- **Cancel is cooperative** without AbortController.
- **Idempotent cancel.**
- **AbortController complements** — signal for real interrupt, closure flag for cooperative throw.
- **`cancelled` getter for inspection.**

## Variants

- **Hot-cancel (one-shot)** vs **resettable** — `reset()` clears the flag.
- **Timeout-based cancel** — `withTimeout(workFn, ms)` wraps with auto-cancel.
- **Tag/reason tracking** — `cancel(reason)`; reasons surface in the rejection.
- **Cancellation chain** — a parent cancel triggers child cancels (via shared controller).
- **WeakRef cancel registry** — track outstanding cancellations and clean up when promises resolve.

## Revision notes

```
withCancel(workFn):
  closure scope:
    cancelled = false
  return {
    promise: (async () => { r = await workFn(); if (cancelled) throw; return r; })(),
    cancel: () => { cancelled = true }
  }

  COOPERATIVE: doesn't interrupt in-flight; just discards result
  for real interrupt: combine with AbortController + pass signal to fetch
  idempotent cancel (set true; setting again no-op)
  
  shape: { promise, cancel, signal?, cancelled (getter) }
  alternative: just use AbortController + AbortSignal directly
```
