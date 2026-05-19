# Top-Level Await — deadlock quiz & module-evaluation semantics

> **Difficulty:** Medium   |   **Time:** ~20 min   |   **Prereqs:** [`concepts/promises.md`](../../concepts/promises.md), [iife-async-bootstrap.md](../02-closures/iife-async-bootstrap.md)
>
> **Source:** ES2022 top-level await (TLA) in ES modules. Asked at Stripe, Atlassian, Cloudflare.

---

## 1. Problem statement

**Setup**
```ts
// config.mjs (ESM)
const data = await fetch('/config.json').then(r => r.json());
export const config = data;
```

**Input / Output examples**

| Setup                                                                                | Behaviour                                              |
|--------------------------------------------------------------------------------------|---------------------------------------------------------|
| Module A awaits at top level                                                          | A's evaluation becomes async; importers wait           |
| `await loadConfig()` at top of CJS file                                              | SyntaxError — CJS doesn't support TLA                  |
| Module A awaits B; Module B awaits A                                                  | **Deadlock** — both stuck waiting                      |
| Parallel inits via `Promise.all`                                                      | Boot time = max, not sum                               |
| TLA reject                                                                            | importer's import statement throws                     |

**Constraints**
- TLA **only in ESM**, not CJS.
- Module evaluation becomes a Promise; importers wait.
- Circular TLA imports = deadlock — fix with lazy getters.
- Use for **initialization**, not request-time work.

---

## 2. Plain-English restatement

Top-level `await` looks innocent — `const config = await loadConfig();` at the top of a module. But TLA *changes module evaluation semantics*: a module that awaits delays the evaluation of *every importer*. Two TLA modules waiting on each other's exports = deadlock. CommonJS doesn't support it. Use it for boot-time init, parallelize independent awaits with `Promise.all`, and break circular deps with lazy getters.

---

## 3. Why this matters in interviews

Top-level `await` is the newest module-loading wrinkle. Interviewers probe: (1) async semantics literacy — TLA turns module bodies into async functions; (2) CJS vs ESM awareness — TLA is ESM-only; (3) failure-mode reasoning — what happens when init promises reject; (4) deadlock detection — circular TLA. Use TLA for *initialization*, not request-time work; bundlers transform it.

---

## 4. Mental model

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
   app.mjs   imports  config.mjs  imports  database.mjs  imports ...
   evaluation order: depth-first; if any has TLA, all upstream wait
```

**Deadlock:**

```
   A.mjs:                    B.mjs:
   import { b } from './B'   import { a } from './A'
   const x = await b()       const y = await a()
   export const a = ...      export const b = ...
   
   A waits for B (import)
   B waits for A (import)
   → deadlock; runtime throws or stalls
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. If `config.mjs` does `await fetch(...)` at top, and `app.mjs` imports it, when does `app.mjs`'s body run?
> 2. Can you use TLA in a `.js` file with `"type": "commonjs"` in package.json?
> 3. If module A imports B and B imports A, both with TLA — what happens?

---

## 6. Brute force — walked through

### Wrong attempt 1: sequential awaits at top
```js
const a = await loadA();   // 200ms
const b = await loadB();   // 200ms (after a)
const c = await loadC();   // 200ms
// total: 600ms
```
Parallelize independent inits with `Promise.all` → 200ms.

### Wrong attempt 2: TLA in CJS
```js
// boot.cjs
const cfg = await loadConfig();   // SyntaxError
```
CJS doesn't support TLA. Use async IIFE: `(async () => { ... })()`.

### Wrong attempt 3: circular TLA
```js
// A.mjs: const x = await b();    B.mjs: const y = await a();
```
Deadlock. Restructure with lazy getters (functions, not awaited values).

---

## 7. The unlocking insight

> **TLA turns the module body into an async function. The module's evaluation becomes a Promise. Any importer waits on that promise before its own body runs. Use `Promise.all` to parallelize independent inits. Deadlock: circular TLA imports — fix by exposing lazy getter functions instead of awaited values.**

Three rules:

1. **ESM only** — CJS `require()` is synchronous; cannot await modules.
2. **Importers pause** — module evaluation is depth-first; TLA inserts await points.
3. **Reject = importer's import throws** — TLA's promise becomes the module's evaluation result; rejection propagates up the import chain.

---

