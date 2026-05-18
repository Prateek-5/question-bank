# `import` vs `require` — Hoisting & Module Semantics

## Source / Origin
- ES Modules vs CommonJS spec — fundamentally different module systems.
- Asked at: Razorpay, Stripe, Atlassian, Node-heavy interviews.
- Concept reference: `concepts/hoisting.md`, sibling `es-module-live-bindings.md`, `04-promises/top-level-await-deadlock-quiz.md`.

## Why this question matters in interviews
"What's the difference between `import` and `require`?" The surface answer is "ESM vs CJS." The senior answer is: hoisting behavior, live bindings vs snapshot, sync vs async, static vs dynamic, evaluation order, interop quirks, top-level await, and `__dirname`/`__filename` differences. This is one of the densest signal questions in a Node interview.

## Concepts involved

### Syntax to lock in
```js
// ESM (.mjs, "type":"module")
import { foo } from './foo.js';         // STATIC, hoisted to top of module
import { bar } from './bar.js';
console.log(foo);

const lazy = await import('./lazy.js'); // DYNAMIC, returns Promise; ESM-only feature

// CJS (.cjs, default in older Node)
const { foo } = require('./foo.js');    // RUNTIME, NOT hoisted
console.log(foo);
// require() is sync; returns module.exports value at the moment of call
```

### Edge cases / interview traps
1. **`import` is hoisted; `require` is not.** All `import` statements move to the top of the module (parsed before evaluation). `require` runs in source order.
2. **`import` bindings are read-only LIVE views.** The exporter mutates `foo`; importers see the new value. CJS bindings are *snapshots* of `module.exports` at require time (unless the export object is mutated in place).
3. **ESM is async load + sync access.** Loader resolves dependencies async; evaluation is synchronous (top-level await aside).
4. **CJS is fully sync.** Blocking `require()`.
5. **Default export interop.** `import x from 'cjs'` — what is `x`? Node's interop: `x === module.exports`. But some bundlers wrap into `{ default: x }`.
6. **`__dirname`, `__filename`** don't exist in ESM; use `import.meta.url` and parse.
7. **Conditional `import`** — only via dynamic `await import(...)`. Static `import` cannot be in a conditional.
8. **CJS in ESM**: `import x from 'cjs-pkg'` — works, but named exports may not be statically analyzable (older Node).
9. **ESM in CJS**: only via dynamic `await import(...)`; can't `require()` an ESM module.

## Mental Model

Two completely different machines:

```
   CommonJS (require):
   ┌─────────────────────────────────────┐
   │ ./a.js                              │
   │   const b = require('./b.js')      │  ← runs synchronously when reached
   │   const c = require('./c.js')      │
   │   // a body runs                    │
   │                                     │
   │ b.js exports = { x: 1 }             │ ← snapshot at require time
   │ a's `b.x` mutates IF b.x is mutated │
   │ but `b` itself rebinding doesn't    │
   └─────────────────────────────────────┘

   ES Modules (import):
   ┌─────────────────────────────────────┐
   │ ./a.mjs                             │
   │   import { x } from './b.mjs'       │  ← hoisted; resolved before a runs
   │   // body runs                      │
   │   console.log(x)                    │  ← `x` is LIVE; re-read each access
   │                                     │
   │ Phase 1: parse — collect all import │
   │ Phase 2: link — resolve graph        │
   │ Phase 3: evaluate (sync, in order)   │
   └─────────────────────────────────────┘
```

## Why interviewers care

- **Module-system literacy** — Node and bundlers diverge here.
- **Hoisting nuance** — ESM imports hoist; require doesn't.
- **Live bindings** — a non-obvious property.
- **Async/sync boundary** — ESM allows TLA; CJS is purely sync.

## Common beginner confusion

- **"`import` is like `require`."** Different semantics: hoisted, live, async load.
- **"`require` is faster."** Not really; depends on the loader. ESM has parallel resolution which can be faster for graphs.
- **"You can `require` ESM."** No (without explicit interop). Use dynamic import.
- **"ESM is always faster."** Tree-shaking helps in bundlers; runtime cost is similar.
- **"`__dirname` works in ESM."** It doesn't.

## Brute force approach

Convert all your CJS to ESM at once. Often introduces TLA deadlocks (see `top-level-await-deadlock-quiz.md`).

## Optimal approach

Pick one (ESM for new code) and stick with it. Bridge with dynamic `import()` for cross-format calls.

