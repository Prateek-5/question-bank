# Circular ESM import — live binding quiz

> **Difficulty:** Senior   |   **Time:** ~15 min   |   **Prereqs:** [es-module-live-bindings.md](./es-module-live-bindings.md), [import-vs-require-hoisting.md](./import-vs-require-hoisting.md)
>
> **Source:** Classic Node ESM interop bug. Stripe, Cloudflare, Razorpay.

---

## 1. Problem statement

A imports B; B imports A. Predict the output.

**Verification examples**

```js
// a.mjs
import { b } from './b.mjs';
export const a = 'a-value';
console.log('a sees b =', b);

// b.mjs
import { a } from './b.mjs';
export const b = 'b-value';
console.log('b sees a =', a);

// node a.mjs output:
//   b sees a = undefined        ← a const not yet initialized
//   a sees b = 'b-value'
```

| Setup                                        | Behaviour                                              |
|----------------------------------------------|---------------------------------------------------------|
| Both `const` exports                          | importer reads → live binding; before init = TDZ throw / undefined |
| `var` export                                  | reads as `undefined` if accessed before assignment    |
| CJS circular cycle                            | `require` returns `module.exports` snapshot — often `{}` |
| Bundler in dev vs prod                         | may behave differently                                 |
| Cyclic class `extends`                         | ReferenceError at extends evaluation                  |

**Constraints**
- ESM uses 2-phase load: link (resolve, allocate bindings) → evaluate (run modules in order).
- Bindings are LIVE — reads always see current cell.
- Entry-point determines evaluation order.
- CJS circular = snapshot of partial `module.exports` (often empty).

---

## 2. Plain-English restatement

ESM parses the entire graph first, allocates binding cells, then evaluates modules depth-first. If module B reads `a` from A before A's evaluation completes, the live binding is still `<uninitialized>` — for `const`/`let`, that's a TDZ throw or `undefined` depending on engine; for `var`, just `undefined`. CJS handles cycles differently — `require` returns whatever `module.exports` looked like at the moment.

---

## 3. Why this matters in interviews

Tests ESM 2-phase load + live-binding mechanics + CJS interop awareness.

---

## 4. Mental model

```
   ESM 2-phase load (per module graph):
   
   Phase 1 — LINK (parse all, allocate cells, hoist imports):
     parse a.mjs → discover import './b.mjs'
       parse b.mjs → discover import './a.mjs' (already parsed)
     allocate binding cells: a.a, b.b (both uninitialized)
     wire importers to point at exporter's cells (LIVE).
   
   Phase 2 — EVALUATE (depth-first, post-order):
     evaluate b.mjs first (deepest in cycle)
       reads a → cell is <uninitialized> → see undefined OR TDZ throw
       assigns b's exports
     evaluate a.mjs
       reads b → already initialized → sees 'b-value'
       assigns a's exports

   CJS circular:
     require('./b') runs b.cjs from top.
     b.cjs hits require('./a') → a already being loaded → returns CURRENT module.exports.
     Often that's {} (initial empty object).
     b sees a as {} regardless of what a eventually exports.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. With ESM and `node a.mjs`, which module's body runs first?
> 2. What does b see when it reads `a` before a's body completes?
> 3. How does the same cycle behave in CJS?

---

## 6. Brute force — walked through

### Wrong attempt 1: "ESM cycles always crash"
Often work — depends on whether bindings are accessed before initialization.

### Wrong attempt 2: "ESM and CJS handle cycles the same"
Different. ESM live bindings; CJS snapshot.

### Wrong attempt 3: "Bundler behavior is consistent"
Bundlers can inline; dev vs prod may differ.

---

## 7. The unlocking insight

> **ESM links all bindings before any evaluation. Reads in cycle see live cell — if cell not yet initialized, undefined (var) or TDZ (let/const). CJS returns partial `module.exports` snapshot. Fix: refactor to remove cycle, lazy access (function-level), or dynamic `import()`.**

Three properties:

1. **2-phase ESM load** — link before evaluate.
2. **Live bindings** — reads always see current state.
3. **CJS cycle returns snapshot** — different mechanics.

---

## 8. Solution (annotated)

```js
// a.mjs
import { b } from './b.mjs';                                          // step 1: hoisted; linked
export const a = 'a-value';                                            // step 2: initialized at exec line
console.log('a sees b =', b);                                          // live read

// b.mjs
import { a } from './a.mjs';                                          // step 3: linked
export const b = 'b-value';
console.log('b sees a =', a);                                          // reads BEFORE a is initialized

// Run: node a.mjs
// Output:
//   b sees a = undefined         ← cell <uninitialized> at this moment
//   a sees b = 'b-value'

