# Mutual Recursion (Even/Odd) and Trampolining

## Source / Origin
- Classic functional programming example.
- Asked at: Stripe, Razorpay, Atlassian.
- Concept reference: `concepts/recursion.md`, sibling `trampoline-pattern.md`.

## Why this question matters in interviews
"Implement isEven/isOdd using only mutual recursion." Tests function hoisting (declarations vs expressions), stack growth, and trampoline conversion. Senior bar: you know V8 doesn't TCO, naive mutual recursion blows the stack at ~10k, and the trampoline fix works for mutual cycles.

## Concepts involved

```js
// Naive — blows stack at large n
function isEven(n) {
  if (n === 0) return true;
  return isOdd(n - 1);
}
function isOdd(n) {
  if (n === 0) return false;
  return isEven(n - 1);
}

isEven(100000);   // RangeError: Maximum call stack size exceeded

// Trampolined
function trampoline(fn) {
  return (...args) => {
    let r = fn(...args);
    while (typeof r === 'function') r = r();
    return r;
  };
}
function isEvenStep(n) { return n === 0 ? true : () => isOddStep(n - 1); }
function isOddStep(n)  { return n === 0 ? false : () => isEvenStep(n - 1); }
const isEvenSafe = trampoline(isEvenStep);
isEvenSafe(100000);   // true (no stack overflow)
```

### Edge cases / traps
1. **Function declarations are hoisted; expressions aren't.** Mutual recursion with `const` won't work because each refers to the other before assignment.
2. **`const isOdd = ...` order matters** — define both as declarations (function ...) or wrap both as references via an object.
3. **V8 doesn't TCO** so mutual recursion overflows like single recursion.
4. **Negative numbers** — guard with `Math.abs(n)` or check sign.
5. **Non-integer** — guard input.
6. **Performance** — thunk-and-loop adds overhead. Use `n % 2` for the actual algorithm; trampoline only when illustrating mutual recursion.

## Mental Model

```
   isEven(4) ─→ isOdd(3) ─→ isEven(2) ─→ isOdd(1) ─→ isEven(0) ─→ true
   call stack depth = 5 frames (linear in n)
   blows at ~10k

   trampoline:
     each step returns a thunk → loop unwraps
     call stack depth = 1
     no overflow
```

## Solution

```js
// Working trampoline-based mutual recursion
function isEvenStep(n) {
  n = Math.abs(n);
  return n === 0 ? true : () => isOddStep(n - 1);
}
function isOddStep(n) {
  n = Math.abs(n);
  return n === 0 ? false : () => isEvenStep(n - 1);
}
function trampoline(fn) {
  return (...args) => {
    let r = fn(...args);
    while (typeof r === 'function') r = r();
    return r;
  };
}
const isEven = trampoline(isEvenStep);
const isOdd  = trampoline(isOddStep);

isEven(100_000);   // true
isOdd(100_001);    // true

// Object-based mutual recursion (alternative)
const ops = {
  even(n) { return n === 0 ? true : ops.odd(n - 1); },
  odd(n)  { return n === 0 ? false : ops.even(n - 1); },
};
// Same stack issue without trampoline; works for small n.

// Iterative form (obviously the real production answer)
function isEvenIter(n) {
  return Math.abs(n) % 2 === 0;
}
```

## Dry run

`isEven(3)` trampolined:

```
trampoline(isEvenStep)(3):
  r = isEvenStep(3) → return () => isOddStep(2)
  typeof r === 'function' → r = r() → isOddStep(2)
    → () => isEvenStep(1)
  r = r() → isEvenStep(1)
    → () => isOddStep(0)
  r = r() → isOddStep(0)
    → false
  typeof r !== 'function' → exit
  return false
```

Call stack stays 1 frame deep regardless of `n`.

## How to think aloud

> "Mutual recursion: A calls B, B calls A. Naive call stack grows linearly with n; blows around 10k in V8. Trampoline: each function returns a thunk to the next; outer loop unwraps. Stack stays 1-deep. Order of declaration matters — use `function ...` declarations or wrap both as object methods. In practice, isEven is `n % 2 === 0`; the mutual-recursion form is a pedagogical example."

## Important takeaways

- **Naive mutual recursion overflows** at ~10k.
- **Trampoline pattern** = each "call" returns a thunk; loop unwraps.
- **Function declarations hoist**; expressions don't.
- **Object methods** as alternative — `ops.even`/`ops.odd`.
- **In real code**, use `n % 2`.

## Variants

- **Even/odd via async generators** — yield each step.
- **Mutual recursion with side-effect accumulation** — pass an accumulator parameter.
- **Three-way mutual recursion** — same trampoline still works.

## Revision notes

```
mutual recursion (even/odd):
  isEven(n): n===0 ? true  : isOdd(n-1)
  isOdd(n):  n===0 ? false : isEven(n-1)
  V8 blows stack at ~10k

trampoline fix:
  return thunk instead of recursing
  outer loop while (typeof r === 'function') r = r()
  stack stays 1-deep

ordering:
  function decl → hoisted; both callable at parse
  const = function → not hoisted; order matters

real-world: just use n % 2 === 0
```
