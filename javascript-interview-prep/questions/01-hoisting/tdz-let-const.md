# Temporal Dead Zone with `let` / `const`

> **Difficulty:** Medium   |   **Time:** ~15 min   |   **Prereqs:** [hoisting-in-javascript.md](./hoisting-in-javascript.md)
>
> **Source:** MDN `let` TDZ section. Canonical senior JS question.

---

## 1. Problem statement

What is the Temporal Dead Zone (TDZ)? Why do `let`/`const`/`class` throw on read before initialization, even though they're hoisted?

**Verification examples**

| Snippet                                              | Result                                                 |
|------------------------------------------------------|---------------------------------------------------------|
| `console.log(x); let x = 5;`                          | `ReferenceError: Cannot access 'x' before initialization` |
| `console.log(typeof x); let x = 5;`                   | THROWS (typeof not safe in TDZ)                        |
| `console.log(typeof y);` (truly undeclared)           | `'undefined'` (typeof SAFE for undeclared)             |
| `const z;`                                            | `SyntaxError` (const requires initializer)             |
| `let a = 1; let a = 2;` (same scope)                  | `SyntaxError` (redeclaration)                          |

**Constraints**
- `let`/`const`/`class` ARE hoisted — just uninitialized.
- TDZ = window from block start to declaration line.
- ANY access during TDZ throws (read, write, typeof).
- `var` skips TDZ entirely.

---

## 2. Plain-English restatement

When you write `let x = 5` inside a block, the binding `x` exists from the moment the block opens, but holds an internal "uninitialized" marker. Any code inside the block that touches `x` BEFORE the `let x = 5` line throws ReferenceError. That window is the **Temporal Dead Zone**.

---

## 3. Why this matters in interviews

Backend engineers from typed languages assume "declared but unassigned" means `null`. JS broke that with ES6. Tests whether you know the **mechanism** (hoisted-but-uninitialized) vs the **symptom** (throws).

---

## 4. Mental model

```
   Three states per binding:
   ┌─────────────────────────────────────────────────────────┐
   │ 1. NOT DECLARED                                          │
   │    Identifier doesn't exist anywhere in reachable scope. │
   │    Access → ReferenceError: x is not defined             │
   │    typeof → 'undefined' (SAFE)                            │
   ├─────────────────────────────────────────────────────────┤
   │ 2. DECLARED BUT IN TDZ                                   │
   │    Binding exists, holds <uninitialized> marker.         │
   │    Access (read/write/typeof) → ReferenceError:         │
   │      Cannot access 'x' before initialization              │
   │    Only for let/const/class.                              │
   ├─────────────────────────────────────────────────────────┤
   │ 3. INITIALIZED                                            │
   │    Normal read/write semantics.                           │
   └─────────────────────────────────────────────────────────┘

   var skips state 2 (goes directly from undeclared → undefined at creation).
   let/const/class traverse all three.

   TDZ spans block-start to declaration line:
   {
     // TDZ for x BEGINS here
     console.log(x);        // throws — TDZ
     let x = 1;             // TDZ for x ENDS here
     console.log(x);        // 1
   }
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Is `let` hoisted? Why does it throw if so?
> 2. Does `typeof undeclaredVar` throw? `typeof letInTDZ`?
> 3. Why is `function f() { return x; } let x = 5; f();` legal?

---

## 6. Brute force — walked through

### Wrong attempt 1: "let isn't hoisted"
Wrong. It IS — just uninitialized. The error message proves it: "Cannot access 'x' before initialization" means the binding exists.

### Wrong attempt 2: `typeof` is always safe
Throws on TDZ. Only safe for genuinely undeclared identifiers.

### Wrong attempt 3: TDZ is spatial (source position)
Temporal — depends on execution time. `function f() { return x; } let x; f();` works because by the time `f` runs, TDZ has ended.

---

## 7. The unlocking insight

> **`let`/`const`/`class` hoist a binding into Lexical Environment but mark it `<uninitialized>` until the declaration line runs. Any access during that window throws ReferenceError. Three states: not-declared, TDZ, initialized. `var` skips TDZ.**

Three properties:

1. **Hoisted but uninitialized** — binding exists; value doesn't.
2. **TDZ is temporal** — time-of-execution, not source-position.
3. **`typeof` unsafe** — throws on TDZ; only safe for undeclared.

---

## 8. Solution (annotated)

```js
function demo() {
  // BLOCK START — Lexical Environment created.
  // Bindings: { x: <uninitialized>, y: <uninitialized> }
  // (let and const are hoisted but in TDZ)

  try {
    console.log(typeof x);                                            // step 1: typeof unsafe
  } catch (e) {
    console.log('TDZ trap:', e.message);                              // "Cannot access 'x' before initialization"
  }

  let x = 10;                                                          // step 2: TDZ for x ENDS
  const y = 20;                                                        // step 3: TDZ for y ENDS

  console.log(x, y);                                                    // 10 20

  console.log(typeof notDeclared);                                      // step 4: 'undefined' (SAFE)
}

