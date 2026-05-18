# Top-Level Await — Deadlock Quiz

## Source / Origin
- ES2022 top-level await (TLA) in ES modules.
- Asked at: Node-shop interviews (Stripe, Atlassian, Cloudflare).
- Concept reference: `concepts/event-loop.md` (top-level-await section).

## Why this question matters in interviews
Top-level `await` looks innocent — `const config = await loadConfig();` at the top of a module. But TLA *changes module evaluation semantics*: a module that awaits delays the evaluation of *every importer*. Two TLA modules waiting on each other's exports = deadlock. Interviewers want you to see this and know that TLA is for *initialization*, not request-time work; that CommonJS doesn't support it; that bundlers transform it.

## Concepts involved

### Syntax to lock in
```js
// config.js (ESM)
const data = await fetch('/config.json').then(r => r.json());
export const config = data;

// app.js
import { config } from './config.js';   // evaluation of app.js waits for config.js to complete
console.log(config);                    // safe — config is fully loaded by here
```

### Edge cases / interview traps
1. **CommonJS doesn't support TLA.** `require()` is synchronous. TLA only works in ES modules (`.mjs`, or `"type": "module"`).
2. **TLA propagates wait upward.** If A awaits and B imports A, B waits for A before B's body runs.
3. **Deadlock via circular TLA imports.** Module A awaits B; B awaits A. Both stuck.
4. **TLA at the bottom of the file vs top** — doesn't matter; the module is async-evaluated as a whole.
5. **Errors in TLA reject the module's evaluation promise** — importing modules see a rejected import. Tooling treats this as a fatal error.
6. **TLA changes import order semantics.** Modules without TLA evaluate in deterministic depth-first order; TLA inserts await points.
7. **Bundlers** — Webpack 5, Rollup, Vite all support TLA but transform it. Some setups (older Webpack, CRA) don't.
8. **Workers and `import()`** — dynamic import handles TLA naturally (returns a Promise). Static import in classic scripts cannot.

## Mental Model

A module is **a Promise of "this module is ready"**:

```
   classic module (no TLA):
   ┌─────────────────┐
   │ run body sync   │
   │ exports filled  │  →  module ready immediately
   └─────────────────┘

   TLA module:
   ┌─────────────────┐
   │ run body...     │
   │ await fetch()   │  →  module evaluation paused
   │ exports filled  │  →  module ready when promise resolves
   └─────────────────┘
   
   import chain:
   app.js   imports  config.js  imports  database.js  imports ...
   evaluation order: depth-first; if any has TLA, all upstream wait
```

Deadlock diagram:

```
   A.mjs:                    B.mjs:
   import { b } from './B'   import { a } from './A'
   const x = await b()        const y = await a()
   export const a = ...       export const b = ...
   
   A waits for B (because of import)
   B waits for A (because of import)
   → deadlock; runtime throws TopLevelAwait error or stalls
```

## Why interviewers care

- **Async semantics literacy** — TLA is the newest module-loading wrinkle.
- **CJS vs ESM awareness** — senior candidates know the boundary.
- **Failure-mode reasoning** — what happens when init promises reject.

## Common beginner confusion

- **"TLA makes startup faster."** It can — parallelize awaits via `Promise.all` — or slower if you serialize awaits.
- **"I can use TLA in CommonJS."** No. `require()` is synchronous.
- **"TLA in a route handler is fine."** It's not in a handler — TLA only exists at module top level. Inside a function body it's just plain `await` requiring an `async` wrapper.
- **"Imports are synchronous."** With TLA they're effectively async-resolved; the consumer module's evaluation pauses.
- **"Workers re-evaluate modules from scratch."** Yes — TLA runs again per worker.

## Brute force approach

```js
// Sequential awaits at the top — adds boot latency
const a = await loadA();   // 200ms
const b = await loadB();   // 200ms (must wait for a)
const c = await loadC();   // 200ms
// total: 600ms
```

## Optimal approach

Parallelize independent inits:

```js
const [a, b, c] = await Promise.all([loadA(), loadB(), loadC()]);
// total: 200ms
```

For circular dependencies — restructure (don't await at top of both sides; lazy-init via getter function).

## Solution (JavaScript)

```js
// config.js — TLA-safe, parallelized init
const [config, secrets, schema] = await Promise.all([
  fetch('/config.json').then(r => r.json()),
  fetchSecrets(),
  fetchSchema(),
]);
export { config, secrets, schema };

// app.js — uses the module; evaluation waits for config.js to settle
import { config } from './config.js';
import express from 'express';

const app = express();
app.get('/x', (req, res) => res.json({ env: config.env }));
app.listen(3000);

// Recovery: don't crash on init failure
let config;
try {
  config = await fetch('/config.json').then(r => r.json());
} catch (err) {
  console.error('Config fetch failed, falling back to defaults', err);
  config = DEFAULTS;
}
export { config };
```

To break a circular TLA deadlock, expose a lazy getter:

```js
// A.mjs
import * as B from './B.mjs';
export function a() { return 'a + ' + B.b(); }    // function, not await

// B.mjs
import * as A from './A.mjs';
export function b() { return 'b + ' + A.a(); }
// no top-level await; deadlock avoided
```

## Step-by-step dry run

```
import chain: index.mjs → app.mjs → config.mjs (TLA: awaits fetch)

t=0   loader: start parsing index.mjs
       parse app.mjs (import found) → parse config.mjs
       config.mjs body: await fetch('/config.json')  → suspended
       app.mjs evaluation: paused (depends on config.mjs)
       index.mjs evaluation: paused (depends on app.mjs)

t=150 fetch resolves → config.mjs body resumes → exports filled → module ready
       app.mjs body resumes → exports filled → module ready
       index.mjs body resumes → runs main()
```

If config fetch threw → all three modules' evaluation promises reject → the top-level `node index.mjs` exits with unhandled rejection.

## How to think aloud in the interview

> "Top-level await turns the module body into an async function effectively. The module's evaluation becomes a Promise. Any importer waits on that promise before its own body runs. Use TLA for one-shot init at boot — config fetch, schema load, secret lookup — and Promise.all in parallel. Deadlock: two modules with TLA importing each other. Break it by lazy getter functions instead of awaited values. CJS doesn't support TLA — boundary."

## Important takeaways

- **TLA only in ESM, not CJS.**
- **Importer pauses until awaited module resolves.**
- **Parallelize with `Promise.all` for independent inits.**
- **Circular TLA = deadlock; resolve via lazy getter pattern.**
- **TLA reject = importer's import throws.**
- **Use for init, not request-time work.**

## Variants

- **Dynamic import with TLA** — `const m = await import('./mod.mjs')` works in any module type; explicit and async-aware.
- **Worker init with TLA** — each worker waits on its own evaluation; orchestrate carefully if workers share an init dep.
- **Sync wrapper for ESM in CJS** — use `import()` dynamically in CJS to bridge.
- **Bundler-specific quirks** — Webpack 5 wraps TLA in async wrappers; older bundlers throw.

## Revision notes

```
top-level await (TLA):
  ESM only (.mjs or "type": "module"); not CJS
  module body becomes async; evaluation = Promise
  importers wait
  
  use:
    Promise.all to parallelize independent awaits
    try/catch for init failure recovery
  
  deadlocks:
    A awaits B; B awaits A → stuck
    fix: expose lazy getters, no top-level await on both sides
  
  CJS bridge: use dynamic await import()
```
