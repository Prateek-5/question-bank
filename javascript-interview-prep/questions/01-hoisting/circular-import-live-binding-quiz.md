# Circular Import — Live Binding Quiz

## Source / Origin
- ES Modules spec; classic Node interop bug.
- Asked at: Stripe, Cloudflare, Razorpay, anywhere with non-trivial module graphs.
- Concept reference: `concepts/hoisting.md`, sibling `es-module-live-bindings.md`, `import-vs-require-hoisting.md`.

## Why this question matters in interviews
"A imports B; B imports A. Predict the output." This is the canonical ESM gotcha. Different from CJS: ESM uses *live bindings* and a *2-phase load* (link before eval), so circular imports work surprisingly often — but with traps around TDZ and "used before initialized." Senior bar: you can predict the order, identify which binding is `undefined` in the cycle, and propose the fix (refactor or lazy access).

## Concepts involved

### Syntax to lock in
```js
// a.mjs
import { b } from './b.mjs';
export const a = 'a-value';
console.log('a sees b =', b);

// b.mjs
import { a } from './a.mjs';
export const b = 'b-value';
console.log('b sees a =', a);

// Output (Node ESM):
//   b sees a = undefined        ← a not yet initialized
//   a sees b = 'b-value'
```

### Edge cases / interview traps
1. **ESM 2-phase load**: (1) link all imports across the graph (resolve dependencies, allocate bindings); (2) evaluate modules in order.
2. **Bindings are LIVE.** When the importer reads `a`, it's reading the live cell. If at that moment `a` is not yet initialized, you see `undefined` (or TDZ throw for `let`/`const`).
3. **The entry point determines order.** If you `node a.mjs`: a is parsed first; a imports b; b is parsed; b imports a (already parsed, no re-parse); b evaluates first → sees `a` not yet assigned → `undefined`; then a evaluates.
4. **`const`/`let` exports throw on TDZ access**, not return undefined. `var` would return undefined.
5. **`export default`** under a cycle is sometimes seen as undefined too if accessed before the defining module evaluates.
6. **CJS cycles** behave differently — `require` returns whatever `module.exports` looked like at the moment, which is often `{}` (the empty initial export).
7. **Bundlers** sometimes break cycles by inlining; behavior changes between dev and prod.
8. **Fix patterns**: lazy access (function-level instead of top-level), restructure to remove the cycle, or use `import()` dynamically.

## Mental Model

ESM module loading is **graph construction then sequential evaluation**:

```
   Phase 1 — LINK:
     parse all modules in the dep graph
     allocate binding slots for every imported name
     all bindings start in TDZ (or hold undefined for `var`/`function` decls)

   Phase 2 — EVALUATE (depth-first, post-order on first encounter):
     run each module's body
     when an export statement is reached, the binding leaves TDZ
     importers can read it (live)

   With a cycle:
     A imports B, B imports A
     start at entry → link both → eval order depends on traversal
     whichever evaluates SECOND can see the FIRST's exports
     whichever evaluates FIRST sees the SECOND's exports as TDZ (or undefined)
```

```
   entry: a.mjs
   parse a → discovers import b
   parse b → discovers import a (already parsed, skip)
   evaluation order: b first (deepest unfinished), then a
   
   b's body runs:
     console.log(a)   → a is in TDZ → ReferenceError (for `const`/`let`)
                       or undefined (for `var`/`function`)
   
   a's body runs:
     console.log(b)   → b is now fully exported → prints 'b-value'
```

## Why interviewers care

- **Module-graph mental model** — separates senior from mid.
- **Live binding awareness** — the entire reason ESM cycles work better than CJS.
- **Debugging skill** — circular-import bugs manifest as `undefined` reads.

## Common beginner confusion

- **"Cycles are illegal."** Both ESM and CJS allow them — they may just produce surprises.
- **"`const` exports always have values."** Not before their module evaluates.
- **"Refactoring to a single file fixes it."** Often the right answer, but sometimes shared utilities legitimately need the cycle.
- **"Bundlers treat cycles identically."** No — Webpack 5, Rollup, esbuild each have edge cases.

## Brute force approach

Rip the cycle by inlining one module's contents into the other. Loses modularity.

## Optimal approach

Two viable paths:

1. **Lazy access** — call the imported value only inside a function body (not at top level). By the time the function runs, the cycle has resolved.
2. **Restructure** — extract the shared piece into a third module that neither cycles back.

```js
// a.mjs
import * as B from './b.mjs';
export const a = 'a-value';
export function useB() { return B.b; }     // lazy — works fine

// b.mjs
import * as A from './a.mjs';
export const b = 'b-value';
export function useA() { return A.a; }     // lazy — works fine
```