// Fix: lazy access via function
// b.mjs (fixed)
import * as A from './a.mjs';
export const b = 'b-value';
console.log('b sees a (lazy) =', () => A.a);                          // function returns live cell value LATER
```

**Try it yourself**

```js
// CJS cycle behavior (different)
// a.cjs
const b = require('./b.cjs');
console.log('a sees b =', b);
module.exports.a = 'a-value';

// b.cjs
const a = require('./a.cjs');   // a is in progress; returns current module.exports = {}
console.log('b sees a =', a);    // {} (empty)
module.exports.b = 'b-value';

// node a.cjs output:
//   b sees a = {}                  ← snapshot of a's empty initial exports
//   a sees b = { b: 'b-value' }
```

---

## 9. Step-by-step dry run

```
Entry: node a.mjs

LINK phase:
  parse a.mjs:
    found import { b } from './b.mjs'
    parse b.mjs:
      found import { a } from './a.mjs' (already in progress)
  Allocate cells:
    a.mjs.a → <uninitialized>
    b.mjs.b → <uninitialized>
  Wire:
    b.mjs's local `a` reference → points at a.mjs.a cell
    a.mjs's local `b` reference → points at b.mjs.b cell

EVALUATE phase (depth-first post-order):
  Evaluate b.mjs first:
    Read a from a.mjs.a cell → cell still <uninitialized> → undefined
    console.log('b sees a =', undefined) → 'b sees a = undefined'
    Assign b.mjs.b = 'b-value'. Cell initialized.
  Evaluate a.mjs:
    Read b from b.mjs.b cell → 'b-value'
    console.log('a sees b =', 'b-value') → 'a sees b = b-value'
    Assign a.mjs.a = 'a-value'. Cell initialized.

Output:
  b sees a = undefined
  a sees b = b-value
```

---

## 10. Common confusion + traps

1. **"ESM cycles always crash"** — often work, just see partial state.
2. **CJS = ESM cycle behavior** — different.
3. **"Live bindings copy on read"** — they're cells; reads always current.
4. **Cyclic class `extends`** → ReferenceError.
5. **Bundler may inline** → cycle disappears in dev vs prod.
6. **Top-level await + cycle** → silent deadlock.
7. **`undefined` for `var` export, TDZ for `let`/`const`** — engine-dependent emit.

---

## 11. Senior follow-ups & variants

### Variant 1 — Fix patterns
Refactor to remove cycle; lazy access via function-level; dynamic `import()`.

### Variant 2 — Cyclic `extends`
`class A extends B {} class B extends A {}` → ReferenceError at extends evaluation.

### Variant 3 — Bundler behavior
Rollup tree-shakes; Webpack handles cycles. Dev vs prod can differ.

### Variant 4 — TLA cycle deadlock
Top-level await + cycle → process hangs (see top-level-await-modules).

### Variant 5 — CJS interop
`import x from 'cjs-pkg'` — Node returns `module.exports`; named imports may not be statically analyzable.

---

## 12. How to think aloud

> "ESM has a 2-phase load. Phase 1 LINK: parse the entire graph, allocate binding cells, wire importers to exporter cells. Phase 2 EVALUATE: run modules depth-first, post-order. With a cycle A↔B, entry point determines order. If entry is A, A imports B, so B evaluates first; B reads `a` from a's cell which is still `<uninitialized>` → undefined (for var) or TDZ throw (for let/const at access). Bindings are LIVE — they're cells, not copies. CJS handles cycles differently: `require` returns whatever `module.exports` is RIGHT NOW (often `{}`). Fix patterns: refactor cycle out, lazy access (function-level read), dynamic `import()`. Cyclic class `extends` always throws. Trap: assuming ESM and CJS cycle behavior is the same."

---

## 13. 60-second revision

> - **ESM 2-phase load:** LINK (parse + allocate cells) → EVALUATE (post-order).
> - **Bindings are LIVE cells** — reads always current.
> - **Cycle:** entry determines order; deepest evaluates first; sees other's `<uninitialized>` cell.
> - **`const`/`let` exports:** TDZ throw or undefined depending on engine emit.
> - **`var` exports:** `undefined` if read before assignment.
> - **CJS cycle:** `require` returns partial `module.exports` snapshot (often `{}`).
> - **Cyclic class `extends`** → ReferenceError.
> - **Fix:** refactor, lazy function-level access, dynamic `import()`.
> - **Trap:** assuming ESM = CJS cycle behavior; TLA cycle deadlock.

---

**Related:** [es-module-live-bindings.md](./es-module-live-bindings.md) · [import-vs-require-hoisting.md](./import-vs-require-hoisting.md) · [`04-promises/top-level-await-deadlock-quiz.md`](../04-promises/top-level-await-deadlock-quiz.md) · [class-hoisting.md](./class-hoisting.md)

**Concept primer:** [`concepts/hoisting.md`](../../concepts/hoisting.md)
