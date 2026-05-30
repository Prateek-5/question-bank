# Implement `debounce(fn, wait, options?)` — defer until silence

> **Difficulty:** Easy-Medium   |   **Time:** ~20 min   |   **Prereqs:** [`concepts/closures.md`](../../concepts/closures.md), [`02-closures/counter.md`](../02-closures/counter.md)
>
> **Source:** <a href="https://leetcode.com/problems/debounce/" target="_blank" rel="noopener noreferrer">LeetCode 2627 — Debounce</a>. The canonical machine-coding warm-up.

---

## 1. Problem statement

**Signature**
```ts
function debounce<F extends (...args: any[]) => any>(
  fn: F,
  wait: number,
  options?: { leading?: boolean; trailing?: boolean }
): F & { cancel(): void; flush(): void };
```

**Input / Output examples**

| Setup                                                            | Behaviour                                              |
|-------------------------------------------------------------------|---------------------------------------------------------|
| `d = debounce(fn, 100); d('a'); d('b');` quickly                | only `fn('b')` fires after 100ms of silence            |
| `d('a'); d('b'); d('c'); ... wait 100ms; d('d')`                  | `fn('c')`, then `fn('d')` after another silence period |
| `{ leading: true, trailing: false }`                              | fires on first call, swallows rest in window           |
| `d.cancel()`                                                       | clears pending timer; nothing fires                    |
| `d.flush()`                                                        | immediately invokes pending call                       |

**Constraints**
- Returns a wrapper that **defers** `fn` until `wait` ms of silence.
- Forward `this` + args via `.apply`.
- Closure over `let timerId` — declared in outer scope, mutated by wrapper.
- Optional `{ leading, trailing }` (default trailing).

---

## 2. Plain-English restatement

You hand `debounce` your function and a wait time. It gives back a new function that, when called rapidly, only fires the original after the calls stop for `wait` ms. Classic use cases: search-as-you-type, autosave triggers, resize handlers. Each rapid call resets the timer; only the last call (with its args) eventually fires.

---

## 3. Why this matters in interviews

Debounce is the **single most-asked machine-coding warm-up** at senior backend / full-stack rounds. It hits four core JS skills in ~30 lines: closures over `timerId`, `this` + `arguments` forwarding, timer semantics, and return-value design. Interviewers use it as a 15-minute warm-up before the real machine-coding problem — fumbling it sets a bad tone. Backend uses: debouncing webhook deliveries, log flush triggers, search-as-you-type proxies, autosave queues, noisy filesystem watchers.

---

## 4. Mental model

A **bell with a 100ms timer**. Each ring resets the timer. The bell only "clangs" (calls `fn`) when 100ms pass without a new ring.

```
   t=0   d('a') →  schedule T1 for t=100, lastArgs='a'
   t=50  d('b') →  clearTimeout T1, schedule T2 for t=150, lastArgs='b'
   t=90  d('c') →  clearTimeout T2, schedule T3 for t=190, lastArgs='c'
   t=190           T3 fires → fn('c')
   t=250 d('d') →  schedule T4 for t=350, lastArgs='d'
   t=350           T4 fires → fn('d')

   4 calls → 2 invocations
```

**Leading vs trailing:**
- Trailing (default): fire at end of silence.
- Leading: fire immediately, swallow rest until silence.
- Both: fire first + last call.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Where should `let timerId` be declared — in the outer factory scope, or inside the returned wrapper?
> 2. Why use `fn.apply(this, args)` instead of `fn(...args)`?
> 3. What does the debounced function return on each call?

---

## 6. Brute force — walked through

### Wrong attempt 1: `timerId` inside wrapper
```js
function debounce(fn, wait) {
  return function (...args) {
    let timerId;                              // BUG: fresh per call
    timerId = setTimeout(() => fn(...args), wait);
  };
}
```
Each call gets its own `timerId` — no `clearTimeout` happens between calls. Every call fires `fn` after `wait`. Debounce = no-op.

### Wrong attempt 2: forget `this` forwarding
```js
timerId = setTimeout(() => fn(...args), wait);   // BUG: this not forwarded
```
For `obj.handler = debounce(obj.method, 100); obj.handler();` — `fn` runs with `this === undefined`. Use `fn.apply(this, args)`.

### Wrong attempt 3: track time with `Date.now()` instead of timers
Conflates debounce with throttle. Don't roll your own time arithmetic; let `clearTimeout`+`setTimeout` do the work.

---

## 7. The unlocking insight

> **Closure over a single `timerId`. On every call: `clearTimeout(timerId)` cancels any pending fire, then schedule a fresh `setTimeout`. The wrapper forwards `this`+args via `fn.apply`.**

Three properties:

1. **`timerId` lives in factory scope** — survives across calls, lets us cancel pending fires.
2. **`clearTimeout` + fresh `setTimeout` on every call** — that's the entire mechanism.
3. **`fn.apply(this, args)`** — preserves method-style usage.

Optional features:
- **`cancel()`** — `clearTimeout(timerId)` + reset state.
- **`flush()`** — invoke pending call immediately.
- **`{ leading: true }`** — fire on first call too; track "did we just fire?"

---

## 8. Solution (annotated)

