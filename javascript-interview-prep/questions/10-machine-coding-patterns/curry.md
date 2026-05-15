# Implement `curry(fn)`

## Source
- Canonical machine-coding interview problem (codedamn "Curry Function Implementation", BFE.dev, Frontend Masters).
- codedamn reference: https://codedamn.com/problem/vqf9CjnUNextjlV5yQ4NP

## Why this question matters in interviews
Curry is the canonical "do you understand higher-order functions, closures, and `Function.length`" question, packaged in a ten-line implementation. It looks trivial until the interviewer asks for **placeholder support** or **infinite curry** (`f(1)(2)(3)...()` triggers invocation). The implementation tests three things: (1) reading `fn.length` to know the target arity, (2) accumulating args across nested calls via closure, (3) deciding **when to invoke** (when accumulated args ≥ arity). Backend engineers see curry less than frontend (where Ramda / lodash/fp lean on it), but it shows up in middleware factories (`logger(level)(message)`), config builders, and partial-application patterns. The senior bonus is showing the placeholder-aware version (`_`), which is what real libraries ship.

## Concepts involved

### Syntax to lock in
```js
const sum = (a, b, c) => a + b + c;
const csum = curry(sum);

csum(1, 2, 3);   // 6
csum(1)(2, 3);   // 6
csum(1)(2)(3);   // 6
csum(1, 2)(3);   // 6

function curry(fn) {
  return function curried(...args) {
    if (args.length >= fn.length) return fn.apply(this, args);
    return (...next) => curried.apply(this, [...args, ...next]);
  };
}
```

### Runtime / engine behavior
- `fn.length` returns the count of **declared formal parameters before the first default or rest**. So `function f(a, b, c) {}` has `length === 3`. `function f(a, b = 1, c) {}` has `length === 1`. `function f(...args) {}` has `length === 0`.
- This is the trap: if `fn` uses defaults or rest, `curry(fn)` won't fire at the expected arity. Document it.
- Each curried call returns a **new function** that closes over the accumulated `args`. No mutation; each branch of the curry tree is independent.
- `apply(this, [...args, ...next])` preserves `this` for method-style use, though curry is usually applied to pure functions.

