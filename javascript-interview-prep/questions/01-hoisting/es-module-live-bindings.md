# ES module imports — hoisted live bindings

## Source
- Canonical senior-JS interview problem (ECMA-262 §16 Modules, V8 / Node ESM design notes, "JavaScript Modules" by Lin Clark).
- MDN reference: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/import

## Why this question matters in interviews
ES module imports look like simple variable bindings, but they have **two non-obvious properties** that every senior backend engineer must know:
1. **Imports are hoisted** to the top of the module — they execute before any code in the module body.
2. **Imports are live read-only bindings** — not copies. If the exporting module mutates the exported value, every importer sees the new value *immediately*, but cannot themselves reassign it.

This trips up engineers coming from CommonJS, where `const x = require('./mod').x` snapshots the value at require-time. The CJS/ESM interop is a *huge* source of bugs in Node 18+ codebases that mix both. Interviewers ask this because it tests: knowledge of the module phases (parse → instantiate → evaluate), the resolution algorithm, and live binding semantics. Bonus: cyclic imports — handling them correctly depends entirely on understanding hoisting.

## Concepts involved

### Syntax to lock in
```js
// a.js
export let counter = 0;
export function inc() { counter++; }

// b.js
import { counter, inc } from './a.js';
console.log(counter); // 0
inc();
console.log(counter); // 1  — live binding, NOT a stale copy
// counter++;         // SyntaxError or TypeError — imports are read-only from the importer's side
```

CommonJS equivalent (different semantics!):
```js
// a.cjs
let counter = 0;
function inc() { counter++; }
module.exports = { counter, inc };

// b.cjs
const { counter, inc } = require('./a.cjs');
console.log(counter); // 0
inc();
console.log(counter); // 0  — STALE. The destructure snapshotted the value at require time.
```

### Runtime / engine behavior — three module phases
ES modules execute in three phases (ECMA-262 §16.2.1.5):

1. **Parsing / Construction:** the source is parsed to AST. Static `import` / `export` declarations are extracted. Dependencies are loaded recursively.
2. **Linking / Instantiation:** all imports are resolved and bound. Each `import { x } from './a'` creates a **slot** in the importing module's environment that points directly at `a.js`'s `x` binding cell. **No code has run yet.** Imports are now wired up but values aren't yet computed.
3. **Evaluation:** module bodies execute in post-order DFS of the dep graph. Side-effects run; `let`/`const`/function declarations are initialized. Imported slots now read live from the exporting module's bindings.

**Imports are hoisted** because phase 2 (linking) runs before phase 3 (evaluation). The binding exists from the very first line of the module body, even if the `import` statement is written at the bottom (which is illegal anyway — static imports must be at the top of the source, though they're hoisted regardless of position).

### Edge cases (the traps)
1. **Live binding direction** — the importer sees changes the exporter makes. The importer **cannot** mutate the binding (read-only on the importer side).
2. **`export default x`** — if `x` is a primitive value (`export default 42`), it's snapshotted; if it's an object, the binding is still live but the *reference* doesn't change (only the object's contents do).
3. **`export { x as y }`** — renames the export; importer sees `y` as live-bound to `x`.
4. **TDZ for imports** — if you import from a module that hasn't finished evaluating yet (cyclic import case), reading the import gives the binding's current value, which may be `undefined` if the exporter's `let` hasn't been initialized.
5. **Dynamic `import()`** — returns a Promise of the module namespace object. The namespace object is also a live view, but dynamic imports are **not hoisted**; they run when the call is reached.
6. **Top-level `await`** — halts the module's evaluation phase. Modules importing it must wait. Can deadlock in cycles.
7. **CJS interop in Node** — `import x from './foo.cjs'` works because Node wraps CJS exports in a synthetic namespace, but **destructuring named imports** from a CJS module only works for statically analyzable `module.exports = { ... }`. Dynamic `module.exports` shapes break this.
8. **Reassigning an export** — only the exporting module can reassign its own `export let x`. Importers cannot.

## Brute force approach
"`import { x } from './a'` is like `const x = require('./a').x`." This is the CommonJS mental model. It's wrong for ESM:
- Reading `x` later in time sees the *current* value, not the value at import time.
- The import is hoisted; the require is not.
- Cyclic imports work differently — ESM threads through the cycle via the live binding mechanism; CJS produces a partial exports object that snapshots whatever was exported before the cycle re-entered.

Drop the CJS mental model when reading ESM code.

## Optimal approach
**Three-phase model with binding cells.** For every `import` you see:
1. Phase 2 (linking) creates a **binding cell** in the current module that points at the exporting module's binding cell.
2. Phase 3 (evaluation) runs module bodies in dep-graph post-order.
3. Reading the import is a **dereference of the cell** — always live.

Annotate code traces with `// HOISTED: import x` at the top, and `// READ: x via live cell → ${value}` at each access.

## Solution (JavaScript)

```js
// ============================
// File: counter.mjs
// ============================
export let count = 0;

export function increment() {
  count++;
}

// Mutating the value AFTER the module first evaluates:
setTimeout(() => { count = 100; }, 0);

// ============================
// File: consumer.mjs
// ============================
import { count, increment } from './counter.mjs';

console.log('initial:', count);     // 0
increment();
console.log('after inc:', count);   // 1  — live binding reflects exporter's mutation
// count = 999;                     // SyntaxError: Assignment to constant variable / read-only

setTimeout(() => {
  console.log('after timeout:', count);  // 100  — exporter mutated; importer sees it
}, 10);

// ============================
// Hoisting demo: import works even when "written" at the bottom
// ============================
// (Note: lint/parser conventions put imports at the top, but the spec hoists them.)

console.log(greet('Sam'));    // works! greet is hoisted via import
import { greet } from './greeter.mjs';
```

