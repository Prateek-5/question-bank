# Function declaration inside an `if` block

> **Difficulty:** Medium   |   **Time:** ~10 min   |   **Prereqs:** [function-declaration-vs-expression-hoisting.md](./function-declaration-vs-expression-hoisting.md)
>
> **Source:** Annex B.3.3 legacy semantics. The single most-cited "browser vs Node vs strict mode" quirk.

---

## 1. Problem statement

`if (cond) { function foo() {} }` — what's the behavior? Browser? Node strict? Node sloppy?

**Verification examples**

```js
'use strict';
if (true) {
  function foo() { return 'inside'; }
}
typeof foo;   // 'undefined' — block-scoped in strict ESM
```

```js
// sloppy mode (legacy script, no 'use strict')
if (true) {
  function foo() { return 'inside'; }
}
typeof foo;   // 'function' — Annex B.3.3 hoists to function scope
```

| Mode                              | Behaviour                                              |
|-----------------------------------|---------------------------------------------------------|
| Strict mode / ESM                 | block-scoped; invisible outside block                  |
| Sloppy mode (legacy)              | Annex B.3.3: hoisted to function scope as `var`        |
| Node CJS (not strict)             | Annex B behavior                                       |
| Node ESM                          | always strict; block-scoped                            |
| Browser non-strict                | Annex B behavior (modern engines)                      |

**Constraints**
- Function-in-block (FiB) is implementation-defined in legacy sloppy mode.
- Always avoid; use `let f = function() {}` instead.
- Babel/SWC rewrite to function-expression-on-`var` when transpiling.

---

## 2. Plain-English restatement

`function foo() {}` is meant for top-of-function or top-of-module. Inside a block, behavior depends on mode. In strict mode (ESM), it's block-scoped — invisible outside the block. In sloppy mode, the legacy "Annex B.3.3" rules hoist it to function scope as `var`, with the assignment happening when control enters the block.

---

## 3. Why this matters in interviews

Exposes whether candidate knows declaration vs expression + Annex B legacy semantics. Common bug in legacy Express handlers conditionally redefining helpers.

---

## 4. Mental model

```
   if (cond) {
     function foo() {}
   }

   STRICT MODE / ESM:
   - `foo` is block-scoped.
   - Hoisted to top of BLOCK as <uninitialized>.
   - Outside block: typeof foo === 'undefined'.

   SLOPPY MODE (legacy script):
   - Annex B.3.3 kicks in.
   - `foo` is BOTH:
     (a) block-scoped (visible inside block).
     (b) hoisted to enclosing function scope as `var foo = undefined`.
   - When control enters the block, var foo = the function object.
   - If cond is false: var foo remains undefined.

   Rule: don't do this. Use:
     const foo = function() {};   ← function expression on let/const
     // or just declare top-level
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. In strict mode ESM, can you call `foo()` outside the `if` block?
> 2. In sloppy mode with `cond = false`, what is `typeof foo` outside?
> 3. What does Babel emit when transpiling this for ES5?

---

## 6. Brute force — walked through

### Wrong attempt 1: "function declarations are always hoisted"
Inside a block, it's implementation-defined.

### Wrong attempt 2: "block-scoped in all modes"
Sloppy hoists to function scope (Annex B).

### Wrong attempt 3: "this works in browser everywhere"
Pre-ES6 browsers were inconsistent.

---

## 7. The unlocking insight

> **Function-in-block (FiB) is implementation-defined in sloppy mode (Annex B.3.3). In strict mode / ESM, it's clean block-scoped. Avoid; use function expression on `let`/`const` instead.**

Three properties:

1. **Strict mode = block-scoped** — clean.
2. **Sloppy mode = Annex B hoist** to function scope.
3. **Avoid FiB pattern** — use let/const + function expression.

---

## 8. Solution (annotated)

```js
'use strict';
if (true) {
  function baz() { return 'inside'; }                                  // step 1: block-scoped
}
typeof baz;                                                            // 'undefined'

// Sloppy mode equivalent (in a script without 'use strict'):
// if (true) { function baz() {} }
// typeof baz;   // 'function' (Annex B hoists to function/script scope)

// PREFERRED PATTERN: function expression on let/const
let helper;
if (someCondition) {
  helper = function () { return 'A'; };
} else {
  helper = function () { return 'B'; };
}
helper();                                                              // safe, no ambiguity
```

**Try it yourself**

```js
// Strict (ESM):
function f() {
  'use strict';
  if (true) {
    function inner() {}
  }
  return typeof inner;
}
f();                                                                    // 'undefined'

