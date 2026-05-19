# Build `once(fn)` that caches and replays the first return value

> **Difficulty:** Easy-Medium   |   **Time:** ~15 min   |   **Prereqs:** [allow-one-function-call.md](./allow-one-function-call.md), [`concepts/closures.md`](../../concepts/closures.md)
>
> **Source:** Classic interview problem (BFE.dev, Frontend Masters, lodash `_.once`).

---

## 1. Problem statement

**Signature**
```ts
function once<F extends (...args: any[]) => any>(fn: F):
  ((...args: Parameters<F>) => ReturnType<F>) & { reset(): void };
```

**Input / Output examples**

| Setup                                              | Sequence of calls         | Output sequence  |
|----------------------------------------------------|---------------------------|------------------|
| `let n=0; const f = once(() => ++n)`               | `f(); f(); f();`          | `1, 1, 1` (cached) |
| `const f = once((x) => x*2)`                       | `f(5); f(99); f(0);`      | `10, 10, 10`     |
| `const f = once(() => undefined)`                  | `f(); f();`               | `undefined, undefined` (distinguish from "no entry") |
| `let n=0; const f = once(() => ++n); f(); f.reset(); f();` | with reset()       | `1, 2`           |

**Constraints**
- After the first call, every subsequent call returns the **cached first result** (lodash semantics — different from LeetCode 2666 which returns `undefined`).
- `fn` is invoked **exactly once** across the wrapper's lifetime (until reset).
- Forward `this` and arguments on the first call. Subsequent args are discarded.
- `undefined` must be cacheable as a legitimate return value.

---

## 2. Plain-English restatement

Build `once(fn)` such that the first invocation runs `fn` and stores its return value, and every subsequent invocation **returns that same stored value** without re-running `fn`. The hard part: `undefined` is a legitimate return value, so you can't use `result === undefined` as the "has it been called yet?" check — you need a separate boolean flag.

This is the cousin of LeetCode's "Allow One Function Call" (which returns `undefined` on subsequent calls) — `once` from lodash, and the canonical lazy-init pattern.

---

## 3. Why this matters in interviews

`once(fn)` is the smallest non-trivial closure problem. It tests whether you can carry **two** pieces of state across calls — a boolean flag *and* a cached return value — and whether you understand why each is necessary. As a backend engineer, you write `once` constantly without naming it: lazy DB pool creation, one-shot migration runners, idempotent webhook handlers, env loaders, singleton config readers. Senior follow-ups: "what if `fn` throws?" and "what if `fn` is async?" — both probe your understanding of closure-held state lifecycles.

---

## 4. Mental model

A **photo booth** that takes one photo and then keeps handing out the same print. The booth has two slots inside: a flag (`called`) saying "have we taken the photo yet?" and a print rack (`result`) holding the developed photo.

```
   once(fn)
     │
     ├── booth: ┌──────────────────┐
     │         │  called: false   │
     │         │  result: <slot>  │
     │         └──────────────────┘
     │
     └── returns ──► wrapper(...args)
                       │
                       ├── called?  yes → return cached result
                       │
                       └── no → flip flag → result = fn.apply(this, args)
                                              → return result
```