## Step-by-step dry run

Input dep graph: `consumer.mjs` imports from `counter.mjs`.

```js
// === Phase 1: Parsing & Construction ===
// Parser scans consumer.mjs, finds: import { count, increment } from './counter.mjs'.
// Loader fetches counter.mjs, parses it.
// Dependency graph built: consumer → counter.

// === Phase 2: Linking / Instantiation ===
// For each module, environment records are created.
//
// counter.mjs env:
//   count: <cell, uninitialized — TDZ>
//   increment: <cell, function object created in this phase since it's a FunctionDeclaration>
//
// consumer.mjs env:
//   count: <pointer to counter.mjs's count cell>
//   increment: <pointer to counter.mjs's increment cell>
//
// NO module BODY has run yet. count is in TDZ.

// === Phase 3: Evaluation (post-order DFS) ===
// counter.mjs evaluates first (it's a dependency).
//   export let count = 0   → counter.count cell now holds 0.
//   export function increment ... — already initialized in linking phase, no-op here.
//   setTimeout(...) — registers the timer, doesn't fire.
//
// consumer.mjs evaluates.
//   console.log('initial:', count)
//     Read consumer.count cell → it points at counter.count cell → 0.
//     prints: "initial: 0"
//
//   increment()
//     Call counter.increment. It does count++ INSIDE counter's scope.
//     counter.count cell is now 1.
//
//   console.log('after inc:', count)
//     consumer.count cell → counter.count cell → 1.
//     prints: "after inc: 1"
//
//   // count = 999  would be a SyntaxError at parse time
//      ("Assignment to constant variable" — imports are read-only).

// === Microtask / task queue drains, ~10ms later ===
//   First, counter.mjs's setTimeout fires: count = 100 (legal — counter owns it).
//   Then, consumer.mjs's setTimeout fires: console.log('after timeout:', count) → 100.
```

Output (assuming a single tick of the loop):
```
initial: 0
after inc: 1
after timeout: 100
```

For the `greet` example at the bottom of the file, the hoisting is the key insight: even though `import { greet }` is the last line of source, Phase 2 wired `greet` before Phase 3 started, so the `console.log(greet('Sam'))` at line 1 works.

## Important takeaways

**Syntax to memorize**
- Static `import` declarations are **hoisted to the top of the module** — order in source doesn't matter for binding visibility.
- Imports are **live read-only views** of the exporter's bindings, not copies.
- Only the **exporter** can mutate its own `export let x`. Importers see the mutation immediately.

**Patterns to reuse**
- Counters, registries, plugin systems: `export let registry = new Map()` + accessor functions in the exporting module. All importers see the same Map.
- For "config that changes at runtime", export a mutable variable from one module and provide setters — importers stay in sync.
- For "snapshot at import time" semantics, export a getter or a function — `export function getCount() { return count; }`.

**Common mistakes**
- Assuming destructured CJS `const { x } = require('./a')` behaves like ESM `import { x } from './a'` — it doesn't.
- Trying to reassign an import: `count = 5` from the importer — `SyntaxError` (parse-time check) or `TypeError` in strict.
- Reading an imported `let` in a cyclic import before the exporting module has reached its initializer — gives `undefined` (TDZ for cycles).
- Expecting dynamic `import()` to be hoisted — it isn't. It runs when the call statement is reached.

**Backend relevance**
- Node 18+ ESM: every microservice config / DI container that exports mutable state relies on live bindings.
- CJS/ESM interop bugs: when importing a CJS file into ESM, named imports may break if the CJS file uses dynamic `module.exports = { ... }` patterns the static analyzer can't see.
- Top-level await: a "ready" gate at module init time. Imports of modules with TLA wait for that module's evaluation to settle.

## Variants

1. **Cyclic imports** — `a.mjs` imports from `b.mjs` which imports from `a.mjs`. Walk through phase 2 + 3 ordering. Show why exporting *functions* (initialized in phase 2) is safe but exporting *let-initialized values* (initialized in phase 3) can produce `undefined` reads during the cycle.
2. **Dynamic `import()` ordering** — async import inside a function; show it does NOT hoist; it's a microtask returning a Promise. Compare timing to static.
3. **CJS interop** — same `count` example but with `require('./counter.cjs')`. Show the destructure snapshots and `increment()` doesn't affect the local copy. Discuss the `module.exports` getter trick to fake live bindings in CJS.

## Revision notes

> **ES module live bindings — 60 second recap**
> - ESM has **three phases**: parse → link → evaluate.
> - `import` declarations are **hoisted** — wired up in phase 2 before any code runs in phase 3.
> - Imports are **live read-only views**, not copies. Exporter mutations are visible to importers immediately.
> - Importers **cannot** reassign imports (`SyntaxError`/`TypeError`).
> - Compare to **CJS**: `const { x } = require(...)` snapshots at require time. Different semantics entirely.
> - **Cycles:** ESM threads via live bindings — `import`-ed values may be `undefined` if the exporter hasn't reached the initializer. Function declarations are safe (initialized in linking).
> - **Dynamic `import()`** returns a Promise, runs at call time — **not hoisted**.
> - **Top-level await** halts a module's evaluation; importers wait. Can deadlock in cycles.
> - **Interop trap:** named destructure from CJS-only files via ESM may break if `module.exports` is dynamic.
> - Use exported getters / accessor functions when you want snapshot semantics from ESM.
