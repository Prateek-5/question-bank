# Implement `once(fn)` — invoke at most once, cache the result

> **Difficulty:** Easy   |   **Time:** ~10 min   |   **Prereqs:** [`concepts/closures.md`](../../concepts/closures.md), [`02-closures/once-with-cached-return.md`](../02-closures/once-with-cached-return.md)
>
> **Source:** lodash `_.once`, Underscore, [LeetCode 2666 — Allow One Function Call](https://leetcode.com/problems/allow-one-function-call/).

---

## 1. Problem statement

**Signature**
```ts
function once<F extends (...args: any[]) => any>(fn: F): F & { reset(): void };
```

**Input / Output examples**

| Setup                                                | Behaviour                                              |
|------------------------------------------------------|---------------------------------------------------------|
| `init = once(fn); init(); init();`                   | `fn` called once; second call returns cached result    |
| `fn` returns `undefined`                             | second call returns cached `undefined` (not re-run)    |
| `fn` throws                                          | choose: rethrow + mark called, OR rollback + retry     |
| `init.reset()` then `init()`                         | `fn` runs again (re-armed)                             |
| `obj.boot = once(obj.boot); obj.boot()`              | `this` forwarded correctly                             |

**Constraints**
- Cache the **result** (including `undefined`/`null`/`0`/`""`).
- Gate on a boolean flag, not on the cached value.
- Forward `this` + args via `.apply`.
- Decide error policy: mark-called-and-rethrow vs rollback.

---

## 2. Plain-English restatement

Wrap a function so it runs at most one time. After the first call, every subsequent call returns the cached result without re-running. Use it for one-shot init routines, lazy singletons, "show this dialog once" flags, module-init guards, idempotent boot.

---

## 3. Why this matters in interviews

`once` is the smallest closure problem with depth. The boolean+slot pattern looks trivial until follow-ups: "what if `fn` throws?", "what if `fn` is async?", "what's the relationship to throttle?" These separate juniors from staff candidates. As a backend engineer you'll see `once` for lazy DB pool init, singleton metric clients, one-shot signal handlers, idempotent migration runners.

---

## 4. Mental model

A **fuse**: triggers once, then conducts the cached value forever.

```
   first call:
   ┌──────────────────────────────┐
   │ called=false                 │
   │ run fn(args) → result        │
   │ called=true, cache result    │
   │ return result                │
   └──────────────────────────────┘

   subsequent calls:
   ┌──────────────────────────────┐
   │ called=true                  │
   │ return cached result         │  ← O(1) hot path: one boolean read
   │ (fn never invoked again)     │
   └──────────────────────────────┘
```

Family relationship: **`once(fn) === throttle(fn, Infinity, {leading: true, trailing: false})`**.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. If `fn` returns `undefined`, will the second call invoke `fn` again? (Hint: depends on what you gate on.)
> 2. If `fn` throws on the first call, should the second call retry or rethrow the cached error?
> 3. Why use `fn.apply(this, args)` instead of `fn(...args)`?

---

## 6. Brute force — walked through

### Wrong attempt 1: gate on cached value
```js
function once(fn) {
  let result;
  return function (...args) {
    if (result !== undefined) return result;        // BUG
    result = fn.apply(this, args);
    return result;
  };
}
```
If `fn` returns `undefined`, every call re-invokes. Gate on a boolean flag, not on the value.

### Wrong attempt 2: set called BEFORE running fn (no rollback)
```js
called = true;
result = fn(...);    // throws → called stays true, future calls return undefined
```
Silently swallows the error on subsequent calls. Either: rollback on throw, or document that "first call's error is permanent."

### Wrong attempt 3: set called AFTER running fn (re-entrant infinite loop)
```js
result = fn.apply(this, args);    // if fn re-invokes the wrapper, recurses forever
called = true;
```
If `fn` itself calls the wrapper (re-entrant), it loops. Set called BEFORE — accept the trade-off.

---

## 7. The unlocking insight

> **Closure over a boolean flag + cached result. Gate the hot path on the flag, not on the value. Forward `this` + args via `.apply`. Pick an error policy (rethrow vs rollback) and document it.**

Three properties:

1. **Boolean flag** as sentinel — handles `undefined`/`null`/`0`/`""` correctly.
2. **`.apply(this, args)`** preserves method-style use.
3. **Error policy:** set `called = true` first, then in `catch` either rollback (`called = false; throw`) or commit (`throw` only). Document the choice.

---

## 8. Solution (annotated)

```js
function once(fn) {
  let called = false;                                            // step 1: closure-scoped flag
  let result;

  function onced(...args) {
    if (called) return result;                                   // step 2: hot path, gate on flag

    called = true;                                                // step 3: set BEFORE to block re-entry
    try {
      result = fn.apply(this, args);                              // step 4: forward this + args
    } catch (err) {
      called = false;                                             // step 5: rollback so caller can retry
      throw err;
    }
    return result;
  }

  onced.reset = () => { called = false; result = undefined; };   // step 6: re-arm for tests

  return onced;
}
```

**Try it yourself**

```js
let counter = 0;
const init = once(() => { counter++; return { id: counter, time: Date.now() }; });

const a = init();
const b = init();
const c = init();
console.log(a === b, b === c, counter);   // true true 1

init.reset();
const d = init();
console.log(d === a, counter);             // false 2
```

Async usage — cache the **Promise** so concurrent callers share the in-flight call:

```js
const fetchConfig = once(() => fetch('/config.json').then(r => r.json()));
const [a, b] = await Promise.all([fetchConfig(), fetchConfig()]);  // 1 network call
console.log(a === b);   // true (same resolved object)
```

---

## 9. Step-by-step dry run

```
let counter = 0
const init = once(() => { counter++; return { id: counter } })

call init():    called=false → enter branch
                set called=true
                run fn → counter=1, return {id:1}
                cache result={id:1}
                return {id:1}
                state: called=true, result={id:1}, counter=1

call init():    called=true → return cached {id:1}
                state unchanged; counter=1

call init():    called=true → return cached {id:1}
                state unchanged; counter=1

call init.reset():
                called=false, result=undefined
                counter unchanged

call init():    called=false → enter branch
                set called=true
                run fn → counter=2, return {id:2}
                cache result={id:2}
                state: called=true, result={id:2}, counter=2
```

---

## 10. Common confusion + traps

1. **Gating on `result != null`** — fails when `fn` legitimately returns `null`/`undefined`/`0`/`""`.
2. **Forgetting `this` forwarding** — breaks `obj.method = once(obj.method)`.
3. **Setting flag after fn runs** — re-entrant infinite loop.
4. **Setting flag before fn runs, no rollback** — first throw poisons future calls.
5. **Async: caching the resolved value** — second concurrent caller re-invokes `fn` before first settles. Cache the Promise.
6. **Forgetting `.reset()`** — interviewer asks "how do you test this?"; no escape hatch.
7. **Memory** — closed-over `fn` retains its captured state forever; null it out after first call if it holds large data.

---

## 11. Senior follow-ups & variants

### Variant 1 — `onceAsync(fn)`
Cache the in-flight Promise so concurrent callers share it. On reject, evict so the next call retries.
```js
function onceAsync(fn) {
  let promise = null;
  return (...args) => {
    if (promise) return promise;
    promise = Promise.resolve().then(() => fn.apply(this, args)).catch((e) => { promise = null; throw e; });
    return promise;
  };
}
```

### Variant 2 — `onceOrThrow(fn)`
Throw on second call instead of returning cached value. For one-shot tokens (CSRF, single-use callbacks, "stream may only be consumed once").

### Variant 3 — N-times variant `times(fn, n)`
Generalize: invoke at most `n` times, then cache. Counter instead of boolean.

### Variant 4 — Memory release
After first call, `fn = null` inside the closure to release the original function's captured state.

### Variant 5 — Relationship to throttle family
`once(fn) === throttle(fn, Infinity, {leading: true, trailing: false})`. State this — it's the link.

---

## 12. How to think aloud

> "Closure over `called` flag + cached `result`. Hot path: `if (called) return result`. First call: set `called = true` first (to block re-entry), then run `fn.apply(this, args)`; on throw, rollback `called = false` so caller can retry. Gate on the flag, not on the value — handles `fn → undefined`. Async variant caches the Promise so concurrent callers share in-flight call. Family: `once === throttle(_, Infinity, {leading, !trailing})`, same shape as memoize (single-slot), lazy. Trap: setting `called = true` after `fn` runs → re-entrant infinite loop."

---

## 13. 60-second revision

> - **Closure over `called` (boolean) + `result`.**
> - **Hot path:** `if (called) return result`.
> - **Set `called = true` BEFORE running** to block re-entry; rollback in catch.
> - **`fn.apply(this, args)`** for method-style use.
> - **Gate on the flag, not on the value** — handles cached `undefined`/`0`/`""`.
> - **Async:** cache the Promise (dedupe in-flight); evict on reject.
> - **Family:** `once === throttle{leading, !trailing, wait=Infinity}`; memoize (single-slot); lazy.
> - **Trap:** gating on result; missing `.apply`; re-entrant loop.

---

**Related:** [`02-closures/once-with-cached-return.md`](../02-closures/once-with-cached-return.md) · [`02-closures/allow-one-function-call.md`](../02-closures/allow-one-function-call.md) · [memoize.md](./memoize.md) · [throttle.md](./throttle.md) · [`04-promises/async-memoize.md`](../04-promises/async-memoize.md)

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md)
