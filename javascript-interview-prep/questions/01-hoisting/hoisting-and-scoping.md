# Hoisting and Scoping — how they interact

## Source
https://codedamn.com/news/javascript/what-is-hoisting-and-scoping-in-javascript — MDN: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Lexical_grammar#variables

## Why this question matters in interviews
Hoisting and scoping are taught separately but tested **together** — interviewers ask "what does this print?" with deeply nested blocks and closures that lean on both. As a senior backend engineer the expected answer goes beyond mechanics: explain **which environment** the binding lives in, **how the scope chain resolves identifiers**, and **why** `var` leaking out of blocks combined with hoisting produces classic bugs (the loop-closure bug being the textbook example). A strong answer here also sets up the closures round that often follows.

## Concepts involved

### Syntax to lock in
```js
// var leaks out of blocks; let/const don't.
if (true) {
  var leaked = 'visible outside';
  let trapped = 'invisible outside';
}
console.log(leaked);   // 'visible outside'
console.log(trapped);  // ReferenceError: trapped is not defined

// Scope chain resolution
const outer = 'outer';
function f() {
  console.log(outer);  // climbs scope chain to global -> 'outer'
}

// Hoisting shadows the outer name
var x = 'global';
function g() {
  console.log(x);      // undefined (local var x hoisted)
  var x = 'local';
}
```

### Runtime / engine behavior

Every Execution Context has two records:

1. **Variable Environment (VE)** — holds `var` and function declarations. Per function (or script/module top level).
2. **Lexical Environment (LE)** — holds `let`/`const`/`class` declarations. Per block.

Each LE has an **OuterEnv** pointer to the enclosing environment, forming the **scope chain**. Identifier resolution walks this chain from innermost outward, stopping at the first match — or throwing `ReferenceError: x is not defined` if it reaches the global record without finding anything.

**Hoisting** populates these environments during the creation phase. **Scoping** determines which environment a name lives in and how lookups traverse the chain. They are orthogonal but interact:
- `var` hoists to the nearest **function** scope, regardless of how many blocks deep it's written.
- `let`/`const` hoist to the nearest **block** scope.
- Closures capture **environments**, not values — they hold a reference to the LE/VE active when the function was created.

### Edge cases (interview traps)
1. **The `for (var i)` loop-closure bug** — `for (var i = 0; i < 3; i++) setTimeout(() => console.log(i), 0)` prints `3 3 3`. All three callbacks close over the **same** `i` in the function's VE. With `let`, each iteration gets a **new** `i` in a fresh block scope → `0 1 2`.
2. **`var` inside a `for` loop** — same as above. The `var` initializer in `for (var i = 0; ...)` lives in the enclosing function.
3. **Shadowing across scopes** — `let x = 1; { let x = 2; console.log(x); /* 2 */ } console.log(x); /* 1 */`. Inner block creates a new binding; lookup finds the inner first.
4. **Module-scope hoisting** — `var` at module top level does NOT attach to `globalThis` in ESM (unlike classic scripts, where it does).
5. **`with` and `eval`** can dynamically extend the scope chain. In strict mode, `with` is forbidden; direct `eval` still adds bindings to the local scope. Both are interview-flag-worthy as anti-patterns.
6. **Function parameters create their own scope** — `function f(a = b, b) {}` throws because parameter `a`'s default expression sees `b` in TDZ.

## Brute force approach
Rusty candidate: *"Inner scope can see outer. Outer can't see inner."* Correct but useless — every output question still trips them up because they haven't internalized **which environment a `var` lives in**. Without the VE-vs-LE distinction, you can't explain why `var` leaks out of an `if` block but `let` doesn't.

## Optimal approach
For any "predict the output" question:

1. List all scopes (script/module, each function, each block).
2. For each scope, draw its VE and LE — populate with hoisted bindings.
3. Draw the OuterEnv arrows (scope chain).
4. Walk the execution phase, resolving each identifier read by climbing the chain.

This procedure mechanically solves every hoisting+scoping question.

## Solution (JavaScript)

```js
// Combined example — hoisting + scoping + closure capture
const x = 'global-x';

function outer() {
  // outer's VE = { y: undefined, inner: <fn> }    (hoisted)
  // outer's LE = {}                                (no let/const)
  console.log(x);              // climb to global -> 'global-x'
  console.log(y);              // undefined (var hoisted in outer)

  var y = 'outer-y';

  for (let i = 0; i < 2; i++) {
    // Each iteration: new block LE = { i: <new binding> }
    setTimeout(() => console.log('i=' + i, 'y=' + y), 0);
    // The arrow captures THIS iteration's LE (with its i) and outer's VE (y).
  }

  function inner() {
    var y = 'inner-y';         // shadows outer.y
    console.log(y);            // 'inner-y'
  }
  inner();
}

outer();
// Output (in order):
// global-x
// undefined
// inner-y
// i=0 y=outer-y
// i=1 y=outer-y
```

