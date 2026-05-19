# TDZ with default parameters

> **Difficulty:** Medium-Senior   |   **Time:** ~12 min   |   **Prereqs:** [tdz-let-const.md](./tdz-let-const.md)
>
> **Source:** ES2015 default parameter semantics. Stripe, Atlassian, Razorpay output-prediction trivia.

---

## 1. Problem statement

Default parameter expressions live in their own scope. Combined with `let`/`const` TDZ semantics, you get surprising errors.

**Verification examples**

| Setup                                              | Result                                              |
|----------------------------------------------------|------------------------------------------------------|
| `function f(a, b = a) { return [a, b] }; f(2)`     | `[2, 2]` (b uses earlier param a)                   |
| `function f(a = b, b = 1) { ... }; f()`            | `ReferenceError` (b in TDZ when a evaluates)        |
| `function f(x = x) { ... }; f()`                   | `ReferenceError` (self-ref in param scope TDZ)     |
| `let n = 1; function f(n = n) { ... }; f()`        | `ReferenceError` (LOCAL n shadows outer; LOCAL in TDZ)|
| Destructuring `function ({a = b, b = 1}) { ... }`  | Same order-sensitive TDZ rules                       |

**Constraints**
- Params live in **separate parameter scope** from body scope.
- Left-to-right initialization; later params unavailable to earlier defaults.
- Self-reference in default → TDZ (local shadows outer; local in TDZ).
- Destructuring defaults follow same rules.

---

## 2. Plain-English restatement

Each function call creates a parameter scope. All params are declared but uninitialized (TDZ) at entry. They initialize in left-to-right order. A default expression can reference EARLIER params; referencing later or self → TDZ error.

---

## 3. Why this matters in interviews

Tests TDZ depth beyond the canonical `let x = x` case. Spec-level scope-chain reasoning.

---

## 4. Mental model

```
   function f(a = expr1, b = expr2) { /* body */ }
   
   At each call, TWO scopes:
   
   ┌─────────── Parameter Scope ───────────┐
   │ a: <uninitialized>                     │
   │ b: <uninitialized>                     │
   └───────────────────────────────────────┘
              ↓ encloses
   ┌─────────── Body Scope ─────────────────┐
   │ local lets, vars, etc.                 │
   └───────────────────────────────────────┘
   
   Per-call evaluation:
   1. Enter parameter scope; all params in TDZ.
   2. For each param in order:
        if arg provided → init from arg.
        else → evaluate default in parameter scope (sees earlier params; later in TDZ).
   3. Enter body scope; body runs.
   
   TRAPS:
   - function f(a = b, b = 1)  → evaluating a's default reads b (still TDZ) → throw.
   - function f(x = x)         → x is LOCAL param; reading own default reads LOCAL x (TDZ) → throw.
                                  (NOT outer x — shadowing kicks in at param-scope entry.)
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. `function f(a = b, b = 1) {}; f()` — throws or returns?
> 2. `let outer = 5; function f(x = outer) { return x }; f()` — output?
> 3. `function f(x = x) {}; f()` — throws or uses outer x?

---

## 6. Brute force — walked through

### Wrong attempt 1: "params are like var"
WRONG — params behave like `let` (TDZ-aware).

### Wrong attempt 2: "defaults evaluated once at definition"
WRONG — per call, in parameter scope, at call time.

### Wrong attempt 3: "f(x = x) uses outer x"
WRONG — local x shadows; reads local in TDZ.

---

## 7. The unlocking insight

> **Params have their own scope. All params declared TDZ at entry; initialize left-to-right. Default expression can read earlier params; later/self → TDZ error. Destructuring defaults follow same rules.**

Three properties:

1. **Parameter scope** is separate from body scope.
2. **Left-to-right init** with per-param TDZ.
3. **Self-reference** is TDZ — local param shadows outer same-name.

---

## 8. Solution (annotated)

```js
// Forward references OK
function ok(a, b = a) {                                                // step 1: b sees earlier a
  return [a, b];
}
ok(2);                                                                 // [2, 2]

// Backward reference fails
function bad1(a = b, b = 1) {                                          // step 2: a's default reads b → TDZ
  return [a, b];
}
try { bad1(); } catch (e) { console.log(e.message); }                  // 'Cannot access b before initialization'

// Self-reference fails
function bad2(x = x) {                                                 // step 3: local x shadows; LOCAL in TDZ
  return x;
}
try { bad2(); } catch (e) { console.log(e.message); }

