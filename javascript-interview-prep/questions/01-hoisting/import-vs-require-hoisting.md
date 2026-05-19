# `import` vs `require` — hoisting & module semantics

> **Difficulty:** Senior   |   **Time:** ~15 min   |   **Prereqs:** [es-module-live-bindings.md](./es-module-live-bindings.md), [hoisting-in-javascript.md](./hoisting-in-javascript.md)
>
> **Source:** ESM vs CJS spec. Razorpay, Stripe, Atlassian Node interviews.

---

## 1. Problem statement

`import` vs `require` differ on: hoisting, live bindings vs snapshot, sync vs async load, static vs dynamic, evaluation order, top-level await, `__dirname`/`__filename`.

**Verification examples**

| Property                    | `import` (ESM)                              | `require` (CJS)                                      |
|-----------------------------|----------------------------------------------|------------------------------------------------------|
| Hoisting                    | hoisted to module top                        | runs in source order                                  |
| Static vs dynamic           | static (parse-time); dynamic via `await import()` | dynamic (runtime call)                              |
| Bindings                    | live read-only                               | snapshot at call time                                |
| Sync/async load             | async load + sync access                     | fully sync                                            |
| Top-level await             | supported (ESM only)                         | not supported                                         |
| `__dirname` / `__filename`  | NOT defined; use `import.meta.url`           | defined                                               |
| Conditional `import`        | only via dynamic `await import()`            | conditional `require()` works                        |
| Interop                     | ESM can import CJS via default               | CJS can `await import('esm')` (dynamic only)         |

**Constraints**
- `import` is HOISTED; `require` is NOT.
- ESM is async load + sync access; CJS is fully synchronous.
- ESM bindings are LIVE; CJS destructure is SNAPSHOT.
- ESM cannot `require()`; CJS cannot use top-level `await import` (only inside async fn).

---

## 2. Plain-English restatement

`import` is the modern ESM syntax — static, hoisted, gives live read-only bindings, supports top-level await. `require` is older CJS — runs at source position, returns a snapshot of `module.exports`, fully synchronous. The two systems are interop-able but with quirks.

---

## 3. Why this matters in interviews

Densest signal question for Node engineers. Mixed CJS/ESM is the #1 modern Node bug source.

---

## 4. Mental model

```
   ESM (modern):
   ┌──────────────────────────────────────┐
   │ Static `import { x } from './a.js'`  │  ← hoisted to top
   │ Parsed at compile time                │
   │ Bindings: live read-only              │
   │ Load: async (parallel fetch)          │
   │ Access: sync                          │
   │ Top-level await: supported            │
   └──────────────────────────────────────┘
   
   CJS (older):
   ┌──────────────────────────────────────┐
   │ `const x = require('./a.cjs').x;`    │  ← runs at source position
   │ Runtime call                          │
   │ Bindings: snapshot of module.exports │
   │ Load: fully sync (blocking)           │
   │ Top-level await: NOT supported        │
   └──────────────────────────────────────┘
   
   Interop in Node:
   ESM imports CJS:
     import pkg from 'cjs-pkg';        // pkg === module.exports
     import { name } from 'cjs-pkg';   // named imports may not be statically analyzable
   
   CJS imports ESM:
     const pkg = await import('./esm.mjs');  // only inside async fn
     // cannot use require()
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Where does `import { x } from './a.js'` execute? Top of module or its source position?
> 2. Can you put `import` inside an `if`?
> 3. What's `__dirname` in ESM?

---

## 6. Brute force — walked through

### Wrong attempt 1: "import and require are interchangeable"
Different semantics — hoisting, sync, bindings.

### Wrong attempt 2: "ESM is sync, CJS is async"
Reversed.

### Wrong attempt 3: "`__dirname` works in ESM"
No; use `import.meta.url` + path utilities.

---

## 7. The unlocking insight

> **ESM `import` is static, hoisted, async-loaded, sync-accessed, with live read-only bindings. CJS `require` is dynamic, runs at source position, fully sync, with snapshot bindings. Top-level await is ESM-only. `__dirname` is CJS-only.**

Three properties:

1. **Hoisting + static** — ESM imports hoist; CJS doesn't.
2. **Live vs snapshot bindings**.
3. **Async load + TLA** — ESM-only.

---

## 8. Solution (annotated)

```js
// ESM (.mjs or "type":"module")
import { foo } from './foo.js';                                        // step 1: STATIC, hoisted
import { bar } from './bar.js';

console.log(foo);                                                       // works (already evaluated)

const lazy = await import('./lazy.js');                                 // step 2: DYNAMIC, returns Promise

