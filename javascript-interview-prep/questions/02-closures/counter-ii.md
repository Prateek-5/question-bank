# Counter II (increment / decrement / reset)

## Source
- https://leetcode.com/problems/counter-ii/

## Why this question matters in interviews
Counter II is the bridge from "single closure" to **"object of methods, all closing over the same private state."** That's the **revealing-module pattern** — the dominant pre-ES6 way of building encapsulated modules in JS, and still the cleanest way to expose a small API without classes. Interviewers use it to test whether you understand that *multiple* returned functions can share *one* LE on the heap. It also previews how you'll structure Event Emitter, Pub/Sub, LRU Cache, and any object-returning factory. As a backend engineer, this is the pattern you'll reach for when you want a tiny state-holder without dragging in a class.

## Concepts involved

### Syntax to lock in
```js
function createCounter(init) {
  let n = init;
  return {
    increment() { return ++n; },
    decrement() { return --n; },
    reset()     { return (n = init); },
  };
}
```
- The outer function's LE has **two** slots: `init` and `n`.
- All three methods are function expressions whose `[[Environment]]` points at this **same** LE. They share the `n` slot — mutation by one is visible to the others.

### Lexical environment / shared state
- One LE on the heap, three function objects all pointing to it.
- This is what makes the methods feel like "methods on an object" while actually being independent functions glued by closure over the same scope.
- Contrast with a class instance, where the three methods are on the *prototype* and share state via `this.n`. The closure version doesn't need `this` at all — `n` resolves through the scope chain.

### Why `increment` returns `++n` (pre-increment)
The LeetCode spec says: starting from `init`, the **first `increment()` returns `init + 1`**. So pre-increment. Mixing `n++` here would be off-by-one. Read the spec carefully — Counter (problem 1) uses post-increment, Counter II uses pre-increment. This trips candidates up.

### Edge cases / interview traps
1. **Pre vs post increment** — LeetCode's Counter II spec: `increment()` after `reset()` returns `init+1`, not `init`. Pre-increment.
2. **`reset()` must restore the original init** — you need to **capture `init` separately** and not lose it. Don't write `n = 0`; the test cases pass non-zero `init`.
3. **Methods must share state** — if you accidentally declare `let n` *inside* each method, each method has its own counter. Classic blunder under stress.
4. **No `this`** — the methods don't need `this`, and using `this` invites bugs when callers destructure (`const { increment } = createCounter(5); increment();` — `this` is now undefined). With closures, destructuring is safe because state lives in the LE, not on `this`.
5. **Memory** — the returned object retains the LE. If you stash the object in a long-lived global, the closure (and anything it captures) lives forever.

## Brute force approach
A class:
```js
class Counter {
  constructor(init) { this.init = init; this.n = init; }
  increment() { return ++this.n; }
  decrement() { return --this.n; }
  reset()     { return (this.n = this.init); }
}
```
Works. But the prompt asks for a *function*, not a class — and crucially, `init` and `n` are public (`c.n = 999` works). Closure version is more idiomatic and exposes a smaller surface.

## Optimal approach
One outer function that captures `init` and a mutable `n`, returning an object of three methods that all close over the same scope. Constant memory per counter, O(1) per operation. True encapsulation — no `this`, no field access from outside.

## Solution (JavaScript)

```js
/**
 * @param {number} init
 * @return {{ increment: Function, decrement: Function, reset: Function }}
 */
var createCounter = function (init) {
  let n = init;
  return {
    increment() { return ++n; },
    decrement() { return --n; },
    reset()     { return (n = init); },
  };
};

// Usage
const c = createCounter(5);
c.increment(); // 6
c.increment(); // 7
c.decrement(); // 6
c.reset();     // 5
c.increment(); // 6
```

## Step-by-step dry run

Input:
```js
const c = createCounter(5);
c.increment(); // expect 6
c.increment(); // expect 7
c.decrement(); // expect 6
c.reset();     // expect 5
c.increment(); // expect 6
```

Trace:
1. `createCounter(5)` is called.
   - LE_outer created: `{ init: 5, n: 5 }`.
   - Three method functions are created, all with `[[Environment]] = LE_outer`.
   - An object `{ increment, decrement, reset }` is built and returned.
   - Outer frame popped; LE_outer retained on heap because the three returned methods reference it.
2. `c.increment()` — `++n`: reads `n=5`, writes `n=6`, returns `6`. LE_outer.n is now `6`.
3. `c.increment()` — `++n`: `6 → 7`, returns `7`.
4. `c.decrement()` — `--n`: `7 → 6`, returns `6`.
5. `c.reset()` — assigns `n = init` → `n = 5`. The assignment expression returns the assigned value `5`. LE_outer.n is now `5`.
6. `c.increment()` — `++n`: `5 → 6`, returns `6`.

All three methods read/wrote **the same `n` slot** in **the same LE** on the heap.

## Important takeaways

**Syntax to memorize**
- `let n = init;` in the outer (so `reset` can restore from `init`).
- Method-shorthand syntax in the returned object literal: `increment() { ... }`.
- Pre-increment `++n` for Counter II (post-increment for Counter I).

**Patterns to reuse**
- **Revealing module pattern**: outer function returns `{ method1, method2, ... }` all sharing private state via closure. This is how you'd write Event Emitter, Pub/Sub, LRU cache, a connection-pool handle, a session-store, etc., without classes.
- The pattern is destructuring-safe: `const { increment } = createCounter(5); increment();` still works because there's no `this`.

**Common mistakes**
- Using `n++` instead of `++n` → off-by-one against the spec.
- Forgetting to capture `init` separately — `reset` then has nothing to restore to.
- Putting `let n` inside each method — each method gets its own counter; mutations don't share.
- Adding a `get n()` accessor "for convenience" — defeats the privacy. If you want a peek, expose `peek()` explicitly.

**Related questions**
- Counter (single-method closure)
- Event Emitter (multi-method closure with `subscribe`/`emit` over a `listeners` map)
- To Be Or Not To Be (returns object with `toBe` / `notToBe` — same pattern)
- LRU Cache (closure over `Map` with `get`/`put`)

## Variants

1. **Add `value()` (peek)** — return the current `n` without mutating. Demonstrates that read-only access is a separate method, not a public field.

2. **Bounded counter** — `createCounter(init, { min, max })`. Throws / clamps on out-of-range. Tests how you'd add validation while keeping state private.

3. **Event-driven counter** — every mutation emits an event to subscribed listeners. Mash this with the Event Emitter problem: closure over both `n` and a `listeners` array.

## Revision notes

> **counter II — 60 second recap**
> - Outer captures `init` and `let n = init`.
> - Returned object has three method functions, all closing over the **same LE**.
> - State is shared across methods but invisible to outside callers — true private fields without `class`.
> - **Pre**-increment in Counter II (vs post-increment in Counter I) — re-read the spec each time.
> - `reset()` needs the original `init`; capture it explicitly.
> - No `this` needed — destructuring methods off the returned object stays safe.
> - **Trap:** declaring `let n` inside each method instead of in the outer.
> - Family: revealing module pattern → Event Emitter, Pub/Sub, LRU Cache, To Be Or Not To Be.
