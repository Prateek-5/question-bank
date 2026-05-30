# Implement `compose` and `pipe` — function composition

> **Difficulty:** Easy-Medium   |   **Time:** ~15 min   |   **Prereqs:** [`concepts/closures.md`](../../concepts/closures.md), [curry.md](./curry.md)
>
> **Source:** <a href="https://leetcode.com/problems/function-composition/" target="_blank" rel="noopener noreferrer">LeetCode 2629 — Function Composition</a>. Redux `compose`, Ramda `R.pipe`, RxJS `pipe`.

---

## 1. Problem statement

**Signature**
```ts
function compose<T>(...fns: Array<(x: T) => T>): (x: T) => T;   // right-to-left
function pipe<T>(...fns: Array<(x: T) => T>): (x: T) => T;       // left-to-right
```

**Input / Output examples**

| Input                                | Behaviour                                 |
|--------------------------------------|--------------------------------------------|
| `compose(f, g, h)(x)`                | `f(g(h(x)))` — rightmost runs first       |
| `pipe(f, g, h)(x)`                   | `h(g(f(x)))` — leftmost runs first        |
| `compose()(x)` / `pipe()(x)`         | identity → returns `x`                    |
| `compose(f)(x)`                      | `f(x)` — single fn applied                |
| `pipe(add1, dbl, neg)(3)`            | `neg(dbl(add1(3))) = neg(8) = -8`        |
| `compose(add1, dbl, neg)(3)`         | `add1(dbl(neg(3))) = add1(-6) = -5`      |

**Constraints**
- Each fn is unary (point-free composition).
- Empty list → identity (`x => x`).
- `compose` uses `reduceRight`; `pipe` uses `reduce`.
- Direction is the #1 trap — interviewers will ask both names.

---

## 2. Plain-English restatement

Take a list of functions and string them together so the output of one becomes the input of the next. `pipe(a, b, c)(x)` means "run `a` on `x`, then `b` on that, then `c` on that" — left-to-right reading order. `compose(a, b, c)(x)` is the math convention: `a(b(c(x)))` — rightmost runs first. Same engine, opposite direction.

---

## 3. Why this matters in interviews

`compose`/`pipe` is the FP litmus test. The sync version is a one-liner; the async variant unlocks middleware-style code that powers Redux, Koa, Express, RxJS, Apollo. Interviewers probe whether you understand the **direction** distinction and whether you can implement the async version via `reduce` over a chained Promise. As a backend engineer you'll meet composition daily in middleware factories and request-transform pipelines.

---

## 4. Mental model

A **conveyor belt of unary functions**:

```
   pipe(add1, dbl, neg)(3):
   ┌─────┐    ┌─────┐    ┌─────┐
   │ +1  │───▶│ ×2  │───▶│ neg │
   └─────┘    └─────┘    └─────┘
       3          4          8         -8
       ↑ input  ↑ acc      ↑ acc      ↑ result

   compose(add1, dbl, neg)(3):
   ┌─────┐    ┌─────┐    ┌─────┐
   │ +1  │◀───│ ×2  │◀───│ neg │
   └─────┘    └─────┘    └─────┘
       -5          -6        -3         3
       ↑ result ↑ acc       ↑ acc     ↑ input
```

**Mnemonic:** **compose** like math — `(f ∘ g)(x) = f(g(x))`, **right-to-left** → `reduceRight`. **pipe** like a unix pipeline — `cat | grep | wc`, **left-to-right** → `reduce`.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What does `compose()(42)` return? `pipe()(42)`?
> 2. With `add1, dbl, neg` and input `3`, which one gives `-5` and which gives `-8`?
> 3. Can you compose async functions? Where does the implementation break?

---

## 6. Brute force — walked through

### Wrong attempt 1: hand-rolled recursion
```js
const compose = (f, ...rest) => rest.length === 0 ? f : (x) => f(compose(...rest)(x));
```
Works but reinvents `reduceRight`. Use the built-in.

### Wrong attempt 2: `reduce` for `compose`
```js
const compose = (...fns) => (x) => fns.reduce((acc, fn) => fn(acc), x);   // BUG
```
This is `pipe`. Direction reversed — interviewer pounces.

### Wrong attempt 3: ignore empty case
```js
const compose = (...fns) => (x) => fns.reduceRight((acc, fn) => fn(acc));   // BUG: no seed
```
`compose()(x)` throws because `reduceRight` on empty array with no seed errors. Always pass `x` as seed.

---

## 7. The unlocking insight

> **`fns.reduceRight((acc, fn) => fn(acc), x)` for compose. `fns.reduce(...)` for pipe. Same engine, opposite direction. Empty array + initial value = identity for free.**

Three properties:

1. **Direction:** compose = right-to-left (`reduceRight`); pipe = left-to-right (`reduce`).
2. **Empty = identity:** `reduce(_, seed)` on `[]` returns `seed` unchanged.
3. **Async variant:** swap value-passing for promise-chaining: `reduce((p, fn) => p.then(fn), Promise.resolve(x))`.

---

## 8. Solution (annotated)

```js
const compose = (...fns) => (x) =>
  fns.reduceRight((acc, fn) => fn(acc), x);                    // step 1: right-to-left

const pipe = (...fns) => (x) =>
  fns.reduce((acc, fn) => fn(acc), x);                          // step 2: left-to-right

// Async variant — fns may return promises
const pipeAsync = (...fns) => (x) =>
  fns.reduce((p, fn) => p.then(fn), Promise.resolve(x));       // step 3: chain via .then

const composeAsync = (...fns) => (x) =>
  fns.reduceRight((p, fn) => p.then(fn), Promise.resolve(x));

// Multi-arg first call (if the rightmost/leftmost fn is variadic)
function composeMulti(...fns) {
  if (fns.length === 0) return (x) => x;
  return function (...args) {
    return fns.reduceRight((acc, fn, i) => {
      return i === fns.length - 1 ? fn.apply(this, args) : fn.call(this, acc);
    }, undefined);
  };
}
```

