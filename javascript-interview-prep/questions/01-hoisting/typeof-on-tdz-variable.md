# `typeof` on a TDZ variable

> **Difficulty:** Medium   |   **Time:** ~10 min   |   **Prereqs:** [tdz-let-const.md](./tdz-let-const.md)
>
> **Source:** ES2015 spec subtle change. Razorpay, Atlassian, Cloudflare output-prediction trap.

---

## 1. Problem statement

Pre-ES2015, `typeof x` was always safe — `'undefined'` for undeclared. ES2015 broke this for TDZ-bound names.

**Verification examples**

| Setup                                              | `typeof`                                       |
|----------------------------------------------------|-------------------------------------------------|
| `typeof x` (truly undeclared)                       | `'undefined'` (SAFE, no throw)                  |
| `typeof v; var v = 1;`                              | `'undefined'` (var hoisted)                     |
| `typeof l; let l = 1;`                              | **THROWS** ReferenceError (TDZ)                 |
| `typeof c; const c = 1;`                            | **THROWS**                                      |
| `typeof C; class C {}`                              | **THROWS**                                      |
| `typeof f; function f() {}`                         | `'function'` (fully hoisted)                    |

**Constraints**
- `typeof` is unsafe on TDZ-bound `let`/`const`/`class`.
- Only safe for: genuinely undeclared, hoisted `var`, hoisted function decl.
- Feature detection idiom broken for `let`/`const`-declared globals.

---

## 2. Plain-English restatement

`typeof someName` was the one "safe" reference pre-ES2015 — `'undefined'` even if undeclared. ES2015 added TDZ for `let`/`const`/`class`; **any reference during TDZ throws**, including `typeof`. Modern feature detection: use `typeof globalThis.X` or `'X' in globalThis`.

---

## 3. Why this matters in interviews

Spec corner case. Tests TDZ depth + feature-detection idiom literacy.

---

## 4. Mental model

```
   Binding states + typeof:
   
   ┌──────────────────┐
   │ undeclared       │  typeof → 'undefined' (SAFE; spec exception)
   ├──────────────────┤
   │ TDZ (let/const)  │  typeof → THROWS ReferenceError
   ├──────────────────┤
   │ var-undefined    │  typeof → 'undefined' (hoisted slot)
   ├──────────────────┤
   │ initialized      │  typeof → 'string'/'number'/...
   └──────────────────┘
   
   Why typeof on TDZ throws:
   - TDZ rule: any reference throws.
   - typeof is a reference operation (must resolve binding to get type).
   - Engine resolves → finds <uninitialized> → throws.
   
   Why typeof on undeclared is safe:
   - Spec explicitly allows typeof to return 'undefined' for undeclared.
   - This is the SOLE pre-ES2015 safe reference.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Does `typeof undeclared` throw?
> 2. Does `typeof letInTDZ` throw?
> 3. How do you safely feature-detect a global that might be `let`/`const`?

---

## 6. Brute force — walked through

### Wrong attempt 1: `typeof` is universally safe
WRONG post-ES2015 for TDZ.

### Wrong attempt 2: `let` not hoisted → typeof safe
`let` IS hoisted (into TDZ). `typeof` throws.

### Wrong attempt 3: typeof globalThis pattern unknown
`typeof globalThis.X` is the modern fix — property access never throws.

---

## 7. The unlocking insight

> **`typeof` is no longer universally safe. TDZ-bound names (`let`/`const`/`class` before declaration) throw. Only safe for: truly undeclared, `var`-hoisted, function-decl-hoisted. For feature detection of names that might be `let`/`const`, use `typeof globalThis.X` or `'X' in globalThis`.**

Three properties:

1. **Spec exception** for undeclared identifiers — only there `typeof` is safe.
2. **TDZ trumps** — `typeof` on TDZ throws.
3. **`globalThis` property access** never throws — safe modern idiom.

---

## 8. Solution (annotated)

```js
function demo() {
  try { console.log(typeof a); } catch (e) { console.log('a:', e.message); }
  try { console.log(typeof b); } catch (e) { console.log('b:', e.message); }
  try { console.log(typeof c); } catch (e) { console.log('c:', e.message); }
  try { console.log(typeof d); } catch (e) { console.log('d:', e.message); }
  console.log(typeof e);                                                // 'function' (hoisted)

  var a = 1;                                                            // hoisted as undefined
  let b = 2;                                                            // TDZ until here
  const c = 3;                                                          // TDZ until here
  class d {}                                                            // TDZ until here
  function e() {}                                                       // fully hoisted
}
demo();
// Output:
// a: undefined                       ← var hoisted slot
// b: Cannot access 'b' before init   ← TDZ
// c: Cannot access 'c' before init   ← TDZ
// d: Cannot access 'd' before init   ← TDZ
// function                           ← fully hoisted
```

**Try it yourself — feature detection idiom**

```js
// PRE-2015 pattern (broken if SomeLib is let/const)
if (typeof SomeLib !== 'undefined') SomeLib.init();
// ReferenceError if SomeLib is declared via let/const later in scope

