# Mutual recursion (even/odd) + trampolining

> **Difficulty:** Senior   |   **Time:** ~8 min   |   **Prereqs:** [trampoline-pattern.md](./trampoline-pattern.md)
>
> **Source:** Classic FP example. Stripe, Razorpay, Atlassian.

---

## 1. Problem statement

Implement isEven/isOdd using only mutual recursion. Naive blows stack at ~10k. Trampoline fixes.

**Verification examples**

```js
// Naive
isEven(4);                                // true
isEven(100_000);                          // RangeError

// Trampolined
const isEvenSafe = trampoline(isEvenStep);
isEvenSafe(100_000);                      // true
```

**Constraints**
- Mutual recursion (no `n % 2`).
- Function declarations hoisted (forward references OK).
- V8 no TCO → naive blows stack.
- Trampoline: thunks + loop.

---

## 2. Plain-English restatement

`isEven` calls `isOdd`, `isOdd` calls `isEven`. Naive: both blow stack at deep n. Trampoline: each returns a thunk; loop unwraps.

---

## 3. Why this matters in interviews

Tests: hoisting (forward references), stack growth, trampoline conversion. Senior bar: know V8 doesn't TCO.

---

## 4. Mental model

```
   Naive:
     isEven(n): n === 0 ? true : isOdd(n - 1)
     isOdd(n):  n === 0 ? false : isEven(n - 1)
   
   Each call → push frame. n calls = n frames.
   V8 cap ~10-15k → RangeError.
   
   Trampolined:
     isEvenStep(n): n === 0 ? true : () => isOddStep(n - 1)   ← thunk
     isOddStep(n):  n === 0 ? false : () => isEvenStep(n - 1)
   
   trampoline returns function that:
     calls fn → gets thunk → calls thunk → gets thunk → ... → gets boolean.
   
   Stack: 1-2 frames forever. Safe at any n.
   
   Hoisting:
     Function declarations are hoisted with body.
     isEven can reference isOdd before isOdd's source.
     Function expressions assigned to vars NOT hoisted same way.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why does naive blow stack?
> 2. Why is hoisting relevant?
> 3. Does trampoline fix work for mutual?

---

## 6. Brute force — walked through

```js
const isEven = function(n) { return n === 0 ? true : isOdd(n - 1); };
const isOdd  = function(n) { return n === 0 ? false : isEven(n - 1); };
// TDZ error if `isEven` calls `isOdd` before line where isOdd is assigned.
// Function declarations don't have this issue (hoisted with body).
```

Naive + expressions: TDZ. Use declarations.

---

## 7. The unlocking insight

> **Naive mutual recursion blows stack at deep n. Trampoline: both return thunks; same trampoline unwraps. Function declarations hoisted.**

Three properties:

1. **Forward references** via function declarations.
2. **Naive blows** at ~10-15k.
3. **Trampoline mutual** works.

---

## 8. Solution (annotated)

```js
// Naive (function declarations — hoisted)
function isEven(n) {
  if (n === 0) return true;
  return isOdd(n - 1);                                                     // step 1: mutual call
}
function isOdd(n) {
  if (n === 0) return false;
  return isEven(n - 1);
}

isEven(100);                                                                // true
// isEven(100_000);                                                         // RangeError

// Trampolined (handles deep n)
function trampoline(fn) {
  return function (...args) {
    let result = fn(...args);
    while (typeof result === 'function') result = result();                 // step 2: unwrap
    return result;
  };
}

function isEvenStep(n) {
  if (n === 0) return true;
  return () => isOddStep(n - 1);                                            // step 3: thunk
}
function isOddStep(n) {
  if (n === 0) return false;
  return () => isEvenStep(n - 1);
}

const isEvenSafe = trampoline(isEvenStep);
const isOddSafe = trampoline(isOddStep);

isEvenSafe(100_000);                                                       // true
isOddSafe(1_000_000);                                                      // false
```

**Try it yourself**

```js
// Naive
isEven(4);                                                    // true
isEven(5);                                                    // false
isEven(0);                                                    // true

// Naive limit
try { isEven(100_000); } catch (e) { console.log('RangeError'); }

// Trampolined safe
isEvenSafe(1_000_000);                                        // true

// Why function declarations matter
// const isEven = function(n) { return n === 0 ? true : isOdd(n - 1); };
// const isOdd  = function(n) { return n === 0 ? false : isEven(n - 1); };
// At parse time, isEven's body references isOdd which is in TDZ until line 2.
// At CALL time, both are defined. Actually works because mutual recursion happens at call time, not parse time.

