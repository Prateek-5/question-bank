# ES module imports — hoisted live bindings

> **Difficulty:** Senior   |   **Time:** ~15 min   |   **Prereqs:** [import-vs-require-hoisting.md](./import-vs-require-hoisting.md), [hoisting-in-javascript.md](./hoisting-in-javascript.md)
>
> **Source:** ECMA-262 §16 Modules; "JavaScript Modules" by Lin Clark.

---

## 1. Problem statement

ES module imports have two non-obvious properties: (1) hoisted to top of module, (2) live read-only bindings (not copies).

**Verification examples**

```js
// a.js
export let counter = 0;
export function inc() { counter++; }

// b.js
import { counter, inc } from './a.js';
console.log(counter);    // 0
inc();
console.log(counter);    // 1 — LIVE BINDING, not a stale copy
// counter++;            // SyntaxError — read-only from importer's side
```

**vs CommonJS:**

```js
// a.cjs
let counter = 0;
function inc() { counter++; }
module.exports = { counter, inc };

// b.cjs
const { counter, inc } = require('./a.cjs');
console.log(counter);    // 0
inc();
console.log(counter);    // 0 — SNAPSHOT at require time
```

**Constraints**
- ESM imports hoisted to top of module.
- ESM bindings are LIVE cells — reads always current.
- ESM imports read-only on importer side.
- CJS destructure is a SNAPSHOT.

---

## 2. Plain-English restatement

In ESM, when you `import { x } from './a.js'`, you don't get a copy of `x` — you get a live reference to `a.js`'s `x` cell. If `a.js` mutates `x`, you see the new value next time you read it. But you can't reassign `x` from outside.

In CJS, `const { x } = require('./a.cjs')` destructures `module.exports` at require time — you have a copy. Mutations inside `a.cjs` to its local `x` don't update yours.

---

## 3. Why this matters in interviews

Trips up engineers from CJS background. Mixed CJS/ESM in Node 18+ codebases is a huge bug source. Tests module phases (parse → instantiate → evaluate) + live binding mechanics.

---

## 4. Mental model

```
   ESM:
   ┌──────────────────────────────────┐         ┌──────────────────────────────────┐
   │ a.js                             │         │ b.js                             │
   ├──────────────────────────────────┤         ├──────────────────────────────────┤
   │ let counter = 0;                 │ ← read  │ import { counter } from './a.js';│
   │ inc() { counter++; }             │ live    │ console.log(counter);             │
   │                                  │         │ // counter++ → SyntaxError       │
   └──────────────────────────────────┘         └──────────────────────────────────┘
   
   Importer's `counter` is NOT a copy — it's a binding pointing at a.js's cell.
   Inc() mutates a.js's cell → b.js sees the new value next read.
   
   CJS:
   ┌──────────────────────────────────┐         ┌──────────────────────────────────┐
   │ a.cjs                            │         │ b.cjs                            │
   ├──────────────────────────────────┤         ├──────────────────────────────────┤
   │ let counter = 0;                 │ snapshot│ const { counter } = require(...);│
   │ inc() { counter++; }             │ at req  │ // counter is a LOCAL copy       │
   │ module.exports = { counter, inc };│        │                                  │
   └──────────────────────────────────┘         └──────────────────────────────────┘
   
   `counter` is destructured at require time — local copy.
   inc() mutates a.cjs's internal `counter` — b.cjs has stale `0`.
   (Note: if you held `require('./a.cjs').counter` LIVE-ish via the object,
    you'd still need re-read; primitives don't track.)
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. After `inc()`, does the importer's `counter` reflect the new value?
> 2. Can you reassign an imported binding?
> 3. What's different about CJS destructuring?

---

## 6. Brute force — walked through

### Wrong attempt 1: "ESM bindings are copies"
Wrong — they're LIVE.

### Wrong attempt 2: "CJS exports are live too"
Only via object reference; primitives are snapshots.

### Wrong attempt 3: "Imports run at their source position"
Hoisted to top of module — execute before any module body code.

---

## 7. The unlocking insight

> **ESM imports: hoisted to module top + live read-only bindings (cells, not copies). CJS: synchronous `require()` returns `module.exports` snapshot; destructured primitives are local copies. Mutations to exporter's cells reflect in ESM importers; CJS primitive destructures don't update.**

Three properties:

1. **Hoisted** — imports run before body code.
2. **Live bindings** — reads always see current cell.
3. **Read-only from importer** — can't reassign.

---

## 8. Solution (annotated)

```js
// a.js
export let counter = 0;                                                // step 1: cell allocated
export function inc() { counter++; }                                    // mutates cell

