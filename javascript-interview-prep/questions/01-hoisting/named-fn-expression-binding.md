# Named function expression — inner binding

> **Difficulty:** Medium   |   **Time:** ~10 min   |   **Prereqs:** [function-declaration-vs-expression-hoisting.md](./function-declaration-vs-expression-hoisting.md)
>
> **Source:** ECMA-262 FunctionExpression evaluation. Senior screens output-prediction.

---

## 1. Problem statement

`const f = function inner() { ... }` creates TWO bindings: outer `f` and inner `inner` (only visible inside).

**Verification examples**

| Setup                                              | Result                                             |
|----------------------------------------------------|-----------------------------------------------------|
| `const f = function bar() { return bar };`         | `f()` returns the function; `bar` outside → ReferenceError |
| `f.name`                                           | `'bar'` (inner name)                                |
| Recursion using inner name                         | safe even if outer var is reassigned                |
| Reassign inner name in strict                      | TypeError (read-only)                                |
| Class expression analog                            | `const C = class Inner { ... }` — Inner local       |

**Constraints**
- Inner name is **read-only** inside the function (strict throws on write).
- Inner name **not visible outside** the function body.
- Useful for safe recursion (immune to outer reassignment).
- Better stack traces (named, not `<anonymous>`).

---

## 2. Plain-English restatement

When you write `const f = function bar() { ... }`, the function has a "backstage" name `bar` callable only inside its body. Outside, only `f` works. `bar` is read-only — protects recursive references from outer-variable reassignment.

---

## 3. Why this matters in interviews

Hoisting nuance + self-recursion patterns + spec literacy. Tests whether you know `arguments.callee` is banned and named function expressions are the replacement.

---

## 4. Mental model

```
   const f = function bar() { ... };
   
   ┌─── Outer scope ───────────────────────┐
   │ f: <function>                          │  (assignable; bound by const here)
   │ bar: NOT visible                       │
   │   ┌─── Function's scope (when called) ┐│
   │   │ bar: <function> (read-only)       ││  ← inner binding
   │   │   body executes here              ││
   │   └────────────────────────────────────┘│
   └────────────────────────────────────────┘
   
   When the function is invoked, JS prepends a scope with `bar` (read-only)
   BEFORE the body's local scope. That's how `bar` is callable inside but
   invisible outside.

   USES:
   - Safe recursion (outer var can be reassigned without breaking).
   - Better stack traces (function.name = 'bar').
   - Module-private state (NFE in IIFE).
   
   TRAPS:
   - Reassigning inner name in strict → TypeError.
   - Confusing with function declaration (which IS visible outside).
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. After `const f = function bar() { return bar }`, can you call `bar()` outside?
> 2. What is `f.name`?
> 3. Why is NFE safer than `const fact = function(n) { return fact(n-1); }` for recursion?

---

## 6. Brute force — walked through

### Wrong attempt 1: "inner name visible outside"
No — function-scoped to its body.

### Wrong attempt 2: "anonymous functions can recurse via the outer var"
They can, but break if outer var is reassigned. NFE is safer.

### Wrong attempt 3: "inner name is writable"
Read-only in strict; assigning throws TypeError.

---

## 7. The unlocking insight

> **NFE has TWO bindings: outer (assignable) and inner (read-only, visible only inside function body). Use inner name for safe recursion + better stack traces. Replaces banned `arguments.callee`.**

Three properties:

1. **Two bindings** — outer var (mutable) + inner name (read-only).
2. **Inner scoped to function body** — invisible outside.
3. **`f.name`** = inner name (debugging benefit).

---

## 8. Solution (annotated)

```js
// Pattern 1: safe recursion
const fact = function fact_(n) {                                       // step 1: inner fact_
  return n === 0 ? 1 : n * fact_(n - 1);                                // safe self-ref
};
const alias = fact;
fact = null;                                                            // wait — const can't reassign
// Use let to demonstrate the safety
let factLet = function factInner(n) {
  return n === 0 ? 1 : n * factInner(n - 1);                            // safe — uses inner
};
const f2 = factLet;
factLet = null;                                                         // outer reassigned
f2(5);                                                                  // 120 — still works via inner