The flag is the discriminator (lets `undefined` be a valid cached value). The result slot is the snapshot. Together they implement "memoize a zero-argument call."

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why can't you check `result === undefined` as the "has it been called yet?" sentinel?
> 2. If `fn` throws on the first call, what should the second call do — return the cached result (there isn't one), retry, or return `undefined`?
> 3. For an async `fn`, what should the *cached* value be — the resolved value, or the Promise itself? Why?

---

## 6. Brute force — walked through

### Wrong attempt 1: use `result === undefined` as the sentinel

```js
function once(fn) {
  let result;
  return function (...args) {
    if (result !== undefined) return result;
    result = fn.apply(this, args);
    return result;
  };
}
```

Looks clean. But: if `fn` legitimately returns `undefined`, the wrapper sees `result === undefined` on every subsequent call → re-runs `fn` every time. Sentinel collision. You need a **separate flag**.

### Wrong attempt 2: flag, but flipped after `fn`

```js
function once(fn) {
  let called = false;
  let result;
  return function (...args) {
    if (called) return result;
    result = fn.apply(this, args);
    called = true;       // ← re-entrancy risk; throw leaves called=false
    return result;
  };
}
```

Same trap as in [allow-one-function-call.md](./allow-one-function-call.md). If `fn` synchronously invokes the wrapper before returning, the inner call sees `called === false` → re-runs `fn` → recursion. If `fn` throws, `called` stays `false` → next caller retries.

### Wrong attempt 3: counter pattern

```js
function once(fn) {
  let count = 0;
  let result;
  return function (...args) {
    if (count++ > 0) return result;
    return result = fn.apply(this, args);
  };
}
```

Works, but uses unnecessary state (a counter when a boolean suffices). Also incrementing every call means the counter could overflow on heavily-called wrappers — though that's largely theoretical.

---

## 7. The unlocking insight

> **You need *two* closure slots — a flag (the discriminator) and a value (the cache). Flip the flag before invoking `fn`, so re-entrancy and throws both leave the wrapper consistent.**

The closure must carry:

1. **`called: boolean`** — distinguishes "never invoked" from "invoked and got `undefined`." Without this, you can't safely cache an `undefined` return.
2. **`result: any`** — the cached return value, set exactly once.

The invocation order matters:

```js
if (called) return result;    // gate first
called = true;                 // flip the flag (before fn — re-entrancy + throw safety)
result = fn.apply(this, args); // invoke
return result;                 // serve the cached value
```

If `fn` synchronously re-enters the wrapper, the second call sees `called === true` and returns `result` (which is whatever was assigned at the point of re-entry — usually `undefined` if `fn` hasn't returned yet). If `fn` throws, `called` is already `true` → the ticket is consumed, next caller gets the (undefined) cached result. Whether throw-consumes-ticket matches your spec depends on the contract — clarify upfront.

---

## 8. Solution (annotated)

```js
function once(fn) {                              // step 1: factory captures fn + 2 private slots
  let called = false;                             // step 2: discriminator (also handles undefined returns)
  let result;                                     // step 3: cache slot

  function wrapper(...args) {                     // step 4: returned wrapper
    if (called) return result;                    // step 5: gate — subsequent calls just return cached value
    called = true;                                 // step 6: FLIP FIRST (re-entrant safe)
    result = fn.apply(this, args);                 // step 7: invoke, forwarding this + args
    return result;                                 // step 8: return (and cache) the first result
  }

  wrapper.reset = () => {                          // step 9: decorated reset() — shares the closure
    called = false;
    result = undefined;
  };

  return wrapper;
}
```

**Try it yourself**

```js
let n = 0;
const init = once((label) => {
  console.log('init:', label);
  return ++n;
});

console.log(init('a'));   // logs "init: a", returns 1
console.log(init('b'));   // no log, returns 1 (cached)
console.log(init('c'));   // no log, returns 1 (cached)

init.reset();
console.log(init('d'));   // logs "init: d", returns 2 (fresh)
```

---

## 9. Step-by-step dry run

Input:

```js
let n = 0;
const f = once((label) => ++n);
f('a'); f('b'); f.reset(); f('c');
```

Values-first trace:

| Step | Call         | `called` | `result` | `fn` invoked? | Returns |
|------|--------------|----------|----------|----------------|---------|
| init | `once(...)`  | `false`  | `undefined` | no          | wrapper |
| 1    | `f('a')`     | `true`   | `1`      | yes            | `1`     |
| 2    | `f('b')`     | `true`   | `1`      | no (gated)     | `1`     |
| 3    | `f.reset()`  | `false`  | `undefined` | no          | undefined |
| 4    | `f('c')`     | `true`   | `2`      | yes            | `2`     |

`fn` was invoked exactly twice across the lifetime — once before reset, once after.

---

## 10. Common confusion + traps

1. **`result === undefined` is not a valid sentinel.**
   Functions can legitimately return `undefined`. Using the result itself as the "has-been-called" check breaks that case. Always use a separate boolean.

2. **Flip-after-invoke breaks re-entrancy and throws.**
   See section 7 — flip-before is the safe order.

3. **Forgetting `this` forwarding.**
   `fn(args)` doesn't pass the receiver. `fn.apply(this, args)` does. Critical for `obj.init = once(obj.init); obj.init();` patterns.

4. **Caching a rejected promise.**
   If `fn` is async and rejects, the cached "result" is a rejected promise. Every subsequent caller awaits it and gets the same rejection — possibly forever. For async with retry-on-fail, delete the cached promise in a `.catch`. See Variant 1.

5. **Memory pinning of large returns.**
   The closure retains `result` indefinitely. If `fn` returns a 1 GB buffer, that buffer is pinned until the wrapper itself is GC'd. For long-lived wrappers around expensive returns, document the lifetime.

6. **Re-arming via property access.**
   Stashing the flag on the wrapper as `wrapper.called` exposes it to mutation. Use closure-over-let for true privacy. Decorate with `wrapper.reset` if you *want* re-arming — that's an explicit API.

---

## 11. Senior follow-ups & variants

### Variant 1 — Async `once` with in-flight dedupe

```js
function onceAsync(fn) {
  let pending = null;        // Promise<T> | null
  return function (...args) {
    if (pending) return pending;
    pending = Promise.resolve()
      .then(() => fn.apply(this, args))
      .catch((err) => { pending = null; throw err; }); // reset on reject so next call retries
    return pending;
  };
}
```

Cache the **Promise**, not the resolved value, so concurrent callers all share one in-flight call. Delete the cache on rejection — your "transient failure" doesn't become "sticky failure for the rest of the process."

This is the **request-dedupe / cache-stampede** pattern. See [`10-machine-coding-patterns/cache-stampede-single-flight.md`](../10-machine-coding-patterns/cache-stampede-single-flight.md).

### Variant 2 — `onceN(fn, n)` — allow N calls, cache last result

```js
function onceN(fn, n) {
  let remaining = n;
  let last;
  return function (...args) {
    if (remaining <= 0) return last;
    remaining--;
    last = fn.apply(this, args);
    return last;
  };
}
```

Counter replaces boolean. Cached result is the *last* invocation, not the first. Useful for "warm up the cache N times" patterns.

### Variant 3 — `.invoked` getter for inspection

```js
function once(fn) {
  let called = false;
  let result;
  function wrapper(...args) {
    if (called) return result;
    called = true;
    return result = fn.apply(this, args);
  }
  Object.defineProperty(wrapper, 'invoked', { get: () => called });
  wrapper.reset = () => { called = false; result = undefined; };
  return wrapper;
}
const f = once(() => 1);
f.invoked;   // false
f();
f.invoked;   // true
```

Exposes the internal flag read-only — useful in tests and metrics.

### Variant 4 — `lazy(fn)` alias

Some libraries (e.g., Vue, RxJS) call this `lazy`. Identical implementation; the alias documents intent: "evaluate this expensive thing the first time it's needed, then memoize."

```js
const config = lazy(() => loadConfigSync());
console.log(config().port);   // first call: loads
console.log(config().host);   // cached
```

---

## 12. How to think aloud in the interview

> "Closure over two slots: a boolean `called` and a value `result`. The flag is the discriminator — without it I can't distinguish 'never called' from 'called and got undefined.' First call: flip the flag (before invoking, for re-entrancy/throw safety), call `fn.apply(this, args)`, store the result. Subsequent calls: gate on the flag and return the cached result. For async, I cache the *Promise* so concurrent callers dedupe, and delete it on rejection so transient failures don't become sticky. Decorate with `.reset()` if re-arming is required."

---

## 13. 60-second revision

> - **Pattern:** closure over `let called = false; let result;` — two slots, both heap-retained.
> - **Set the flag *before* invoking** `fn` → re-entrant-safe and throw-safe.
> - **Forward** `this` + `args` with `fn.apply(this, args)`. Args are discarded on subsequent calls.
> - Use the **boolean flag**, not `result === undefined`, as the sentinel.
> - **Async variant:** cache the **Promise**, not the resolved value. Delete on rejection for retry-on-fail.
> - **Memory:** the cached result is retained forever — large returns become leaks.
> - **Family:** `memoize` (Map cache), `lazy`, leading-only `throttle`, request dedupe.
> - **Trap:** flag-after-call → infinite recursion on re-entry; throw leaves wrapper un-consumed.
> - **Trap:** `result === undefined` as sentinel → breaks for `undefined`-returning functions.

---

**Related:** [allow-one-function-call.md](./allow-one-function-call.md) · [memoize-with-ttl.md](./memoize-with-ttl.md) · [memoize-with-deep-equality.md](./memoize-with-deep-equality.md) · [`10-machine-coding-patterns/cache-stampede-single-flight.md`](../10-machine-coding-patterns/cache-stampede-single-flight.md)

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md)
