# Top-level `await` in ES modules

## Source
- TC39 proposal (Stage 4, ES2022): https://github.com/tc39/proposal-top-level-await
- v8.dev: https://v8.dev/features/top-level-await
- Node.js ESM docs: https://nodejs.org/api/esm.html#top-level-await
- Module evaluation algorithm spec: https://tc39.es/ecma262/#sec-moduleevaluation

## Why this question matters in interviews
Top-level await **blocks module evaluation**. In a microservice that pre-loads config, validates schema, or warms a DB pool at boot, this is great — you can do it cleanly without an async IIFE wrapper. But it has **two real gotchas**: it deadlocks under cyclic imports (one of the few ways to actually deadlock JS), and **sibling modules execute in parallel** during await — which surprises engineers who think modules are strictly sequential. Senior interviews ask this to gauge whether you understand the ESM evaluation algorithm (a graph traversal, not a linear walk).

## Concepts involved

### What it does
You can `await` at the top level of an ES module — no `async function` wrapper required:

```js
// db.mjs
const conn = await connectDB();   // module evaluation pauses here
export { conn };
```

```js
// main.mjs
import { conn } from './db.mjs';  // waits for db.mjs to finish evaluating
console.log(conn);                 // conn is ready
```

The importing module's evaluation is **suspended** until the awaited module's evaluation completes.

### The evaluation algorithm (the senior detail)
ESM evaluation is a **graph traversal**. The spec algorithm:
1. **Parse** all modules in the graph (sync, no execution).
2. **Link** all imports/exports (sync, sets up the binding graph).
3. **Evaluate**: depth-first, post-order. A module is evaluated **only after** all its dependencies finish evaluating. With top-level await, "finish" means "the awaited Promise settles."

Crucially: **sibling modules (different branches of the dep graph) can evaluate in parallel** during top-level await. If `main` imports `A` and `B`, and `A` does `await delay(100)`, then `B` evaluates while `A` is waiting.

### Syntax to lock in
```js
// config.mjs
export const config = await fetch('/config.json').then(r => r.json());

// schema.mjs
export const schema = await loadSchemaFromS3();

// server.mjs
import { config } from './config.mjs';   // both config.mjs and schema.mjs
import { schema } from './schema.mjs';   // evaluate in parallel
// server.mjs evaluates only after BOTH settle.
```

### The cyclic deadlock
```js
// a.mjs
import { b } from './b.mjs';
export const a = await Promise.resolve('A');

// b.mjs
import { a } from './a.mjs';
export const b = await Promise.resolve('B');
```

In cyclic imports without top-level await, ESM handles cycles via **live bindings** (you get an uninitialized binding that fills in later). With top-level await, the spec rule: a module **can't be awaited if it's an ancestor in the dep cycle that hasn't started evaluating yet**. Specifically, this case isn't quite a deadlock — but if both modules `await` *each other's exports*, you do get a TypeError from accessing uninitialized bindings. **The classic deadlock case** is:

```js
// a.mjs
import { b } from './b.mjs';
console.log(b);
await new Promise(() => {}); // forever pending

// b.mjs — imports a, can never complete because a is still awaiting
```

### Edge cases
1. **CommonJS modules can't use top-level await** — `.cjs` and the implicit `commonjs` package type. Only `.mjs` or `"type": "module"`.
2. **`import()` (dynamic import)** of a TLA module returns a Promise that settles once the TLA resolves. Used to gate startup.
3. **Async errors at top level** become rejected module evaluation — the import throws. Wrap in try/catch is impossible at top level; use `import().catch(...)` from the parent.
4. **Order of execution**: even with TLA, the post-order property holds — a module's body runs *after* all its deps. TLA just inserts an async pause in the middle of evaluation.
5. **Workers can use TLA** in their entry modules.
6. **Hot reloading is hard** — module instances are cached; the TLA promise is cached too. Re-importing the same path doesn't re-evaluate.
7. **`process.exit(0)` inside a TLA module** can prevent graceful logging — be careful.

## Brute force approach
Pre-TLA pattern (still common in CommonJS):

```js
let conn;
async function init() {
  conn = await connectDB();
}
const ready = init();    // call immediately, store the promise
module.exports = { ready, get conn() { return conn; } };
```

Consumers must `await ready` first. Boilerplate, error-prone, leaks the "is it ready?" question into every consumer. TLA replaces this entirely.

## Optimal approach
Use TLA at module boundaries that represent "this module needs async setup at boot." Common cases:
- Loading config (env-backed JSON, S3, vault).
- Connecting to a DB and exporting a pool.
- Loading a WASM module.
- Schema validation that needs to fetch a remote spec.

Avoid TLA inside library modules where consumers may want lazy init — they can't avoid paying the await cost.

## Solution (JavaScript)

### A real boot sequence

```js
// config.mjs
import { readFile } from 'node:fs/promises';
export const config = JSON.parse(await readFile('./config.json', 'utf8'));
console.log('config loaded');
```

