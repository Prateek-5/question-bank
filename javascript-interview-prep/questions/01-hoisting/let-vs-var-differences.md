# Difference between `let` and `var`

## Source
https://codedamn.com/news/javascript/difference-between-let-and-var-in-javascript — MDN: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/let

## Why this question matters in interviews
This is the most common "do you know modern JS?" gate question. Backend engineers who learned JS pre-ES6 (or only briefly) often answer "let is the new var" — instantly dating them. Senior screens expect you to enumerate **five distinct differences** (scope, hoisting, redeclaration, global-object attachment, loop binding) and to explain the engine-level reason for each. This question also doubles as a closure setup — interviewers often pivot from "let vs var" directly into "explain the loop-closure bug."

## Concepts involved

### Syntax to lock in
```js
// 1. Scope
function f() {
  if (true) {
    var v = 'function-scoped';
    let l = 'block-scoped';
  }
  console.log(v);   // 'function-scoped'
  console.log(l);   // ReferenceError
}

// 2. Hoisting + TDZ
console.log(a);     // undefined
console.log(b);     // ReferenceError (TDZ)
var a = 1;
let b = 2;

// 3. Redeclaration
var x = 1; var x = 2;     // OK — re-declaration allowed
let y = 1; let y = 2;     // SyntaxError

// 4. Global object attachment (classic scripts)
var g = 'global';
let h = 'global';
console.log(globalThis.g); // 'global'
console.log(globalThis.h); // undefined

// 5. Loop binding
for (var i = 0; i < 3; i++) setTimeout(() => console.log(i), 0);
// prints: 3, 3, 3

for (let j = 0; j < 3; j++) setTimeout(() => console.log(j), 0);
// prints: 0, 1, 2
```

### Runtime / engine behavior

| Property | `var` | `let` |
|---|---|---|
| **Scope** | function (or global) | block (`{...}`) |
| **Hoisting** | binding registered, value = `undefined` | binding registered, value = `<uninitialized>` (TDZ) |
| **Read before declaration** | `undefined` | `ReferenceError` |
| **`typeof` before declaration** | `'undefined'` | `ReferenceError` |
| **Redeclaration in same scope** | allowed | `SyntaxError` |
| **Global object attachment** | yes (in classic scripts only) | never |
| **Loop binding per iteration** | one shared binding | fresh binding per iteration |
| **Lives in** | Variable Environment | Lexical Environment |
| **Strict-mode behavior** | unchanged | unchanged |

The engine implements both by registering bindings during the **creation phase**, but `let` bindings stay in `<uninitialized>` until their declaration line runs (this is the TDZ). `var` bindings start at `undefined` and are immediately readable.

### Edge cases (interview traps)
1. **`let` redeclaration across blocks** — `let x = 1; { let x = 2; }` is fine (different blocks). `let x = 1; let x = 2;` in the same block is `SyntaxError`.
2. **`var` + `let` collision** — `let x = 1; var x = 2;` is `SyntaxError` (mixing redeclares).
3. **`var` in `for-in`/`for-of`** — works but the binding outlives the loop. `let` is the right choice.
4. **Module-level `var` doesn't attach to `globalThis`** in ESM — only in classic scripts. Subtle gotcha when moving code between Node CJS and ESM.
5. **`switch` blocks** — all `case`s share one block scope. `let` in one case is visible in others (and TDZ before its line). Wrap each case in `{}` to isolate.
6. **`const` is `let` + immutability of binding** — same scope/hoisting/TDZ semantics; only difference is you can't reassign the binding (the value can still be a mutable object).

## Brute force approach
Rusty candidate: *"`let` is block-scoped and `var` is function-scoped. That's it."* This answer scores 4/10 — it's correct but covers one out of five differences. Interviewers always follow up with "what else?" and watch you flail. Senior candidates volunteer the full table without prompting.

## Optimal approach
Answer in five buckets, in order of importance:

1. **Scope** — function vs block.
2. **Hoisting behavior** — undefined vs TDZ.
3. **Redeclaration** — allowed vs `SyntaxError`.
4. **Global attachment** — yes (classic script) vs no.
5. **Loop binding** — shared vs per-iteration (drives the closure bug).

Then add: "in production code, always use `const` first, `let` if reassigning, never `var` in new code."

## Solution (JavaScript)

