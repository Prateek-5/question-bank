# `var` hoisting output prediction

> **Difficulty:** Easy-Medium   |   **Time:** ~10 min   |   **Prereqs:** [hoisting-in-javascript.md](./hoisting-in-javascript.md)
>
> **Source:** #1 warm-up question on JS-rusty backend screens.

---

## 1. Problem statement

```js
function f() {
  console.log(a);
  var a = 2;
  console.log(a);
}
var a = 1;
f();
```

What does this print? Explain via the two-phase execution model.

**Answer:** `undefined`, then `2`.

**Verification examples**

| Variation                                            | Output                                  |
|------------------------------------------------------|------------------------------------------|
| Original                                              | `undefined, 2`                          |
| Replace inner `var a = 2` with `let a = 2`            | `ReferenceError` (TDZ on first log)     |
| Add `function a() {}` after var inside f              | tricky — function decl wins at creation |
| Move outer `var a = 1` to inside f                    | same: inner var shadows                  |

**Constraints**
- `var` is function-scoped (not block).
- Inner `var` shadows from line 1 of function (hoisted at creation).
- Hoisted to `undefined`; assignment runs at execution time.

---

## 2. Plain-English restatement

The inner `var a` is hoisted to the top of `f`'s VE as `undefined`. So when `console.log(a)` runs first, it reads `undefined` (NOT the outer `a = 1`, because the inner shadow already exists). Then `var a = 2` runs the assignment. Second log: `2`.

---

## 3. Why this matters in interviews

The 60-second test of your engine mental model. Fumbling it signals you'll fumble closures, TDZ, and async ordering.

---

## 4. Mental model

```
   Two-pass execution per scope:

   PASS 1 — CREATION (build VE)
     scan all var declarations → bind to undefined
     scan all function decls   → bind to full fn object

   PASS 2 — EXECUTION (run code)
     assignments update bindings
     identifier reads walk scope chain

   For our snippet:

   Global VE after creation:
     a → undefined
     f → <function f>

   f's VE after creation:
     a → undefined         ← inner var a hoisted; SHADOWS outer

   Execution:
     var a = 1            global.VE.a = 1
     f() called → push f's EC
       console.log(a)     resolves to f.VE.a = undefined → print
       var a = 2          f.VE.a = 2 (declaration already hoisted; just assigns)
       console.log(a)     f.VE.a = 2 → print
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Replace `var a = 2` with `let a = 2` — what changes?
> 2. Why doesn't `console.log(a)` print `1`?
> 3. What does `function f(a) { console.log(a); var a = 2; ...} f(7)` print?

---

## 6. Brute force — walked through

### Wrong attempt 1: "prints 1 then 2"
Lexical-scope-then-shadow without hoisting. Misses the inner `var` shadow at creation.

### Wrong attempt 2: "throws — `a` not defined yet"
That's `let`/TDZ behavior. `var` initializes to `undefined`.

### Wrong attempt 3: forget the two phases
Misses why the inner `var` shadows from line 1, not from line 2.

---

## 7. The unlocking insight

> **Inner `var` is hoisted at creation phase to `undefined`. From line 1 of `f`, the inner binding shadows the outer. First log reads `undefined`. Then assignment sets to 2. Second log reads 2.**

Three properties:

1. **Two-pass model** — creation then execution.
2. **Hoist-to-undefined** — not TDZ, not "not defined".
3. **Inner shadow from line 1** — not from declaration line.

---

## 8. Solution (annotated)

```js
var a = 1;

function f() {
  // CREATION PHASE of f's EC:
  //   VE = { a: undefined }          // inner var a hoisted
  //   OuterEnv → global { a: 1, f: <fn> }
  //
  // EXECUTION PHASE:
  console.log(a);                                                      // step 1: reads f.VE.a → undefined
  var a = 2;                                                            // step 2: declaration was already hoisted; assigns only
  console.log(a);                                                       // step 3: reads f.VE.a → 2
}

f();
// Output: undefined, 2
```

**Try it yourself**

```js
// Variant 1: replace var with let
function g() {
  console.log(a);                                                       // ReferenceError (TDZ)
  let a = 2;
}
let a = 1;
g();

