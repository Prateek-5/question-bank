# Allow One Function Call (`once`)

## Source
- https://leetcode.com/problems/allow-one-function-call/

## Why this question matters in interviews
`once(fn)` is the smallest closure-over-a-flag problem and a backend staple. It maps directly to **initialization guards**, **idempotency wrappers**, **singleton resource setup** (open DB pool once, register signal handlers once), **one-shot event listeners** (`EventEmitter#once`), and **promise resolvers** (which reject if called twice). Interviewers love it because the body is 6 lines but each line tests a separate concept: closure over a boolean, argument forwarding, return-value handling, and (the trap) what to return on subsequent calls. Get it crisp and the interviewer moves on; fumble the "what does the second call return" question and they'll drill.

## Concepts involved

### Syntax to lock in
```js
function once(fn) {
  let called = false;
  return function (...args) {
    if (called) return undefined;
    called = true;
    return fn.apply(this, args);
  };
}
```
- Closure captures a **single boolean flag** `called`.
- On call 1: flip the flag, forward args + `this`, return the result.
- On call 2+: short-circuit with `undefined`.

### LeetCode-specific spec
- LeetCode's "Allow One Function Call" requires the second-and-later calls to return `undefined`. Some variants (and lodash's `_.once`) **cache the first return value** and return it on every subsequent call. Always clarify before writing — interviewers will ask both.

### Lexical environment / what's captured
- LE_outer holds `called: false` and the captured `fn` reference.
- The returned wrapper closes over both. Each subsequent invocation reads/writes `called` in the **same** LE on the heap.
- Crucially, after the wrapper has fired once, the closure still retains `fn` — even though it'll never be called again. If you want aggressive cleanup (release the heap reference), null out `fn` after the call. Rarely necessary, but worth a one-liner mention for senior signal.

### Edge cases / interview traps
1. **What to return on call 2+?** — LeetCode: `undefined`. Lodash: cached first result. **Ask.**
2. **`this` forwarding** — `fn.apply(this, args)`. Without it, calling `obj.init = once(obj.init); obj.init()` breaks.
3. **Argument forwarding** — `...args` rest + `apply`. Don't capture by position.
4. **Re-entrancy** — what if `fn` internally calls the wrapped function again? The flag is set *before* `fn` runs, so re-entrant calls return `undefined`. (If you flip the flag *after* `fn.apply`, re-entrant calls would actually re-execute `fn` — subtle but wrong.) **Flip the flag first.**
5. **Throwing `fn`** — if `fn` throws, is the call "used"? In our solution, yes (flag is already flipped). Lodash matches this. If interviewer wants retry-on-throw, move the flag flip below the `apply`. Discuss the tradeoff.
6. **Memory** — closure retains `fn` and any `this` / `args` captured. Long-lived `once` wrappers around heavy `fn` keep `fn` alive.

## Brute force approach
"Use a counter, check if count === 0." Works but wasteful: you only need a boolean. Reject because it's slightly less idiomatic — though if the interviewer asks for "allow N calls" (the natural follow-up), the counter pattern wins.

A class with `this.called`? Functional. But more code and no benefit over the closure. Closure is the idiom.

## Optimal approach
Closure over a boolean flag. Flip it **before** invoking `fn` to make the wrapper re-entrancy-safe and throw-safe. Use `apply(this, args)` for forwarding. O(1) memory per wrapper, O(1) per call.

## Solution (JavaScript)

```js
/**
 * @param {Function} fn
 * @return {Function}
 */
var once = function (fn) {
  let called = false;
  return function (...args) {
    if (called) return undefined;
    called = true;
    return fn.apply(this, args);
  };
};

// Usage
const fn = (a, b, c) => a + b + c;
const onceFn = once(fn);
onceFn(1, 2, 3); // 6
onceFn(2, 3, 6); // undefined
```

### Variant: cache-first-result (`lodash _.once`)

```js
function onceCached(fn) {
  let called = false;
  let result;
  return function (...args) {
    if (called) return result;
    called = true;
    result = fn.apply(this, args);
    return result;
  };
}
```

## Step-by-step dry run

Input:
```js
const sum = (a, b, c) => a + b + c;
const onceSum = once(sum);
console.log(onceSum(1, 2, 3));   // expect 6
console.log(onceSum(10, 20, 30)); // expect undefined
console.log(onceSum(5, 5, 5));    // expect undefined
```

Trace:
1. `once(sum)` is called.
   - LE_outer created: `{ called: false, fn: sum }`.
   - Wrapper function returned with `[[Environment]] = LE_outer`. Outer frame popped, LE_outer retained on heap.
2. `onceSum(1, 2, 3)`:
   - `called` is `false` → don't short-circuit.
   - Set `called = true` (LE_outer mutated).
   - `fn.apply(this, [1,2,3])` → `sum(1,2,3)` → `6`.
   - Returns `6`.
3. `onceSum(10, 20, 30)`:
   - `called` is `true` → return `undefined` immediately. `fn` is **not** invoked. Side-effect-free.
4. `onceSum(5, 5, 5)`:
   - Same as call 3 → `undefined`.

LE_outer's `called` slot went `false → true` exactly once and stayed there.

## Important takeaways

**Syntax to memorize**
- `let called = false` in outer, `if (called) return undefined; called = true;` at top of wrapper.
- `fn.apply(this, args)` for forwarding.
- Flip the flag **before** calling `fn` (re-entrancy + throw safety).

**Patterns to reuse**
- "Closure over a boolean flag" → also used in: lazy initialization, singleton accessor, idempotent webhook handler, register-once event listener.
- The "cache first result" variant doubles as `memoize` for zero-arg functions.

**Common mistakes**
- Flipping the flag *after* `fn.apply` — re-entrant call reruns `fn`; thrown `fn` leaves the wrapper "unused" forever (depending on the spec you want, this may actually be desirable — clarify).
- Forgetting `this` / `...args` forwarding.
- Returning `fn(args)` instead of `fn.apply(this, args)` — works for plain functions, breaks method binding.
- Storing the flag on `this` or on the wrapper function as a property — exposes it to callers.

**Related questions**
- Counter (same skeleton, different state type)
- `memoize` (closure over a Map of results)
- `EventEmitter#once` (closure + unsubscribe)
- `debounce` (closure over a timerId)

## Variants

1. **Cache-first-result `once`** — lodash semantics. Return the first call's result on every subsequent call. Closure adds a `result` slot.

2. **`allowN(fn, n)`** — generalize the boolean flag to a counter. First `n` calls go through, rest return `undefined`. Pattern: `let remaining = n; if (remaining === 0) return; remaining--; return fn.apply(...)`.

3. **Async `once`** — `fn` is async; ensure concurrent callers all `await` the *same* promise (don't run `fn` twice). Pattern: closure over a `Promise` slot. This is essentially **request deduplication** — a real backend pattern for cache stampedes.

## Revision notes

> **once — 60 second recap**
> - Closure over `let called = false` (and optionally `let result`).
> - First call: flip flag → call `fn.apply(this, args)` → return result.
> - Subsequent calls: short-circuit with `undefined` (LeetCode) or cached result (lodash) — **clarify first**.
> - Flip the flag **before** invoking `fn`: makes it re-entrancy-safe and throw-safe.
> - Forward `this` + `...args` via `apply`.
> - **Trap:** doing `if (called) return; called = true;` after the call — re-entrant call reruns `fn`.
> - Family: lazy init, singleton, idempotent handlers, EventEmitter#once.
> - Async variant = request deduplication (closure over a Promise).
