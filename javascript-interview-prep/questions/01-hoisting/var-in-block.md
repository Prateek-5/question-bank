# `var` inside blocks — function-scoped leak

> **Difficulty:** Easy-Medium   |   **Time:** ~10 min   |   **Prereqs:** [hoisting-in-javascript.md](./hoisting-in-javascript.md), [let-vs-var-differences.md](./let-vs-var-differences.md)
>
> **Source:** Canonical output-prediction warm-up. BFE.dev, "You Don't Know JS".

---

## 1. Problem statement

`var` ignores `if`/`for`/`while`/`{}` blocks — it hoists to the nearest enclosing function (or module/script top).

**Verification examples**

| Snippet                                               | Output                                       |
|-------------------------------------------------------|----------------------------------------------|
| `function f() { if (false) { var x = 1; } log(x); }` | `undefined` (not `ReferenceError`)           |
| `function f() { if (true) { var x = 1; } log(x); }`  | `1`                                          |
| `for (var i = 0; i < 3; i++) {} log(i);`              | `3` (i leaks out of loop)                   |
| `try { throw 0; } catch (var e) { var f = e; } log(f);` | `0` (var leaks)                            |
| `{ var x = 1; } { var x = 2; }` — same function       | one binding; final value `2`                |

**Constraints**
- `var` lives in nearest function or module/script.
- `var` ignores block boundaries (`if`, `for`, `while`, `try`, bare `{}`).
- Hoisted to `undefined` at creation; assignment runs at execution.
- `let`/`const` lives in nearest block.

---

## 2. Plain-English restatement

When you write `var x` inside an `if` or `for`, the binding doesn't live in that block — it lives in the enclosing function. The block boundary is invisible to `var`. So `if (false) { var x = 1; }` STILL creates `x` (as `undefined`) in the function scope; only the assignment is skipped.

---

## 3. Why this matters in interviews

#1 warm-up output-prediction puzzle. Tests whether you can apply the two-phase model + scope rules.

---

## 4. Mental model

```
   function scope (VE)                     block scope (LE)
   ┌──────────────────────┐                ┌──────────────────────┐
   │ var, function decls   │                │ let, const, class    │
   │ function-scoped       │                │ block-scoped         │
   │ hoisted to undefined  │                │ hoisted to TDZ       │
   └──────────────────────┘                └──────────────────────┘

   var ignores: if, for, while, try, bare {}.
   var stops at: function boundary, module/script top.

   function f() {
     if (false) {
       var x = 1;        ← declaration hoisted to f's VE; assignment skipped (false)
     }
     console.log(x);     ← x exists in f.VE → undefined
   }

   for (var i = 0; i < 3; i++) {}  ← i lives in enclosing function/module
   console.log(i);        ← 3 (loop counter persists)
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. `function f() { if (false) { var x = 1; } console.log(x); }` — output?
> 2. `for (var i = 0; i < 3; i++); console.log(i);` — output?
> 3. `var x = 1; { var x = 2; } console.log(x);` — output?

---

## 6. Brute force — walked through

### Wrong attempt 1: "var x in `if (false)` doesn't exist"
Wrong. Declaration is hoisted; only assignment is skipped.

### Wrong attempt 2: "var is block-scoped like let"
Function-scoped. Ignores block boundaries.

### Wrong attempt 3: read top-to-bottom assuming C-style scope
JS predates block scope (for var). Apply two-phase model.

---

## 7. The unlocking insight

> **`var` declarations register in the function's Variable Environment during creation phase, regardless of which block they're written in. Only the assignment runs in execution order.**

Three properties:

1. **`var` is function-scoped** — ignores blocks.
2. **Declaration hoisted at creation** — bound to `undefined`.
3. **Assignment runs at execution** — may not run if guarded by `if (false)`.

---

## 8. Solution (annotated)

```js
function demo() {
  // CREATION phase: VE = { a: undefined, i: undefined }
  // (var a and var i are scanned out of nested blocks)

  console.log(a);                                                     // step 1: undefined (hoisted)

  if (true) {
    var a = 1;                                                         // step 2: a = 1 (VE update)
    let b = 2;                                                         // block-scoped to if
  }

  console.log(a);                                                     // step 3: 1
  try {
    console.log(b);                                                    // ReferenceError (let-scoped)
  } catch (e) {
    console.log('b not defined');
  }

  for (var i = 0; i < 2; i++) {}
  console.log(i);                                                     // step 4: 2 (i in f's VE)
}

