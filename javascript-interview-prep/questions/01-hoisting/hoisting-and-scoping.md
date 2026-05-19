# Hoisting and scoping — how they interact

> **Difficulty:** Medium-Senior   |   **Time:** ~15 min   |   **Prereqs:** [hoisting-in-javascript.md](./hoisting-in-javascript.md), [let-vs-var-differences.md](./let-vs-var-differences.md)
>
> **Source:** Senior JS screens, output-prediction puzzles.

---

## 1. Problem statement

Walk through output-prediction snippets that combine hoisting + scope chains + closures. Demonstrate the **VE** vs **LE** distinction and **OuterEnv** pointer.

**Verification examples**

| Snippet                                                | Behaviour                                              |
|--------------------------------------------------------|---------------------------------------------------------|
| `if (true) { var x = 5; } console.log(x);`             | `5` — `var` leaks to enclosing function                |
| `if (true) { let x = 5; } console.log(x);`             | `ReferenceError` — block-scoped                        |
| `for (var i = 0; i < 3; i++) setTimeout(() => log(i))` | `3, 3, 3` (shared `i`)                                  |
| `for (let i = 0; i < 3; i++) setTimeout(() => log(i))` | `0, 1, 2` (fresh `i` per iteration)                     |
| Nested function reads outer `var`                      | climbs scope chain to outer EC                          |

**Constraints**
- Every EC has VE (var/function) + LE (let/const/class) + OuterEnv pointer.
- Scope chain: identifier resolution walks LE → VE → OuterEnv → ... → global.
- Closures capture **environments**, not values.

---

## 2. Plain-English restatement

Each execution context has two binding tables — VE for `var`/function, LE for `let`/`const`/`class` — and a pointer to its parent. When you read an identifier, the engine walks up the chain. Hoisting populates these tables during creation; scoping decides which table holds which name.

---

## 3. Why this matters in interviews

Output-prediction puzzles depend on knowing **which environment** holds each binding. Sets up closures and async-output rounds.

---

## 4. Mental model

```
   Every Execution Context:
   ┌────────────────────────────────────┐
   │ Variable Environment (VE)          │   var, function declarations
   │ Lexical Environment (LE)           │   let, const, class, params
   │ OuterEnv pointer ──────▶ parent EC │
   └────────────────────────────────────┘

   Scope chain (resolution order):
   current LE → current VE → OuterEnv.LE → OuterEnv.VE → ... → global

   Closure captures the ENVIRONMENT, not the value.
   That's why mutations to var after capture are visible.

   for (var i)  → one i in function's VE; all closures share.
   for (let i)  → new LE per iteration; closures capture own i.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. `for (var i = 0; i < 3; i++) setTimeout(() => log(i))` — output?
> 2. Why does the same loop with `let` print `0, 1, 2`?
> 3. In `function f() { var x = 1; if (true) { var x = 2; } log(x); }`, what's the output?

---

## 6. Brute force — walked through

### Wrong attempt 1: "Inner scope can see outer"
Correct but useless — doesn't explain WHY `var` leaks out of blocks.

### Wrong attempt 2: treat `var i` in `for` as block-scoped
It's not — function-scoped. One shared `i` across iterations.

### Wrong attempt 3: closures capture values
They capture environments. Mutations are visible.

---

## 7. The unlocking insight

> **Per EC: VE + LE + OuterEnv. Identifier resolution walks LE → VE → OuterEnv chain. `var` lives in VE (function-scoped); `let` lives in LE (block-scoped). Each `for (let i)` iteration creates a NEW LE.**

Three properties:

1. **VE vs LE distinction** — function-scoped vs block-scoped.
2. **OuterEnv chain** — resolution walks outward.
3. **Closures capture environment** — mutations visible.

---

## 8. Solution (annotated)

```js
const x = 'global-x';                                                 // global LE

function outer() {
  // outer's VE: { y: undefined, inner: <fn> }   (hoisted at creation)
  // outer's LE: {}                                (no let/const here)
  console.log(x);                                                     // climb chain → 'global-x'
  console.log(y);                                                     // undefined (var hoisted)

  var y = 'outer-y';

  for (let i = 0; i < 2; i++) {                                       // step 1: fresh LE per iter
    setTimeout(() => console.log('i=' + i, 'y=' + y), 0);              // captures iter's LE + outer's VE
  }

  function inner() {
    var y = 'inner-y';                                                  // shadows outer.y
    console.log(y);                                                     // 'inner-y' (own VE wins)
  }
  inner();
}

outer();
// Output:
// global-x
// undefined
// inner-y
// i=0 y=outer-y
// i=1 y=outer-y
```

**Try it yourself — the loop-closure bug:**

```js
// Bug: shared i
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 0);
}
// Output: 3, 3, 3 (all closures share function's VE.i; final value 3)

