# Implement `debounce(fn, wait, options?)`

## Source
- Canonical machine-coding interview problem (variants on codedamn, LeetCode #2627 "Debounce", Frontend Masters, BFE.dev).
- LeetCode reference: https://leetcode.com/problems/debounce/

## Why this question matters in interviews
Debounce is the single most-asked machine-coding warm-up at senior backend / full-stack rounds. It hits four core JS skills in ~30 lines: **closures over `timerId`**, **`this` + `arguments` forwarding**, **timer semantics**, and **return-value design**. Interviewers use it as a 15-minute warm-up before the real machine-coding problem — fumbling it sets a bad tone. As a backend engineer you'll also see it in real life: debouncing webhook deliveries, log flush triggers, search-as-you-type proxies, autosave queues, and noisy filesystem watchers.

## Concepts involved

### Syntax to lock in
```js
const debounced = debounce(fn, 300);
debounced(...args); // calls fn(...args) only after 300ms of silence

function debounce(fn, wait) {
  let timerId;                          // closed-over state
  return function (...args) {           // returned wrapper
    clearTimeout(timerId);              // reset on every call
    timerId = setTimeout(() => {
      fn.apply(this, args);             // preserve `this` + args
    }, wait);
  };
}
```

### Runtime / engine behavior
- `setTimeout` returns a **Timeout** object in Node (a number in the browser). Both are valid args to `clearTimeout`.
- Each call to the wrapper schedules a fresh timer in the **timers phase** of Node's libuv loop, or the browser's task queue. Microtasks (promise callbacks) drain *between* timers, so debounced callbacks land on macrotask boundaries — not microtask boundaries.
- Closure mechanics: `timerId` lives in the outer function's lexical scope and is **mutated** across calls. This is the canonical example of "closures over mutable state."

### Edge cases (these are the interview traps)
1. **`this` binding** — `fn.apply(this, args)` is mandatory; arrow function inside `setTimeout` is what allows `this` to flow through. If you use `function () {}` inside `setTimeout`, `this` becomes `undefined` (strict) or `globalThis`.
2. **Argument forwarding** — `...args` rest in the wrapper + `apply` is the safe pattern. Don't capture individual args by position.
3. **Cancellation** — interviewers will follow up: "expose `.cancel()`." Pre-plan for it (see Variants).
4. **Leading-edge mode** — "fire immediately, then suppress further calls for `wait` ms" is a common twist (lodash-style `{ leading: true, trailing: false }`).
5. **Trailing-only firing race** — if `wait` is `0`, the call still defers to the next tick, not synchronous. Many candidates miss this and assert sync.
6. **Multiple instances** — each call to `debounce(...)` returns its own wrapper with its own `timerId`. State is per-wrapper, not global.
7. **Memory leak via closure** — if `fn` holds a large heap reference and the wrapper is never released, `fn` is retained. Mention this for bonus points.
8. **`new Date()` drift** — don't try to compute "time since last call" by hand; let `clearTimeout` + fresh `setTimeout` do the work.

## Brute force approach
Naive thought: "I'll keep track of the last call time and inside `fn` check if enough time has passed." This conflates **debounce** with **throttle** and forces you to invoke `fn` on every call, which is the opposite of what's wanted. Drop this path immediately.

## Optimal approach
Closure over a single `timerId`. On every call, clear the prior timer and schedule a fresh one. The only state needed is the timer handle and the latest `args`/`this`. O(1) memory, O(1) per call.

## Solution (JavaScript)

```js
/**
 * Returns a debounced version of `fn`.
 * @param {Function} fn
 * @param {number} wait  ms of silence required before firing
 * @param {{ leading?: boolean, trailing?: boolean }} [options]
 * @returns {Function & { cancel: () => void, flush: () => void }}
 */
function debounce(fn, wait, { leading = false, trailing = true } = {}) {
  let timerId = null;
  let lastArgs = null;
  let lastThis = null;

  function invoke() {
    fn.apply(lastThis, lastArgs);
    lastArgs = lastThis = null;
  }

  function debounced(...args) {
    const callNow = leading && timerId === null;
    lastArgs = args;
    lastThis = this;

    if (timerId !== null) clearTimeout(timerId);

    timerId = setTimeout(() => {
      timerId = null;
      if (trailing && lastArgs) invoke();
    }, wait);

    if (callNow) invoke();
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

## Step-by-step dry run

Input:
```js
const log = (msg) => console.log('fired:', msg, Date.now() % 1000);
const d = debounce(log, 100);

d('a');                 // t=0
setTimeout(() => d('b'), 50);   // t=50
setTimeout(() => d('c'), 90);   // t=90
setTimeout(() => d('d'), 250);  // t=250
```

Trace:
- `t=0` — `d('a')`: `timerId === null` → schedule timer T1 for `t=100`. `lastArgs=['a']`.
- `t=50` — `d('b')`: clear T1 (cancels the 'a' fire). Schedule T2 for `t=150`. `lastArgs=['b']`.
- `t=90` — `d('c')`: clear T2. Schedule T3 for `t=190`. `lastArgs=['c']`.
- `t=190` — T3 fires. `trailing=true` → `invoke()` → `log('c')`. Output: `fired: c 190`.
- `t=250` — `d('d')`: `timerId === null` (T3 already fired and cleared it). Schedule T4 for `t=350`. `lastArgs=['d']`.
- `t=350` — T4 fires. `log('d')`. Output: `fired: d 350`.

Net: 2 invocations from 4 calls. Exactly what debounce promises.

If `leading=true, trailing=false`, the `t=0` call fires immediately, all subsequent within 100ms are swallowed, then `t=250` fires immediately again. Total: 2 invocations but at different timestamps.

## Important takeaways

**Syntax to memorize**
- `let timerId` in outer scope. **Never** declare it inside the returned function.
- Inner timer callback **must** be an arrow function (or you must capture `self = this` / `args` manually).
- `fn.apply(this, args)` for argument + `this` forwarding.

**Patterns to reuse**
- "Closure over a single mutable handle that's reset on every call" is the same pattern as: throttle, retry-with-backoff (the `attempt` counter), once-only (`called` flag), batchProcessor (`buffer + timerId`).
- Returning a function with `.cancel` / `.flush` attached as methods is the **decorated-function pattern**. Used by lodash everywhere.

**Common mistakes**
- Putting `let timerId` inside the returned wrapper (creates a fresh timer every call — debounce becomes a no-op).
- Forgetting `this` forwarding — breaks method-style usage like `obj.onSearch = debounce(obj.handler, 200)`.
- Using `Date.now()` arithmetic instead of letting `setTimeout` handle the timing.
- Treating the debounced return value as if it returns `fn`'s result. **It returns nothing** (the result is deferred). If interviewer wants the return value, they want a *promise* — say so.

**Related questions**
- `throttle(fn, wait)` (same family, different semantics)
- `once(fn)`
- `batchProcessor(fn, { maxWait, maxSize })`
- `rateLimiter(maxCalls, perMs)`

## Variants

1. **Promise-returning debounce** — "Make the debounced function return a promise that resolves with `fn`'s eventual return value, with prior pending promises rejected on each new call." Tests knowledge of promise resolvers stored in closure scope.

2. **Async-aware debounce** — "If `fn` is async, ensure overlapping calls don't interleave; the next debounced call should `await` the previous one." Distinguishes debounce semantics from request deduplication (which is a different problem worth pushing back on).

3. **`debounceWithMaxWait`** — "Add a `maxWait` so the function fires at least every `maxWait` ms even if calls keep coming." Mirrors lodash's `maxWait` option. Forces you to track both `timerId` (for trailing) and a separate `maxTimerId` (for the upper bound).

## Revision notes

> **debounce — 60 second recap**
> - Returns a wrapper that **defers** `fn` until `wait` ms of silence.
> - Closure over `let timerId`; `clearTimeout` + `setTimeout` on every call.
> - Forward `this` + `args` with `fn.apply(this, args)`.
> - Options: `{ leading, trailing }` (default trailing-only).
> - Expose `.cancel()` and `.flush()`.
> - Family: throttle, batchProcessor, rateLimiter — same "closure over a handle" skeleton.
> - **Trap:** declaring `timerId` *inside* the wrapper → broken. Forgetting `this` → broken for method-style use.
