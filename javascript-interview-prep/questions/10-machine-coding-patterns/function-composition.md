# Implement `compose` and `pipe`

## Source
- Canonical machine-coding interview problem (LeetCode #2629 "Function Composition", BFE.dev, redux/ramda source).
- LeetCode reference: https://leetcode.com/problems/function-composition/

## Why this question matters in interviews
Function composition is the canonical "do you actually understand higher-order functions" question. It's short, it has a single elegant answer (`reduceRight`), and it's the entry point to a whole family of follow-ups: pipe, async pipe, middleware chains, transducers. Backend engineers see composition daily: Express middleware (`app.use`), Redux middleware, Koa's `compose`, RxJS operators, GraphQL resolver pipelines, AWS Lambda layers. The interview answer needs to nail two things: (1) the **direction** — `compose(f,g,h)(x) = f(g(h(x)))`, applied right-to-left, vs `pipe` which is left-to-right; (2) the **reduce mechanic** — `reduceRight` for compose, `reduce` for pipe. A senior bonus is the async variant using `reduce` over a chained promise.

## Concepts involved

### Syntax to lock in
```js
const compose = (...fns) => (x) => fns.reduceRight((acc, fn) => fn(acc), x);
const pipe    = (...fns) => (x) => fns.reduce     ((acc, fn) => fn(acc), x);

const add1 = (x) => x + 1;
const dbl  = (x) => x * 2;
const neg  = (x) => -x;

compose(add1, dbl, neg)(3); // add1(dbl(neg(3))) = add1(dbl(-3)) = add1(-6) = -5
pipe   (add1, dbl, neg)(3); // neg(dbl(add1(3))) = neg(dbl(4))  = neg(8)  = -8
```

### Runtime / engine behavior
- `compose(f, g, h)` returns a function `x => f(g(h(x)))`. Right-to-left because math notation `(f∘g)(x) = f(g(x))`.
- `pipe(f, g, h)` returns `x => h(g(f(x)))`. Left-to-right, reading-order — friendlier for most JS code.
- `reduce(fn, init)` walks left→right, accumulator starts as `init`. `reduceRight` walks right→left.
- Both compose and pipe with **zero functions** should return the identity function (`x => x`). Test it.
- Both with **one function** should be equivalent to that function — but the wrapper still invokes `reduce`, which handles it correctly.

### Edge cases (these are the interview traps)
1. **Direction confusion** — every candidate gets this wrong once. Memorize: **compose = compose like math = right-to-left**. Pipe = pipeline = left-to-right.
2. **Variadic first function** — by convention, only the **first** function in the chain (rightmost for compose, leftmost for pipe) accepts multiple args. Subsequent functions take one arg (the previous result). Implement accordingly.
3. **Empty input** — `compose()(x)` must return `x` (identity). `reduceRight` with no functions and an initial value gives back the initial value — works for free.
4. **`this` binding** — typically not preserved in compose. The composed functions are usually pure or pre-bound. Don't over-engineer.
5. **Async functions** — if any `fn` returns a promise, the standard sync compose breaks. Use `composeAsync` that chains `.then`. Show this — it's a senior must.
6. **Throwing functions** — exceptions propagate normally through the reduce chain. No special handling needed unless asked.
7. **Memory / call stack** — `reduceRight` builds the chain via iteration, not recursion, so no stack-depth issues. Calling `f(g(h(x)))` does create N stack frames, but that's normal call-stack usage.
8. **Argument arity for the first call** — `compose(f, g, h)(a, b, c)` — should `a, b, c` all go to `h`? Convention: yes. Implement with `(...x) => fns.reduceRight((acc, fn) => fn(acc), fns[fns.length-1](...x))` if you want to preserve. Or, simpler: peel the rightmost function as the seed.

## Brute force approach
Hand-roll a recursive helper: `compose(f, g, h)(x) = f(compose(g, h)(x))`. Works, but you've reinvented `reduceRight`. Skip it.

## Optimal approach
`fns.reduceRight((acc, fn) => fn(acc), x)`. Two lines including the wrapper. The cleanest line of code in this entire bucket.

For multi-arg input to the innermost function:
```js
const compose = (...fns) => (...args) =>
  fns.reduceRight((acc, fn, i) =>
    i === fns.length - 1 ? fn(...args) : fn(acc),
    undefined
  );
```
Or peel the rightmost function:
```js
const compose = (...fns) => {
  if (fns.length === 0) return (x) => x;
  const [last, ...rest] = [...fns].reverse();
  return (...args) => rest.reduceRight((acc, fn) => fn(acc), last(...args)).
  // wait — reverse + reduceRight is confusing. Easier:
};
```
Stick with the simple version unless interviewer asks.

## Solution (JavaScript)

```js
/**
 * compose(f, g, h)(x) === f(g(h(x)))
 * Right-to-left composition. Returns identity for zero functions.
 */
function compose(...fns) {
  if (fns.length === 0) return (x) => x;
  return function (...args) {
    return fns.reduceRight((acc, fn, idx) => {
      // The rightmost function receives the original args; all others get acc.
      if (idx === fns.length - 1) return fn.apply(this, args);
      return fn.call(this, acc);
    }, undefined);
  };
}

/**
 * pipe(f, g, h)(x) === h(g(f(x)))
 * Left-to-right composition.
 */
function pipe(...fns) {
  if (fns.length === 0) return (x) => x;
  return function (...args) {
    return fns.reduce((acc, fn, idx) => {
      if (idx === 0) return fn.apply(this, args);
      return fn.call(this, acc);
    }, undefined);
  };
}

/**
 * Async pipe — each fn may return a promise; chains via await.
 * pipeAsync(f, g, h)(x) === await h(await g(await f(x)))
 */
function pipeAsync(...fns) {
  return function (...args) {
    return fns.reduce(
      (p, fn, idx) => p.then((acc) => (idx === 0 ? fn.apply(this, args) : fn.call(this, acc))),
      Promise.resolve()
    );
  };
}
```

If the LeetCode problem only needs single-arg, the canonical one-liner is enough:

```js
const compose = (...fns) => (x) => fns.reduceRight((acc, fn) => fn(acc), x);
const pipe    = (...fns) => (x) => fns.reduce     ((acc, fn) => fn(acc), x);
```

## Step-by-step dry run

Input:
```js
const add1 = (x) => x + 1;
const dbl  = (x) => x * 2;
const neg  = (x) => -x;

const c = compose(add1, dbl, neg);
const p = pipe   (add1, dbl, neg);
c(3); p(3);
```

Trace `c(3)`:
- `fns = [add1, dbl, neg]`. `reduceRight` iterates from index 2 → 0.
- idx=2, `fn = neg`, `acc` initially `undefined`. We're at the rightmost → `fn(...args) = neg(3) = -3`. acc = -3.
- idx=1, `fn = dbl`. `fn(acc) = dbl(-3) = -6`. acc = -6.
- idx=0, `fn = add1`. `fn(acc) = add1(-6) = -5`. acc = -5.
- Return `-5`.

Trace `p(3)`:
- `fns = [add1, dbl, neg]`. `reduce` iterates 0 → 2.
- idx=0, `fn = add1`. Leftmost → `fn(...args) = add1(3) = 4`. acc = 4.
- idx=1, `fn = dbl`. `dbl(4) = 8`. acc = 8.
- idx=2, `fn = neg`. `neg(8) = -8`. acc = -8.
- Return `-8`.

Async trace — `pipeAsync(loadUser, fetchPosts, summarize)(userId)`:
- Initial `p = Promise.resolve()`.
- idx=0: `p.then(() => loadUser(userId))` → promise of user.
- idx=1: `.then(user => fetchPosts(user))` → promise of posts.
- idx=2: `.then(posts => summarize(posts))` → promise of summary.
- Each `.then` chains the next call to the prior resolution. Errors propagate via `.catch` like normal promise chains.

## Important takeaways

**Syntax to memorize**
- `compose = (...fns) => (x) => fns.reduceRight((acc, fn) => fn(acc), x)`.
- `pipe    = (...fns) => (x) => fns.reduce     ((acc, fn) => fn(acc), x)`.
- Both: zero functions → identity; one function → that function applied.

**Direction mnemonic**
- **Compose** like math: `(f ∘ g)(x) = f(g(x))` — **right side runs first**. So `reduceRight`.
- **Pipe** like a unix pipeline: `cat | grep | wc` — left runs first, output flows right. So `reduce`.

**Patterns to reuse**
- `reduce` over an array of functions is the same engine that powers: Redux middleware, Koa middleware (with continuation passing instead of value passing), Express handler chains (with `next()`), RxJS `pipe`, Ramda `R.pipe`.
- The async variant — `fns.reduce((p, fn) => p.then(fn), Promise.resolve())` — is the standard "chain N async tasks sequentially" pattern. Worth memorizing on its own.

**Common mistakes**
- Reversing the direction (writing pipe when interviewer asked for compose, and vice versa).
- Using `reduce` for compose and getting the order backwards.
- Returning the wrong identity for empty input.
- Forgetting that `reduce`/`reduceRight` need a sensible initial value when the array is empty.

**Related questions**
- Redux's `applyMiddleware` — uses compose internally.
- Express middleware chain — onion model, uses `next()` instead of return values.
- Transducers — compose, but for transformations of a reducer.

## Variants

1. **`pipeAsync` / `composeAsync`** — handle promises in the chain. Use `reduce` over `Promise.resolve()` and chain `.then`. Errors short-circuit via promise rejection.

2. **Middleware-style compose (onion / Koa)** — each function takes `(arg, next)` and decides whether to call `next`. Allows pre- and post-processing around the inner functions. This is the more interesting senior follow-up: `compose([m1, m2, m3])(arg)` → `m1(arg, () => m2(arg, () => m3(arg, () => {})))`.

3. **Curried compose** — `compose` that itself is curried so `compose(f)(g)(h)(x)` works. Rarely useful in practice; mention briefly.

4. **Transducers (Ramda / Clojure style)** — compose-able reducer transformers. `compose(map(double), filter(even))` produces a single-pass reducer over an iterable. Senior bonus topic.

## Revision notes

> **compose / pipe — 60 second recap**
> - `compose(f,g,h)(x) === f(g(h(x)))` → **reduceRight**.
> - `pipe(f,g,h)(x) === h(g(f(x)))` → **reduce**.
> - Empty → identity. One fn → that fn.
> - Async: `reduce((p, fn) => p.then(fn), Promise.resolve())`.
> - **Trap:** reversing direction. Compose = mathematical right-to-left.
> - Middleware (Koa/Express) is composition with continuation-passing, not value-passing.