// Fix: let per-iteration binding
for (let i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 0);
}
// Output: 0, 1, 2 (each iter has fresh LE.i; each closure owns one)

// Pre-ES6 fix: IIFE
for (var i = 0; i < 3; i++) {
  (function (j) {
    setTimeout(() => console.log(j), 0);
  })(i);
}
// Output: 0, 1, 2 (IIFE creates fresh function scope each iter)
```

---

## 9. Step-by-step dry run

```
Global EC:
  LE: { x: <uninitialized> }                          (const)
  VE: { outer: <function> }

Execution:
  const x = 'global-x'  → x = 'global-x'
  outer() called → push outer's EC.

outer's EC:
  VE: { y: undefined, inner: <function inner> }       (creation phase)
  LE: {}
  OuterEnv → global

  console.log(x)        → not in outer.LE, not in outer.VE → walk to global.LE → 'global-x'
  console.log(y)        → outer.VE.y = undefined → print 'undefined'
  var y = 'outer-y'     → outer.VE.y = 'outer-y'
  
  for (let i = 0; i < 2; i++):
    iter 0: new block LE = { i: 0 }. Schedule cb_A. cb_A's OuterEnv → THIS LE.
    iter 1: new block LE = { i: 1 }. Schedule cb_B. cb_B's OuterEnv → THIS LE.
  
  inner() → push inner's EC.

inner's EC:
  VE: { y: undefined }                                 (creation)
  OuterEnv → outer
  
  var y = 'inner-y'     → inner.VE.y = 'inner-y'
  console.log(y)        → resolves to inner.VE.y (first match) → 'inner-y'

Pop inner. Pop outer. Global continues.

Microtask drain (after sync):
  cb_A: resolves i from its captured LE → 0; y from outer.VE → 'outer-y'. Log.
  cb_B: i=1; y='outer-y'. Log.
```

---

## 10. Common confusion + traps

1. **`var i` in `for` is block-scoped** — no, function-scoped; loop-closure bug.
2. **Closures capture values** — no, environments; mutations visible.
3. **Scope chain "merges"** — no, walks; first match wins.
4. **`var` inside `if` doesn't leak** — it does (function-scoped).
5. **Parameters share function VE** — separate parameter scope; default params can hit TDZ.
6. **Module-level `var` attaches to `globalThis`** — only in scripts, NOT in ESM.
7. **`with` and `eval`** can dynamically extend scope chain — avoid.

---

## 11. Senior follow-ups & variants

### Variant 1 — Loop-closure bug
`for (var i)` shares one `i`; closures see final value. Fix: `let` (per-iter LE) or IIFE.

### Variant 2 — Nested shadowing
Three nested fns each `var x = ...`. Each `console.log(x)` resolves to nearest VE.

### Variant 3 — Parameter scope TDZ
`function f(a = b, b) {}` — `a`'s default reads `b` in TDZ → throws.

### Variant 4 — IIFE pre-ES6 pattern
`(function(j) { setTimeout(() => log(j)); })(i)` — IIFE creates fresh fn scope per iter.

### Variant 5 — Module scope
ESM is strict; top-level var doesn't attach to globalThis; `this === undefined`.

---

## 12. How to think aloud

> "Every EC has Variable Environment (var/function) + Lexical Environment (let/const/class) + OuterEnv pointer. Identifier resolution walks LE → VE → OuterEnv → ... → global. `var` lives in VE (function-scoped); `let` in LE (block-scoped). Closures capture the ENVIRONMENT, not the value — that's why `for (var i)` callbacks share one i (loop-closure bug) but `for (let i)` works (fresh LE per iteration). Whiteboard trick: draw VE+LE tables per EC, draw OuterEnv arrows. Mechanically solves every output-prediction puzzle. Trap: var-block leak; closures-capture-values; chain merges."

---

## 13. 60-second revision

> - **Per EC:** VE (var/function), LE (let/const/class), OuterEnv pointer.
> - **Scope chain:** LE → VE → OuterEnv → ... → global. First match wins.
> - **`var`** = function-scoped (VE). **`let`/`const`** = block-scoped (LE).
> - **Closures capture ENVIRONMENT**, not value.
> - **`for (var i)`** = shared i (loop-closure bug). **`for (let i)`** = fresh LE per iter.
> - **Whiteboard:** draw scope diagram for any prediction puzzle.
> - **Trap:** `var` block-scope assumption; values-not-environments; module vs script.

---

**Related:** [hoisting-in-javascript.md](./hoisting-in-javascript.md) · [let-vs-var-differences.md](./let-vs-var-differences.md) · [let-in-for-loop-binding.md](./let-in-for-loop-binding.md) · [`02-closures/loop-closure-var-let.md`](../02-closures/loop-closure-var-let.md)

**Concept primer:** [`concepts/hoisting.md`](../../concepts/hoisting.md), [`concepts/closures.md`](../../concepts/closures.md)
