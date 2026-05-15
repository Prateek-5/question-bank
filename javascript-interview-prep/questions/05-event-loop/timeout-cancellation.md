# Timeout Cancellation

## Source
- LeetCode #2715 "Timeout Cancellation": https://leetcode.com/problems/timeout-cancellation/
- Canonical: maps directly to the `setTimeout` / `clearTimeout` primitives every Node developer uses.

## Why this question matters in interviews
This is the warm-up that screens whether you actually understand **how a macrotask gets parked on the libuv timers queue** vs how a microtask is drained. The code is six lines, but the interviewer expects you to (1) name the queue the timer lands on, (2) explain what `clearTimeout` actually does (it does NOT stop a fired callback — it removes the handle before it fires), and (3) talk about the difference between "cancel" and "no-op once executed". Backend engineers hit this every day: request timeouts, lease expirations, retry windows, circuit-breaker open-state durations.

## Concepts involved

### Syntax to lock in
```js
function cancellable(fn, args, t) {
  const id = setTimeout(() => fn(...args), t);
  return () => clearTimeout(id);
}
```

### Runtime / engine behavior
- `setTimeout(cb, ms)` enqueues `cb` into Node's **timers phase** (libuv phase 1 of 6). The timer is checked at the start of each loop iteration; if `now >= scheduledAt`, the callback runs.
- The `ms` value is a **minimum** delay, not exact. If the loop is busy on a long sync task, the timer fires late.
- `clearTimeout(id)` removes the handle from the heap libuv uses to order pending timers. If the callback has already moved from the heap to the call stack, `clearTimeout` is a no-op.
- Browsers behave similarly but use a flat task queue rather than libuv phases.

### Edge cases (interview traps)
1. **`t = 0`** — still goes through the timer queue. **Microtasks (Promise.then) and `process.nextTick` always run first.** So `setTimeout(fn, 0)` runs after every queued microtask.
2. **Calling cancel after the timer fired** — must be a safe no-op. `clearTimeout(undefined)` is also safe.
3. **Calling cancel twice** — also a no-op the second time. Don't add guard flags unless asked.
4. **Long delays** — Node caps `setTimeout` delay at ~2^31-1 ms (~24.8 days); larger values are coerced to 1.
5. **Negative or NaN `t`** — coerced to 1 ms by the spec.
6. **Closure capture of `args`** — pass them through `fn(...args)`, don't `.bind` (which would create extra allocations).
7. **Returning a function vs returning the id** — interviewers prefer the closure pattern because it hides the timer handle.

## Brute force approach
"I'll set a flag `cancelled` and inside the callback check it." This works but is wasteful: the callback still runs on the timers phase, allocates a stack frame, and only then bails out. `clearTimeout` removes the handle before that ever happens — it's strictly better.

## Optimal approach
Schedule with `setTimeout`, return an arrow that closes over the handle and calls `clearTimeout`. O(1) work, no extra state, no flag.

## Solution (JavaScript)

```js
/**
 * Schedules fn(...args) to run after t ms unless the returned canceller
 * is invoked before the timer fires.
 *
 * @param {(...args: any[]) => any} fn
 * @param {any[]} args
 * @param {number} t  delay in ms
 * @returns {() => void}  cancellation function
 */
function cancellable(fn, args, t) {
  const id = setTimeout(() => fn(...args), t);
  return () => clearTimeout(id);
}
```

## Step-by-step dry run

Input:
```js
const result = [];
const fn = (x) => result.push(x);
const cancel = cancellable(fn, [42], 100);
setTimeout(cancel, 50);   // cancels before fire
// vs. setTimeout(cancel, 150); // cancels after fire — no effect
```

Trace (cancel BEFORE fire):

| Time (ms) | Call stack | Timers heap | Microtask Q |
|-----------|-----------|-------------|-------------|
| 0 | `cancellable(...)` runs → `setTimeout(cbA, 100)` | `[cbA@100]` | empty |
| 0 | outer `setTimeout(cancel, 50)` | `[cbA@100, cancel@50]` | empty |
| 50 | timers phase: dequeue `cancel`, run it → `clearTimeout(idA)` | `[]` | empty |
| 100 | timers phase: heap is empty, nothing to do | `[]` | empty |

Final `result` is `[]` — fn never ran.

Trace (cancel AFTER fire):

| Time (ms) | Call stack | Timers heap | Output |
|-----------|-----------|-------------|--------|
| 0 | schedule cbA@100, schedule cancel@150 | `[cbA@100, cancel@150]` | — |
| 100 | timers phase: cbA runs → `fn(42)` → `result.push(42)` | `[cancel@150]` | `result=[42]` |
| 150 | timers phase: cancel runs → `clearTimeout(idA)` (idA already fired → no-op) | `[]` | `result=[42]` |

## Important takeaways

**Syntax to memorize**
- `const id = setTimeout(cb, t); return () => clearTimeout(id);`
- The returned canceller is itself a function — gives the caller a clean, opaque handle.

**Patterns to reuse**
- "Schedule + return canceller" is the same shape as `AbortController`'s `signal.aborted` pattern.
- Used identically for: request timeouts, retry delays, lease expirations, snackbar auto-dismiss, polling stop tokens.

**Common mistakes**
- Returning the raw timer `id` instead of a function — leaks the timer handle and forces the caller to know the API.
- Wrapping the timer in a Promise then trying to "reject on cancel" — overengineered for this problem; mention it only if asked.
- Assuming `t=0` runs immediately. **It doesn't** — it runs after all microtasks drain.

**Where it sits in the event loop**
- `setTimeout` callbacks fire in libuv's **timers phase**.
- They run **after** the current synchronous chunk, **after** `process.nextTick`, **after** all queued microtasks (Promise jobs), and only then on the next loop iteration when their deadline has passed.

## Variants

1. **Promise-based timeout** — `function withTimeout(promise, ms)` rejects if `promise` doesn't settle in time. Combine `Promise.race` with `setTimeout`; clear the timer on settle to avoid leaks.

2. **`AbortSignal`-driven cancellation** — accept an `AbortSignal` instead of returning a canceller. Inside, `signal.addEventListener('abort', () => clearTimeout(id))`. Idiomatic modern Node.

3. **Reschedulable timeout** — expose `reset()` that clears and re-arms (the building block of `debounce`). Same closure-over-handle pattern.

## Revision notes

> **timeout-cancellation — 60 second recap**
> - `setTimeout` enqueues into libuv's **timers phase** (phase 1 of 6).
> - `clearTimeout(id)` removes the handle from the timers heap; it's a no-op if the callback already fired.
> - Return a **canceller closure** `() => clearTimeout(id)`, not the raw id.
> - `t=0` is NOT synchronous — runs after microtasks and `process.nextTick` drain.
> - Long delays (> 2^31-1 ms) collapse to 1 ms in Node.
> - Same skeleton powers debounce, throttle reset, request timeouts.
> - **Trap:** assuming the callback can't run once you've called cancel. If cancel is invoked from a later macrotask, fn may already have fired.
> - **Trap:** confusing `clearTimeout` with `clearImmediate` / `clearInterval` — they each target a different libuv phase.
