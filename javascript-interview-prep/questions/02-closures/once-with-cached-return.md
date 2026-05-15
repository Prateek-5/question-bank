# Implement `once(fn)` that caches the first return value

## Source
- Classic interview problem (BFE.dev, Frontend Masters, lodash `_.once`).
- Underpins lodash's `_.once` and the "init only once" idiom used in DB clients, config loaders, and singletons.

## Why this question matters in interviews
`once(fn)` is the smallest non-trivial closure problem an interviewer can ask. It tests whether you can carry **two** pieces of state across calls — a boolean flag *and* a cached return value — and whether you understand why the cached return must be reused. As a backend engineer you write `once` constantly without naming it: lazy DB pool creation, one-shot migration runners, idempotent webhook handlers, env-loaders. Senior interviewers will follow up with "what if `fn` throws?" and "what if `fn` is async?" — both probe your understanding of closure-held state lifecycles.

## Concepts involved

### Syntax to lock in
```js
function once(fn) {
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

### Runtime / engine behavior
- Two variables (`called`, `result`) are captured in the inner function's closure and live on the heap as long as the returned wrapper is reachable.
- Setting `called = true` **before** invoking `fn` would protect against re-entry if `fn` itself calls the wrapper synchronously — but loses the return value if `fn` throws. The standard order (set flag, then assign result) is the common LeetCode answer; the "set flag first" variant is the *re-entrant-safe* answer. Mention both.
- This is the closure form of the **memoize-with-arity-0** pattern: same skeleton as `memoize`, but with no cache key (one slot only).

### Edge cases (the interview traps)
1. **`fn` throws on first call** — should the wrapper be "consumed" or retry? Default: the wrapper is consumed, second call returns `undefined`. Lodash matches this. Some interviewers expect retry-on-throw — clarify upfront.
2. **`this` and arguments** — forward both with `fn.apply(this, args)`. The cached return ignores subsequent args, by definition.
3. **Async `fn`** — the cached "result" is the **Promise itself**, so concurrent callers all `await` the same promise. This is the dedupe-in-flight pattern (see Variants).
4. **`undefined` as a valid return value** — that's why you use a separate `called` flag instead of checking `result === undefined`.
5. **Memory** — `result` is retained forever. If `fn` returns a 1GB buffer, that buffer never GCs. Mention this for senior bonus points.
6. **Re-entrancy** — if `fn(...)` synchronously calls the wrapper, you either get infinite recursion (flag-after) or the cached `undefined` (flag-before).
7. **Resettability** — interviewers may ask for `.reset()`. Trivial closure addition.

## Brute force approach
"I'll use a counter and check if count > 0." Works but reveals you don't understand that this is a **boolean state** problem, not a counting problem. Also vulnerable to the `undefined`-result trap if you use the result itself as the sentinel.

## Optimal approach
Closure over a `called` boolean and a `result` slot. O(1) memory, O(1) per call. The whole pattern is < 10 lines.

## Solution (JavaScript)

```js
/**
 * Returns a function that invokes `fn` at most once.
 * Subsequent calls return the cached first result.
 * @param {Function} fn
 * @returns {Function & { reset: () => void }}
 */
function once(fn) {
  let called = false;
  let result;

  function wrapper(...args) {
    if (called) return result;
    called = true;                // set BEFORE invoking — re-entrant safe
    result = fn.apply(this, args);
    return result;
  }

  wrapper.reset = () => {
    called = false;
    result = undefined;
  };

  return wrapper;
}
```

## Step-by-step dry run

Input:
```js
let n = 0;
const init = once((label) => {
  console.log('init:', label);
  return ++n;
});

console.log(init('a'));   // logs "init: a", returns 1
console.log(init('b'));   // no log, returns 1 (cached)
console.log(init('c'));   // no log, returns 1 (cached)
```

Trace:
- Initial closure state: `called = false`, `result = undefined`.
- `init('a')`: `called` is false → set `called = true`, call `fn('a')` → logs `init: a`, `n` becomes 1, returns 1. `result = 1`. Wrapper returns 1.
- `init('b')`: `called` is true → return `result` (which is 1). `fn` is **not** called; `'b'` is discarded; `n` stays 1.
- `init('c')`: same as `'b'`. Returns 1.

Net: `fn` invoked exactly once. Cached return value (`1`) served to all subsequent callers.

What's on the heap: the wrapper holds `called` and `result` in its closure record. The original `fn` is also retained (referenced by the wrapper). Until `wrapper` itself becomes unreachable, none of these can be GC'd.

## Important takeaways

**Syntax to memorize**
- Two closed-over variables: a **flag** and a **value slot**.
- Set the flag **before** calling `fn` to be re-entrant-safe.
- Forward `this` + `args` via `fn.apply(this, args)`.

**Patterns to reuse**
- This is **`memoize` with a single cache slot** (no key). If you generalize the slot to a `Map<key, value>`, you get `memoize(fn)`.
- It's also `throttle(fn, Infinity)` and `debounce` with `{ leading: true, trailing: false, wait: Infinity }` — the "leading-only" forever pattern.
- Lazy-init singletons (DB pool, logger, config loader) are `once` in disguise.

**Common mistakes**
- Using `result === undefined` as the sentinel — breaks when `fn` legitimately returns `undefined`.
- Setting `called = true` *after* the call — re-entrant calls inside `fn` recurse forever.
- Forgetting `this` forwarding — breaks `obj.init = once(obj.init)` patterns.
- Forgetting that the cached result holds heap references — memory leak risk on big returns.

**Related questions**
- `memoize(fn)` (closure over a `Map`)
- `memoize(fn, { ttl })`
- Async `once` / in-flight dedupe (cache the promise)
- `lazy(fn)` (alias for `once` in some libraries)

## Variants

1. **Async `once` (in-flight dedupe)** — "If `fn` is async, multiple concurrent callers should share the same in-flight promise; if it rejects, the next call retries." Cache the Promise, not the resolved value; reset `called` on rejection.

2. **`once` with `.reset()` and `.invoked` getter** — Expose internal state so callers can re-arm the function. Tests whether you can attach metadata methods to a returned function.

3. **`onceN(fn, n)`** — Call `fn` at most `n` times; thereafter return the last result. Generalises `once` and shows you can swap a boolean for a counter while preserving the cached-value slot.

## Revision notes

> **once — 60 second recap**
> - Closure over a `called` flag + a `result` slot. Two pieces of state, both heap-retained.
> - Set the flag **before** invoking `fn` → re-entrant safe.
> - Forward `this` + `args` with `fn.apply(this, args)`. After the first call, args are ignored.
> - Use a **boolean flag**, not `result === undefined`, as the sentinel (functions can return `undefined`).
> - Async variant: cache the **Promise**, not the resolved value — concurrent callers share one in-flight call.
> - Memory: `result` is retained forever — big returns become leaks.
> - Family: `memoize` (Map cache), `lazy`, leading-only `throttle`.
> - **Trap:** flag-after-call → infinite recursion if `fn` calls the wrapper. Using `undefined`-check → breaks on `undefined` return.
