# Timeout Cancellation — `setTimeout` + `clearTimeout`

> **Difficulty:** Easy   |   **Time:** ~10 min   |   **Prereqs:** [event-loop-concurrency.md](./event-loop-concurrency.md)
>
> **Source:** [LeetCode 2715 — Timeout Cancellation](https://leetcode.com/problems/timeout-cancellation/).

---

## 1. Problem statement

**Signature**
```ts
function cancellable(fn: (...args: any[]) => any, args: any[], t: number): () => void;
```

**Input / Output examples**

| Setup                                            | Behaviour                                              |
|--------------------------------------------------|---------------------------------------------------------|
| `cancel = cancellable(fn, args, 100)`             | schedule `fn(...args)` at t=100ms                      |
| Call `cancel()` before t=100                       | `fn` never runs                                         |
| Call `cancel()` after t=100                       | no-op (fn already fired)                                |
| Call `cancel()` twice                              | safe no-op                                              |
| `t = 0`                                            | runs AFTER microtasks drain (not synchronous)         |

**Constraints**
- Return a CANCELLER closure, not the timer ID.
- `clearTimeout` removes handle before fire; no-op if already fired.
- `setTimeout(0)` → coerced to `setTimeout(1)` in Node.

---

## 2. Plain-English restatement

Schedule `fn(...args)` to run after `t` ms. Return a function that, when called, prevents the scheduled call if it hasn't already fired. The clean idiom: closure over the timer ID + `clearTimeout`.

---

## 3. Why this matters in interviews

The warm-up that screens whether you understand timer phase placement and what `clearTimeout` actually does. Real backend uses: request timeouts, lease expirations, retry windows, circuit-breaker open durations.

---

## 4. Mental model

```
   t=0    setTimeout(cb, 100) → cb queued in timers phase heap at t+100
   t=50   clearTimeout(id) → cb removed from heap
   t=100  timers phase visits heap → cb gone → nothing fires

   Alternative timing:
   t=0    setTimeout(cb, 100)
   t=100  cb fires (heap → call stack)
   t=150  clearTimeout(id) → no-op (already fired)

   The returned canceller closes over `id`:
     return () => clearTimeout(id);
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. After `cancel()` runs, what's the side effect of calling it again?
> 2. Does `t = 0` make `fn` run synchronously?
> 3. Why return a function instead of the timer ID?

---

## 6. Brute force — walked through

### Wrong attempt 1: flag-based cancel
```js
let cancelled = false;
setTimeout(() => { if (!cancelled) fn(...args); }, t);
return () => { cancelled = true; };
```
Wasteful — cb still allocates stack frame to check flag. `clearTimeout` removes handle before fire.

### Wrong attempt 2: return raw ID
Caller has to know the API; `clearTimeout(id)` is the cancel idiom. Return closure for opaque handle.

### Wrong attempt 3: assume `t=0` is immediate
No — runs after microtasks drain, at next iteration's timers phase.

---

## 7. The unlocking insight

> **`const id = setTimeout(...); return () => clearTimeout(id);` — closure-returned canceller. `clearTimeout` is a no-op if the callback already fired. `t=0` still goes through the timers phase, after microtasks drain.**

Three properties:

1. **Closure over id** — opaque cancel handle.
2. **`clearTimeout` is safe** at any time (no-op if fired).
3. **`t=0` isn't 0ms** — 1ms minimum + microtasks drain first.

---

## 8. Solution (annotated)

```js
function cancellable(fn, args, t) {
  const id = setTimeout(() => fn(...args), t);                       // step 1: schedule
  return () => clearTimeout(id);                                      // step 2: closure canceller
}
```

**Try it yourself**

```js
const result = [];
const fn = (x) => result.push(x);

// Case 1: cancel BEFORE fire
const cancel = cancellable(fn, [42], 100);
setTimeout(cancel, 50);
// At t=200, result === []

// Case 2: cancel AFTER fire
const cancel2 = cancellable(fn, [99], 100);
setTimeout(cancel2, 150);
// At t=200, result === [99]
```

---

## 9. Step-by-step dry run

```
Cancel before fire:
t=0    cancellable → setTimeout(cb_A, 100). timers heap: [cb_A@100].
       outer setTimeout(cancel, 50). timers heap: [cb_A@100, cancel@50].
       sync done.
t=50   timers phase: cancel runs → clearTimeout(idA). heap: [].
t=100  timers phase: heap empty → nothing fires.
       result === [].

Cancel after fire:
t=0    schedule cb_A@100 and cancel@150.
t=100  cb_A fires → fn(42) → result.push(42). heap: [cancel@150].
t=150  cancel runs → clearTimeout(idA). idA already fired → no-op. heap: [].
       result === [42].
```

---

## 10. Common confusion + traps

1. **Flag-based cancel** — wasteful; `clearTimeout` is cleaner.
2. **Return raw ID** — leaks the API; return closure.
3. **`t=0` is synchronous** — no; runs after microtasks.
4. **`clearTimeout(null)` throws** — no, safe no-op.
5. **Cancel after fire stops fn mid-execution** — no; only stops if not yet on stack.
6. **`setInterval` uses same cancel** — no, use `clearInterval`.
7. **Long delays > 2^31-1 ms** — coerced to 1 ms (Node).

---

## 11. Senior follow-ups & variants

### Variant 1 — Promise-based timeout
`Promise.race([promise, delay(ms).then(() => { throw new TimeoutError() })])`. Clear timer on settle to avoid leak.

### Variant 2 — AbortSignal-driven
Accept `AbortSignal`; `signal.addEventListener('abort', () => clearTimeout(id))`. Modern idiomatic.

### Variant 3 — Reschedulable timeout
Expose `reset()` that clears and re-arms — the debounce primitive.

### Variant 4 — Browser equivalent
Same API; HTML5 spec enforces 4ms minimum for nested timers (not 1ms).

### Variant 5 — Bounded timers
Use `setImmediate` for "yield CPU" instead of `setTimeout(0)` — cheaper in Node.

---

## 12. How to think aloud

> "`const id = setTimeout(() => fn(...args), t); return () => clearTimeout(id);`. Closure over id, returned as opaque canceller. `clearTimeout` removes the handle from the timers heap before fire; no-op if already fired. `t=0` is NOT synchronous — runs after microtasks drain at next iteration's timers phase (Node enforces 1ms minimum). Same skeleton powers debounce, throttle reset, request timeouts. Trap: returning the raw ID; flag-based cancel (wasteful); assuming `t=0` is 0ms; calling cancel mid-execution doesn't stop fn."

---

## 13. 60-second revision

> - **`setTimeout(cb, t)`** → timers phase heap; `clearTimeout(id)` removes handle.
> - **Return closure** `() => clearTimeout(id)`, NOT raw id.
> - **`t=0` NOT synchronous** — runs after microtasks; Node 1ms minimum.
> - **`clearTimeout`** safe at any time (no-op if fired).
> - **Cancel doesn't stop fn mid-execution** — only prevents start.
> - **Same skeleton** for debounce, throttle reset, request timeouts.
> - **Long delays** > 2^31-1 ms → coerced to 1 ms.
> - **Trap:** flag-based cancel; raw id leak; `t=0` synchronous assumption.

---

**Related:** [interval-cancellation.md](./interval-cancellation.md) · [cancellable-function.md](./cancellable-function.md) · [`10-machine-coding-patterns/debounce.md`](../10-machine-coding-patterns/debounce.md) · [`10-machine-coding-patterns/cancellable-promise-wrapper.md`](../10-machine-coding-patterns/cancellable-promise-wrapper.md)

**Concept primer:** [`concepts/event-loop.md`](../../concepts/event-loop.md)
