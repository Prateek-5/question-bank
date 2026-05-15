# Implement `once(fn)` — return-value caching

## Source
- Canonical machine-coding warm-up (lodash `_.once`, Underscore, BFE.dev, codedamn frontend rounds).
- Related to LeetCode #2666 "Allow One Function Call."

## Why this question matters in interviews
`once` is the smallest useful closure problem an interviewer can ask. It clocks in at ~5 lines but probes **closure over mutable state**, **`this`/`arguments` forwarding**, **return-value caching**, and an understanding of how `once` relates to the broader family — throttle, debounce, memoize. Senior interviewers like it because the obvious answer (`let called = false`) is correct, but the follow-ups — "what if `fn` is async?", "what about errors?", "what's the relationship to throttle?" — separate juniors from staff-level candidates. As a backend engineer you'll hit `once` in real systems: idempotent boot routines, lazy singletons, one-shot signal handlers, "show this dialog once," and module-init guards in Node servers.

## Concepts involved

### Syntax to lock in
```js
const init = once(expensiveBoot);
init();  // runs expensiveBoot, caches result
init();  // returns cached result; expensiveBoot NOT invoked again

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
- The boolean `called` and the cached `result` live in the closure scope of the outer function. They survive between calls because the returned function retains a reference to that scope.
- `fn.apply(this, args)` forwards both `this` and arguments — the same forwarding pattern as `debounce`/`throttle`.
- Once `called` flips to `true`, the closure permanently shortcuts. The `fn` reference can be **nulled out** after the first call to free its heap retention (lodash does this).
- Hot path after first call is `if (called) return result` — a single boolean read and a return. Cheaper than a memoize Map lookup.

### Edge cases (these are the interview traps)
1. **What does `fn` returning `undefined` mean?** — `result` stays `undefined`, but `called` is `true`. Subsequent calls return `undefined`, which is correct. Don't gate on `result == null`.
2. **What if `fn` throws on first call?** — naive impl sets `called = true` first, then throws → next call returns stale `undefined` silently. Better: set `called = true` **only after** `fn` returns successfully. Or expose both: "permanently failed" vs "not-yet-called."
3. **Async `fn`** — if `fn` returns a Promise, caching the Promise is what you want (concurrent callers share the in-flight Promise). Caching the resolved value would require `await`-ing inside, which changes the signature to async.
4. **`this` binding** — `fn.apply(this, args)`. If you forget, method-style usage like `obj.boot = once(obj.boot)` loses `this`.
5. **Reset?** — interviewers will ask: "expose `.reset()` so testing can re-arm it." Easy add: clear `called` and `result`.
6. **`new`-ability** — if `fn` is a constructor, `once` will not behave as a constructor. Out of scope for the common case; mention if asked.
7. **Memory** — after the first call, you can `fn = null` inside the closure to release the original function. Useful when `fn` holds large captured state (config, db handles).
8. **Relationship to throttle** — `once(fn)` is mathematically `throttle(fn, { leading: true, trailing: false, wait: Infinity })`. State the equivalence — interviewers love it.

## Brute force approach
"I'll use a counter and check `count === 0`." Works but conflates a flag with a counter — you've introduced state you don't need. Drop. The boolean is canonical.

Another wrong path: "I'll set `fn = () => result` after the first call." This would re-bind `fn` inside the closure, but you'd lose the original arity / name and it doesn't simplify anything. The boolean-flag version is what interviewers expect.

## Optimal approach
Closure over a single boolean + cached return value. O(1) memory, O(1) per call (after first). The first call pays the cost of `fn`; every call after is a boolean check and a return.

## Solution (JavaScript)

```js
/**
 * Returns a function that invokes `fn` at most once. Subsequent calls return
 * the cached result of the first invocation.
 *
 * @param {Function} fn
 * @returns {Function & { reset: () => void }}
 */
function once(fn) {
  let called = false;
  let result;

  function onced(...args) {
    if (called) return result;
    // Set called BEFORE fn runs so re-entrant calls (fn calls onced)
    // don't infinitely recurse. Trade-off: a throw still marks it as called.
    called = true;
    try {
      result = fn.apply(this, args);
    } catch (err) {
      // Roll back so the next call can retry. Pick one policy and document it.
      called = false;
      throw err;
    }
    return result;
  }

  onced.reset = () => {
    called = false;
    result = undefined;
  };

  return onced;
}
```

## Step-by-step dry run

Input:
```js
let counter = 0;
const init = once(() => {
  counter++;
  return { id: counter, time: Date.now() };
});

const a = init();
const b = init();
const c = init();
console.log(a === b, b === c, counter);
```

Trace:
- Call 1 (`init()`): `called=false` → enter. Set `called=true`. Run `fn`: `counter=1`, returns `{id:1, time:T}`. Store in `result`. Return `result`. `a = {id:1, time:T}`.
- Call 2 (`init()`): `called=true` → return cached `result`. `b === a` (same reference).
- Call 3 (`init()`): same. `c === a`.
- `counter` is still `1`. `fn` ran exactly once.

Output: `true true 1`.

If `init.reset()` is called between 2 and 3, call 3 re-runs `fn`, `counter` becomes 2, and `c !== a`.

## Important takeaways

**Syntax to memorize**
- `let called = false, result;` in outer scope. Never inside the returned function.
- `if (called) return result;` as the first line of the wrapper — the hot path.
- `fn.apply(this, args)` for forwarding.

**Patterns to reuse**
- The "closure over a boolean + cached value" pattern is the skeleton of: `memoize` (Map instead of single slot), `lazy(getter)` (no args), `singleton(factory)` (DI containers).
- `once(fn) === throttle(fn, Infinity, { leading: true, trailing: false })`. State this equivalence in the interview — it shows you see the family.

**Common mistakes**
- Forgetting `this` forwarding (breaks `obj.method = once(obj.method)`).
- Setting `called = true` **after** `fn.apply` — re-entrant calls from inside `fn` will loop forever.
- Gating on `result != null` instead of `called`. Fails when `fn` legitimately returns `null`/`undefined`/`0`/`""`.
- Returning the cached `result` even when `fn` threw — caller never sees the error on subsequent calls.

**Related questions**
- `memoize(fn)` — same shape, Map-keyed by args.
- `lazy(getter)` — zero-arg variant.
- `throttle(fn, wait, { leading, trailing })` — `once` is the `wait=Infinity` case.
- Singleton in DI container.

## Variants

1. **`onceAsync(fn)`** — `fn` returns a Promise. Cache the Promise itself so concurrent callers all `await` the same in-flight call. If you cache the resolved value instead, the second concurrent caller would re-invoke `fn` before the first settles.

2. **`onceWithReset(fn)`** — expose `.reset()` (shown above). Useful for tests and circuit-breaker style "after cooldown, try again."

3. **`onceOrThrow(fn)`** — instead of returning the cached value, throw on second call. Used for one-shot tokens (CSRF, single-use callbacks, "you can only consume this stream once").

4. **N-times variant — `times(fn, n)`** — generalize: invoke `fn` at most `n` times, return cached `result` after. Same shape with a counter.

## Revision notes

> **once — 30 second recap**
> - Closure over `called` flag + cached `result`.
> - First call: run `fn.apply(this, args)`, cache result, set flag. Subsequent: return cached.
> - Forward `this` + args; gate on the flag, not on `result`.
> - Same family as throttle (`once == throttle{leading, !trailing, wait: Infinity}`), memoize (single-slot Map), lazy.
> - Trap: setting `called=true` after `fn` runs → re-entrant infinite loop. Or before → throw leaves it permanently broken.
> - Expose `.reset()` for tests.