// In strict mode + class body, declarations behave differently.

// Class method version
class Number_ {
  static isEven(n) { return n === 0 ? true : Number_.isOdd(n - 1); }
  static isOdd(n)  { return n === 0 ? false : Number_.isEven(n - 1); }
}

// Real-world: state machines via mutual recursion
function parseStart(input, i) { /* state A */ return parseRest(input, i + 1); }
function parseRest(input, i) { /* state B */ return parseStart(input, i + 1); }
// Each "state transition" is a call → blow stack on long input.
// Trampoline conversion → safe state machine.
```

---

## 9. Step-by-step dry run

```
isEven(3) naive:
  isEven(3) → push frame.
    isOdd(2) → push.
      isEven(1) → push.
        isOdd(0) → return false.
      return false.
    return false.
  return false.

Max stack: 4 frames. For n=100k: 100k+ frames → RangeError.

Trampolined isEvenSafe(3):
  trampoline calls isEvenStep(3) → returns thunk `() => isOddStep(2)`.
  result is function → call it:
    isOddStep(2) → returns thunk `() => isEvenStep(1)`.
  result is function → call:
    isEvenStep(1) → returns thunk `() => isOddStep(0)`.
  result is function → call:
    isOddStep(0) → returns false.
  result is boolean → exit loop. Return false.

Stack at any moment: trampoline frame + one Step frame = 2.
n=1M: still 2 frames. Safe.

Hoisting:
  function declarations are hoisted to top of scope.
  At parse time, both isEven and isOdd are in scope.
  Function expressions on const/let are TDZ until line of definition.
  At call time (later), all defined regardless.
  So function declarations strictly safer for mutual recursion.
```

---

## 10. Common confusion + traps

1. **Naive on deep n** — RangeError.
2. **Function expressions** — TDZ if called too early in scope.
3. **`n < 0`** — undefined behavior; recurses forever or to negative.
4. **V8 TCO assumption** — no.
5. **Trampoline lone (not mutual)** — works for any recursion.
6. **Performance** — trampoline slower than `n % 2`.
7. **Async mutual** — async trampoline.

---

## 11. Senior follow-ups & variants

### Variant 1 — Generic mutual recursion
Pair any two recursive functions.

### Variant 2 — State machine
Each state is a function; trampoline-safe.

### Variant 3 — `n % 2`
Real answer; mutual is academic.

### Variant 4 — Async trampoline
For async mutual.

### Variant 5 — CPS (continuation-passing)
Generalize trampoline.

---

## 12. How to think aloud

> "Naive mutual recursion: `isEven(n) = n === 0 ? true : isOdd(n - 1)`; `isOdd(n) = n === 0 ? false : isEven(n - 1)`. Each call pushes a stack frame; V8 caps at ~10-15k → `RangeError` on `isEven(100_000)`. V8 does NOT do tail-call optimization (only Safari/JSC does, despite ES2015 spec). Trampoline fix: each function returns a THUNK (closure) instead of recursing directly; outer trampoline wrapper unwraps in a loop — `while (typeof result === 'function') result = result()`. Same trampoline works for both mutual functions because the thunks alternate. Net stack depth: 1-2 frames forever. Hoisting note: function DECLARATIONS are hoisted with their bodies, so `isEven` referencing `isOdd` before its source line is fine; function EXPRESSIONS on const/let are TDZ until their assignment line — would fail if mutual recursion structure is split poorly. Real-world use: state machine where each state is a function calling the next; deep input blows stack without trampoline. Practical: `n % 2` is the real answer — mutual recursion for booleans is academic. Trap: naive on deep n; expression-based with hoisting issues; expect V8 TCO."

---

## 13. 60-second revision

> - **Naive mutual blows stack** at deep n.
> - **Function declarations hoisted** (forward refs OK).
> - **Trampoline: thunks + loop**.
> - **Same trampoline** works for mutual.
> - **V8 NO TCO** — academic gap.
> - **`n % 2`** is the real answer.
> - **State machines** benefit from trampoline.
> - **Async variant** for async mutual.
> - **Trap:** naive at scale; TDZ with expressions.

---

**Related:** [trampoline-pattern.md](./trampoline-pattern.md) · [iterative-from-recursive.md](./iterative-from-recursive.md) · [recursive-descent-parser.md](./recursive-descent-parser.md)

**Concept primer:** [`concepts/recursion-and-the-call-stack.md`](../../concepts/recursion-and-the-call-stack.md)