## 8. Solution (annotated)

```js
// config.mjs — TLA-safe, parallelized init
const [config, secrets, schema] = await Promise.all([     // step 1: parallel inits
  fetch('/config.json').then((r) => r.json()),
  fetchSecrets(),
  fetchSchema(),
]);
export { config, secrets, schema };

// app.mjs — uses the module; evaluation waits for config.mjs to settle
import { config } from './config.mjs';                     // step 2: import waits
import express from 'express';
const app = express();
app.get('/x', (req, res) => res.json({ env: config.env }));
app.listen(3000);

// Recovery: don't crash on init failure
let config;
try {
  config = await fetch('/config.json').then((r) => r.json());
} catch (err) {
  console.error('Config fetch failed, falling back to defaults', err);
  config = DEFAULTS;
}
export { config };
```

**Break circular TLA deadlock with lazy getters:**

```js
// A.mjs
import * as B from './B.mjs';
export function a() { return 'a + ' + B.b(); }    // function, not await

// B.mjs
import * as A from './A.mjs';
export function b() { return 'b + ' + A.a(); }
// no top-level await; deadlock avoided
```

**Try it yourself**

```js
// Run with node --experimental-top-level-await or node 14.8+ on .mjs / "type": "module"
const result = await Promise.all([
  loadDb(),
  loadCache(),
  loadConfig(),
]);
export const services = result;
```

---

## 9. Step-by-step dry run

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

If config fetch threw → all three modules' evaluation promises reject → `node index.mjs` exits with unhandled rejection.

---

## 10. Common confusion + traps

1. **"TLA makes startup faster"** — only if you parallelize with `Promise.all`; serializing awaits makes it slower.
2. **"TLA works in CJS"** — no, `require()` is synchronous.
3. **"TLA in a route handler"** — TLA is only at module top level. Inside functions it's plain `await` (requires `async`).
4. **"Imports are synchronous"** — with TLA, the importer pauses.
5. **"Workers re-evaluate modules from scratch"** — yes; TLA runs per worker.
6. **Circular TLA = deadlock** — fix with lazy getter functions.
7. **TLA reject propagates** — importer's import statement throws.

---

## 11. Senior follow-ups & variants

### Variant 1 — Dynamic import with TLA
`const m = await import('./mod.mjs')` works in any module type; explicit and async-aware.

### Variant 2 — Worker init with TLA
Each worker waits on its own evaluation; orchestrate carefully if workers share an init dep.

### Variant 3 — Sync wrapper for ESM in CJS
Use `import()` dynamically in CJS to bridge: `(async () => { const mod = await import('./esm.mjs'); ... })()`.

### Variant 4 — Bundler-specific quirks
Webpack 5 wraps TLA in async wrappers; older bundlers throw. Vite supports TLA natively.

---

## 12. How to think aloud

> "Top-level await turns the module body into an async function effectively. The module's evaluation becomes a Promise. Any importer waits on that promise before its own body runs. Use TLA for one-shot init at boot — config fetch, schema load, secret lookup — and `Promise.all` in parallel. Deadlock: two modules with TLA importing each other. Break it by lazy getter functions instead of awaited values. CJS doesn't support TLA — the boundary."

---

## 13. 60-second revision

> - **TLA only in ESM** (`.mjs` or `"type": "module"`); not CJS.
> - **Module body becomes async**; evaluation = Promise.
> - **Importers wait** on each TLA module before their body runs.
> - **Parallelize with `Promise.all`** for independent inits.
> - **Circular TLA = deadlock**; fix with lazy getter functions.
> - **TLA reject = importer's import throws.**
> - **Use for init, not request-time work.**
> - **CJS bridge:** `await import('./esm.mjs')` dynamic import.
> - **Trap:** sequential awaits adds latency; CJS doesn't support TLA; circular TLA deadlocks.

---

**Related:** [iife-async-bootstrap.md](../02-closures/iife-async-bootstrap.md) · [build-promise-from-scratch.md](./build-promise-from-scratch.md) · [`01-hoisting/import-vs-require-hoisting.md`](../01-hoisting/import-vs-require-hoisting.md) · [`01-hoisting/circular-import-live-binding-quiz.md`](../01-hoisting/circular-import-live-binding-quiz.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md), [`concepts/event-loop.md`](../../concepts/event-loop.md)