// Pattern 2: better stack traces
const debounce = function debounceInner(fn, ms) {                      // step 2: named for trace
  let timer;
  return function debounceWrapper(...args) {                            // step 3: named inner fn
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
};

// Pattern 3: NFE in IIFE for private state
const counter = (function counterImpl() {                              // step 4: named IIFE
  let n = 0;
  return { inc: () => ++n, peek: () => n };
})();
counter.inc(); counter.inc(); counter.peek();                           // 2
```

**Try it yourself**

```js
// Inner name not visible outside
const f = function bar() { return bar; };
f();                                                                    // returns the function
try { bar(); } catch (e) { console.log(e.message); }                    // 'bar is not defined'

// f.name reflects inner name
console.log(f.name);                                                    // 'bar'

// Class expression analog
const Cat = class FelineImpl {
  static who() { return FelineImpl.name; }                              // inner visible inside
};
Cat.who();                                                              // 'FelineImpl'
try { FelineImpl; } catch (e) { console.log(e.message); }               // 'FelineImpl is not defined'

// Inner name is read-only (strict mode)
const g = function self() {
  'use strict';
  self = 99;                                                            // TypeError
  return self;
};
try { g(); } catch (e) { console.log(e.message); }                      // 'Assignment to constant'
```

---

## 9. Step-by-step dry run

```
const a = function inner(n) {
  if (n === 0) return 'done';
  return inner(n - 1);
};
a(2);
inner;     // ReferenceError outside
```

```
Outer scope creation:
  a: <uninitialized> (TDZ; const)

Evaluate RHS:
  Create function object:
    name: 'inner'
    [[Environment]] holds outer scope
    Inside function: prepend a scope with `inner` (read-only) pointing to this fn.
  Bind a := this function. TDZ ends.
  a.name === 'inner'.

Call a(2):
  Push function's EC.
  Scope chain: [inner-binding scope] → [body local scope] → [outer]
  Body: n=2, not 0, return inner(1)
    Resolve inner → finds in inner-binding scope → recursive call.
  ...

`inner` lookup in outer scope:
  Walk outer.LE → only has `a`. Not found.
  Walk further → not found.
  ReferenceError.
```

---

## 10. Common confusion + traps

1. **Inner name visible outside** — no, function-scoped.
2. **Inner name writable** — read-only in strict.
3. **`arguments.callee` is fine** — banned in strict.
4. **NFE adds another `function.name`** — the inner name IS the name.
5. **Anonymous functions can't recurse** — they can via outer var (unsafe if reassigned).
6. **Class expression's inner name** — same pattern, local to body.
7. **NFE hoists outer name** — no, only outer var hoists per its declarator.

---

## 11. Senior follow-ups & variants

### Variant 1 — Class expression
`const C = class Inner {...}` — `Inner` only visible inside class body.

### Variant 2 — Object-method shorthand
`{ method() {} }` — function name is `'method'`.

### Variant 3 — Generator NFE
`function* gen() {}` — same rules.

### Variant 4 — Async NFE
`async function self() {}` — same rules.

### Variant 5 — Default-export named
`export default function name() {}` — name is local; outside, the export is `default`.

---

## 12. How to think aloud

> "Named function expression: `function name() {}` on the RHS. Two bindings: the OUTER variable (assignable per its declarator) and the INNER name (read-only, only visible inside the function body via a prepended scope). Uses: safe recursion (inner name immune to outer reassignment), better stack traces (`function.name` = inner), module-private state (NFE in IIFE). Replaces banned `arguments.callee`. Class expressions follow the same pattern: `const C = class Inner {}` — `Inner` is local. Inner is read-only in strict — assigning throws TypeError. Trap: 'inner visible outside'; 'inner writable'; treating NFE like function declaration."

---

## 13. 60-second revision

> - **NFE:** `const f = function bar() {}` — outer `f` + inner `bar`.
> - **Inner is read-only**, visible ONLY inside function body.
> - **Outer follows declarator** (var/let/const) for hoisting.
> - **`f.name`** reflects inner name (debugging).
> - **Safe recursion** — inner name immune to outer reassignment.
> - **Replaces** banned `arguments.callee`.
> - **Class expression analog:** `const C = class Inner {}`.
> - **Trap:** "inner visible outside"; "inner writable"; treating like declaration.

---

**Related:** [function-declaration-vs-expression-hoisting.md](./function-declaration-vs-expression-hoisting.md) · [class-hoisting.md](./class-hoisting.md) · [`02-closures/closures.md`](../../concepts/closures.md) · [`02-closures/private-data-counter.md`](../02-closures/private-data-counter.md)

**Concept primer:** [`concepts/hoisting.md`](../../concepts/hoisting.md), [`concepts/closures.md`](../../concepts/closures.md)
