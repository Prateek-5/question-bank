# Implement `curry(fn)` — accumulate args until arity is met

> **Difficulty:** Medium   |   **Time:** ~20 min   |   **Prereqs:** [`concepts/closures.md`](../../concepts/closures.md), [`02-closures/partial-application.md`](../02-closures/partial-application.md)
>
> **Source:** Lodash `_.curry`, Ramda `R.curry`, [codedamn Curry](https://codedamn.com/problem/vqf9CjnUNextjlV5yQ4NP). Common at FE/full-stack rounds.

---

## 1. Problem statement

**Signature**
```ts
function curry<F extends (...args: any[]) => any>(fn: F, arity?: number): (...args: any[]) => any;
```

**Input / Output examples**

| Setup                                  | Behaviour                                              |
|----------------------------------------|---------------------------------------------------------|
| `csum = curry((a,b,c) => a+b+c)`       | `fn.length === 3`                                       |
| `csum(1, 2, 3)`                        | `6` — full arity                                        |
| `csum(1)(2)(3)`                        | `6` — one at a time                                     |
| `csum(1, 2)(3)`                        | `6` — partial then complete                             |
| `csum(1)(2, 3)`                        | `6` — partial mixed                                     |
| `csum(1)(2)`                           | still a function (incomplete)                           |
| `const add5 = csum(5); add5(1, 2)`     | `8` — partial is reusable, no contamination             |
| Variadic fn `(...args) => sum(args)`   | `fn.length === 0` — naive curry fires immediately       |

**Constraints**
- Accumulate args across closure boundaries.
- Fire when `args.length >= fn.length`.
- Support partial applications that are independent (no shared mutable state).
- Allow explicit arity override (for variadic / default-param fns).

---

## 2. Plain-English restatement

`curry(fn)` returns a function that you can call piecemeal — with one arg at a time, or several at a time. It collects args until it has enough (matching the original `fn`'s declared arity), then invokes `fn`. Used in middleware factories (`logger(level)(scope)(msg)`), Ramda/lodash-fp pipelines, and partial-application patterns.

---

## 3. Why this matters in interviews

Curry is the canonical "do you understand higher-order functions, closures, and `Function.length`" question — packaged in a 10-line implementation. Senior bonus: **placeholder support** (`_`) or **infinite curry**. Tests three things: (1) reading `fn.length` to know target arity, (2) accumulating args across nested calls via closure, (3) deciding **when to invoke** (when accumulated args ≥ arity).

---

## 4. Mental model

A **piggy bank of args**: each call drops in more args; once it hits the threshold (`fn.length`), the bank breaks and runs `fn`.

```
   csum = curry((a,b,c) => a+b+c)    arity = fn.length = 3

   csum(1)        accumulated=[1]   length=1 < 3  → return wrapper
        │
        ▼
   csum(1)(2)     accumulated=[1,2] length=2 < 3  → return wrapper
                  ┃ each call builds a NEW args array — siblings independent
        │
        ▼
   csum(1)(2)(3)  accumulated=[1,2,3] length=3 ≥ 3 → fn.apply(this, [1,2,3]) = 6
```

**Independence of branches:**
```
   const add5 = csum(5)             accumulated=[5]
   add5(1, 2)   → curried([5,1,2])  → 8
   add5(10, 20) → curried([5,10,20]) → 35
   ↑ same `add5`, fresh args array each call — no contamination
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What is `((a, b = 0, c) => a+b+c).length`? Why does it matter for curry?
> 2. If `csum = curry(sum)`, will `const add5 = csum(5); add5(1); add5(2)` give `6` and `7`?
> 3. What happens if you call `csum(1, 2, 3, 4)` — does the extra arg break anything?

---

## 6. Brute force — walked through

### Wrong attempt 1: fixed arities
Write `curry1`, `curry2`, `curry3` separately. Embarrassing. Skip.

### Wrong attempt 2: mutate shared args
```js
function curry(fn) {
  const args = [];                        // BUG: shared across all branches
  return function curried(...next) {
    args.push(...next);
    if (args.length >= fn.length) return fn.apply(this, args);
    return curried;
  };
}
```
`add5 = csum(5)` writes `[5]` into the shared `args`. Calling `add5(1, 2)` appends → `[5, 1, 2]`. But calling `add5(10, 20)` again → `[5, 1, 2, 10, 20]`. Sibling partials contaminate each other. Always fresh array.

### Wrong attempt 3: blindly trust `fn.length`
For `(...args) => sum(args)`, `fn.length === 0`. Curry fires on the first call with no accumulated args — useless. Accept an explicit `arity` parameter.

---

## 7. The unlocking insight

> **A self-recursive curried function that accumulates args via closure. On each call, if `args.length >= fn.length`, invoke `fn`; else return a new function closing over a FRESH `[...args, ...next]` array.**

Three properties:

1. **`fn.length`** = declared arity (defaults/rest break it → allow override).
2. **Fresh array per branch** — `[...args, ...next]` (not `args.push`) so partials are independent.
3. **`apply(this, ...)`** for method-style use.

---

## 8. Solution (annotated)

```js
function curry(fn, arity = fn.length) {                        // step 1: arity override hook
  return function curried(...args) {
    if (args.length >= arity) {                                // step 2: fire when full
      return fn.apply(this, args);
    }
    return function (...next) {                                 // step 3: return wrapper
      return curried.apply(this, [...args, ...next]);          // step 4: fresh args array
    };
  };
}

// Placeholder-aware curry (Lodash style)
const _ = Symbol.for('curry.placeholder');

function curryWithPlaceholder(fn, arity = fn.length) {
  return function curried(...args) {
    const concrete = args.filter((a) => a !== _);
    const hasPlaceholder = args.some((a) => a === _);

    if (!hasPlaceholder && concrete.length >= arity) {
      return fn.apply(this, args);
    }

    return function (...next) {
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

**Try it yourself**

```js
const sum = (a, b, c) => a + b + c;     // fn.length === 3
const csum = curry(sum);

csum(1)(2)(3);          // 6
csum(1, 2)(3);          // 6
csum(1)(2, 3);          // 6
csum(1, 2, 3);          // 6

const add5 = csum(5);
add5(1, 2);             // 8
add5(10, 20);           // 35  (no contamination — fresh args branch)

// Variadic — need explicit arity
const v = (...args) => args.reduce((a, b) => a + b, 0);
const cv = curry(v, 3);                  // fn.length is 0; pass arity
cv(1)(2)(3);            // 6

// Placeholder
csum(_, 2, _)(1)(3);    // 6  (fills _ slots in order)
```

---

## 9. Step-by-step dry run

```
csum(1)(2)(3):
  call csum(1):     args=[1], 1 < 3 → return wrapper W1 closed over [1]
  call W1(2):       invokes curried.apply(this, [...[1], 2]) = curried(1, 2)
                    args=[1,2], 2 < 3 → return wrapper W2 closed over [1,2]
  call W2(3):       invokes curried(1, 2, 3)
                    args=[1,2,3], 3 ≥ 3 → return sum.apply(this, [1,2,3]) = 6

csum(1, 2)(3):
  call csum(1,2):   args=[1,2], 2 < 3 → return wrapper W closed over [1,2]
  call W(3):        invokes curried(1, 2, 3) → sum(1,2,3) = 6

Branch independence:
  add5 = csum(5):   args=[5], length=1 < 3 → return wrapper W
                    wrapper closes over [5]; csum's outer scope is shared but [5] is its own array
  add5(1, 2):       curried(5, 1, 2) → builds NEW args=[5,1,2], 3 ≥ 3 → fn(5,1,2) = 8
  add5(10, 20):     curried(5, 10, 20) → builds NEW args=[5,10,20], 3 ≥ 3 → fn(5,10,20) = 35
                    each call to W creates a fresh [...args, ...next] — no shared mutable list
```

Placeholder dry run (`_` = placeholder):

```
csum(_, 2, _)(1)(3):
  call csum(_, 2, _):  args=[_, 2, _]. concrete=[2]. hasPlaceholder=true → return wrapper
  call wrapper(1):     walk args, fill first _ with 1 → [1, 2, _]. hasPlaceholder=true → wrapper
  call wrapper(3):     walk args, fill first _ with 3 → [1, 2, 3]. no _ → fn(1,2,3) = 6
```

---

## 10. Common confusion + traps

1. **`fn.length` doesn't count defaults** — `((a, b=0, c) => ...).length === 1`. Curry fires too early.
2. **`fn.length === 0` for rest args** — `(...args) => ...`. Curry fires immediately on the first call.
3. **Shared mutable args** — `args.push(...next)` contaminates sibling partials.
4. **`.apply(null, ...)`** — loses `this`. Use `.apply(this, ...)`.
5. **Returning the wrapper directly** instead of `curried.apply(...)` — breaks deeper currying.
6. **Treating extra args as errors** — convention: extras pass through to `fn` and are ignored if unused.
7. **Zero-arity functions** — `curry(() => 42)` — first call returns `42` immediately.

---

## 11. Senior follow-ups & variants

### Variant 1 — Explicit arity
```js
curry(fn, 3)
```
Required for variadic / default-param functions. Always offer this hook.

### Variant 2 — Placeholder support
`curry(fn)(_, 2)(1, 3)` skips slots. Real libraries (Lodash, Ramda) ship this. Snippet above.

### Variant 3 — Infinite curry
`f(1)(2)(3)()` — empty-call terminates and invokes. Useful for variadic accumulators: `sum(1)(2)(3)() === 6`.
```js
function curryInfinite(fn) {
  const helper = (acc) => (...args) =>
    args.length === 0 ? fn(...acc) : helper([...acc, ...args]);
  return helper([]);
}
```

### Variant 4 — Async curry
Args can be promises; curry awaits them before applying. Niche.

### Variant 5 — `partial(fn, ...presets)`
Weaker than curry; fixes leading args once. `partial(fn, a)(b, c) === fn(a, b, c)`.

---

## 12. How to think aloud

> "Self-recursive curried function. Outer `curry` returns `curried`. Each call to `curried(...args)`: if `args.length >= arity`, invoke `fn.apply(this, args)`; else return `(...next) => curried.apply(this, [...args, ...next])`. Three things to get right: arity (default to `fn.length`, allow override for variadic / default-param fns); fresh args array per branch (`[...args, ...next]`, not `push` — otherwise sibling partials contaminate); `apply(this, ...)` for method-style use. Senior follow-up: placeholder `_` — walk both args lists and fill placeholders left-to-right. Infinite curry: terminate on zero-arg call."

---

## 13. 60-second revision

> - **`curried(...args)` → `args.length >= fn.length` ? `fn.apply(this, args)` : `(...next) => curried(...args, ...next)`**.
> - **`fn.length`** = declared arity (broken by defaults / rest — allow explicit override).
> - **Fresh `[...args, ...next]` array** per branch — never `args.push`.
> - **`.apply(this, ...)`** for method use.
> - **Placeholder `_`** — walk and fill left-to-right.
> - **Infinite curry** — zero-arg call terminates.
> - **Trap:** `fn.length === 0` for variadic; mutating args; losing `this`.

---

**Related:** [`02-closures/partial-application.md`](../02-closures/partial-application.md) · [`02-closures/curry-via-closures.md`](../02-closures/curry-via-closures.md) · [function-composition.md](./function-composition.md) · [bind-polyfill.md](./bind-polyfill.md)

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md)
