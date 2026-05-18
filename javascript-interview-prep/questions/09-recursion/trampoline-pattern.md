# Trampoline Pattern — Recursion Without Stack Overflow

## Source / Origin
- Functional programming idiom; predates TCO.
- Asked at: Stripe, Atlassian — anywhere recursion meets V8's lack of TCO.
- Concept reference: `concepts/recursion.md`.

## Why this question matters in interviews
V8 doesn't do proper tail-call optimization. A naively recursive `factorial(100000)` blows the stack. Trampolining converts recursion to iteration: each "recursive call" returns a *thunk* (a function), and a loop unwraps thunks until you get a value. Senior bar: you know V8 doesn't TCO (despite the spec), can implement trampoline in 10 lines, and recognize when to reach for it.

## Concepts involved

### Syntax to lock in
```js
function trampoline(fn) {
  return function (...args) {
    let result = fn(...args);
    while (typeof result === 'function') result = result();
    return result;
  };
}

// Adapter: recursive function returns a thunk instead of recursing directly
function factorialStep(n, acc = 1) {
  if (n <= 1) return acc;
  return () => factorialStep(n - 1, n * acc);    // return thunk
}

const factorial = trampoline(factorialStep);
factorial(100000);   // works — no stack overflow
```

### Edge cases / traps
1. **You must return a thunk** for every "recursive" step. Returning the result of the recursive call directly defeats the purpose.
2. **Accumulator pattern** — convert to tail-recursive form first (move state into params).
3. **Mutual recursion** — both functions return thunks that point at each other; same trampoline works.
4. **Async trampoline** — same idea, but `await result()` and use `while (typeof result === 'function')` after awaiting.
5. **Performance** — slower than a hand-written loop due to function allocation per step. Use for clarity, not speed.
6. **Stack depth limit in V8** — ~10k-50k for non-tail recursive; trampoline removes the limit entirely.
7. **Not a substitute for memoization** — trampoline just removes stack growth; doesn't speed up exponential recursion.

## Mental Model

```
   Naive recursion:
   fact(5) → fact(4) → fact(3) → fact(2) → fact(1)
   call stack: 5 deep; multiply on the way back

   Trampoline:
   factorialStep(5) → thunk_for(4)
   loop: call thunk_for(4) → thunk_for(3)
   loop: call thunk_for(3) → thunk_for(2)
   loop: call thunk_for(2) → thunk_for(1)
   loop: call thunk_for(1) → returns final value
   loop: exits

   call stack stays 1-deep (just the loop and the current thunk)
```

## Why interviewers care

- **V8 TCO awareness** — spec says yes; V8 says no. Senior gotcha.
- **Functional idiom literacy.**
- **Tail-recursive conversion** — fundamental skill.

## Common confusion

- **"V8 implements TCO."** It doesn't (deliberately, due to debugging concerns). Only Safari/JSC ever shipped TCO; even that's spotty.
- **"Trampoline makes recursion faster."** No — function allocation per step is slower than iteration. Use for clarity or to remove stack limits.
- **"Any recursive function works."** Only tail-recursive ones. Non-tail recursion (e.g., binary tree post-order) needs explicit stack.
- **"Convert to a `for` loop instead."** Yes — that's often clearer. Trampoline is for when the recursive form is more natural.

## Brute force

```js
function fact(n) { if (n <= 1) return 1; return n * fact(n - 1); }
fact(100000);   // RangeError: Maximum call stack size exceeded
```

## Optimal approach

Two-step:
1. Convert to tail-recursive (move state into accumulator).
2. Return a thunk instead of recursing directly.

Run with trampoline.

## Solution

```js
function trampoline(fn) {
  return function (...args) {
    let r = fn.apply(this, args);
    while (typeof r === 'function') r = r();
    return r;
  };
}

// Factorial
const factorial = trampoline(function step(n, acc = 1) {
  return n <= 1 ? acc : () => step(n - 1, n * acc);
});
factorial(100000);   // works

// Sum
const sum = trampoline(function step(arr, i = 0, acc = 0) {
  return i >= arr.length ? acc : () => step(arr, i + 1, acc + arr[i]);
});
sum([...Array(1e6).keys()]);   // 499999500000; no stack overflow

// Mutual recursion (is-even / is-odd)
function isEvenStep(n) { return n === 0 ? true : () => isOddStep(n - 1); }
function isOddStep(n)  { return n === 0 ? false : () => isEvenStep(n - 1); }
const isEven = trampoline(isEvenStep);
isEven(100000);   // true

// Async trampoline
function trampolineAsync(fn) {
  return async function (...args) {
    let r = await fn.apply(this, args);
    while (typeof r === 'function') r = await r();
    return r;
  };
}

// Tree fold via explicit stack (when recursion isn't tail-recursive)
function treeSum(root) {
  const stack = [root];
  let sum = 0;
  while (stack.length) {
    const node = stack.pop();
    sum += node.value;
    if (node.left) stack.push(node.left);
    if (node.right) stack.push(node.right);
  }
  return sum;
}
```

## Dry run

```
factorial(4):
  trampoline wrapper called
  r = step(4, 1)
    n=4, return () => step(3, 4*1)   ← thunk
  r is function → r = r() → step(3, 4)
    return () => step(2, 3*4)
  r is function → r = r() → step(2, 12)
    return () => step(1, 2*12)
  r is function → r = r() → step(1, 24)
    n=1, return 24                   ← value, not function
  r is not function → exit loop
  return 24
```

Stack stays 1-deep throughout.

## How to think aloud

> "V8 doesn't do TCO, so deep recursion blows the stack. Trampoline: convert function to tail-recursive (state in accumulator), return a thunk instead of calling self, run with a loop that unwraps thunks. Stack stays 1-deep. Works for mutual recursion too. For non-tail-recursive shapes like binary-tree post-order, use an explicit stack instead — trampoline only handles tail position. Slower than a plain loop because of function allocation; reach for it for clarity or when natural form is recursive."

## Important takeaways

- **V8 doesn't TCO** — deep tail recursion still overflows.
- **Trampoline = thunks + loop.**
- **Only works for tail-recursive** functions. Non-tail needs explicit stack.
- **Accumulator pattern** moves state into params.
- **Async trampoline** with `await`.
- **Slower than a loop** — clarity, not speed.

## Variants

- **Step-based generators** — `function* () { yield ... }` consumed in a loop; similar effect.
- **Continuations** — heavier; uncommon in JS.
- **Explicit stack** — for non-tail-recursive (tree traversal post-order, mutual recursion that builds a result tree).

## Revision notes

```
trampoline(fn) → wrapper:
  r = fn(...args)
  while (typeof r === 'function') r = r()
  return r

steps:
  1. convert to tail-recursive (state in accumulator)
  2. each "recursive call" returns a thunk (no-arg function)
  3. wrap with trampoline

USES:
  - very deep tail recursion (V8 doesn't TCO)
  - mutual recursion
  - async: trampolineAsync with await

LIMITS:
  - only tail-recursive shapes
  - slower than a loop (function alloc per step)
  - non-tail (post-order tree, multiple recursive results) → explicit stack
```