// Sloppy (CJS without use strict):
function g() {
  if (true) {
    function inner() {}
  }
  return typeof inner;
}
g();                                                                    // 'function' in Node sloppy

// Babel transpilation output (approximate):
function h() {
  var inner;
  if (true) {
    inner = function () {};
  }
  return typeof inner;
}
// Babel converts FiB to function-expression-on-var to preserve semantics.
```

---

## 9. Step-by-step dry run

```
'use strict';
function outer() {
  if (true) {
    function inner() { return 'in'; }
  }
  console.log(typeof inner);
}
outer();

STRICT MODE:
  outer's body parses.
    Inside if block: function inner() {} is a function declaration in a block.
    Per spec: hoisted to TOP OF BLOCK (the if's LE), NOT to outer's VE.
  outer's VE: { inner: undefined? NO — not in VE at all }
  
  Execution:
    Enter if-block. LE: { inner: <function> }.
    Block ends.
    console.log(typeof inner) → resolve inner in outer's scope → not found → 'undefined'.

SLOPPY MODE (Annex B.3.3):
  outer's VE: { inner: undefined } at creation.
  
  Execution:
    Enter if-block.
    Annex B: set outer's `inner` to the function object.
    Block ends.
    console.log(typeof inner) → 'function'.

Output:
  Strict: 'undefined'
  Sloppy: 'function'
```

---

## 10. Common confusion + traps

1. **"Always hoisted"** — inside block is implementation-defined.
2. **"Sloppy and strict same"** — different.
3. **"Block-scoped always"** — sloppy hoists to function scope.
4. **"This works in browser everywhere"** — pre-ES6 browsers inconsistent.
5. **`if (false) { function foo() {} }`** — sloppy: `foo` hoisted to function scope as `undefined`; assignment never runs.
6. **Babel emits same code** — actually transpiles to `var` + function expression.
7. **Modules are sloppy** — no, ESM is always strict.

---

## 11. Senior follow-ups & variants

### Variant 1 — Hoisted across `if/else`
Sloppy mode: `if(cond){function f(){A}} else {function f(){B}}` — only one `var f` in function scope; assigned based on branch.

### Variant 2 — Strict-mode test
Add `'use strict'` to outer function or use `.mjs` extension.

### Variant 3 — Transpilation
Babel/SWC convert FiB to function expression on `var` to preserve Annex B semantics across ES5 targets.

### Variant 4 — Loop with FiB
`for (var i = 0; i < 3; i++) { function f() { return i; } }` — sloppy: one `f` in function scope; reads `i` after loop (3).

### Variant 5 — Switch case
`switch (x) { case 1: function f() {} break; }` — same Annex B issues; avoid.

---

## 12. How to think aloud

> "Function declarations inside blocks (Function-in-Block, FiB) are the single most-cited 'browser vs Node vs strict mode' quirk. In strict mode and ESM, the function is block-scoped — invisible outside. In sloppy mode (legacy scripts, non-strict CJS), Annex B.3.3 kicks in: the function is BOTH block-scoped AND hoisted to the enclosing function scope as `var fooName = undefined`, with assignment happening when control enters the block. Pre-ES6 browsers were inconsistent. Modern engines follow Annex B. Always avoid this pattern; use `let helper = function() {}` or assign conditionally. Babel transpiles FiB to function expression on `var` to preserve sloppy semantics. Trap: 'always hoisted'; 'block-scoped always'; assuming consistent browser behavior."

---

## 13. 60-second revision

> - **Function-in-block (FiB)** is implementation-defined in sloppy mode (Annex B.3.3).
> - **Strict mode / ESM:** block-scoped; invisible outside.
> - **Sloppy mode:** Annex B hoists to function scope as `var`.
> - **Pre-ES6 browsers** inconsistent.
> - **Avoid FiB;** use `let f = function() {}` instead.
> - **Babel transpiles** FiB to function expression on `var`.
> - **ESM is always strict** — no sloppy mode.
> - **Trap:** "always hoisted"; "always block-scoped"; consistent browser assumption.

---

**Related:** [function-declaration-vs-expression-hoisting.md](./function-declaration-vs-expression-hoisting.md) · [named-fn-expression-binding.md](./named-fn-expression-binding.md) · [var-in-block.md](./var-in-block.md)

**Concept primer:** [`concepts/hoisting.md`](../../concepts/hoisting.md)