## Solution (JavaScript)

```js
// ESM module
// ./logger.mjs
let level = 'info';
export function setLevel(l) { level = l; }
export function getLevel() { return level; }

// ./app.mjs
import { getLevel, setLevel } from './logger.mjs';
console.log(getLevel());       // 'info'
setLevel('debug');
console.log(getLevel());       // 'debug'   — LIVE binding; reflects mutation

// CJS equivalent demonstrating snapshot semantics
// ./cjs-logger.cjs
let level = 'info';
module.exports = {
  setLevel(l) { level = l; },
  getLevel() { return level; },
};
// ./cjs-app.cjs
const logger = require('./cjs-logger.cjs');
console.log(logger.getLevel());    // 'info'
logger.setLevel('debug');
console.log(logger.getLevel());    // 'debug' — works through the object methods

// But:
const { getLevel, setLevel } = require('./cjs-logger.cjs');  // destructuring captures CURRENT values
// getLevel and setLevel still work because they're functions closed over `level`
// BUT if module exported a primitive:
//   module.exports.x = 1;  later module.exports.x = 2;
//   const { x } = require(...);  // x is 1; later assignments don't update
```

Dynamic import (works in both ESM and CJS):

```js
async function loadLazy() {
  const mod = await import('./lazy.mjs');
  return mod.default;
}
```

ESM `__dirname` replacement:

```js
import { fileURLToPath } from 'url';
import path from 'path';
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
```

## Step-by-step dry run

ESM live binding:

```js
// counter.mjs
export let n = 0;
export function inc() { n++; }

// main.mjs
import { n, inc } from './counter.mjs';
console.log(n);       // 0
inc();
console.log(n);       // 1   — LIVE
n = 99;               // SyntaxError — imports are read-only views
```

CJS snapshot:

```js
// counter.cjs
let n = 0;
module.exports = { n, inc: () => n++ };

// main.cjs
const { n, inc } = require('./counter.cjs');
console.log(n);       // 0
inc();
console.log(n);       // 0   — destructured snapshot
```

ESM hoisting:

```js
// a.mjs
console.log(b);           // 'hello' — imports hoisted; b initialized before this line
import { b } from './b.mjs';
```

```js
// a.cjs
console.log(b);           // ReferenceError — `b` not declared yet
const { b } = require('./b.cjs');
```

## How to think aloud in the interview

> "ESM and CJS are different module systems. ESM: static imports hoisted to top of module, live read-only bindings (importers see exporter mutations), async load + sync access, supports top-level await. CJS: synchronous require() runs in source order, exports are an object you can read/mutate, importers get a snapshot at require time, no TLA. In ESM, `__dirname` becomes `fileURLToPath(import.meta.url)`. To bridge CJS ↔ ESM: dynamic `import()` works both ways; `require()` of ESM doesn't work."

## Important takeaways

- **`import` is hoisted; `require` is not.**
- **ESM bindings are LIVE; CJS snapshots are by-value (but objects are by-ref).**
- **ESM static imports are statically analyzable** (enables tree-shaking).
- **`import()` is dynamic** (Promise-returning, works in both).
- **TLA is ESM-only.**
- **`__dirname` is CJS-only.**

## Variants

- **Bundler interop** (Webpack, esbuild) — wrap CJS in ESM-like shape; `import('cjs-pkg').default`.
- **Dual-package** (CJS + ESM via `exports` map in package.json) — supports both consumers.
- **Conditional exports** — `node`, `browser`, `import`, `require` field-specific resolutions.
- **`import.meta`** — module metadata (URL, environment hints).
- **Worker-thread interop** — workers can be ESM or CJS independently.

## Revision notes

```
ESM (import):
  - STATIC, HOISTED to top of module
  - LIVE READ-ONLY bindings (importer sees exporter mutations)
  - async load + sync access (TLA supported)
  - tree-shakeable
  - .mjs or "type":"module"
  - no __dirname (use fileURLToPath(import.meta.url))
  - import() dynamic returns Promise

CJS (require):
  - RUNTIME, NOT hoisted
  - snapshot of module.exports at call time (objects still by-ref)
  - synchronous, blocking
  - .cjs or default in old Node
  - __dirname / __filename present
  - cannot await at top level

Interop:
  - CJS → ESM: import works (default = module.exports)
  - ESM → CJS: require() does NOT work; use dynamic await import()
```