```js
// db.mjs
import { config } from './config.mjs';     // waits for config to finish
import pg from 'pg';
export const pool = new pg.Pool(config.db);
await pool.query('SELECT 1');               // verify connection
console.log('db ready');
```

```js
// schema.mjs
import { config } from './config.mjs';     // also waits for config
const r = await fetch(config.schemaUrl);
export const schema = await r.json();
console.log('schema ready');
```

```js
// server.mjs
import { pool } from './db.mjs';
import { schema } from './schema.mjs';
// Both db.mjs and schema.mjs are SIBLINGS — they evaluate in parallel
// (after config.mjs finishes).
import express from 'express';
const app = express();
app.listen(3000, () => console.log('listening, all systems ready'));
```

Boot sequence:
1. Parse and link entire graph (~ms).
2. `config.mjs` evaluates first (it's the root dependency).
3. `db.mjs` and `schema.mjs` start evaluating **in parallel** as soon as config finishes.
4. `server.mjs` evaluates only after both finish.

If config takes 50ms, db takes 200ms, schema takes 300ms: total boot is **50ms + max(200, 300) = 350ms**, not 50+200+300=550ms. The parallelism is automatic.

### The deadlock case

```js
// a.mjs
import './b.mjs';
await new Promise(() => {}); // never resolves
export const a = 1;
```

```js
// b.mjs
import { a } from './a.mjs';  // can't access a until a.mjs finishes — but a.mjs is awaiting forever
console.log('b:', a);
```

Running `node a.mjs` (or anything that imports a.mjs): the process hangs. No error, no log. Same flavor as `process.nextTick` starvation — silent hang.

## Step-by-step dry run

Consider this graph:

```
main.mjs imports A.mjs and B.mjs
A.mjs imports C.mjs and does `await delay(100)`
B.mjs imports C.mjs and does `await delay(200)`
C.mjs has no top-level await, just exports a constant
```

Evaluation order:
1. **Parse**: all four modules parsed.
2. **Link**: import/export bindings wired up.
3. **Evaluate**:
   - C.mjs first (it's a leaf, no async). Returns sync.
   - A.mjs starts evaluating. Hits `await delay(100)`. **Suspends.**
   - B.mjs starts evaluating (sibling — runtime moves on). Hits `await delay(200)`. **Suspends.**
   - Wall-clock 100ms passes. A.mjs resumes, finishes evaluation.
   - Wall-clock 200ms passes (total). B.mjs resumes, finishes.
   - main.mjs evaluates last.

**Total wall-clock time**: 200ms (not 100+200=300ms). Sibling parallelism.

If you had three sibling modules each with a 100ms `await fetch`, **all three fetches fire concurrently** during evaluation.

## Important takeaways

**Syntax to memorize**
- `await expr` at the top level of `.mjs` (or `"type": "module"` `.js`).
- `try { await ... } catch (e) { ... }` at top level — yes, this works (the try/catch wraps the await, not a fn).
- Importing a TLA module suspends the importer until evaluation finishes.

**Patterns to reuse**
- Boot-time config / schema / db init.
- Loading WASM at module load.
- Conditional polyfill loading: `if (!globalThis.fetch) await import('node-fetch').then(...)`.

**Common mistakes**
- Using TLA in a library where consumers want lazy init — they're forced to pay the await.
- Cyclic imports + TLA → silent hang.
- Assuming modules evaluate in source-import order — they don't strictly; siblings parallelize.
- Trying TLA in CommonJS — syntax error.
- Forgetting that import errors at the TLA level reject the import — consumers must `import().catch` to handle.

**Related questions**
- ESM live bindings (import is a live view, not a copy)
- Dynamic `import()` returning a Promise
- CommonJS vs ESM interop

## Variants

1. **"How would you implement a polyfill / fallback for environments without TLA?"** — wrap the module body in an async IIFE that resolves a sentinel Promise, export that Promise alongside the values.
2. **"What happens if the top-level await rejects?"** — the module's evaluation Promise rejects. Importers see a rejected import; in Node, the process exits non-zero on unhandled top-level errors.
3. **"How does Webpack handle TLA in chunks?"** — TLA modules become async chunks; the chunk's "ready" promise is awaited by importers. Adds runtime weight; check your bundler config.
4. **"Can `await` at top level starve other modules?"** — no. Sibling modules evaluate in parallel. Only **importers** wait.

## Revision notes

> **Top-level await — 60 second recap**
> - Allowed at the top of `.mjs` (or `"type":"module"`). NOT in CommonJS.
> - **Blocks module evaluation** until the awaited Promise settles.
> - Sibling modules **evaluate in parallel** — total boot time = longest chain, not sum.
> - **Use for**: boot-time config, DB pool init, WASM load, schema fetch.
> - **Avoid in libraries** — forces every consumer to pay the await.
> - **Cyclic imports + TLA → silent hang** (the JS deadlock).
> - Top-level errors reject the module's evaluation Promise — importers fail.
> - `import('./mod.mjs').then(m => ...)` is how you gate consumption.