// Outer shadow gotcha
let n = 1;
function bad3(n = n) {                                                  // step 4: LOCAL n shadows outer
  return n;
}
try { bad3(); } catch (e) { console.log(e.message); }                   // throws — local n in TDZ

// Outer reference (NOT same name) OK
function ok2(m = n) {                                                   // step 5: m references outer n
  return m;
}
ok2();                                                                  // 1
```

**Try it yourself**

```js
// Destructuring defaults follow same rules
function f({a = 1, b = a} = {}) { return [a, b]; }
f();                                                                    // [1, 1]
f({a: 3});                                                              // [3, 3]
f({b: 5});                                                              // [1, 5]

// Order matters in destructuring too
function bad({a = b, b = 1} = {}) {}
try { bad(); } catch (e) { console.log(e.message); }                    // TDZ on b

// `function.length` reports params BEFORE first default
function g(a, b = 1, c) {}
g.length;                                                               // 1
```

---

## 9. Step-by-step dry run

```js
function tdz(a = b, b = 1) { return [a, b]; }
tdz();
```

```
Per-call evaluation:

1. Enter parameter scope:
   a: <uninitialized> (TDZ)
   b: <uninitialized> (TDZ)

2. Evaluate param a:
   argument provided? no
   default expression: `b`
   resolve b in parameter scope → b is <uninitialized> → THROW ReferenceError.

3. (never reached) Body never runs.
```

For `function f(x = x) { return x; }; f()`:

```
1. Enter parameter scope:
   x: <uninitialized> (TDZ)

2. Evaluate param x:
   argument provided? no
   default expression: `x`
   resolve x → LOCAL x (parameter scope), in TDZ → THROW.

NOTE: shadowing rule means RHS `x` resolves to the LOCAL parameter x,
      NOT any outer x. Local x is in TDZ → error.
```

---

## 10. Common confusion + traps

1. **Params like `var`** — like `let` (TDZ).
2. **Defaults evaluated at definition** — per call.
3. **`f(x = x)` uses outer x** — local shadows; throws.
4. **Order doesn't matter** — it does (left-to-right).
5. **Arrow functions different** — same rules.
6. **`arguments` synced with params under defaults** — separate in strict.
7. **Rest + default combo** — `function f(...args, x = 1)` is SyntaxError (rest must be last).

---

## 11. Senior follow-ups & variants

### Variant 1 — Class field initializers
Same TDZ rules apply in class body.

### Variant 2 — Computed default expressions
Any expression allowed (function call, ternary, etc.); can throw.

### Variant 3 — `function.length`
Defaults reduce length; `function f(a, b = 1, c) {}.length === 1`.

### Variant 4 — `arguments` divergence
Strict mode with defaults: `arguments` doesn't sync with params.

### Variant 5 — Destructuring TDZ
`function ({a = b, b = 1})` — order-sensitive.

---

## 12. How to think aloud

> "Each call creates a parameter scope separate from body scope. All params declared as `<uninitialized>` (TDZ) at entry. Then initialize left-to-right: if arg provided, init from arg; else evaluate default IN PARAMETER SCOPE. Default can reference earlier params (already initialized) but NOT later ones (still TDZ) or itself (local shadows outer; local TDZ). So `function f(a = b, b = 1)` throws because `b` is TDZ when `a`'s default evaluates. `function f(x = x)` throws because the local `x` shadows any outer `x`, and the RHS resolves to the local TDZ binding. Fix: order params so defaults reference only earlier ones; never self-reference. Destructuring follows same rules. Trap: 'params like var'; 'defaults evaluated at definition'; 'f(x = x) uses outer x'."

---

## 13. 60-second revision

> - **Params live in separate parameter scope** from body scope.
> - **All params TDZ at entry**; init left-to-right.
> - **Default can read earlier params** only; later/self → TDZ error.
> - **`f(x = x)`** → throws (local shadows outer; local TDZ).
> - **`f(a = b, b = 1)`** → throws (b TDZ when a evaluates).
> - **Destructuring defaults** follow same order rules.
> - **`function.length`** = params before first default.
> - **Trap:** "params like var"; "defaults at definition"; "self-ref uses outer".

---

**Related:** [tdz-let-const.md](./tdz-let-const.md) · [hoisting-and-scoping.md](./hoisting-and-scoping.md) · [`02-closures/private-data-counter.md`](../02-closures/private-data-counter.md)

**Concept primer:** [`concepts/hoisting.md`](../../concepts/hoisting.md)