// MODERN safe pattern: query globalThis
if (typeof globalThis.SomeLib !== 'undefined') globalThis.SomeLib.init();
// Property access never throws; returns undefined for missing

// Equivalent
if ('SomeLib' in globalThis) globalThis.SomeLib.init();
```

---

## 9. Step-by-step dry run

```js
console.log(typeof x);   // truly undeclared
console.log(typeof y);   // let y declared below
let y = 1;
```

```
Parse phase: collect lexical bindings
  scope has `y` as let → TDZ until `let y = 1` line.

Execution:
  line 1: typeof x
    Resolve x → no binding anywhere → SPEC: typeof returns 'undefined' (no throw).
    Print 'undefined'.
  line 2: typeof y
    Resolve y → finds let binding in TDZ → THROWS ReferenceError.
    (line 3 never reached.)
```

Feature-detection fix:

```
typeof globalThis.SomeLib
  globalThis is always defined.
  .SomeLib property access:
    if SomeLib is a let/const at module top → does NOT attach to globalThis → property is undefined.
    → typeof returns 'undefined' (safe).
  if SomeLib is a var or assigned → attaches → typeof returns actual type.
```

---

## 10. Common confusion + traps

1. **`typeof` never throws** — wrong post-ES2015.
2. **`let` hoists to undefined** — to TDZ.
3. **Pre-2015 idiom still safe** — broken for `let`/`const`.
4. **`window` everywhere** — only browsers; use `globalThis`.
5. **Dead-code elimination strips `typeof === 'undefined'`** — depends on bundler.
6. **Module-scope `let` attaches to globalThis** — no.
7. **Distinguish two ReferenceErrors:** "not defined" vs "before initialization".

---

## 11. Senior follow-ups & variants

### Variant 1 — Module vs global TDZ
Both have TDZ for `let`/`const`. ESM doesn't attach top-level to globalThis.

### Variant 2 — `typeof` on property
`typeof obj.foo` is always safe (returns `'undefined'` if not present).

### Variant 3 — Bundler quirks
Dead-code-elim may strip `typeof someLet === 'undefined'` checks; result depends on tooling.

### Variant 4 — Strict mode
Same TDZ behavior — strict doesn't change `typeof`.

### Variant 5 — Polyfill / shim patterns
`if (typeof globalThis.fetch === 'undefined') globalThis.fetch = require('node-fetch')`.

---

## 12. How to think aloud

> "Pre-ES2015, `typeof someName` was the SOLE safe reference — returned `'undefined'` even for genuinely undeclared identifiers. ES2015 added TDZ for `let`/`const`/`class`. Any reference during TDZ throws, including `typeof`, because the engine must resolve the binding to determine type — and resolution on `<uninitialized>` throws. So `typeof letInTDZ` throws ReferenceError. For modern feature detection of names that might be `let`/`const`, switch to `typeof globalThis.X !== 'undefined'` or `'X' in globalThis` — property access never throws. `var` and function-decl are safe because they hoist with `undefined` slot or full body. Trap: 'typeof never throws'; pre-2015 idiom still safe; module-scope let attaches to globalThis."

---

## 13. 60-second revision

> - **`typeof undeclared`** → `'undefined'` (SAFE — spec exception).
> - **`typeof letInTDZ`** → THROWS ReferenceError.
> - **`typeof var-before-assign`** → `'undefined'` (hoisted slot).
> - **`typeof function-decl`** → `'function'` (fully hoisted).
> - **Feature detection modern:** `typeof globalThis.X` or `'X' in globalThis`.
> - **Property access never throws** — that's why globalThis pattern works.
> - **Trap:** "typeof never throws"; pre-2015 idiom; module-let-globalThis attachment.

---

**Related:** [tdz-let-const.md](./tdz-let-const.md) · [hoisting-in-javascript.md](./hoisting-in-javascript.md) · [let-vs-var-differences.md](./let-vs-var-differences.md) · [es-module-live-bindings.md](./es-module-live-bindings.md)

**Concept primer:** [`concepts/hoisting.md`](../../concepts/hoisting.md)
