# Curry an arity-N function via closures (no `fn.length` tricks)

## Source
- Classic FP interview problem (BFE.dev, LeetCode #2632 "Curry", lodash `_.curry`).
- Foundational to Ramda, fp-ts, and any FP-flavored JS library.

## Why this question matters in interviews
Curry tests whether you can write a closure that **accumulates state across calls** and returns either another function (still collecting) or the final result (when satisfied). It is the single best problem for showing you understand **closures over arrays**. Senior backend interviewers reach for it when they want to see your FP literacy — middleware composition (Express, Koa), Redux selectors, and HOFs in TypeScript libraries all build on the same pattern. The "no `fn.length` tricks" constraint forces an explicit `arity` argument, which is the more general and honest formulation.

## Concepts involved

### Syntax to lock in
```js
function curry(fn, arity = fn.length) {
  return function curried(...args) {
    if (args.length >= arity) return fn.apply(this, args.slice(0, arity));
    return function (...more) {
      return curried.apply(this, [...args, ...more]);
    };
  };
}

const add3 = (a, b, c) => a + b + c;
const c = curry(add3, 3);
c(1)(2)(3);     // 6
c(1, 2)(3);     // 6
c(1)(2, 3);     // 6
c(1, 2, 3);     // 6
```

### Runtime / engine behavior
- Each partial application creates a **new closure** capturing the accumulated `args` array. The chain forms a small linked list of closure records on the heap, one per partial call.
- The recursion isn't true call-stack recursion: each `curried(...)` returns a *new function* whose call site is independent. No stack growth — the inner functions are scheduled by the caller, not stacked.
- `args.slice(0, arity)` truncates excess args (lodash matches this). Some implementations pass *all* args through; clarify with the interviewer.
- `fn.length` counts named params **before** the first default value or rest param. Don't rely on it for variadic or default-param functions — hence the explicit `arity`.

### Edge cases (interview traps)
1. **Default parameters** — `(a, b = 1) => ...` has `fn.length === 1`. Curry will fire after one arg. Always allow explicit `arity` override.
2. **Rest params** — `(...args) => ...` has `fn.length === 0`. Curry fires immediately. Same fix.
3. **Zero arity** — `curry(() => 'hi', 0)`. The curried call should fire on the first invocation `c()`, not on definition.
4. **`this` binding** — pass through with `.apply(this, ...)` for method-style use.
5. **Variadic spread within a single call** — `c(1, 2, 3, 4)` with `arity=3`. Truncate or pass through? Interview default: truncate.
6. **Currying with placeholders** — `c(1, _, 3)(2)` is lodash's flavour. Not required unless asked, but worth knowing it exists.
7. **Memory** — each partial pins the accumulated `args` array on the heap. Long currying chains over heavy args = leak risk.

## Brute force approach
"Loop until I have enough args, then call `fn`." Doesn't work as written — currying is **call-by-call**, so the loop is implicit in the caller's invocation pattern, not in your code. The closure-recursion form *is* the natural shape.

## Optimal approach
Closure over an accumulated `args` array. On each call:
1. If `args.length >= arity` → call `fn` and return result.
2. Otherwise → return a new closure that, when called, concatenates new args and re-checks.

O(N) closures created for an N-arity curry (one per partial). O(N) `args` array growth.

## Solution (JavaScript)

```js
/**
 * Curry an N-arity function. No reliance on fn.length — pass arity explicitly.
 * @param {Function} fn
 * @param {number} [arity=fn.length]
 * @returns {Function}
 */
function curry(fn, arity = fn.length) {
  return function curried(...args) {
    // Enough args collected → invoke
    if (args.length >= arity) {
      return fn.apply(this, args.slice(0, arity));
    }
    // Not enough — return a closure that keeps collecting
    return function next(...more) {
      return curried.apply(this, [...args, ...more]);
    };
  };
}

// Usage
const sum3 = (a, b, c) => a + b + c;
const cSum = curry(sum3, 3);
cSum(1)(2)(3);    // 6
cSum(1, 2)(3);    // 6
cSum(1, 2, 3);    // 6
cSum(1)(2, 3);    // 6
```

## Step-by-step dry run

Input:
```js
const add3 = (a, b, c) => a + b + c;
const c = curry(add3, 3);

const step1 = c(1);        // partial #1
const step2 = step1(2);    // partial #2
const result = step2(3);   // invocation
```

Trace:
- `c = curry(add3, 3)` → returns `curried` (closure #0 over `arity=3`, `fn=add3`).
- `c(1)`:
  - `curried` called with `args = [1]`.
  - `1 < 3` → return `next` (closure #1 capturing `args=[1]` + reference to `curried`).
  - `step1` is now `next`.
- `step1(2)`:
  - `next` called with `more = [2]`.
  - It calls `curried.apply(this, [1, 2])` → re-enter `curried` with `args=[1,2]`.
  - `2 < 3` → return a fresh `next` (closure #2 capturing `args=[1,2]`).
  - `step2` is that fresh `next`.
- `step2(3)`:
  - `next` called with `more = [3]`.
  - Calls `curried.apply(this, [1, 2, 3])` → re-enter `curried` with `args=[1,2,3]`.
  - `3 >= 3` → call `add3(1, 2, 3)` → returns 6.
  - `result === 6`.

Heap snapshot at peak: three closure records exist (closure #0 still bound to `c`; closure #1 still bound to `step1`; closure #2 still bound to `step2`). Each retains its accumulated `args` array. When all three go out of scope, GC collects them.

## Important takeaways

**Syntax to memorize**
- Outer `curry(fn, arity)` returns the recursive `curried(...args)`.
- Inside `curried`: branch on `args.length >= arity`.
- Continuation closure does `[...args, ...more]` then recurses.
- Use `.apply(this, ...)` for `this`-correctness and clean spreading.

**Patterns to reuse**
- "Closure over accumulated args" is the spine of: curry, partial application, builder pattern (`.with(x).with(y).build()`), and FP pipelines.
- Currying enables **point-free composition**: `pipe(curry(add)(1), curry(mul)(2))` is the FP idiom for "add 1 then double."
- Used heavily by Ramda and `fp-ts`: every Ramda function is auto-curried.

**Common mistakes**
- Relying on `fn.length` — silently broken for default params, rest params, destructured params.
- Mutating a shared `args` array instead of building a new one each call — leaks args across sibling partials. The `[...args, ...more]` spread is critical.
- Forgetting to truncate to `arity` — extra args may break `fn` that uses `arguments.length`.
- Confusing curry with partial application — see Variants and the separate `partial-application.md`.

**Related questions**
- `partial(fn, ...presetArgs)` — closure over a single preset arg list, no recursion
- `pipe(...fns)` / `compose(...fns)` — function composition
- `flip(fn)` — swap argument order, closure trick
- Builder pattern (method chaining) — same idea, OOP flavour

## Variants

1. **Curry with placeholders** — `c(1, _, 3)(2)` fills the gap. Requires storing a sparse args array and tracking placeholder positions. Tests deeper closure work.

2. **Right-curry (`curryRight`)** — args fill from the right: `cR(3)(2)(1)` calls `fn(1, 2, 3)`. Mirror image; useful for `divide`-shaped functions where the second operand is the one you partially apply more often.

3. **Auto-curry on method definition (decorator)** — `@curried` on a class method. Tests decorator + closure interaction. (Decorator proposal status: stage 3.)

## Revision notes

> **curry-via-closures — 60 second recap**
> - Closure over an accumulated `args` array; recurse via a returned continuation function.
> - Branch: `args.length >= arity` → invoke `fn`; else return another closure.
> - Pass `arity` explicitly — `fn.length` lies for default/rest/destructured params.
> - `[...args, ...more]` (new array) — never mutate a shared accumulator.
> - Each partial creates a new closure record on the heap; chain forms a linked list.
> - Use `.apply(this, ...)` for method-style use.
> - Family: partial application (single preset), builder pattern, pipe/compose.
> - **Trap:** zero-arity / rest-param functions break `fn.length` defaults. Always allow explicit arity.