// __dirname not available; use import.meta.url
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// CJS (.cjs)
const { foo } = require('./foo.js');                                    // step 3: RUNTIME, NOT hoisted
console.log(foo);

// __dirname / __filename are defined globally in CJS
console.log(__dirname);
```

**Try it yourself**

```js
// Conditional import requires dynamic in ESM
const isProd = process.env.NODE_ENV === 'production';
// Static (illegal):
// if (isProd) import './prod.js';   // SyntaxError
// Dynamic (works):
const mod = isProd ? await import('./prod.js') : await import('./dev.js');

// CJS conditional require works directly
const mod = isProd ? require('./prod.js') : require('./dev.js');

// Cannot mix:
// In CJS file: const x = await import('./esm.mjs');  // valid only inside async fn
// In ESM file: const x = require('./cjs.cjs');       // ReferenceError (no require)
```

---

## 9. Step-by-step dry run

```
ESM module load (entry: main.mjs):

LINK phase:
  parse main.mjs → find import './a.js', './b.js'
    parse a.js, b.js recursively
  resolve all dependencies (async, parallel-eligible)
  allocate binding cells, wire importers

EVALUATE phase:
  evaluate in post-order:
    a.js body runs
    b.js body runs
    main.mjs body runs
  console.log(foo) → foo's cell already initialized → log

  Imports HOISTED — already linked + values ready when main body runs.

CJS module load (entry: main.cjs):

require('./a.cjs') executes at source position:
  enters a.cjs, runs top-to-bottom, sets module.exports.
  returns module.exports object.

After require returns, main.cjs continues.

Compare:
  ESM:    hoisted; all imports resolved before body code.
  CJS:    in-order; each require() blocks until module loaded.
```

---

## 10. Common confusion + traps

1. **Interchangeable** — different semantics.
2. **`__dirname` in ESM** — undefined; use `import.meta.url`.
3. **Top-level await in CJS** — not supported.
4. **`import` in conditional** — only via dynamic.
5. **CJS `require` of ESM** — error; use `await import()`.
6. **ESM imports stale snapshot** — live bindings.
7. **Cyclic import works same way** — ESM lazily resolves; CJS returns partial.

---

## 11. Senior follow-ups & variants

### Variant 1 — `package.json` `"type"`
`"type": "module"` makes `.js` files ESM by default.

### Variant 2 — Dual-package hazard
Library shipping both CJS and ESM — singletons may duplicate.

### Variant 3 — `.cjs` / `.mjs` extensions
Force module type regardless of `"type"`.

### Variant 4 — Bundler emit
Webpack/Rollup wrap modules differently; dev vs prod may differ.

### Variant 5 — `import.meta.resolve`
Future API for resolving module specifiers at runtime.

---

## 12. How to think aloud

> "ESM `import` is STATIC (parse-time), HOISTED to module top, with LIVE READ-ONLY bindings. Async load + sync access. Supports top-level await. CJS `require` is dynamic — runs at source position, blocks synchronously, returns `module.exports` SNAPSHOT. Top-level await NOT supported. `__dirname`/`__filename` are CJS-only; in ESM use `import.meta.url`. Conditional imports: in ESM, only via dynamic `await import()`; in CJS, plain `require()` works. Interop: ESM importing CJS gives `module.exports` as default; CJS importing ESM requires `await import()` inside an async function (cannot `require` an ESM module). Trap: assuming interchangeable; using `__dirname` in ESM; TLA in CJS; live vs snapshot bindings."

---

## 13. 60-second revision

> - **`import`** static, hoisted, async load + sync access, live bindings, supports TLA.
> - **`require`** dynamic, source-position, fully sync, snapshot bindings, NO TLA.
> - **ESM** = `.mjs` or `"type":"module"`. **CJS** = `.cjs` or default older Node.
> - **`__dirname`** CJS-only; ESM uses `import.meta.url`.
> - **Conditional:** ESM via dynamic `await import()`; CJS via plain `require()`.
> - **Interop:** ESM ↔ CJS allowed but quirky; default + named import differences.
> - **Top-level await** ESM-only.
> - **Trap:** assume interchangeable; `__dirname` in ESM; live vs snapshot.

---

**Related:** [es-module-live-bindings.md](./es-module-live-bindings.md) · [circular-import-live-binding-quiz.md](./circular-import-live-binding-quiz.md) · [`04-promises/top-level-await-deadlock-quiz.md`](../04-promises/top-level-await-deadlock-quiz.md) · [`05-event-loop/top-level-await-modules.md`](../05-event-loop/top-level-await-modules.md)

**Concept primer:** [`concepts/hoisting.md`](../../concepts/hoisting.md)
