# Top-level `await` in ES modules

> **Difficulty:** Senior   |   **Time:** ~20 min   |   **Prereqs:** [microtask-macrotask-order.md](./microtask-macrotask-order.md), [`04-promises/top-level-await-deadlock-quiz.md`](../04-promises/top-level-await-deadlock-quiz.md)
>
> **Source:** TC39 proposal (Stage 4, ES2022); v8.dev. Asked at Stripe, Atlassian, Cloudflare.

---

## 1. Problem statement

Top-level `await` blocks module evaluation. Two gotchas: (1) sibling modules evaluate in parallel during await; (2) cyclic imports can silently deadlock.

**Verification examples**

| Setup                                              | Behaviour                                              |
|----------------------------------------------------|---------------------------------------------------------|
| `db.mjs` does `await connectDB(); export pool`     | importer waits for evaluation to finish                |
| Two siblings both with TLA awaiting `delay(100)`/`delay(200)` | parallel — total = max(100, 200) = 200ms |
| Cyclic A↔B with TLA awaiting other's exports        | silent hang OR TypeError (uninitialized binding)       |
| TLA in CommonJS                                     | SyntaxError                                             |
| TLA rejection                                       | importer's `import` statement throws                   |

**Constraints**
- ESM only (`.mjs` or `"type": "module"`).
- Sibling modules parallelize evaluation.
- Cyclic TLA → silent hang.
- Use for boot-time init; avoid in libraries (forces consumers to wait).

---

## 2. Plain-English restatement

Inside `.mjs`, you can `await` at the top level without an `async` wrapper. Module evaluation pauses; importing modules wait. The clever bit: sibling modules (different dep branches) evaluate **in parallel** during await — boot time is max(chains), not sum. The gotcha: cyclic imports with TLA can silently deadlock.

---

## 3. Why this matters in interviews

Newest module-loading wrinkle. Probes async semantics literacy, CJS vs ESM awareness, failure-mode reasoning, deadlock detection.

---

## 4. Mental model

```
   Module evaluation = graph traversal:
     1. Parse (sync, all modules)
     2. Link (sync, set up binding graph)
     3. Evaluate (depth-first, post-order)

   With TLA: "finish" means "awaited Promise settles."

   Boot graph:
   main.mjs
     ├── A.mjs (await delay(100))
     └── B.mjs (await delay(200))

   Evaluation:
     C.mjs (leaf, sync) → done.
     A.mjs starts → await delay(100) → SUSPEND.
     B.mjs starts (sibling, runtime moves on) → await delay(200) → SUSPEND.
     wall t=100: A resumes, finishes.
     wall t=200: B resumes, finishes.
     main.mjs evaluates last.

   Total wall time: 200ms (NOT 300ms). Sibling parallelism.

   Cyclic deadlock:
   a.mjs: import { b } from './b.mjs'; await new Promise(()=>{})  ← never resolves
   b.mjs: import { a } from './a.mjs'  ← can't proceed; a never finishes
   → process hangs.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. If three sibling modules each `await fetch(...)`, do they fire sequentially or concurrently?
> 2. Why can't CJS use TLA?
> 3. What happens when a TLA rejects?

---

## 6. Brute force — walked through

### Wrong attempt 1: pre-TLA pattern
```js
let conn;
async function init() { conn = await connectDB(); }
const ready = init();
module.exports = { ready, get conn() { return conn } };
```
Consumers must `await ready` first. Boilerplate, leaks readiness check.

### Wrong attempt 2: TLA in a library
Forces every consumer to pay the await cost. Use IIFE + readiness Promise for lazy init.

### Wrong attempt 3: rely on source-import order
Modules don't strictly evaluate in source order — siblings parallelize.

---

## 7. The unlocking insight

> **TLA suspends module evaluation. Importers wait. Sibling modules (different dep branches) evaluate IN PARALLEL during await. Cyclic TLA → silent hang. Use at boundaries where you need async setup at boot.**

Three properties:

1. **TLA pauses evaluation** — importer suspended too.
2. **Siblings parallelize** — boot time = max chain, not sum.
3. **Cyclic TLA** = silent hang (no error, no log).

---

## 8. Solution (annotated)

```js
// config.mjs
import { readFile } from 'node:fs/promises';
export const config = JSON.parse(await readFile('./config.json', 'utf8'));  // step 1: TLA at module level

// db.mjs
import { config } from './config.mjs';                                       // step 2: waits for config.mjs
import pg from 'pg';
export const pool = new pg.Pool(config.db);
await pool.query('SELECT 1');                                                  // verify connection

// schema.mjs
import { config } from './config.mjs';                                       // also waits for config
const r = await fetch(config.schemaUrl);
export const schema = await r.json();

