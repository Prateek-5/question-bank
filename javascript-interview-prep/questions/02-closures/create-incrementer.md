# `createIncrement(by)` — closure-based incrementer factory

## Source
- Foundational closure interview problem (BFE.dev #18 "Counter", every front-end / Node bootcamp).
- Variants on LeetCode #2620 "Counter."

## Why this question matters in interviews
`createIncrement(by)` is the **simplest possible factory closure** — it tests whether you can return a function that holds private state and produces a new value each call. Senior interviewers ask it as a 5-minute warm-up, then immediately follow up with "now make it support `reset()`," "now make two of these independent," "now make `by` configurable per call." Each follow-up surfaces whether you actually understand how closures partition state. Backend uses: ID generators, sequence numbers for log lines, sequence-per-tenant counters, deterministic test fixtures.

## Concepts involved

### Syntax to lock in
```js
function createIncrement(by = 1) {
  let count = 0;                              // closed-over state
  return function () {
    count += by;
    return count;
  };
}

const inc = createIncrement(2);
inc();   // 2
inc();   // 4
inc();   // 6
```

### Runtime / engine behavior
- `count` and `by` are captured in the inner function's closure record. Both live on the heap as long as the returned wrapper is reachable.
- **Each call to `createIncrement` makes a fresh `count` slot.** Two incrementers from the same factory are completely independent — that's the whole point of factory functions.
- The factory's lexical environment is created at call time, destroyed when nothing references it. Returning the inner function keeps the environment alive.
- Arrow function or `function` doesn't matter here — there's no `this` involved.

### Edge cases (interview traps)
1. **Negative or zero `by`** — should work; the spec doesn't say "positive only." `createIncrement(-1)` is a decrementer.
2. **Float `by`** — works but accumulates floating-point error: `createIncrement(0.1)` after 10 calls gives `0.9999999999999999`. Mention if asked about decimals.
3. **Concurrent callers** — single-threaded JS, so no race. But in a worker thread with shared `SharedArrayBuffer`, you'd need `Atomics.add`. Mention for senior bonus.
4. **Starting value** — usually 0; allow override `createIncrement(by, start)`.
5. **`reset()`** — common follow-up. Expose by attaching to the returned function.
6. **Per-call step** — `createIncrement(2)(); inc(5);` overriding step? Tests whether you can extend the API cleanly.
7. **Memory** — `count` is small; no leak risk. But factories that close over large config objects do retain them.

## Brute force approach
"Use a global counter and add `by`." Breaks isolation — every caller shares the same counter. Fails the "factory" test. Or "stash count on the returned function as a property" — works but exposes mutable state to outside tampering. Closures are the right encapsulation.

## Optimal approach
Closure over `count` initialised inside the factory. Each `createIncrement(...)` call creates a fresh closure with its own `count`. O(1) state per incrementer, O(1) per call.

## Solution (JavaScript)

```js
/**
 * Returns an incrementer that adds `by` to its private counter on each call.
 * @param {number} [by=1]
 * @param {number} [start=0]
 * @returns {(() => number) & { reset: () => void, value: () => number }}
 */
function createIncrement(by = 1, start = 0) {
  let count = start;

  function inc() {
    count += by;
    return count;
  }

  inc.reset = () => { count = start; };
  inc.value = () => count;
  return inc;
}

// Usage — independent counters
const a = createIncrement(1);
const b = createIncrement(10);
a(); a(); a();    // 1, 2, 3
b(); b();         // 10, 20
a.value();        // 3 — totally independent of b
a.reset();
a();              // 1
```

## Step-by-step dry run

Input:
```js
const tick = createIncrement(2, 100);
tick();   // returns 102
tick();   // returns 104
tick.reset();
tick();   // returns 102
```

Trace:
- `createIncrement(2, 100)`:
  - Function body runs: `by = 2`, `start = 100`, `count = 100`.
  - Defines `inc`. `inc`'s closure captures `count`, `by`, `start`.
  - Attaches `inc.reset` and `inc.value`. Both share the same closure as `inc` (they're defined in the same scope).
  - Returns `inc`. `tick = inc`.
- `tick()` (1st):
  - `count = 100 + 2 = 102`. Returns 102.
- `tick()` (2nd):
  - `count = 102 + 2 = 104`. Returns 104.
- `tick.reset()`:
  - `count = start = 100`. Returns undefined.
- `tick()` (3rd):
  - `count = 100 + 2 = 102`. Returns 102.

What's on the heap: one closure record containing `count`, `by`, `start`. The three functions (`inc`, `reset`, `value`) all reference it. `tick` keeps the whole graph alive.

If we had also done `const tick2 = createIncrement(2, 100)`, `tick2` would have its **own** closure record with its **own** `count` — calling `tick()` wouldn't affect `tick2()` at all. This is the factory-function isolation guarantee.

## Important takeaways

**Syntax to memorize**
- `let count = start` in the **outer** scope (the factory body), never inside the returned function.
- Return the inner function directly.
- For follow-ups, attach methods (`reset`, `value`) onto the returned function — they share the same closure.

**Patterns to reuse**
- This is the **simplest factory closure**. The skeleton extends to: rate-limiter buckets, request-ID generators, log-sequence counters, retry-attempt counters, animation frame counters.
- "Multiple methods sharing one closure" = the **module pattern's** sibling. Define methods in the factory body so they all see the same private state.
- Attaching methods to the returned function (decorated-function pattern) is what lodash does for `.cancel` / `.flush` on debounce/throttle.

**Common mistakes**
- Declaring `let count` **inside** the returned function — resets every call, counter never advances.
- Returning the function and then assigning a property *to the count from outside* — `inc.count` doesn't exist; consumers can't reach the closure variable directly (that's the feature, not a bug).
- Confusing global counter with closure counter — global = shared, closure = per-instance.
- Forgetting that arrow vs `function` doesn't change closure semantics here.

**Related questions**
- `createCounter(init)` — same skeleton, return `{ increment, decrement, get }`
- `once(fn)` — same skeleton, swap counter for a boolean
- `createUUID()` / `createId()` — factory closure with a counter as the disambiguator
- React's `useState` (set/get pair) — closure-based at heart

## Variants

1. **`createCounter(init)` returning `{ increment, decrement, reset, value }`** — same closure, multiple methods. Variant of `module-pattern-iife`. Tests whether you understand that all methods defined in the same scope share state.

2. **Step-overridable on call** — `inc()` adds `by`, `inc(n)` adds `n` instead. One-line change inside the wrapper.

3. **Capped incrementer** — `createIncrement(1, 0, max)` returns `null`/throws/cycles after hitting `max`. Tests bounds + closure state combined.

## Revision notes

> **create-incrementer — 60 second recap**
> - Factory pattern: `function createIncrement(by) { let count = 0; return () => (count += by); }`.
> - `count` lives in the **factory's** scope. Each call to `createIncrement` makes a fresh `count` → independent incrementers.
> - Methods defined in the same scope (e.g., `reset`, `value`) all share the same closure — that's how `module-pattern-iife` works under the hood.
> - Attach helper methods to the returned function (decorated-function pattern) for `.reset()`/`.value()`.
> - Heap: closure record per incrementer; pinned while the returned function is reachable.
> - Concurrency: safe in single-threaded JS; needs `Atomics.add` in worker threads with `SharedArrayBuffer`.
> - Family: `once`, `createCounter`, debounce/throttle (closure over a single mutable handle).
> - **Trap:** declaring `count` inside the returned function — resets per call; counter is broken.
