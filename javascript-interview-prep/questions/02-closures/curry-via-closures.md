# Curry an arity-N function — collect args call-by-call until arity is met

> **Difficulty:** Medium   |   **Time:** ~25 min   |   **Prereqs:** [partial-application.md](./partial-application.md), [`concepts/closures.md`](../../concepts/closures.md)
>
> **Source:** [LeetCode 2632 — Curry](https://leetcode.com/problems/curry/); lodash `_.curry`; classic FP interview problem.

---

## 1. Problem statement

**Signature**
```ts
function curry<F extends (...args: any[]) => any>(fn: F, arity?: number):
  (...args: any[]) => any;   // either ReturnType<F> when arity met, or another wrapper
```

**Input / Output examples**

| Setup                          | Sequence of calls       | Output |
|--------------------------------|-------------------------|--------|
| `const add3 = (a,b,c) => a+b+c; const c = curry(add3, 3)` | `c(1)(2)(3)`        | `6` |
| same                           | `c(1, 2)(3)`             | `6` |
| same                           | `c(1)(2, 3)`             | `6` |
| same                           | `c(1, 2, 3)`             | `6` |
| `const c0 = curry(() => 'hi', 0)` | `c0()`                | `'hi'` |
| Default-param trap: `(a, b=1)=>...` has `fn.length===1` | `curry(fn)` fires after 1 arg | pass `arity` explicitly |

**Constraints**
- Caller can supply args in **any partition** that totals `arity` arguments.
- Returns either the final result (when arity is met) or another wrapper (when not).
- Pass `arity` explicitly — don't rely on `fn.length` (lies for default params, rest params, destructuring).
- Forward `this`.

---

## 2. Plain-English restatement

Wrap a function `fn` of arity `N` so callers can supply its arguments **one at a time, several at a time, or all at once**. As long as the supplied args don't total `N` yet, each call returns *another* function waiting for more. Once the total reaches `N`, the wrapper invokes `fn` and returns the result.

In FP terms, currying turns an N-arity function into a chain of N unary functions (plus the convenience of accepting more than one at a time).

---

## 3. Why this matters in interviews

Curry tests whether you can write a closure that **accumulates state across calls** and returns either another function (still collecting) or the final result (when satisfied). It's the single best problem for showing you understand **closures over arrays**. Senior backend interviewers reach for it to gauge FP literacy — middleware composition (Express, Koa), Redux selectors, and HOFs in TS libraries all build on the same pattern. The "no `fn.length` tricks" constraint forces an explicit `arity` argument, which is the honest, general formulation.

---

## 4. Mental model

A **multi-stage clamping fixture**. You hand parts (arguments) one or several at a time. The fixture tracks how many parts it's holding. When the count reaches the threshold (`arity`), it pulls the lever and you get the finished assembly (`fn(...args)`); otherwise it hands you back the same fixture, asking for more.

```
   curry(add3, 3)
     │
     └── returns curried(...args)
             │
             ├── args.length >= 3?  yes → fn(...args.slice(0, 3))
             │
             └── no → return next(...more) → curried(...[...args, ...more])

   c(1)        →  next₁(args=[1])
   c(1)(2)     →  next₂(args=[1,2])
   c(1)(2)(3)  →  args.length=3 → fn(1,2,3) → 6
```

Each partial creates a fresh closure on the heap that captures the accumulated args so far. The chain forms a linked list of closures — three closures for a 3-arity curry called one-arg-at-a-time.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why doesn't relying on `fn.length` work for `function f(a, b=1) { ... }`?
> 2. If you call `c(1, 2, 3, 4)` on a 3-arity curry, what happens to the 4th argument — passed through, truncated, or error?
> 3. Why use `[...args, ...more]` instead of `args.concat(more)` or `args.push(...more)`?

---

## 6. Brute force — walked through

### Wrong attempt 1: rely on `fn.length`

```js
function curry(fn) {
  return function curried(...args) {
    if (args.length >= fn.length) return fn.apply(this, args);
    return (...more) => curried.apply(this, [...args, ...more]);
  };
}
```

Looks elegant. Breaks subtly:

- `function f(a, b = 1) {}` → `fn.length === 1`. Curry fires after one arg even though `f` would naturally take two.
- `function f(...args) {}` → `fn.length === 0`. Curry fires immediately.
- `function f({a, b}) {}` → `fn.length === 1`. Same default-param trap.

Always allow an explicit `arity` override.

### Wrong attempt 2: mutate a shared `args` array

```js
function curry(fn, arity) {
  const args = [];
  return function curried(...more) {
    args.push(...more);              // BUG: shared closure poisons all chains
    if (args.length >= arity) return fn.apply(this, args.slice(0, arity));
    return curried;
  };
}
const c = curry(add3, 3);
c(1); c(2); c(3);  // works
c(1); c(2); c(3);  // BUG: args has 6 entries; fires after first call
```

The single shared `args` array leaks state between unrelated partial chains. Each partial step must produce a **new** closure with a **new** accumulator.

### Wrong attempt 3: forget `this`

```js
return (...more) => curried(...args, ...more);
```

Arrow function `this` is the outer `this` (often `globalThis`). For method-style use (`obj.action = curry(genericAction)`), this breaks. Use `.apply(this, ...)` to forward.

---

## 7. The unlocking insight

> **Each partial call creates a new closure capturing the accumulated args so far. The chain forms a linked list of closures on the heap — one per partial step — until arity is met.**

The shape:

```js
function curry(fn, arity = fn.length) {
  return function curried(...args) {
    if (args.length >= arity) return fn.apply(this, args.slice(0, arity));
    return function (...more) {
      return curried.apply(this, [...args, ...more]);
    };
  };
}
```

Two key invariants make this correct:

1. **Per-call accumulator is fresh.** `[...args, ...more]` produces a *new* array on each step. The closure for partial #1 holds `[a]`; partial #2 holds `[a, b]`; partial #3 holds `[a, b, c]` — none share storage.
2. **Recursion is conceptual, not call-stack.** The inner `return function (...)` doesn't recurse on the JS call stack — it returns a new function whose call site is the *caller's* business. No stack growth.

The fact that we slice to `arity` (`args.slice(0, arity)`) matters when a caller over-supplies in a single call: `c(1, 2, 3, 4)` on a 3-arity curry truncates to `[1, 2, 3]`. Lodash matches this. Some shops want pass-through — clarify with the interviewer.

---

## 8. Solution (annotated)

```js
function curry(fn, arity = fn.length) {        // step 1: explicit arity (fn.length lies for default/rest)
  return function curried(...args) {           // step 2: each call accumulates args
    if (args.length >= arity) {                // step 3: enough? invoke fn
      return fn.apply(this, args.slice(0, arity));  //         truncate excess (lodash behaviour)
    }
    return function (...more) {                // step 4: not enough — return a continuation
      return curried.apply(this, [...args, ...more]);  // step 5: combine into FRESH array, re-enter
    };
  };
}
```

**Try it yourself**

```js
const sum3 = (a, b, c) => a + b + c;
const cSum = curry(sum3, 3);

cSum(1)(2)(3);    // 6
cSum(1, 2)(3);    // 6
cSum(1)(2, 3);    // 6
cSum(1, 2, 3);    // 6

// Method-style (this forwarded)
const obj = {
  prefix: '>>',
  log(a, b, c) { return `${this.prefix} ${a} ${b} ${c}`; },
};
obj.curriedLog = curry(obj.log, 3);
console.log(obj.curriedLog(1)(2)(3));   // ">> 1 2 3"
```

---

## 9. Step-by-step dry run

Input:

```js
const add3 = (a, b, c) => a + b + c;
const c = curry(add3, 3);
const step1 = c(1);
const step2 = step1(2);
const result = step2(3);
```

Values-first trace:

| Step | Call          | Accumulated `args` | Closure created | `fn` called? | Returns |
|------|---------------|--------------------|-----------------|---------------|---------|
| init | `curry(add3, 3)` | —                | closure #0 (just `curried`) | no | the `curried` function |
| 1    | `c(1)`        | `[1]` (in next closure) | closure #1 (captures `[1]`) | no  | the next function       |
| 2    | `step1(2)`    | `[1, 2]`           | closure #2 (captures `[1, 2]`) | no | another next            |
| 3    | `step2(3)`    | `[1, 2, 3]` → enough | —              | yes (`add3(1,2,3)`) | `6`               |

At the peak, three closures coexist on the heap (`c`, `step1`, `step2`). When `step2(3)` returns and you drop references to `step1`, `step2`, the closures become unreachable and are GC'd.

<details>
<summary><b>Engine internals (click to expand)</b></summary>

Each `[...args, ...more]` allocates a new array — never mutates the outer one. So closure #2's `args` is `[1, 2]` while closure #1's `args` remains `[1]`. They're independent.

`curried.apply(this, [...args, ...more])` re-enters `curried` recursively at the JS-syntax level, but each re-entry pops back to the wrapper closure that called it. No unbounded call-stack growth — each "step" is a single function call.

</details>

---

## 10. Common confusion + traps

1. **`fn.length` lies for default/rest/destructured params.**
   `function f(a, b = 1) {}` has `length: 1`. `function f(...args) {}` has `length: 0`. `function f({a, b}) {}` has `length: 1`. Always allow `arity` override.

2. **Mutating a shared accumulator across partial chains.**
   The closure-captured `args` array must be treated as immutable; `[...args, ...more]` is the discipline. Mutation poisons sibling partials.

3. **Forgetting `this` forwarding.**
   Arrow function in the continuation captures the outer `this`. Use a regular `function (...more)` and `curried.apply(this, ...)`.

4. **Truncate vs pass-through over-supply.**
   `c(1, 2, 3, 4)` on 3-arity → truncate or pass through? Lodash truncates. Some interviewers want pass-through. Clarify.

5. **Confusing curry with partial.**
   Curry keeps returning wrappers until arity is met. Partial fires `fn` on the next call regardless. They're related but not interchangeable.

6. **Memory.**
   Each partial pins its accumulated args. Long curry chains over big args = retained memory. Usually not an issue.

7. **Variadic curry doesn't exist (cleanly).**
   For `(...args) => ...`, there's no natural "done" signal. lodash's `_.curry` requires explicit arity. Don't try to over-engineer this.

---

## 11. Senior follow-ups & variants

### Variant 1 — Placeholder-aware curry

```js
const _ = Symbol('curry.placeholder');

function curry(fn, arity = fn.length) {
  return function curried(...args) {
    const filled = args.filter((a) => a !== _);
    if (filled.length >= arity && !args.slice(0, arity).includes(_)) {
      return fn.apply(this, args.slice(0, arity));
    }
    return function (...more) {
      // fill placeholders left-to-right, then append
      const merged = [];
      let j = 0;
      for (const a of args) merged.push(a === _ && j < more.length ? more[j++] : a);
      while (j < more.length) merged.push(more[j++]);
      return curried.apply(this, merged);
    };
  };
}

const cSub = curry((a, b, c) => a - b - c, 3);
cSub(_, 2)(10)(1);    // 10 - 2 - 1 = 7
```

### Variant 2 — Right-curry

Args fill from the right: `cR(3)(2)(1)` calls `fn(1, 2, 3)`. Reverse the merge order.

```js
function curryRight(fn, arity = fn.length) {
  return function curried(...args) {
    if (args.length >= arity) return fn.apply(this, args.slice(0, arity).reverse());
    return function (...more) {
      return curried.apply(this, [...args, ...more]);
    };
  };
}
```

### Variant 3 — Auto-curried compose / pipe

Currying is the substrate for FP pipelines. Every Ramda function is auto-curried, which is why you can write `R.map(R.multiply(2))(arr)` instead of `arr.map(x => x*2)`.

```js
const map = curry((f, arr) => arr.map(f), 2);
const filter = curry((p, arr) => arr.filter(p), 2);
const double = (x) => x * 2;
const isEven = (x) => x % 2 === 0;

const transform = (arr) => map(double, filter(isEven, arr));
// or, point-free:
const transformPF = (arr) => map(double)(filter(isEven)(arr));
```

### Variant 4 — TypeScript curried type

The hard part of curry isn't the JS — it's the TS types. A 3-arity TS curry has return-type `(a: A) => (b: B) => (c: C) => R`. The general form requires recursive conditional types.

```ts
type Curry<F> = F extends (a: infer A, ...rest: infer R) => infer Ret
  ? R extends [] ? () => Ret : (a: A) => Curry<(...args: R) => Ret>
  : never;
```

---

## 12. How to think aloud in the interview

> "Curry: closure over an accumulated `args` array. On each call, if `args.length >= arity`, invoke `fn`; else return a continuation that re-enters with `[...args, ...more]`. Pass `arity` explicitly — `fn.length` lies for default/rest/destructured params. Use `.apply(this, ...)` to forward `this`. Slice to `arity` on invocation to truncate over-supply (lodash behaviour). Memory: each partial pins its accumulated args; usually fine. Curry vs partial: curry keeps returning wrappers until arity met; partial fires on next call regardless. Curry is the substrate for Ramda's point-free FP pipelines."

---

## 13. 60-second revision

> - **Pattern:** closure over accumulated `args`; recurse via a continuation function until `args.length >= arity`.
> - **Pass `arity` explicitly** — `fn.length` lies for default/rest/destructured params.
> - **Fresh array on every step:** `[...args, ...more]`, never mutate.
> - **`.apply(this, ...)` everywhere** — forward `this`.
> - **Truncate** to `arity` on final invocation (lodash behaviour).
> - **Curry ≠ partial:** curry keeps returning wrappers; partial fires once.
> - **Family:** partial, builder pattern (`.with().with().build()`), compose/pipe, Ramda.
> - **Trap:** relying on `fn.length`; mutating accumulator; arrow `this`.

---

**Related:** [partial-application.md](./partial-application.md) · [`10-machine-coding-patterns/curry.md`](../10-machine-coding-patterns/curry.md) · [`10-machine-coding-patterns/function-composition.md`](../10-machine-coding-patterns/function-composition.md) · [`10-machine-coding-patterns/async-compose-pipe.md`](../10-machine-coding-patterns/async-compose-pipe.md)

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md)