**Try it yourself**

```js
const add1 = (x) => x + 1;
const dbl  = (x) => x * 2;
const neg  = (x) => -x;

compose(add1, dbl, neg)(3);  // -5
pipe   (add1, dbl, neg)(3);  // -8

// Async — sequential request enrichment
const handler = pipeAsync(
  (body) => JSON.parse(body),
  async (obj) => ({ ...obj, ts: Date.now() }),
  (obj) => { if (!obj.id) throw new Error('no id'); return obj; },
  async (obj) => ({ ...obj, saved: true }),
);
const result = await handler('{"id":42}');
```

---

## 9. Step-by-step dry run

```
compose(add1, dbl, neg)(3):
  fns = [add1, dbl, neg]
  reduceRight starts at idx=2 with seed=3

  idx=2  fn=neg  acc=3   → neg(3)  = -3   ⇒ acc=-3
  idx=1  fn=dbl  acc=-3  → dbl(-3) = -6   ⇒ acc=-6
  idx=0  fn=add1 acc=-6  → add1(-6)= -5   ⇒ acc=-5
  return -5

pipe(add1, dbl, neg)(3):
  reduce starts at idx=0 with seed=3

  idx=0  fn=add1 acc=3   → add1(3) = 4    ⇒ acc=4
  idx=1  fn=dbl  acc=4   → dbl(4)  = 8    ⇒ acc=8
  idx=2  fn=neg  acc=8   → neg(8)  = -8   ⇒ acc=-8
  return -8
```

Async pipe with `parse → enrich → validate → persist`:

```
seed = Promise.resolve('{"id":42}')
.then(parse)    → resolves to {id:42}
.then(enrich)   → enrich is async → resolves to {id:42, ts:...}
.then(validate) → sync, id truthy → returns object
.then(persist)  → async → resolves to {id:42, ts:..., saved:true}

await handler(...)  ⇒ {id:42, ts:..., saved:true}
```

If `validate` throws, `.then(persist)` is skipped, rejection surfaces at `await`.

---

## 10. Common confusion + traps

1. **Reversed direction** — compose with `reduce` (gives pipe) or pipe with `reduceRight` (gives compose).
2. **Empty pipeline** — forgetting the seed (`reduce` without initial value throws on `[]`).
3. **Multi-arg expectation** — `compose(f, g)(a, b)` — only first call gets multi-args; intermediate fns are unary.
4. **`this` binding lost** — composed functions are usually pure; bind methods first if needed.
5. **Async fns in sync `pipe`** — second fn receives a Promise, not the resolved value. Use `pipeAsync`.
6. **`Promise.resolve()` without arg** — first fn gets `undefined`. Always pass `x`.
7. **`await` inside reducer body** — forces outer to be async; lazier to return `p.then(fn)`.

---

## 11. Senior follow-ups & variants

### Variant 1 — Middleware compose (Koa onion model)
Each fn takes `(ctx, next)` and chooses whether/when to call `next`. Allows pre- and post-processing:
```js
const compose = (mws) => (ctx) => {
  const dispatch = (i) => i === mws.length ? Promise.resolve() : Promise.resolve(mws[i](ctx, () => dispatch(i+1)));
  return dispatch(0);
};
```
Used in Koa, Apollo, custom request pipelines.

### Variant 2 — Either/Result pipe
Each step returns `{ok: true, value} | {ok: false, error}`; pipe short-circuits on error. Avoids exception-based control flow.

### Variant 3 — Cancellable pipe
Pass `AbortSignal`; each step checks `signal.aborted` and short-circuits.

### Variant 4 — Transducers (Ramda/Clojure)
Compose-able reducer transformers: `compose(map(double), filter(even))` builds a single-pass reducer.

### Variant 5 — Parallel fan-out
`fanOut(a, b, c)(x) = Promise.all([a(x), b(x), c(x)])`. Different semantics — clarify which.

---

## 12. How to think aloud

> "Reduce over an array of unary fns. `compose` = `reduceRight` (math convention, right-to-left). `pipe` = `reduce` (left-to-right reading order). Empty list = identity, falls out of `reduce` with a seed for free. Async variant swaps value-passing for `acc.then(fn)` with `Promise.resolve(x)` as the seed — handles mixed sync/async transparently because `.then` autoboxes. Direction is the #1 trap; I'll state which one I'm naming. Middleware compose (Koa) is the senior follow-up — fns take `(ctx, next)` instead of value-passing."

---

## 13. 60-second revision

> - **`compose(f,g,h)(x) === f(g(h(x)))`** → `fns.reduceRight((acc, fn) => fn(acc), x)`.
> - **`pipe(f,g,h)(x) === h(g(f(x)))`** → `fns.reduce(...)`.
> - **Empty list → identity** (seed `x` survives an empty reduce).
> - **Async:** `fns.reduce((p, fn) => p.then(fn), Promise.resolve(x))`.
> - **Each fn unary;** state direction explicitly.
> - **Middleware compose** = continuation-passing (Koa), not value-passing.
> - **Trap:** reversed direction; missing seed; `await` inside reducer body.

---

**Related:** [async-compose-pipe.md](./async-compose-pipe.md) · [curry.md](./curry.md) · [bind-polyfill.md](./bind-polyfill.md) · [`04-promises/async-reduce.md`](../04-promises/async-reduce.md)

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md), [`concepts/promises.md`](../../concepts/promises.md)
