# Counter

## Source
- https://leetcode.com/problems/counter/

## Why this question matters in interviews
Counter is the second-most-asked JS warm-up after debounce. In ~10 lines it forces you to demonstrate the **single most important closure pattern in the language**: a function that retains and mutates private state across calls. It maps directly to backend reality — request-id generators, sequence numbers, retry counters, connection pools, rate-limiter token counts, idempotency keys. Interviewers also use it as a launching pad: "now make it thread-safe-ish" (Counter II), "now reset it" (Counter II), "now make it private without using closures" (compare to `#field`). Whiff this and the rest of the round goes downhill.

## Concepts involved

### Syntax to lock in
```js
function createCounter(n) {
  return function () {
    return n++;     // post-increment: returns then increments
  };
}
```
- `n` is the parameter of the outer function — it's a **local variable** of `createCounter`'s LE.
- The inner function captures `n` by reference to the LE binding, not by value. Mutating `n` from inside the inner function mutates the same slot.

### Lexical environment / what survives after return
- When `createCounter(10)` is called, a new LE is created with `n = 10` as a slot.
- The returned function holds `[[Environment]] = LE_createCounter`. So after the outer call returns, the LE is retained on the heap.
- Every invocation of the returned function looks up `n` via the scope chain → finds it in `LE_createCounter` → reads it, then post-increments it. The new value is written back to the *same* slot.
- Two calls to `createCounter()` produce two *independent* counters because each invocation creates a *new* LE. This is the source of true privacy — and the model for the "factory of stateful function" idiom.

### Why this is private state (better than class fields, in interview terms)
- Inside the closure, `n` is unreachable from outside. No `.n` accessor, no `Object.getOwnPropertyNames`, no Reflection, nothing. It's literally bound to a function's LE.
- Compare to a class with `this.n`: easily readable / mutable from outside.
- Compare to a class with `#n` (private field): also private, but introduced in ES2022 and the closure pattern predates it by 20 years — interviewers expect you to know both.

### Edge cases / interview traps
1. **`return n++` vs `return ++n`** — LeetCode wants the **first call to return `n`** (the initial value), so post-increment is right. Pre-increment returns `n+1` on the first call, off-by-one.
2. **Capture by reference, not value** — newbies think the inner function "freezes" `n` at creation. It doesn't; the LE binding is live.
3. **Two counters share nothing** — even if the outer is called with the same `n`, each call makes a fresh LE.
4. **Memory leak via long-lived closure** — if a counter is registered on a long-lived emitter and never released, its LE stays in memory forever. For a single number this is trivial; for a counter that closes over a 50MB cache it isn't.
5. **`this` is unused** — the inner function doesn't reference `this`. Don't introduce it.

## Brute force approach
"I'll store the count on a global." Works mechanically but defeats the whole purpose: no isolation, two callers collide, no parallel instances. Reject in 5 seconds.

"I'll use a class with a public field." Works, but exposes the count to any caller. The interviewer asked for a *function*, not a class — read the prompt.

## Optimal approach
A factory function that captures the initial value in its LE and returns a function that post-increments and returns the captured slot. O(1) state per counter, O(1) per call. True privacy.

## Solution (JavaScript)

```js
/**
 * @param {number} n
 * @return {Function} counter
 */
var createCounter = function (n) {
  return function () {
    return n++;
  };
};

// Usage
const counter = createCounter(10);
counter(); // 10
counter(); // 11
counter(); // 12
```

## Step-by-step dry run

Input:
```js
const c = createCounter(10);
c(); c(); c();
```

Trace:
1. `createCounter(10)` is called.
   - LE_outer created: `{ n: 10 }`.
   - Inner function object created with `[[Environment]] = LE_outer`.
   - Function object returned. `c` now points to it.
   - `createCounter`'s frame is popped from the call stack. `LE_outer` is retained on the heap because `c` holds a reference.
2. `c()` — first call.
   - LE_inner created with parent = LE_outer.
   - Expression `n++` evaluated. Lookup `n` via scope chain → found in LE_outer with value `10`.
   - Post-increment returns `10`, then writes `11` back to LE_outer's `n` slot.
   - LE_inner popped. Returns `10`.
3. `c()` — second call.
   - New LE_inner, same parent LE_outer.
   - Reads `n = 11`, returns `11`, writes `12`.
4. `c()` — third call. Reads `12`, returns `12`, writes `13`.

LE_outer's `n` slot has gone `10 → 11 → 12 → 13`. Every call read-then-wrote the *same* slot in *the same* LE on the heap.

## Important takeaways

**Syntax to memorize**
- `function outer(n) { return function () { return n++; }; }` — the canonical "private state via closure" skeleton.
- Post-increment `n++` for "first call returns the initial value."

**Patterns to reuse**
- "Private state via outer function's LE" is the idiom for: ID generators, sequence numbers, once/flag, debounce timerId, throttle lastCall, memoize cache, EventEmitter listener list.
- The closure-based **module pattern** (pre-ES6) is exactly this scaled up: outer returns an *object* of methods, all closing over private variables.

**Common mistakes**
- Pre-increment by accident (off-by-one).
- Treating the returned function as if it can be reset from outside — it can't. If reset is needed, expose a method (Counter II).
- Forgetting that two factory calls give independent state.
- Closing over a large object unnecessarily (memory bloat).

**Related questions**
- Counter II — extends this with increment/decrement/reset (multi-method closure).
- Allow One Function Call — closure over a boolean instead of a number.
- Memoize — closure over a `Map`.
- Currying — chained closures.

## Variants

1. **`createCounter(n, step)`** — step argument, capture both. Same pattern, two slots in the LE.

2. **Closure vs class `#field`** — interviewer asks "rewrite with a class using true privacy." Show the `class { #n; constructor(n){this.#n=n;} inc(){return this.#n++;} }` version, then discuss tradeoffs: closure is lighter, class is more discoverable; closure has no prototype overhead, class is easier to extend.

3. **Counter with a "peek"** — return an object `{ next, peek }` where `peek` reads without incrementing. Sets up Counter II naturally.

## Revision notes

> **counter — 60 second recap**
> - Outer captures `n`; returned inner does `return n++`.
> - The LE of the outer call survives on the heap as long as the returned function does — that's the closure.
> - Two factory calls = two independent LEs = two independent counters.
> - **Privacy:** `n` is unreachable from outside. Stronger isolation than a regular class field, equivalent to `#n`.
> - **Trap:** `++n` instead of `n++` is an off-by-one.
> - **Trap:** declaring `n` inside the inner — resets on every call.
> - Memory: keep an eye on what else the closure captures; long-lived closures = retained heap.
> - Family: ID generators, once, memoize, debounce timerId, module pattern.