## Solution (JavaScript)

```js
// Diagnose: log binding state at module-eval time
// Common fix: extract shared
// shared.mjs
export const CONFIG = { url: 'http://x' };

// a.mjs
import { CONFIG } from './shared.mjs';
export const a = `a:${CONFIG.url}`;

// b.mjs
import { CONFIG } from './shared.mjs';
export const b = `b:${CONFIG.url}`;

// No cycle; no surprises.
```

```js
// If a cycle is necessary, use namespace + lazy access
// circular-graph-of-types.mjs
import * as Node from './node.mjs';
export const Edge = {
  describe(edge) { return `${edge.from} → ${edge.to}`; },
  fromNodes(a, b) { return Node.Node.makeEdge(a, b); },   // lazy access
};

// node.mjs
import * as Edge from './circular-graph-of-types.mjs';
export const Node = {
  makeEdge(a, b) { return { from: a, to: b }; },
  edgeDescribe: (e) => Edge.Edge.describe(e),             // lazy access
};
```

## Step-by-step dry run

```js
// a.mjs
import { b } from './b.mjs';
console.log('a body:', b);
export const a = 1;
```

```js
// b.mjs
import { a } from './a.mjs';
console.log('b body:', a);
export const b = 2;
```

Run `node a.mjs`:

```
LINK phase:
  parse a.mjs → imports {b from './b.mjs'}
  parse b.mjs → imports {a from './a.mjs'}
  bindings allocated:
    a's binding (in a.mjs)  : TDZ
    b's binding (in b.mjs)  : TDZ

EVALUATE phase (depth-first, but a's deps must finish first):
  ENTRY=a → a imports b → eval b first
  b.mjs body:
    line 1: import (already linked)
    line 2: console.log('b body:', a)
              → look up `a` in a.mjs's bindings → still TDZ
              → throws ReferenceError (since `const`)
  (a.mjs never runs)

Output:
  ReferenceError: Cannot access 'a' before initialization
```

If `a` were `var` or `function`:

```js
// a.mjs
import { b } from './b.mjs';
console.log('a body:', b);
var a = 1;
export { a };
```

```
LINK: a binding holds `undefined` (var, hoisted)
EVAL:
  b's body: console.log('b body:', a) → reads a-binding → undefined → prints "b body: undefined"
  b finishes (b = 2 now in binding)
  a's body: console.log('a body:', b) → reads b-binding → 2 → prints "a body: 2"
  a = 1
```

## How to think aloud in the interview

> "Cycles work in ESM because of 2-phase loading: link, then evaluate. Bindings allocated at link time, populated at evaluate time. The module that evaluates *second* sees the first's exports. The first one sees the second's TDZ or `undefined`. With `const` or `let`, that's a ReferenceError. With `var` or function declarations, it's `undefined`. Fix: lazy access (function-level), or restructure to extract shared deps into a third module."

## Important takeaways

- **ESM 2-phase load**: link allocates bindings, evaluate fills them.
- **Bindings are LIVE** — second-evaluated module sees first's exports.
- **`const`/`let` in cycle → TDZ ReferenceError** if read too early.
- **`var`/`function` → `undefined`** if read too early.
- **Fix patterns**: (1) lazy access inside function bodies; (2) extract shared module; (3) dynamic `import()` for true lateness.
- **CJS cycles differ** — `require()` returns whatever `module.exports` was at the time (often `{}`).

## Variants

- **CJS cycle** — `module.exports = {}` initially; first-encounter caller sees empty object; later mutations land but bindings already captured snapshot.
- **Bundler-resolved cycle** — Webpack 5 has runtime helpers; Rollup may inline; esbuild may bail.
- **Worker-thread separate evaluation** — each worker re-evaluates from scratch; cycles re-encountered there too.
- **`import()` dynamic** — defers binding to call time; useful for breaking cycles.

## Revision notes

```
ESM cycle:
  LINK: parse all, allocate binding slots (TDZ or undefined)
  EVAL: depth-first, post-order; second-eval sees first's exports
  
  RESULTS:
    const/let read before init in cycle → ReferenceError (TDZ)
    var/function read before init in cycle → undefined
    second-eval module always sees first-eval module's bindings populated
  
  FIX:
    - lazy access (read inside a function body, not at top level)
    - extract shared module (no cycle)
    - dynamic await import()
  
CJS cycle:
  require() returns whatever module.exports IS at the moment
  often empty object {} → caller gets partial export
  no TDZ; just confusing behavior
```
