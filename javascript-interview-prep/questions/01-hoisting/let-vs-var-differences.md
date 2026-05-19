# `let` vs `var` — the five differences

> **Difficulty:** Medium   |   **Time:** ~10 min   |   **Prereqs:** [hoisting-in-javascript.md](./hoisting-in-javascript.md), [tdz-let-const.md](./tdz-let-const.md)
>
> **Source:** The "do you know modern JS?" gate question on every senior screen.

---

## 1. Problem statement

Enumerate the **five differences** between `let` and `var`, with engine-level reasoning for each.

**Verification examples**

| Property                              | `var`                          | `let`                                |
|----------------------------------------|--------------------------------|--------------------------------------|
| Scope                                  | function (or global)           | block (`{...}`)                       |
| Hoisting                               | binding + `undefined`          | binding + `<uninitialized>` (TDZ)    |
| Read before declaration                | `undefined`                    | `ReferenceError`                     |
| `typeof` before declaration            | `'undefined'`                  | `ReferenceError`                     |
| Redeclaration in same scope            | allowed                        | `SyntaxError`                        |
| Global object attachment (classic script) | yes                          | no                                   |
| Loop binding per iteration             | one shared                     | fresh per iteration                  |
| Lives in                               | Variable Environment           | Lexical Environment                  |

**Constraints**
- Use `const` by default; `let` when reassigning; never `var` in new code.
- `let` redeclaration in same scope = `SyntaxError` at parse.
- ESM top-level `var` does NOT attach to `globalThis`.

---

## 2. Plain-English restatement

`var` is the ES5 keyword — function-scoped, hoisted as `undefined`, allows redeclaration, leaks out of blocks. `let` (and `const`) are ES6 fixes — block-scoped, hoisted but in TDZ, forbid redeclaration, give fresh bindings per loop iteration.

---

## 3. Why this matters in interviews

The most common "do you know modern JS?" gate. Weak answers stop at "scope is different." Strong answers enumerate FIVE differences with mechanism + an output example. Sets up closure round.

---

## 4. Mental model

```
   var:                                  let:
   ┌──────────────────────────┐          ┌──────────────────────────┐
   │ Variable Environment      │          │ Lexical Environment       │
   │ Function-scoped           │          │ Block-scoped              │
   │ Hoisted as undefined      │          │ Hoisted as <uninitialized>│
   │ Read before init: undefined│          │ Read before init: TDZ error│
   │ Redeclaration: silent      │          │ Redeclaration: SyntaxError│
   │ globalThis (in scripts)    │          │ Never globalThis          │
   │ Loop: one shared binding   │          │ Loop: fresh per iter      │
   └──────────────────────────┘          └──────────────────────────┘

   Engine: both registered at creation; var → undefined; let → TDZ.

   for (var i = 0; i < 3; i++)           for (let j = 0; j < 3; j++)
     ↓                                     ↓
   one i in function's VE                  fresh j in each iter's LE
   all closures share final value          each closure owns its j
   prints 3, 3, 3                          prints 0, 1, 2
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What does `for (var i = 0; i < 3; i++) setTimeout(() => log(i))` print? With `let`?
> 2. Does `var x = 1; var x = 2` throw?
> 3. Does `let y = 1; var y = 2` throw?

---

## 6. Brute force — walked through

### Wrong attempt 1: only mention scope
"`let` is block-scoped, `var` is function-scoped." Scores 4/10. Interviewer asks "what else?" and you flail.

### Wrong attempt 2: "`let` isn't hoisted"
It IS — into TDZ.

### Wrong attempt 3: assume `var` redeclaration warns
Silent — accidental shadowing slips through code review.

---

## 7. The unlocking insight

> **Five buckets: scope (function vs block), hoisting (undefined vs TDZ), redeclaration (yes vs no), globalThis attachment (script-only vs never), loop binding (shared vs fresh). Drive each with mechanism + output example.**

Three properties:

1. **VE vs LE residence** — function vs block scope.
2. **Init at creation vs TDZ** — `undefined` vs throw.
3. **Per-iteration fresh `let`** — closures work in loops.

---

## 8. Solution (annotated)

```js
'use strict';

// 1. Scope
function scopeDemo() {
  if (true) {
    var v = 'in-block';
    let l = 'in-block';
  }
  console.log(v);                                                     // 'in-block' — leaked
  try { console.log(l); }                                              // ReferenceError
  catch (e) { console.log('let trapped in block'); }
}
scopeDemo();

// 2. Hoisting / TDZ
function hoistDemo() {
  console.log('var before:', typeof a);                                // 'undefined' — safe
  try { console.log(typeof b); }                                       // ReferenceError on TDZ
  catch (e) { console.log('let TDZ on typeof'); }
  var a = 1;
  let b = 2;
}
hoistDemo();