```js
function debounce(fn, wait, { leading = false, trailing = true } = {}) {
  let timerId = null;                                   // step 1: closure-shared state
  let lastArgs = null;
  let lastThis = null;

  function invoke() {
    fn.apply(lastThis, lastArgs);                       // step 2: forward this+args
    lastArgs = lastThis = null;
  }

  function debounced(...args) {
    const callNow = leading && timerId === null;
    lastArgs = args;
    lastThis = this;

    if (timerId !== null) clearTimeout(timerId);        // step 3: cancel pending fire
    timerId = setTimeout(() => {                         // step 4: schedule new fire
      timerId = null;
      if (trailing && lastArgs) invoke();
    }, wait);

    if (callNow) invoke();                               // step 5: leading edge
  }

  debounced.cancel = () => {
    if (timerId !== null) clearTimeout(timerId);
    timerId = null;
    lastArgs = lastThis = null;
  };

  debounced.flush = () => {
    if (timerId !== null) {
      clearTimeout(timerId);
      timerId = null;
      if (lastArgs) invoke();
    }
  };

  return debounced;
}
```

**Try it yourself**

```js
const log = (msg) => console.log('fired:', msg, Date.now() % 1000);
const d = debounce(log, 100);

d('a');                                   // t=0
setTimeout(() => d('b'), 50);             // t=50
setTimeout(() => d('c'), 90);             // t=90
// t=190: fires "c"
setTimeout(() => d('d'), 250);            // t=250
// t=350: fires "d"

// Method-style usage
const obj = {
  name: 'searchBox',
  onInput: debounce(function (q) { console.log(this.name, q); }, 100),
};
obj.onInput('hello');   // 'searchBox hello' after 100ms
```

---

## 9. Step-by-step dry run

```
t=0   d('a'): timerId=null → leading?no. clearTimeout(null)=noop.
              schedule T1 (t=100). lastArgs=['a']
t=50  d('b'): clearTimeout(T1). schedule T2 (t=150). lastArgs=['b']
t=90  d('c'): clearTimeout(T2). schedule T3 (t=190). lastArgs=['c']
t=190 T3 fires: trailing&&lastArgs → invoke() → fn('c'). timerId=null.
t=250 d('d'): timerId=null → schedule T4 (t=350). lastArgs=['d']
t=350 T4 fires → fn('d').
```

4 calls → 2 invocations.

With `{ leading: true, trailing: false }`:
- t=0: callNow=true → invoke('a'); schedule timer (but trailing=false → no fire)
- t=50-90: timer keeps resetting
- t=190: timer fires, trailing=false → no invoke
- t=250: callNow=true → invoke('d')

2 invocations again, but at t=0 and t=250.

---

## 10. Common confusion + traps

1. **`let timerId` inside the returned wrapper** — fresh per call; debounce becomes a no-op.
2. **Forget `this` forwarding** — breaks method-style use.
3. **Use `Date.now()` arithmetic** — conflates debounce with throttle.
4. **Treat debounced return value as `fn`'s result** — returns `undefined`; result is deferred. If the interviewer wants the result, they want a Promise — say so.
5. **Confuse with throttle** — debounce waits for *silence*; throttle enforces *spacing*.
6. **Forget `.cancel()` / `.flush()`** — common follow-up; pre-plan for them.
7. **Long-lived debounced fn holding large `fn` reference** — memory pinning.

---

## 11. Senior follow-ups & variants

### Variant 1 — Promise-returning debounce
Return a Promise that resolves with `fn`'s eventual return; prior pending promises reject on each new call.

### Variant 2 — Async-aware debounce
If `fn` is async, ensure overlapping calls don't interleave; the next debounced call `awaits` the previous one.

### Variant 3 — `debounceWithMaxWait`
Add `maxWait` so the function fires at least every `maxWait` ms even if calls keep coming. Mirrors lodash. Tracks `timerId` (trailing) + `maxTimerId` (upper bound).

### Variant 4 — `requestAnimationFrame` debounce
Browser-only; coalesce rapid events to the next frame. `cancelAnimationFrame` to cancel.

---

## 12. How to think aloud

> "Closure over `let timerId`. Wrapper: `clearTimeout(timerId)` + fresh `setTimeout` + store latest `this`/args. Inside the timer, `fn.apply(lastThis, lastArgs)`. For `leading`, track whether we fired this window and invoke immediately on first call. For `.cancel()` / `.flush()`, attach them to the returned function — closure-shared state lets them reach in. Trap: declaring `timerId` inside the wrapper makes debounce a no-op. Trap: forgetting `this` forwarding breaks `obj.handler = debounce(obj.method, 100)`. Family: throttle, batchProcessor, rateLimiter — same 'closure over a handle' skeleton."

---

## 13. 60-second revision

> - **Closure over `let timerId`** in factory scope.
> - **`clearTimeout` + fresh `setTimeout`** on every call.
> - **`fn.apply(this, args)`** for method-style use.
> - **Options:** `{ leading, trailing }` (default trailing-only).
> - **Expose `.cancel()` and `.flush()`.**
> - **vs throttle:** debounce waits for *silence*; throttle enforces *spacing*.
> - **Family:** throttle, batchProcessor, rateLimiter.
> - **Trap:** `let timerId` inside wrapper → broken. Forgetting `this` → broken methods.

---

**Related:** [throttle.md](./throttle.md) · [`02-closures/counter.md`](../02-closures/counter.md) · [`02-closures/ring-buffer-via-closure.md`](../02-closures/ring-buffer-via-closure.md) · [batched-request-coalescer.md](./batched-request-coalescer.md)

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md)