### Edge cases (these are the interview traps)
1. **Variadic functions** (`...args`) → `fn.length === 0`, so the curry fires on the first call with zero args. Useless. Require the user to pass arity explicitly: `curry(fn, arity)`.
2. **Default parameters** drop `fn.length` to the count before the first default. `curry((a, b = 0) => a + b).length` is `1`, so `csum(5)` would invoke immediately, ignoring `b`. Same fix: explicit arity.
3. **Placeholder support** (`_`) — Lodash and Ramda allow `curry(fn)(_, 2)(1, 3)` to skip an argument slot. Requires storing the placeholder positions and reconciling on each call. Show as a variant.
4. **Calling with more args than arity** — `csum(1, 2, 3, 4)` — extras are passed through (ignored by `fn` if it doesn't use them). Don't error.
5. **Re-using a partially-applied curry** — `const add1 = csum(1)`. `add1(2, 3)` and `add1(5, 10)` should both work and not contaminate each other. The implementation above is correct because `args` is fresh per branch.
6. **`this` binding** — preserve via `.apply(this, ...)`. Curry is usually used on pure functions, but interviewers sometimes test method-style use.
7. **Zero-arity functions** — `curry(() => 42)` has `fn.length === 0`, so the first call (with no args) returns `42` immediately. Handle gracefully.
8. **Infinite curry** — variant where `f()()()` keeps going until you call `.value()` or pass no args. Different problem; mention as a variant.

## Brute force approach
Write three separate functions: `curry1`, `curry2`, `curry3` for fixed arities. Embarrassing. Skip.

## Optimal approach
A self-recursive curried function that accumulates args via closure and checks against `fn.length`. Eight-line implementation. The whole problem fits on one screen.

## Solution (JavaScript)

```js
/**
 * Curries `fn`. The returned function takes any number of args at a time;
 * it fires the underlying fn when accumulated args >= fn.length.
 * @param {Function} fn
 * @param {number} [arity=fn.length]  override for variadic / default-param fns
 * @returns {Function}
 */
function curry(fn, arity = fn.length) {
  return function curried(...args) {
    if (args.length >= arity) {
      return fn.apply(this, args);
    }
    return function (...next) {
      return curried.apply(this, [...args, ...next]);
    };
  };
}
```

With placeholder support (Lodash-style):

```js
const _ = Symbol.for('curry.placeholder');

function curryWithPlaceholder(fn, arity = fn.length) {
  return function curried(...args) {
    // Fill placeholders left-to-right
    const filled = [];
    let i = 0, j = 0;
    while (i < args.length || j < filled.length) {
      // (simplified — real impl walks both lists)
    }
    const concrete = args.filter((a) => a !== _);
    const hasPlaceholder = args.some((a) => a === _);

    if (!hasPlaceholder && concrete.length >= arity) {
      return fn.apply(this, args);
    }

    return function (...next) {
      // Merge: fill placeholders in `args` from `next`, then append remaining `next`.
      const merged = [];
      let k = 0;
      for (const a of args) {
        if (a === _ && k < next.length) merged.push(next[k++]);
        else merged.push(a);
      }
      while (k < next.length) merged.push(next[k++]);
      return curried.apply(this, merged);
    };
  };
}
```

Placeholder version is a fair amount more code — only write it if asked.

## Step-by-step dry run

Input:
```js
const sum = (a, b, c) => a + b + c;     // fn.length === 3
const csum = curry(sum);

csum(1)(2)(3);
csum(1, 2)(3);
csum(1)(2, 3);
csum(1, 2, 3);
```

Trace `csum(1)(2)(3)`:
- `csum(1)`: `args = [1]`, length=1 < arity 3 → return `next => curried([1, ...next])`. Call this `f1`.
- `f1(2)`: invokes `curried([1, 2])`. length=2 < 3 → return `next => curried([1, 2, ...next])`. Call this `f2`.
- `f2(3)`: invokes `curried([1, 2, 3])`. length=3 ≥ 3 → return `sum(1, 2, 3) = 6`.

Trace `csum(1, 2)(3)`:
- `csum(1, 2)`: args=[1,2], length=2 < 3 → return `f`.
- `f(3)`: invokes `curried([1, 2, 3])`. length=3 ≥ 3 → `sum(1,2,3) = 6`.

Trace `csum(1)(2, 3)`:
- `csum(1)`: args=[1], length=1 < 3 → return `f1`.
- `f1(2, 3)`: invokes `curried([1, 2, 3])`. length=3 ≥ 3 → `sum(1,2,3) = 6`.

Trace `csum(1, 2, 3)`:
- Direct call. args=[1,2,3], length=3 ≥ 3 → `sum(1,2,3) = 6`.

Now reuse:
```js
const add5 = csum(5);
add5(10, 20);   // 35
add5(100, 200); // 305 — fresh args, no contamination
```

Because each call to `curried(...args)` builds a fresh return function closing over **that call's** args, partial applications are independent.

Placeholder trace (`_` = placeholder):
```js
csum(_, 2, _)(1)(3);
// step 1: args=[_, 2, _]. concrete count = 1 < 3, has placeholder → return inner fn.
// step 2: call with next=[1]. Walk args, replace first _ with 1 → [1, 2, _].
//         Still has placeholder → return inner fn.
// step 3: call with next=[3]. Replace first _ with 3 → [1, 2, 3]. No placeholders. → sum(1,2,3) = 6.
```

## Important takeaways

**Syntax to memorize**
- `fn.length` = arity = number of formal parameters (not counting defaults or rest).
- Recursive helper that returns either the result (when full) or a new wrapper that appends more args.
- `[...args, ...next]` — spread merge of accumulated and new args.

**Patterns to reuse**
- "Accumulate state across closure boundaries until a threshold is met" is the same pattern as: batchProcessor (collect args, flush when count ≥ N), retry-with-attempts (count attempts, give up when ≥ max), throttle (count time elapsed).
- Currying is the foundation of **point-free programming** and **partial application** — useful for building config factories: `const log = curry((level, scope, msg) => ...); const errInDB = log('error', 'db');`.

**Common mistakes**
- Relying on `fn.length` without realizing default params or rest args break it. Always allow explicit arity override.
- Mutating `args` (e.g., `args.push(...next)`) — corrupts other branches of the curry tree. Always create a new array.
- Forgetting `this` forwarding — `.apply(this, ...)` not `.apply(null, ...)`.
- Returning the wrapper function directly instead of `curried.apply(this, ...)` — breaks deeper currying.

**Related questions**
- `partial(fn, ...presetArgs)` — fixes args upfront; degenerate case of curry.
- `compose` / `pipe` — work much better when functions are curried (so they're all unary).
- Placeholder curry (Ramda `R.__`).

## Variants

1. **Curry with explicit arity** — `curry(fn, 3)` overrides `fn.length`. Required for variadic functions.

2. **Placeholder curry** — `curry(fn)(_, 2)(1, 3)` skips slots. Real-world libraries (Lodash, Ramda) ship this. Bonus depth — see snippet above.

3. **Infinite / unbounded curry** — `f(1)(2)(3)()` invokes when called with no args. Useful for variadic accumulators: `sum(1)(2)(3)() === 6`. Detect zero-arg call to terminate.

4. **Async curry** — args can be promises; curry awaits them. Niche; mention if asked.

5. **`partial`** — `partial(fn, a)(b, c) === fn(a, b, c)`. Strictly weaker than curry but simpler. Useful when arity is unknown.

## Revision notes

> **curry — 60 second recap**
> - Recursive: `curried(...args)` → if `args.length >= fn.length`, invoke; else return `(...next) => curried([...args, ...next])`.
> - `fn.length` = declared arity (broken by defaults / rest → pass arity explicitly).
> - Each partial application is independent (new args array per call).
> - Variants: placeholder (`_`), infinite curry (terminates on zero-arg call), explicit arity.
> - **Trap:** `fn.length === 0` for rest/variadic fns — naive curry fires immediately.
> - **Trap 2:** mutating `args` contaminates sibling partials.