demo();
```

**Try it yourself**

```js
// TDZ is temporal, not spatial
function lookup() { return val; }
let val = 42;
lookup();                                                              // 42 — TDZ already ended

// const requires initializer
const a;                                                                // SyntaxError

// Redeclaration not allowed in same scope
let b = 1;
let b = 2;                                                              // SyntaxError

// But OK across blocks
let c = 1;
{ let c = 2; console.log(c); }                                          // 2 (inner)
console.log(c);                                                         // 1 (outer)

// const objects are mutable; binding is const
const arr = [];
arr.push(1);                                                            // OK
arr = [2];                                                              // TypeError (assign to const)
```

---

## 9. Step-by-step dry run

```
Block entry (function demo's body):

CREATION phase (LE):
  x → <uninitialized>
  y → <uninitialized>

EXECUTION:
  Line: typeof x (inside try)
    Engine resolves x → finds binding → <uninitialized> → THROW
    catch: prints 'TDZ trap: Cannot access x before initialization'

  Line: let x = 10
    Transition x from <uninitialized> → 10
    TDZ for x ENDS.

  Line: const y = 20
    Transition y from <uninitialized> → 20
    TDZ for y ENDS.

  Line: console.log(x, y) → resolves both → 10, 20.

  Line: typeof notDeclared
    Resolve notDeclared → not in any scope.
    typeof on undeclared identifier → 'undefined' (SAFE, no throw).
    Print 'undefined'.
```

---

## 10. Common confusion + traps

1. **"let isn't hoisted"** — wrong; just uninitialized.
2. **`typeof` safe on `let`** — throws.
3. **TDZ is spatial** — temporal; depends on execution time.
4. **`switch` cases share scope** — `let` in one case is in TDZ in earlier cases. Wrap in `{}`.
5. **Redeclare with `let`** — `SyntaxError` at parse time.
6. **Top-level `let` attaches to globalThis** — no (unlike `var` in scripts).
7. **Distinguish "not defined" from "before initialization"** — different errors → different root causes.

---

## 11. Senior follow-ups & variants

### Variant 1 — TDZ in default parameters
`function f(a = b, b) {}; f()` throws — `a`'s default reads `b` in TDZ.

### Variant 2 — `class` TDZ
`new Foo(); class Foo {}` throws TDZ (not "not a constructor"). Same hoist behavior as `let`.

### Variant 3 — Circular import TDZ
In ESM, if A imports `x` from B while B imports from A, accessing `x` before B's evaluation completes throws TDZ.

### Variant 4 — `for` loop fresh binding
`for (let i = 0; ...)` creates new `i` per iteration. Closures over `let` work; `var` doesn't.

### Variant 5 — Switch case wrapping
`switch (x) { case 1: { let y = 1; ... break } case 2: ... }` — `{}` per case isolates TDZ.

---

## 12. How to think aloud

> "Three states per binding: not-declared, TDZ, initialized. `var` skips TDZ — goes directly from undeclared to undefined at creation. `let`/`const`/`class` traverse all three: hoisted into Lexical Environment as `<uninitialized>`, transition to value at declaration line. Any access during TDZ — read, write, typeof — throws `ReferenceError: Cannot access X before initialization`. Distinct from "not defined" (truly undeclared). `typeof` is unsafe on TDZ (only safe for undeclared). Top-level `let`/`const` don't attach to globalThis. Class TDZ throws "before initialization", not "not a constructor". Trap: 'let isn't hoisted'; typeof safe; conflating two ReferenceError types."

---

## 13. 60-second revision

> - **`let`/`const`/`class`** hoisted to LE as `<uninitialized>`.
> - **TDZ** = window from block start to declaration line.
> - **Any TDZ access throws** `ReferenceError: Cannot access X before initialization`.
> - **`var` skips TDZ** (initialized to `undefined` at creation).
> - **`typeof` unsafe** on TDZ; safe only for truly undeclared.
> - **`const` requires initializer**; objects still mutable.
> - **Three states:** not-declared / TDZ / initialized.
> - **Class TDZ throws** (not "not a constructor"); same as `let`.
> - **Trap:** "let isn't hoisted"; typeof safe; spatial-not-temporal.

---

**Related:** [hoisting-in-javascript.md](./hoisting-in-javascript.md) · [typeof-on-tdz-variable.md](./typeof-on-tdz-variable.md) · [tdz-with-default-parameter.md](./tdz-with-default-parameter.md) · [class-hoisting.md](./class-hoisting.md) · [let-vs-var-differences.md](./let-vs-var-differences.md)

**Concept primer:** [`concepts/hoisting.md`](../../concepts/hoisting.md)
