# Hoisting in JavaScript — the two-phase execution model

> **Difficulty:** Medium   |   **Time:** ~15 min   |   **Prereqs:** [`concepts/hoisting.md`](../../concepts/hoisting.md)
>
> **Source:** Canonical opener for senior JS screens. MDN: Glossary/Hoisting.

---

## 1. Problem statement

"Explain hoisting." Cover: two-phase execution model, four kinds of hoisting (`var`, function decl, `let`/`const`/`class`, import), and the scope rules (function vs block vs module).

**Verification examples**

| Snippet                                  | Output                                  |
|------------------------------------------|------------------------------------------|
| `console.log(a); var a = 1;`             | `undefined`                              |
| `console.log(b); let b = 2;`             | `ReferenceError` (TDZ)                  |
| `greet(); function greet(){...}`         | works                                    |
| `new Foo(); class Foo {}`                | `ReferenceError` (TDZ)                  |
| `foo(); import {foo} from './x.js'`      | works (import hoists to module top)    |

**Constraints**
- **Phase 1 (creation):** scan declarations, register bindings.
- **Phase 2 (execution):** run statements top to bottom.
- `var` → `undefined`; function decl → full body; `let`/`const`/`class` → TDZ; import → live binding.
- Scope: var/function → function; let/const/class → block; import → module.

---

## 2. Plain-English restatement

The engine processes each scope in two passes. First it scans all declarations and registers bindings — `var` as `undefined`, function declarations with the full body, `let`/`const`/`class` as "uninitialized" (TDZ). Then it runs the code top to bottom. **Nothing physically moves**; the engine just pre-registers names.

---

## 3. Why this matters in interviews

Open-ended 5-min oral check on whether you understand the engine. Weak answer: "declarations move to the top." Strong: two-phase model + per-keyword behavior + per-scope rules. Backend uses: debugging stack traces, reading transpiled code, knowing what's safe before declaration.

---

## 4. Mental model

```
   Two phases per scope (script, module, function, block):

   ┌─── PHASE 1: CREATION (hoist) ───┐
   │ Scan all declarations.          │
   │ var      → VE: undefined         │
   │ function → VE: <full fn object>  │
   │ let/const/class → LE: TDZ        │
   │ import   → ModuleEnv: live link  │
   │ OuterEnv pointer set.            │
   └──────────────────────────────────┘
                ↓
   ┌─── PHASE 2: EXECUTION ──────────┐
   │ Run top-to-bottom.              │
   │ Assignments update bindings.    │
   │ let/const/class transition       │
   │   from TDZ to value.             │
   │ TDZ access → ReferenceError.    │
   └──────────────────────────────────┘

   Scope rules:
   var, function decl → enclosing FUNCTION (or script/module top)
   let, const, class  → enclosing BLOCK
   import             → top of MODULE
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Does `console.log(typeof y); let y = 5;` print `'undefined'` or throw?
> 2. Does `let` get hoisted?
> 3. What error does `new Foo(); class Foo {}` throw — TDZ or "not a constructor"?

---

## 6. Brute force — walked through

### Wrong attempt 1: "declarations move to the top"
Misleading — nothing physically moves. Engine pre-registers bindings during creation phase.

### Wrong attempt 2: "let isn't hoisted"
WRONG. It is hoisted — just sits in TDZ.

### Wrong attempt 3: "typeof is safe for any variable"
Throws on TDZ `let`/`const`. Only safe for genuinely undeclared identifiers.

---

## 7. The unlocking insight

> **Two phases per scope: creation registers bindings, execution runs code. `var` → `undefined`; function decl → full body; `let`/`const`/`class` → TDZ; import → live binding. Scope is function/block/module-specific.**

Three properties:

1. **Two phases** — creation hoists, execution runs.
2. **Per-keyword initial state** — `undefined` vs TDZ vs full body.
3. **Scope rules** differ for var vs let vs class.

---

## 8. Solution (annotated)

```js
import { helper } from './helper.js';                                // step 1: hoisted to module top

console.log(typeof fnDecl);                                           // 'function' — fully hoisted
console.log(typeof varX);                                             // 'undefined' — var hoisted
try { console.log(letY); }                                            // ReferenceError — TDZ
catch (e) { console.log('TDZ for letY'); }
try { new ClassZ(); }                                                 // ReferenceError — TDZ
catch (e) { console.log('TDZ for ClassZ'); }
helper();                                                              // works — import live binding

function fnDecl() {}                                                   // step 2: hoisted earlier
var varX = 10;
let letY = 20;
class ClassZ {}