// server.mjs
import { pool } from './db.mjs';                                              // step 3: siblings parallel
import { schema } from './schema.mjs';                                        //         after config resolves
import express from 'express';
const app = express();
app.listen(3000);
```

**Try it yourself**

```js
// Parallelize independent inits inside one module:
const [config, secrets, schema] = await Promise.all([
  fetch('/config.json').then((r) => r.json()),
  fetchSecrets(),
  fetchSchema(),
]);
export { config, secrets, schema };

// Boot time = max(config, secrets, schema), not sum.

// Cyclic deadlock:
// a.mjs: import './b.mjs'; await new Promise(() => {});
// b.mjs: import { a } from './a.mjs';
// node a.mjs → hangs forever. No error.
```

---

## 9. Step-by-step dry run

```
Graph:
  main.mjs imports A and B
  A.mjs imports C; awaits delay(100)
  B.mjs imports C; awaits delay(200)
  C.mjs: no TLA, just exports a constant

Phase 1 - Parse (all four modules):
  Recursively parse from main entry.

Phase 2 - Link:
  Set up binding graph.

Phase 3 - Evaluate (depth-first, post-order):
  C.mjs first (leaf, no TLA). Sync. Done.
  A.mjs starts:
    body runs; hits await delay(100). SUSPEND A.
  B.mjs starts (sibling - runtime moves on):
    body runs; hits await delay(200). SUSPEND B.
  
  wall t=100: A.mjs resumes; body finishes; A's eval promise resolves.
  wall t=200: B.mjs resumes; body finishes; B's eval promise resolves.
  
  main.mjs evaluates last (its dependencies all done).

Total wall time: 200ms (max), not 300ms (sum).
```

---

## 10. Common confusion + traps

1. **TLA works in CommonJS** — no, ESM only. CJS `require` is sync.
2. **Sibling modules sequential** — no, parallel during await.
3. **TLA inside a route handler** — TLA is only at module top level; inside fns it's regular `await`.
4. **Cyclic TLA throws an error** — sometimes; often just hangs silently.
5. **`process.exit(0)` inside TLA** — can prevent graceful logging.
6. **Hot reload doesn't re-evaluate** — module instances cached, including their evaluation promise.
7. **TLA in libraries** — forces consumers to pay; bad for lazy init.

---

## 11. Senior follow-ups & variants

### Variant 1 — Polyfill for environments without TLA
Wrap module body in async IIFE; export a readiness Promise alongside values.

### Variant 2 — TLA reject behavior
Module's evaluation Promise rejects. In Node, process exits non-zero on unhandled top-level errors.

### Variant 3 — Webpack TLA chunks
TLA modules become async chunks; importers `await` chunk readiness.

### Variant 4 — Dynamic `import()` of TLA module
Returns Promise that settles when TLA resolves. Used to gate startup.

### Variant 5 — Workers + TLA
Each worker evaluates its modules separately. Per-worker TLA.

---

## 12. How to think aloud

> "Top-level await blocks module evaluation. Importers wait. Sibling modules — different dep branches — evaluate in parallel during await; total boot is max(chains), not sum. ESM only — `.mjs` or `'type':'module'`. CJS can't use TLA. Cyclic imports + TLA can silently hang (no error, no log). Use TLA at boundaries that need async setup at boot: config fetch, DB pool init, WASM load, schema fetch. Avoid in libraries — forces every consumer to pay the await cost. Trap: thinking TLA in CJS works; assuming sequential evaluation; cyclic deadlock; trapping in a library."

---

## 13. 60-second revision

> - **ESM only** (`.mjs` or `"type":"module"`); NOT CJS.
> - **Blocks module evaluation** until awaited Promise settles.
> - **Sibling modules parallelize** during await — boot = max, not sum.
> - **`Promise.all`** inside a module for parallel independent inits.
> - **Cyclic TLA → silent hang** (the JS deadlock).
> - **TLA reject** = importer's import statement throws.
> - **Use for** boot-time init; **avoid in libraries**.
> - **CJS bridge:** `await import('./esm.mjs')` dynamic import.
> - **Trap:** TLA in CJS; sequential assumption; cyclic deadlock; in libraries.

---

**Related:** [`04-promises/top-level-await-deadlock-quiz.md`](../04-promises/top-level-await-deadlock-quiz.md) · [`01-hoisting/circular-import-live-binding-quiz.md`](../01-hoisting/circular-import-live-binding-quiz.md) · [`04-promises/iife-async-bootstrap.md`](../04-promises/iife-async-bootstrap.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md), [`concepts/event-loop.md`](../../concepts/event-loop.md)
