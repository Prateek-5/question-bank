# Build `once(fn)` — call once, subsequent calls return `undefined`

> **Difficulty:** Easy   |   **Time:** ~10 min   |   **Prereqs:** [counter.md](./counter.md), [`concepts/closures.md`](../../concepts/closures.md)
>
> **Source:** [LeetCode 2666 — Allow One Function Call](https://leetcode.com/problems/allow-one-function-call/)

---

## 1. Problem statement

**Signature**
```ts
function once<F extends (...args: any[]) => any>(fn: F):
  (...args: Parameters<F>) => ReturnType<F> | undefined;
```

**Input / Output examples**

| Setup                          | Sequence of calls                    | Output sequence       |
|--------------------------------|--------------------------------------|-----------------------|
| `const f = once((a,b)=>a+b)`   | `f(1,2); f(3,4); f(5,6);`            | `3, undefined, undefined` |
| `const f = once(() => 'go')`   | `f(); f();`                          | `'go', undefined`     |
| `const f = once(() => { throw new Error('x'); })` | `try{f()}catch{}; f();` | `(throws), undefined` (consumed) |
| `const a = once(fn); const b = once(fn);` | `a(); a(); b();`            | independent — each `once` wrapper is separate |

**Constraints**
- After the first call, subsequent calls return `undefined` and do **not** invoke `fn`.
- Forward `this` and **all arguments** to `fn` on the first call.
- The wrapper is "consumed" even if `fn` throws (default LeetCode contract).

---

## 2. Plain-English restatement

Wrap `fn` so it can only be called once. The first call invokes `fn` with whatever arguments you pass and returns its result. Every subsequent call short-circuits — returns `undefined` and doesn't run `fn` at all. The wrapper holds a hidden flag that flips from "not yet called" to "called" on the first invocation, and that flag survives between calls thanks to the closure.

---

## 3. Why this matters in interviews

`once(fn)` is the smallest closure-over-a-flag problem and a backend staple. It maps directly to initialization guards, idempotent webhook handlers, singleton resource setup (open the DB pool once, register signal handlers once), one-shot event listeners (`EventEmitter#once`), and promise resolvers (which reject if called twice). In 6 lines, the interviewer checks: closure over a boolean, argument forwarding, return-value handling, and (the trap) what to return on subsequent calls. Get it crisp and the interviewer moves on; fumble it and they'll drill on re-entrancy and throw semantics.

---

## 4. Mental model

A **single-use ticket**. The wrapper holds one stamp. First call: if the ticket is unstamped, stamp it, forward to `fn`, return the result. All later calls: ticket already stamped, refuse silently (return `undefined`). The stamp lives inside the wrapper's closure — invisible from outside, persistent across calls.

```
   once(fn)
     │
     ├── ticket: ┌────────────────┐
     │          │  called: false │  ← single boolean slot
     │          └────────────────┘
     │
     └── returns ──► wrapper(...args)
                       │
                       ├── called?  yes → return undefined (fn NOT invoked)
                       │
                       └── no → flip flag → fn.apply(this, args)
                                              → return result
```

After the first call, `called` is permanently `true`. The flag never resets (unless you expose a `reset()` method).

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. After `const f = once(console.log); f('a'); f('b');` — what gets logged?
> 2. If `fn` synchronously calls the wrapper inside its own body, what happens — infinite recursion, single execution, or `undefined`?
> 3. If `fn` throws on the first call, what should the second call do — retry or return `undefined`?

---

## 6. Brute force — walked through

### Wrong attempt 1: counter instead of boolean

```js
function once(fn) {
  let count = 0;
  return function (...args) {
    if (count > 0) return undefined;
    count++;
    return fn.apply(this, args);
  };
}
```

Works, but uses 8 bytes of counter where 1 bit of flag would do. Reject because it's slightly less idiomatic — though if the follow-up is "allow N calls," the counter pattern wins. Flag this in your monologue.

### Wrong attempt 2: stash flag on the wrapper function as a property

```js
function once(fn) {
  function wrapper(...args) {
    if (wrapper.called) return undefined;
    wrapper.called = true;
    return fn.apply(this, args);
  }
  return wrapper;
}
```

Works mechanically, but `f.called = false` from outside can re-arm the wrapper — defeating the "called once" guarantee. Closure-over-let is properly private.

### Wrong attempt 3: flip the flag *after* invoking `fn`

```js
function once(fn) {
  let called = false;
  return function (...args) {
    if (called) return undefined;
    const result = fn.apply(this, args);
    called = true;                  // ← BUG: re-entrant call inside fn() recurses
    return result;
  };
}
```

If `fn` synchronously invokes the wrapper (re-entrancy), `called` is still `false` when the re-entrant call runs → infinite recursion. Also, if `fn` throws, `called` stays `false` → the next caller gets to run `fn` again. Whether you want "throw consumes the ticket" or "throw lets the next caller retry" is a *design choice* — but you must make it deliberately, not by accident.

---

## 7. The unlocking insight

> **Flip the flag *before* invoking `fn`. That makes the wrapper safe under both re-entrancy and `fn` throws.**

When you wrap `fn`, the closure holds two captures: a `called` boolean (mutable) and `fn` itself (read-only). The wrapper's entire job is to gate a single forward-call to `fn` based on the flag.

Order matters:

- **Flag-before-invoke** (the canonical order): set `called = true` first, then `fn.apply(this, args)`. Re-entrant calls from inside `fn` see `called === true` and return `undefined`. Throws from `fn` propagate but leave `called === true` (the ticket is consumed). This matches LeetCode and lodash's `_.once`.
- **Flag-after-invoke** (the buggy order): re-entrancy infinite-loops, throws leave the wrapper un-consumed. Avoid unless the interviewer explicitly asks for retry-on-throw.

The flag-before order is the closure's superpower: state mutated synchronously inside the wrapper is visible to any re-entrant call through the same closure on the same heap. There's no race because JS is single-threaded.

Also forward `this` and `args` properly. `fn.apply(this, args)` covers method-style callsites like `obj.init = once(obj.init); obj.init();` — without `apply`, the inner `fn` loses its receiver.

---

## 8. Solution (annotated)

```js
var once = function (fn) {                     // step 1: factory captures `fn` and a private `called` slot
  let called = false;                            // step 2: flag starts false

  return function (...args) {                    // step 3: returned wrapper accepts any args
    if (called) return undefined;                // step 4: guard — short-circuit on subsequent calls
    called = true;                                // step 5: FLIP FIRST (re-entrancy + throw safety)
    return fn.apply(this, args);                  // step 6: forward `this` + args, return result
  };
};
```

**Try it yourself**

```js
const sum = (a, b, c) => a + b + c;
const onceSum = once(sum);
console.log(onceSum(1, 2, 3));    // 6
console.log(onceSum(10, 20, 30)); // undefined  (fn NOT called)
console.log(onceSum(99, 99, 99)); // undefined

// Independent wrappers from independent factory calls
const a = once(sum), b = once(sum);
console.log(a(1, 2, 3));          // 6
console.log(b(1, 2, 3));          // 6  (different closure, different flag)

// this forwarding
const obj = { greet: once(function (n) { return `hi ${this.name}, ${n}`; }), name: 'alice' };
console.log(obj.greet(1));        // "hi alice, 1"
console.log(obj.greet(2));        // undefined
```

---

## 9. Step-by-step dry run

Input:

```js
const sum = (a, b, c) => a + b + c;
const f = once(sum);
f(1, 2, 3); f(10, 20, 30); f(5, 5, 5);
```

Values-first trace:

| Step | Call          | `called` (before → after) | `fn` invoked? | Returns       |
|------|---------------|---------------------------|---------------|---------------|
| init | `once(sum)`   | `false`                   | no            | the wrapper   |
| 1    | `f(1, 2, 3)`  | `false → true`            | yes (`sum(1,2,3)`) | `6`        |
| 2    | `f(10, 20, 30)` | `true → true`           | no (gated)    | `undefined`   |
| 3    | `f(5, 5, 5)`  | `true → true`             | no            | `undefined`   |

LE: `{called, fn}`. `called` mutated exactly once and stayed `true`. `fn` invoked exactly once.

---

## 10. Common confusion + traps

1. **Flag-after-invoke breaks re-entrancy.**
   If `fn` synchronously calls the wrapper, you need the flag to be `true` *before* `fn` runs. Otherwise the inner call sees `called === false` and runs `fn` again → infinite recursion (or unbounded side effects).

2. **Flag-after-invoke and `fn` throws.**
   If `fn` throws and you only set `called = true` after the call, the wrapper is "un-consumed." The next caller runs `fn` again. Whether that's desirable depends on the spec — clarify before coding.

3. **Argument and `this` forwarding.**
   Use `fn.apply(this, args)`, not `fn(args)`. The former forwards `this`; the latter doesn't. Breaks `obj.init = once(obj.init); obj.init();`.

4. **Storing the flag on the wrapper function as a property.**
   `wrapper.called = ...` lets callers re-arm with `f.called = false`. Defeats the privacy guarantee.

5. **Memory pinning.**
   The closure retains `fn` forever, even after the single call. If `fn` references a 50 MB blob and the wrapper outlives the work, that blob is pinned. For aggressive cleanup, null out `fn` after the call (rarely necessary):

   ```js
   var once = function (fn) {
     let called = false;
     return function (...args) {
       if (called) return undefined;
       called = true;
       const result = fn.apply(this, args);
       fn = null;        // optional: release reference
       return result;
     };
   };
   ```

6. **LeetCode vs lodash semantics.**
   LeetCode: subsequent calls return `undefined`. Lodash `_.once`: subsequent calls return the *cached first result*. **Clarify upfront** — interviewers will sometimes ask both.

---

## 11. Senior follow-ups & variants

### Variant 1 — Cache the first result (`lodash _.once`)

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

Different return semantics on subsequent calls. See [once-with-cached-return.md](./once-with-cached-return.md) for the full deep-dive.

### Variant 2 — `allowN(fn, n)` — generalize to N calls

```js
function allowN(fn, n) {
  let remaining = n;
  return function (...args) {
    if (remaining <= 0) return undefined;
    remaining--;
    return fn.apply(this, args);
  };
}
```

Counter replaces flag; pattern unchanged. Useful for "you have 3 retries" gates.

### Variant 3 — Async `once` (in-flight dedupe)

```js
function onceAsync(fn) {
  let pending = null;
  return function (...args) {
    if (pending) return pending;
    pending = Promise.resolve().then(() => fn.apply(this, args));
    return pending;
  };
}
```

Concurrent callers all `await` the *same* promise. This is the **request deduplication** pattern — see [`10-machine-coding-patterns/cache-stampede-single-flight.md`](../10-machine-coding-patterns/cache-stampede-single-flight.md).

### Variant 4 — Retry-on-throw

```js
function onceRetry(fn) {
  let called = false;
  return function (...args) {
    if (called) return undefined;
    const result = fn.apply(this, args);   // throw lets called stay false
    called = true;
    return result;
  };
}
```

Now a throwing `fn` doesn't consume the ticket — the next caller retries. Useful when transient failures shouldn't disable initialization forever.

### Variant 5 — Re-armable with `.reset()`

```js
function once(fn) {
  let called = false;
  function wrapper(...args) {
    if (called) return undefined;
    called = true;
    return fn.apply(this, args);
  }
  wrapper.reset = () => { called = false; };
  return wrapper;
}
```

Same decorated-function pattern from `create-incrementer.md`. The reset method shares the closure, so it can mutate `called` from outside the main wrapper.

---

## 12. How to think aloud in the interview

> "Closure over a `called` boolean. Wrapper: if the flag is true, return `undefined`; else flip the flag, then invoke `fn` with `this` and all args. Flip-first is the key choice — protects against re-entrancy (inner call sees the flag set) and means a throw still consumes the ticket. If they want retry-on-throw, I'd move the flip below the `apply`. If they want lodash semantics (return cached first result on subsequent calls), I add a `result` slot. Use `fn.apply(this, args)`, not `fn(args)`, so method-style callsites work. Memory note: closure pins `fn`; null it out after the call if cleanup matters."

---

## 13. 60-second revision

> - **Pattern:** closure over `let called = false`; on first call set `called = true` **before** invoking `fn`.
> - **Always forward**: `fn.apply(this, args)`.
> - **Subsequent calls** return `undefined` (LeetCode) or cached first result (lodash) — clarify spec.
> - **Flip-before-invoke** = re-entrant-safe and throw-safe (ticket is consumed even on throw).
> - **Trap:** flip-after-invoke → re-entrant infinite loop; throw leaves the ticket un-consumed.
> - **Trap:** `fn(args)` instead of `fn.apply(this, args)` — breaks method-style callsites.
> - **Family:** lazy init, singleton, idempotent handlers, `EventEmitter#once`, request dedupe.
> - Async variant = closure over a Promise = request deduplication.

---

**Related:** [once-with-cached-return.md](./once-with-cached-return.md) · [counter.md](./counter.md) · [memoize-with-ttl.md](./memoize-with-ttl.md) · [`10-machine-coding-patterns/cache-stampede-single-flight.md`](../10-machine-coding-patterns/cache-stampede-single-flight.md)

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md)