demo();
// Output:
// undefined
// 1
// b not defined
// 2
```

**Try it yourself**

```js
// var skips false branch but binding still exists
function g() {
  if (false) {
    var x = 1;
  }
  console.log(typeof x);                                              // 'undefined' (hoisted, never assigned)
}
g();

// var leaks from try/catch
function h() {
  try { throw new Error('boom'); }
  catch (e) {
    var captured = e.message;
  }
  console.log(captured);                                              // 'boom' (var leaks)
}
h();

// var re-declared in nested block (same function): same binding
function i() {
  var x = 1;
  { var x = 2; }
  console.log(x);                                                     // 2 (same x)
}
i();
```

---

## 9. Step-by-step dry run

```
function demo() body:

CREATION phase:
  Scan all var declarations across body (ignore block boundaries).
  VE: { a: undefined, i: undefined }
  LE: { }                                                              (let b is created lazily in its block's LE)

EXECUTION phase:
  console.log(a)         → VE.a = undefined → 'undefined'
  
  enter if-block:
    block LE: { b: <uninitialized> (TDZ) }
    var a = 1            → VE.a = 1 (still f's VE, not the block's LE)
    let b = 2            → block-LE.b = 2 (block-scoped)
  exit if-block (block LE popped; b gone)
  
  console.log(a)         → VE.a = 1 → '1'
  console.log(b) (in try) → b not in current scope → ReferenceError
  
  for-loop:
    var i = 0            → VE.i = 0
    iterations...
    after exit: VE.i = 2
  
  console.log(i)         → VE.i = 2 → '2'
```

---

## 10. Common confusion + traps

1. **`var` in `if (false)` doesn't exist** — wrong; binding hoisted.
2. **`var` is block-scoped** — function-scoped.
3. **`for (var i)` is fresh per iter** — no, one shared (loop-closure bug).
4. **`switch` cases share scope** — yes; `var` in case 1 visible in case 2.
5. **`try/catch` block scope for var** — no, var leaks out.
6. **`typeof var-in-block-before-assign`** — `'undefined'` (safe, hoisted).
7. **Module-top `var` attaches to `globalThis`** — only in scripts; not ESM.

---

## 11. Senior follow-ups & variants

### Variant 1 — `let` same shape
Replace every var with let; first log throws TDZ ReferenceError.

### Variant 2 — `switch` case bug
`switch (x) { case 1: var v = 1; case 2: console.log(v); }` — v leaks; bug.

### Variant 3 — `var` in nested function
Shadows outer var only in inner function's VE; outer untouched.

### Variant 4 — Loop-closure bug
`for (var i)` shares one i — all closures see final value.

### Variant 5 — Babel transpilation
Babel emits renamed `var` for `let` when targeting ES5, preserving block semantics.

---

## 12. How to think aloud

> "JS has two execution phases: creation (hoist) and execution (run). `var` is function-scoped, so the engine scans the entire function body during creation — IGNORING block boundaries — and registers every `var` name in the Variable Environment as `undefined`. The assignment runs at execution time, so `if (false) { var x = 1; }` STILL creates `x` (as `undefined`) but skips the `= 1`. `let`/`const` are different — block-scoped, in TDZ during creation. Whiteboard trick: draw VE (function-scoped vars) and LE (block-scoped lets) separately. Trap: 'var in if(false) is undeclared' (wrong); 'var is block-scoped' (function-scoped); for-loop counter persists after loop exit."

---

## 13. 60-second revision

> - **`var`** hoisted to nearest **function/module/script** (not block).
> - **`let`/`const`/`class`** hoisted to nearest **block**.
> - **Creation:** var → `undefined`; let/const → TDZ.
> - **`var` ignores** if, for, while, try, bare {}. Stops at function boundary.
> - **`for (var i)` counter persists** after loop exit (in enclosing scope).
> - **`try/catch` doesn't block var** — leaks out.
> - **Whiteboard:** VE for vars; LE for lets per block.
> - **Trap:** "`var` in `if(false)` is undeclared"; var is block-scoped; switch case bug.

---

**Related:** [hoisting-in-javascript.md](./hoisting-in-javascript.md) · [let-vs-var-differences.md](./let-vs-var-differences.md) · [let-in-for-loop-binding.md](./let-in-for-loop-binding.md) · [hoisting-in-try-catch.md](./hoisting-in-try-catch.md)

**Concept primer:** [`concepts/hoisting.md`](../../concepts/hoisting.md)
