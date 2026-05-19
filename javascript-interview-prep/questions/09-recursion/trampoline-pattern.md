# Trampoline pattern — recursion without stack overflow

> **Difficulty:** Senior   |   **Time:** ~10 min   |   **Prereqs:** [iterative-from-recursive.md](./iterative-from-recursive.md)
>
> **Source:** Functional idiom. Stripe, Atlassian — where recursion meets V8's no-TCO.

---

## 1. Problem statement

V8 doesn't optimize tail calls. Naive `factorial(100000)` blows stack. Trampoline = recursive function returns a thunk; loop unwraps thunks.

**Verification examples**

```js
function factorialStep(n, acc = 1) {
  if (n <= 1) return acc;
  return () => factorialStep(n - 1, n * acc);     // thunk, not direct recurse
}

const factorial = trampoline(factorialStep);
factorial(100_000);                                // works — no overflow
```

**Constraints**
- Each "recursive" step returns a THUNK (function).
- Trampoline loop calls thunks until result is non-function.
- Function-allocation overhead per step (slower than for-loop).
- Use for clarity, not speed.

---

## 2. Plain-English restatement

Convert recursion to a thunk-returning function. Outer loop calls thunks until you get the final value. No stack growth.

---

## 3. Why this matters in interviews

V8/Node don't TCO (despite ES2015 spec — only Safari/JSC does). Trampoline removes stack limit. Senior signal: know the gap.

---

## 4. Mental model

```
   trampoline(fn):
     return function(...args):
       result = fn(...args)
       while typeof result === 'function':
         result = result()
       return result
   
   Adapter (tail-recursive style):
     factorialStep(n, acc=1):
       if n <= 1: return acc          ← base
       return () => factorialStep(n-1, n*acc)   ← thunk
   
   Why no stack growth:
     Each thunk invocation:
       1. Returns from current call (frame popped).
       2. Trampoline calls next thunk (one new frame).
     Net: stack stays at 1-2 frames forever.

   Performance:
     1M iterations: ~10× slower than hand-written for-loop
     (function alloc + call overhead per step).
     Use when expressing as recursion is clearer.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why thunks not direct recursion?
> 2. Does V8 do TCO?
> 3. Performance vs for-loop?

---

## 6. Brute force — walked through

```js
function factorial(n, acc = 1) {
  if (n <= 1) return acc;
  return factorial(n - 1, n * acc);   // direct call → grows stack despite "tail" form
}
factorial(100_000);                    // RangeError on V8
```

---

## 7. The unlocking insight

> **Each step returns a thunk; trampoline loop calls thunks. No stack growth. V8 doesn't TCO.**

Three properties:

1. **Thunk return** instead of direct recurse.
2. **Loop unwraps** thunks.
3. **Slower than for-loop** — use for clarity.

---

## 8. Solution (annotated)

```js
function trampoline(fn) {
  return function (...args) {
    let result = fn(...args);                                              // step 1: initial call
    while (typeof result === 'function') {                                 // step 2: unwrap thunks
      result = result();
    }
    return result;
  };
}

// Adapt: tail-recursive function returns thunks
function factorialStep(n, acc = 1) {
  if (n <= 1) return acc;
  return () => factorialStep(n - 1, n * acc);                              // step 3: thunk
}

const factorial = trampoline(factorialStep);
factorial(100_000);                                                        // step 4: no overflow

// Even / odd via mutual recursion
function isEvenStep(n) {
  if (n === 0) return true;
  return () => isOddStep(n - 1);                                           // step 5: mutual
}
function isOddStep(n) {
  if (n === 0) return false;
  return () => isEvenStep(n - 1);
}

const isEven = trampoline(isEvenStep);
isEven(100_000);                                                            // true

// Async trampoline
function asyncTrampoline(fn) {
  return async function (...args) {
    let result = await fn(...args);
    while (typeof result === 'function') {
      result = await result();
    }
    return result;
  };
}
```

**Try it yourself**

```js
// Sum of 1..N — usually for-loop, but trampoline demos pattern
function sumStep(n, acc = 0) {
  if (n === 0) return acc;
  return () => sumStep(n - 1, acc + n);
}
const sum = trampoline(sumStep);
sum(1_000_000);                                                // works (huge N)

// Compare to naive recursive
function sumNaive(n, acc = 0) {
  if (n === 0) return acc;
  return sumNaive(n - 1, acc + n);
}
// sumNaive(1_000_000);                                        // RangeError

// vs for-loop (fastest)
function sumLoop(n) {
  let s = 0;
  for (let i = 1; i <= n; i++) s += i;
  return s;
}
// for-loop ~10x faster than trampoline.