// b.js
import { counter, inc } from './a.js';                                 // step 2: live binding
console.log(counter);                                                   // 0
inc();
console.log(counter);                                                   // 1 — reflects mutation
// counter = 99;                                                         // SyntaxError (read-only)

// Re-export pattern (ESM)
export { counter as count } from './a.js';                              // live re-export
```

**Try it yourself**

```js
// CJS contrast
// a.cjs
let counter = 0;
function inc() { counter++; }
module.exports = { counter, inc };                                      // snapshot at this line

// b.cjs
const { counter, inc } = require('./a.cjs');
console.log(counter);                                                   // 0
inc();
console.log(counter);                                                   // 0 — STALE (local copy)

// To get "live-ish" in CJS, hold the module object:
const a = require('./a.cjs');
a.inc();
console.log(a.counter);                                                  // 0 still — module.exports.counter was a snapshot too
// Use getter to make it work:
// (in a.cjs) Object.defineProperty(module.exports, 'counter', { get: () => counter });
```

---

## 9. Step-by-step dry run

```
Module evaluation:

a.js evaluated first (imported by b):
  allocate cell `counter`, init to 0.
  define function `inc` (captures cell).
  exports: { counter (cell ref), inc (fn) }.

b.js evaluated:
  import binding `counter` → points at a.js's cell.
  import binding `inc` → points at a.js's fn.
  log counter → read cell → 0.
  inc() → fn body: counter++ → mutate cell → cell now 1.
  log counter → read cell → 1.
  
Critically: b.js's `counter` is NEVER assigned a value;
            it's a binding that aliases a.js's cell.

CJS contrast:
require('./a.cjs') runs a.cjs top-to-bottom.
  Local `counter = 0`.
  At `module.exports = { counter, inc }`:
    Object created with property `counter: 0` (copy of value at this moment).
  
b.cjs:
  destructure { counter } from module.exports → local var counter = 0.
  inc() → mutates a.cjs's internal `counter` (local in that closure) → 1.
  But b.cjs's `counter` is unaffected → still 0.
```

---

## 10. Common confusion + traps

1. **ESM bindings are copies** — LIVE.
2. **CJS exports are live** — snapshot at `module.exports = ...`.
3. **Imports execute at source position** — hoisted to top.
4. **Can reassign imports** — read-only.
5. **`export default` is different** — same live-binding rules.
6. **Bundlers may simulate CJS for ESM** — interop layers can change semantics.
7. **Default export of CJS in ESM** — `import x from 'cjs'` → `x === module.exports`.

---

## 11. Senior follow-ups & variants

### Variant 1 — `export * from`
Re-exports preserve live bindings.

### Variant 2 — Mutable mocking in tests
Some test libs use Proxy or hot-reload to mutate ESM imports — non-trivial.

### Variant 3 — Top-level await + live bindings
Importer sees live binding once exporter finishes evaluating.

### Variant 4 — CJS getter for live-ish
`Object.defineProperty(module.exports, 'x', { get: () => x })` simulates live binding in CJS.

### Variant 5 — Bundle interop
Webpack/Rollup wrap ESM-from-CJS or vice versa; can change live-binding semantics.

---

## 12. How to think aloud

> "Two things about ESM imports: (1) hoisted to top of module — they run before any module body code. (2) live read-only bindings — they're cells, not copies. If `a.js` mutates `counter`, every importer sees the new value on next read. But importers can't reassign — `counter = 99` is SyntaxError. CJS is different: `require()` is synchronous; destructure of `module.exports` is a SNAPSHOT of primitive values at require time. To get live-ish in CJS, hold the module object and read properties, or use a getter. Mixed CJS/ESM interop in Node 18+ is a huge bug source. Trap: 'ESM bindings are copies'; reassigning imports; treating CJS exports as live."

---

## 13. 60-second revision

> - **ESM imports HOISTED** to top of module.
> - **ESM bindings LIVE** — cells, not copies.
> - **ESM imports READ-ONLY** from importer side.
> - **CJS `require()`** synchronous; destructured primitives are snapshots.
> - **For live-ish CJS:** hold module object + getters.
> - **Mutations visible** in ESM; not in CJS primitive destructure.
> - **Trap:** "ESM copies"; reassign import; CJS live assumption; mixed interop.

---

**Related:** [import-vs-require-hoisting.md](./import-vs-require-hoisting.md) · [circular-import-live-binding-quiz.md](./circular-import-live-binding-quiz.md) · [`04-promises/top-level-await-deadlock-quiz.md`](../04-promises/top-level-await-deadlock-quiz.md)

**Concept primer:** [`concepts/hoisting.md`](../../concepts/hoisting.md)