## Step-by-step dry run

**Global Execution Context — Creation phase**

| Binding | Environment | Value         |
|---------|-------------|---------------|
| `x`     | LE (const)  | `<uninitialized>` (TDZ) |
| `outer` | VE          | `<function outer>` |

**Execution phase (global)**
- `const x = 'global-x'` → TDZ ends, `x = 'global-x'`.
- `outer()` → push `outer`'s EC.

**`outer`'s Execution Context — Creation phase**

| Binding | Environment | Value         |
|---------|-------------|---------------|
| `y`     | VE          | `undefined`   |
| `inner` | VE          | `<function inner>` |

Scope chain: `outer.LE -> outer.VE -> global`.

**Execution phase (outer)**
1. `console.log(x)` → not in outer.LE → not in outer.VE → found in global LE → `'global-x'`. Print.
2. `console.log(y)` → outer.VE.y is `undefined`. Print `undefined`.
3. `var y = 'outer-y'` → outer.VE.y becomes `'outer-y'`.
4. **`for` loop with `let i`** — for each iteration, a new block LE is created with a fresh `i`. The arrow function captures that iteration's LE.
   - Iter 0: block LE = `{ i: 0 }`. Schedule callback A.
   - Iter 1: block LE = `{ i: 1 }`. Schedule callback B.
5. `inner()` — push `inner`'s EC.

**`inner`'s Execution Context — Creation phase**

| Binding | Environment | Value         |
|---------|-------------|---------------|
| `y`     | VE          | `undefined`   |

Scope chain: `inner.VE -> outer.VE -> global`.

**Execution phase (inner)**
- `var y = 'inner-y'` → inner.VE.y = `'inner-y'`.
- `console.log(y)` → resolves to `inner.VE.y` (first match) → `'inner-y'`. Print.

Pop `inner`. Pop `outer`. Continue global script — nothing else.

**Microtask + macrotask drain**
- After the script finishes, the event loop picks up the two scheduled `setTimeout(..., 0)` callbacks (in order):
  - Callback A: `i=0` from its captured block LE; `y='outer-y'` from outer's VE (still alive via closure). Print `i=0 y=outer-y`.
  - Callback B: `i=1`, `y='outer-y'`. Print `i=1 y=outer-y`.

## Important takeaways

**Syntax to memorize**
- Two environment records per EC: **VE** (`var`/function) and **LE** (`let`/`const`/`class`).
- Scope chain = chain of LE → VE → OuterEnv → ... → global.
- Closure captures **the environment**, not the value — that's why `let` in a `for` loop fixes the bug (new env per iteration).

**Patterns to reuse**
- The "draw the scope diagram" technique solves every output-prediction question.
- When debugging unexpected values, ask: which environment does this name resolve to? Walk the chain.
- Prefer block scope (`let`/`const`) to function scope (`var`) — it eliminates a whole class of bugs.

**Common mistakes**
- Treating `var i` in a `for` loop as block-scoped (it's not).
- Forgetting that closures capture the **live** environment, so mutations after capture are visible.
- Confusing scope (which name is visible where) with hoisting (when the binding becomes valid).

**Related questions**
- `var` vs `let` in loops (closure bug)
- TDZ behavior
- IIFE pattern (pre-ES6 way to create block scope)
- Module scope vs script scope

## Variants

1. **Loop closure prediction** — `for (var i = 0; i < 3; i++) setTimeout(() => console.log(i), 0)` — answer `3 3 3` and explain WHY: all callbacks share one `i` in the function's VE. Fix with `let` or IIFE.

2. **Nested shadowing** — three nested functions, each with `var x = ...`. Ask which `x` each `console.log(x)` resolves to. Tests scope-chain traversal precision.

3. **Hoisting + parameter scope** — `let x = 1; function f(x = x) {}` — calling `f()` throws TDZ because parameter `x`'s default reads its own binding before initialization. Tests parameter-list TDZ.

## Revision notes

> **Hoisting + scoping — 60 second recap**
> - Every EC has **VE** (`var`/function) and **LE** (`let`/`const`/`class`). Hoisting populates them during creation.
> - **Scope chain** = LE → VE → OuterEnv → ... → global. Lookups stop at the first match.
> - `var` is **function-scoped**; `let`/`const` are **block-scoped**.
> - Closures capture the **environment**, not the value — mutations are visible across captures.
> - `for (var i)` shares one `i` (loop-closure bug). `for (let i)` creates a fresh `i` per iteration.
> - **Trap:** `var` inside `if`/`for`/`{}` leaks to the enclosing function. `let`/`const` don't.
> - **Trap:** identifier resolution walks the chain; shadowing happens at the first match — no "merge."