// 3. Redeclaration
function redeclareDemo() {
  var x = 1;
  var x = 2;                                                            // fine
  console.log(x);                                                       // 2
  // let y = 1; let y = 2;                                               // SyntaxError at parse
}

// 5. Loop binding
function loopDemo() {
  for (var i = 0; i < 3; i++) setTimeout(() => console.log('var i:', i), 0);
  for (let j = 0; j < 3; j++) setTimeout(() => console.log('let j:', j), 0);
}
loopDemo();
// After current task:
// var i: 3 (×3)
// let j: 0, 1, 2
```

---

## 9. Step-by-step dry run

```
loopDemo trace:

for (var i = 0; i < 3; i++):
  var i in loopDemo's VE. ONE binding.
  iter 0: schedule cb_A capturing VE. VE.i=0.
  iter 1: schedule cb_B capturing same VE. VE.i=1.
  iter 2: schedule cb_C capturing same VE. VE.i=2.
  loop exits. VE.i=3.

  Microtask drain:
    cb_A: reads VE.i → 3
    cb_B: reads VE.i → 3
    cb_C: reads VE.i → 3

for (let j = 0; j < 3; j++):
  Each iteration creates NEW block LE.
  iter 0: LE_0 = {j: 0}. schedule cb_D capturing LE_0.
  iter 1: LE_1 = {j: 1}. schedule cb_E capturing LE_1.
  iter 2: LE_2 = {j: 2}. schedule cb_F capturing LE_2.

  Microtask drain:
    cb_D: reads LE_0.j → 0
    cb_E: reads LE_1.j → 1
    cb_F: reads LE_2.j → 2
```

---

## 10. Common confusion + traps

1. **Listing only scope** — 4/5 differences missing.
2. **"let isn't hoisted"** — into TDZ.
3. **`var` redeclaration silent** — shadowing slips review.
4. **ESM top-level `var` attaches to globalThis** — no.
5. **`switch` cases share scope** — `let` in one is TDZ in earlier.
6. **`const` immutable values** — only the binding; objects still mutable.
7. **`typeof` safe on `let` TDZ** — throws.

---

## 11. Senior follow-ups & variants

### Variant 1 — "Mixed `var`/`let` in block"
`var x = 1; { let x = 2; var x = 3; }` — `SyntaxError` (var x redeclares let x).

### Variant 2 — `switch` without braces
case A `let v`; case B reads `v` before line → TDZ.

### Variant 3 — `const` mutability gotcha
`const arr = []; arr.push(1)` works; `arr = [1]` throws TypeError. Binding const, value mutable.

### Variant 4 — `for-in` / `for-of` with `var`
Works but binding outlives loop; `let` is the right choice.

### Variant 5 — Module vs script `var` attachment
Script: top-level `var` → `globalThis.x`. Module: never.

---

## 12. How to think aloud

> "Five differences. (1) Scope: `var` function-scoped, `let` block-scoped. (2) Hoisting: `var` initializes to `undefined` at creation, `let` is `<uninitialized>` in TDZ. (3) Redeclaration: `var` silent, `let` SyntaxError at parse. (4) globalThis attachment: `var` in classic scripts attaches, `let` never; ESM top-level `var` doesn't attach either. (5) Loop binding: `for (var i)` shares one i in function's VE → loop-closure bug (3,3,3); `for (let j)` creates fresh LE per iteration (0,1,2). Engine: both registered at creation phase but `let` stays uninitialized until declaration line. Modern style: const by default, let when reassigning, never var. Trap: 'let isn't hoisted'; typeof safe on TDZ; mixed var/let redeclares throw."

---

## 13. 60-second revision

> - **5 differences:** scope, hoisting, redeclaration, globalThis attachment, loop binding.
> - **`var`:** function-scoped, `undefined` at creation, redeclarable, attaches to globalThis (scripts), shared loop binding.
> - **`let`:** block-scoped, TDZ at creation, non-redeclarable, never globalThis, fresh per loop iteration.
> - **`const`:** like `let` + no rebinding (values still mutable).
> - **Style:** `const` default, `let` when reassigning, never `var`.
> - **Trap:** "let isn't hoisted"; typeof safe; var redeclaration silent; ESM var-globalThis assumption.

---

**Related:** [hoisting-in-javascript.md](./hoisting-in-javascript.md) · [tdz-let-const.md](./tdz-let-const.md) · [let-in-for-loop-binding.md](./let-in-for-loop-binding.md) · [var-hoisting-output.md](./var-hoisting-output.md) · [`02-closures/loop-closure-var-let.md`](../02-closures/loop-closure-var-let.md)

**Concept primer:** [`concepts/hoisting.md`](../../concepts/hoisting.md)