```js
// Demonstrate all five differences in one file
'use strict';

// === 1. Scope ===
function scopeDemo() {
  if (true) {
    var v = 'in-block';
    let l = 'in-block';
  }
  console.log(v);                 // 'in-block' — leaked
  try { console.log(l); }         // ReferenceError
  catch (e) { console.log('let trapped in block'); }
}
scopeDemo();

// === 2. Hoisting / TDZ ===
function hoistDemo() {
  console.log('var before:', typeof a); // 'undefined' — safe
  try { console.log(typeof b); }       // ReferenceError on TDZ
  catch (e) { console.log('let TDZ on typeof'); }
  var a = 1;
  let b = 2;
}
hoistDemo();

// === 3. Redeclaration ===
function redeclareDemo() {
  var x = 1;
  var x = 2;                       // fine
  console.log('var re-declared:', x);  // 2
  // let y = 1; let y = 2;         // would SyntaxError at parse
}
redeclareDemo();

// === 4. Global attachment (classic-script-only behavior) ===
// (in modules this won't attach; demo skipped here)

// === 5. Loop binding ===
function loopDemo() {
  for (var i = 0; i < 3; i++) setTimeout(() => console.log('var i:', i), 0);
  for (let j = 0; j < 3; j++) setTimeout(() => console.log('let j:', j), 0);
}
loopDemo();
// After current task drains:
// var i: 3 (x3)
// let j: 0, let j: 1, let j: 2
```

## Step-by-step dry run

Focus on **loopDemo** — the highest-yield difference.

**`for (var i = 0; ...)`**

`var i` hoists to `loopDemo`'s VE. There is **one `i`** across the loop's lifetime.

| Iteration | `i` value when scheduled | Callback closes over |
|-----------|--------------------------|----------------------|
| 0         | 0                        | the shared `i` |
| 1         | 1                        | the shared `i` |
| 2         | 2                        | the shared `i` |

After the loop exits, `i === 3`. When the three `setTimeout` callbacks run (after current task drains), each reads the shared `i` → `3` three times.

**`for (let j = 0; ...)`**

Each iteration creates a **fresh block scope** with its own `j` binding. The spec literally describes this as "per-iteration binding."

| Iteration | Block LE | Callback closes over |
|-----------|----------|----------------------|
| 0         | `{ j: 0 }` | iter-0's `j` |
| 1         | `{ j: 1 }` | iter-1's `j` |
| 2         | `{ j: 2 }` | iter-2's `j` |

Each callback reads its own captured `j` → `0, 1, 2`.

This single example is the cleanest illustration of why scope + hoisting interaction matters in real code.

## Important takeaways

**Syntax to memorize**
- `var` → function-scoped, hoisted as `undefined`, redeclarable, attaches to `globalThis` in scripts.
- `let` → block-scoped, hoisted but TDZ, non-redeclarable, never attaches to `globalThis`, fresh binding per loop iteration.
- `const` → like `let` but no reassignment (object contents still mutable).

**Patterns to reuse**
- "Use `const` by default; `let` when reassigning; never `var`" is the modern style guide.
- When porting old `var` code, watch for: leaked block scope, loop-closure bugs, and `globalThis` attachments.
- For loops with async callbacks, **always** use `let`.

**Common mistakes**
- Listing only the scope difference and missing the other four.
- Saying "let isn't hoisted" — it is, just in TDZ.
- Forgetting that `var` redeclaration is silent, so accidental shadowing slips through code review.
- Assuming module-top `var` attaches to `globalThis` (it doesn't in ESM).

**Related questions**
- TDZ deep dive
- Loop closure bug
- `var` hoisting output prediction
- Why `const obj = {}; obj.x = 1` is legal

## Variants

1. **"Predict the output" with mixed `var`/`let`** — `var x = 1; { let x = 2; var x = 3; }` → `SyntaxError`: `var x` inside a block tries to redeclare the `let x` in the same scope (the engine forbids the mix). Tests parser-vs-runtime distinction.

2. **`let` in `switch` without braces** — case A declares `let v`, case B reads `v` before its declaration → TDZ error if execution falls through B first. Fix with `case 'A': { let v = ...; break; }`.

3. **`const` mutability gotcha** — `const arr = []; arr.push(1); console.log(arr);` works (`[1]`). `const arr = []; arr = [1];` throws `TypeError: Assignment to constant variable`. The binding is const, not the value.

## Revision notes

> **let vs var — 60 second recap**
> - Five differences: **scope** (function vs block), **hoisting** (undefined vs TDZ), **redeclaration** (yes vs no), **globalThis attachment** (yes-in-scripts vs no), **loop binding** (shared vs per-iteration).
> - `let` and `const` ARE hoisted — into TDZ.
> - `var` redeclaration is silent; `let` redeclaration is `SyntaxError`.
> - `for (var i)` → one shared `i`; closures see final value. `for (let j)` → fresh `j` per iteration; closures see iteration value.
> - `const` = `let` + no rebinding (values still mutable).
> - Style rule: `const` default, `let` when reassigning, never `var`.
> - **Trap:** `typeof` on TDZ `let` throws — only safe for genuinely undeclared identifiers.