// Tree traversal with trampoline (deeper than V8 stack)
function walkStep(node, visit) {
  if (!node) return;
  visit(node.value);
  return () => walkStep(node.next, visit);
}
const walk = trampoline(walkStep);
// Build 100k-node linked list and walk safely.

// Without trampoline (or recursive flatten):
// RangeError on 100k+ depth.
```

---

## 9. Step-by-step dry run

```
factorial(3):
  trampoline(factorialStep)(3):
    result = factorialStep(3) = () => factorialStep(2, 3).   ← thunk
    
    typeof result === 'function' → yes.
    result = result() = factorialStep(2, 3) = () => factorialStep(1, 6).
    
    typeof function → yes.
    result = factorialStep(1, 6) = 6 (base case).
    
    typeof === 'number' → loop exit.
    return 6.

Stack frames during:
  Iter 1: trampoline frame + factorialStep frame. Return thunk. Pop factorialStep.
  Iter 2: trampoline frame + factorialStep frame. Return thunk. Pop.
  Iter 3: trampoline frame + factorialStep frame. Return 6. Pop.
  
  Net stack: 2 frames at any moment. Never grows.

vs naive factorial(3):
  factorial(3, 1) calls factorial(2, 3) calls factorial(1, 6) returns 6.
  3 nested frames.
  For factorial(100k): 100k frames → blow.

Why "tail-recursive form" alone doesn't help in V8:
  V8 doesn't recognize tail call → still pushes frame.
  Trampoline is explicit conversion to iteration.

Async variant:
  Each step returns a Promise that resolves to a thunk or value.
  Loop: result = await result(). Same idea.
```

---

## 10. Common confusion + traps

1. **Return result directly** instead of thunk — defeats purpose.
2. **Assume V8 TCO** — no.
3. **Use for performance** — slower than for-loop.
4. **Forget accumulator** — non-tail-recursive shape; convert first.
5. **Mutual recursion** — works if both return thunks.
6. **Async + thunk** — needs async trampoline.
7. **Closure overhead** — function alloc per step.

---

## 11. Senior follow-ups & variants

### Variant 1 — Mutual recursion
isEven/isOdd thunks.

### Variant 2 — Async trampoline
`await result()` inside while.

### Variant 3 — Lazy stream
Each thunk yields one item; trampoline collects.

### Variant 4 — Bind trampoline
Bake function in; cleaner API.

### Variant 5 — Generator-based alternative
`yield* recursive()` — same idea via generators.

---

## 12. How to think aloud

> "V8 (Node, Chrome) does NOT optimize tail calls — only Safari/JSC does, despite TCO being in the ES2015 spec. So `function fact(n, acc) { if (n<=1) return acc; return fact(n-1, n*acc); }` (textbook 'tail-recursive') still pushes a frame per call in V8 — `fact(100_000)` throws `RangeError`. Trampoline converts recursion to iteration: instead of returning the recursive call directly, return a THUNK (a zero-arg function that, when called, makes the next 'recursive' step). Then the trampoline wrapper has a `while (typeof result === 'function') result = result();` loop that unwraps thunks until you get a non-function value. Net stack depth: 1-2 frames forever; no growth. Adapter: 'tail-recursive' shape (state in accumulator params) then wrap return in `() => ...`. Mutual recursion (isEven/isOdd) works because both return thunks pointing at each other; same trampoline. Async variant: `async` wrapper, `await result()` inside while. Performance: ~10× slower than hand-written for-loop because of function allocation per step — use for clarity (algorithm expressed naturally as recursion) not for speed. Trap: returning result instead of thunk (no benefit); expecting V8 TCO; using as perf optimization (it's not)."

---

## 13. 60-second revision

> - **V8 NO TCO** — recursive blows stack.
> - **Trampoline:** thunk return + loop unwraps.
> - **Each step: `return () => recursiveCall(...)`**.
> - **No stack growth** — 1-2 frames at all times.
> - **Mutual recursion** works.
> - **Async variant:** `await result()`.
> - **Slower than for-loop** — clarity not speed.
> - **Trap:** return direct (no benefit); expect V8 TCO; perf.

---

**Related:** [iterative-from-recursive.md](./iterative-from-recursive.md) · [mutual-recursion-even-odd.md](./mutual-recursion-even-odd.md) · [flatten-deeply-nested-array.md](./flatten-deeply-nested-array.md) · [deep-clone-with-cycles.md](./deep-clone-with-cycles.md)

**Concept primer:** [`concepts/recursion-and-the-call-stack.md`](../../concepts/recursion-and-the-call-stack.md)