// Output: function, undefined, TDZ for letY, TDZ for ClassZ, <helper output>
```

**Try it yourself**

```js
// var hoisting — function-scoped
function f() {
  console.log(x);   // undefined (NOT ReferenceError)
  var x = 5;
  console.log(x);   // 5
}

// let hoisting — TDZ
function g() {
  console.log(y);   // ReferenceError: Cannot access 'y' before initialization
  let y = 5;
}

// var leaks out of blocks
if (true) { var z = 1; }
console.log(z);     // 1 (leaked)

if (true) { let w = 1; }
console.log(w);     // ReferenceError (not defined)
```

---

## 9. Step-by-step dry run

```
Module body:

CREATION phase:
  helper   → ModuleEnv: <live binding>
  fnDecl   → VE: <function fnDecl>
  varX     → VE: undefined
  letY     → LE: <uninitialized> (TDZ)
  ClassZ   → LE: <uninitialized> (TDZ)

EXECUTION phase:
  1. typeof fnDecl       → 'function' (binding holds fn)
  2. typeof varX         → 'undefined' (binding holds undefined)
  3. letY access (in try)→ TDZ → ReferenceError → catch prints 'TDZ for letY'
  4. new ClassZ()        → TDZ → ReferenceError → catch prints 'TDZ for ClassZ'
  5. helper()            → resolves live binding, invokes
  6. function fnDecl(){} → no-op (already hoisted)
  7. var varX = 10       → VE.varX = 10
  8. let letY = 20       → LE.letY transitions from TDZ to 20
  9. class ClassZ {}     → LE.ClassZ transitions from TDZ to class
```

---

## 10. Common confusion + traps

1. **"let isn't hoisted"** — it IS, just in TDZ.
2. **`typeof` safe on `let`** — throws if in TDZ.
3. **Functions in blocks** — sloppy hoists to function; strict block-scopes.
4. **Function decl vs expression** — only declarations fully hoist.
5. **ESM top-level `var`** — does NOT attach to `globalThis` (unlike scripts).
6. **Function decls beat var** for same name during creation.
7. **Circular ESM imports** — late-loaded module sees other's bindings in TDZ.

---

## 11. Senior follow-ups & variants

### Variant 1 — "Walk me through what happens when this file loads"
Recite creation phase (all bindings, in order) before execution. Practice on real code.

### Variant 2 — Script vs module differences
Scripts: top-level var attaches to globalThis. Modules: strict by default, imports hoisted, no globalThis attachment.

### Variant 3 — `var` + function decl combo
`console.log(foo); var foo = 5; function foo(){}` → prints `[Function: foo]` (declaration wins at creation), then assigns 5.

### Variant 4 — TDZ scope precision
`{ tempBlock; let x = 1; }` — TDZ for x starts at block open, ends at `let x = 1` line.

### Variant 5 — `class` hoisting vs function decl
Both hoisted; class stays in TDZ until declaration line; function decl is fully usable immediately.

---

## 12. How to think aloud

> "Two phases per scope: creation registers bindings, execution runs code. During creation: `var` and function decls go in Variable Environment; `let`/`const`/`class` go in Lexical Environment as uninitialized (TDZ). Functions hoist with full body — callable from line 1. `var` initializes to `undefined`. `let`/`const`/`class` stay in TDZ until their declaration line — any access throws ReferenceError. Imports hoist to module top as live bindings. Scope: var/function → function; let/const/class → block; import → module. Trap: 'let isn't hoisted' is wrong; typeof throws on TDZ; ESM top-level var doesn't attach to globalThis."

---

## 13. 60-second revision

> - **Two phases:** creation (hoist) → execution (run).
> - **`var`** → `undefined`; **function decl** → full body; **`let`/`const`/`class`** → TDZ; **`import`** → live binding.
> - **Scope:** var/function → function; let/const/class → block; import → module.
> - **TDZ access** (read, write, `typeof`) → `ReferenceError: Cannot access X before initialization`.
> - **Function decls beat `var`** for same name during creation; runtime assignment overwrites.
> - **ESM:** top-level var does NOT attach to globalThis; strict by default.
> - **Trap:** "let isn't hoisted"; typeof safe on TDZ; functions in blocks (sloppy quirks).

---

**Related:** [hoisting-and-scoping.md](./hoisting-and-scoping.md) · [tdz-let-const.md](./tdz-let-const.md) · [let-vs-var-differences.md](./let-vs-var-differences.md) · [function-declaration-vs-expression-hoisting.md](./function-declaration-vs-expression-hoisting.md)

**Concept primer:** [`concepts/hoisting.md`](../../concepts/hoisting.md)