// Variant 2: parameter + var combo
function h(a) {
  console.log(a);   // prints argument (e.g., 7)
  var a = 2;        // re-declare; no-op on existing binding
  console.log(a);   // 2
}
h(7);
// Parameters are initialized BEFORE body's var redeclarations.

// Variant 3: function decl beats var
function i() {
  console.log(typeof x);   // 'function' — function decl wins at creation
  var x;
  function x() {}
  console.log(typeof x);   // 'function' still — var without initializer is no-op
}
i();
```

---

## 9. Step-by-step dry run

```
Global EC — Creation phase:
  a → undefined           (hoisted var)
  f → <function f>        (hoisted function decl)

Global EC — Execution phase:
  var a = 1                 global.VE.a = 1
  f()                       push f's EC

f's EC — Creation phase:
  a → undefined             (inner var a hoisted; shadows outer)
  OuterEnv → global

f's EC — Execution phase:
  console.log(a)            resolves f.VE.a = undefined → print 'undefined'
  var a = 2                 f.VE.a = 2 (declaration already hoisted; assigns)
  console.log(a)            f.VE.a = 2 → print 2

Pop f's EC. Global a still 1 (untouched).

Output: undefined, 2
```

---

## 10. Common confusion + traps

1. **"declarations move to the top"** — nothing physically moves; engine pre-registers.
2. **Inner `var` shadows from line 2** — no, from line 1 (creation phase).
3. **First log prints outer `a`** — no, inner shadow exists from creation.
4. **Two `var` in same scope** — silent re-declare; second initializer wins.
5. **`var` inside `if` is block-scoped** — function-scoped; leaks.
6. **Parameter + var combo** — params init first; var without initializer is no-op.
7. **Function decl + var same name** — function decl wins at creation.

---

## 11. Senior follow-ups & variants

### Variant 1 — Replace inner `var` with `let`
First log throws TDZ ReferenceError. Outer `a = 1` is shadowed but inaccessible.

### Variant 2 — Parameter shadowing
`function f(a) { console.log(a); var a = 2; }; f(7)` → `7, 2`. Param initialized first.

### Variant 3 — Function decl + `var` same name
`function g() { console.log(typeof g); var g; function g(){} console.log(typeof g); }` → `function, function`. Function wins; var without initializer is no-op.

### Variant 4 — Nested fn shadowing
Three nested fns each with `var x`; each `console.log(x)` resolves to nearest VE.

### Variant 5 — Loop closure bug
`for (var i = 0; i < 3; i++) setTimeout(() => log(i))` → `3, 3, 3` (shared i).

---

## 12. How to think aloud

> "Two-phase model: creation registers bindings, execution runs code. f's creation: inner `var a` hoisted to `undefined`, shadowing the outer `a`. f's execution: first `console.log(a)` resolves to f's local `a` (undefined), then `var a = 2` runs the assignment (declaration already hoisted), second log reads 2. Output: undefined, 2. Trap: thinking inner var shadows only from its declaration line — it shadows from line 1 (creation phase). Trap: thinking first log throws — that's `let` behavior; `var` initializes to `undefined`."

---

## 13. 60-second revision

> - **Two phases:** creation (hoist `var` → `undefined`) → execution (assign).
> - **Inner `var` shadows from line 1** of function, not from declaration line.
> - **Reading hoisted `var` before assignment** → `undefined` (NEVER throws).
> - **`var` is function-scoped** (not block).
> - **Whiteboard:** draw VE table per EC.
> - **Output of canonical snippet:** `undefined, 2`.
> - **Trap:** "prints 1, 2" (no — inner shadow); "throws" (no — that's `let`/TDZ).

---

**Related:** [hoisting-in-javascript.md](./hoisting-in-javascript.md) · [hoisting-and-scoping.md](./hoisting-and-scoping.md) · [function-declaration-vs-expression-hoisting.md](./function-declaration-vs-expression-hoisting.md) · [var-in-block.md](./var-in-block.md)

**Concept primer:** [`concepts/hoisting.md`](../../concepts/hoisting.md)
