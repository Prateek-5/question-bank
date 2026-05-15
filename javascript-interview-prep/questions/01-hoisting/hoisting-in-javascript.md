# Hoisting in JavaScript — full conceptual walkthrough

## Source
https://codedamn.com/news/javascript/hoisting-in-javascript — MDN reference: https://developer.mozilla.org/en-US/docs/Glossary/Hoisting

## Why this question matters in interviews
"Explain hoisting" is the most common open-ended JS question on senior screens — it's a 5-minute oral check on whether you understand the engine, not just JS syntax. Strong answers cover the **two-phase execution model**, the **four kinds of hoisting** (`var`, function decl, `let`/`const`/`class`, import), and the **scope rules** that hoist into (function vs block vs module). Weak answers just repeat "declarations move to the top." As a backend engineer, you'll be expected to use the precise terminology — `Variable Environment`, `Lexical Environment`, `TDZ` — when reviewing teammates' code or debugging production stack traces.

## Concepts involved

### Syntax to lock in
```js
// 1. var — hoisted, initialized to undefined
console.log(a); // undefined
var a = 1;

// 2. function declaration — fully hoisted (body + name)
greet();        // 'hi'
function greet() { console.log('hi'); }

// 3. let / const — hoisted, but TDZ
console.log(b); // ReferenceError
let b = 2;

// 4. class — hoisted, but TDZ (same as let)
new Foo();      // ReferenceError
class Foo {}

// 5. import — hoisted to top of module (live binding)
foo();          // works even though import is on line 2
import { foo } from './foo.js';
```

### Runtime / engine behavior

When the engine evaluates a script, module, function body, or block, it processes the source in **two phases**:

**Phase 1 — Creation (a.k.a. compilation, hoisting phase)**
- Scan all declarations.
- For each `var`: create a binding in the **Variable Environment**, initialize to `undefined`.
- For each function declaration: create a binding in the VE, initialize to the **full function object**.
- For each `let`/`const`/`class`: create a binding in the **Lexical Environment**, mark as `<uninitialized>` (TDZ).
- For each `import` (in ES modules): create a binding linked to the exporter (a "live binding").
- Resolve the scope chain (`OuterEnv` pointer to the parent environment).

**Phase 2 — Execution**
- Run statements top-to-bottom.
- Assignments update bindings.
- `let`/`const`/`class` declarations transition their bindings from `<uninitialized>` to the assigned value (or `undefined` for bare `let x;`).
- Reads from a `<uninitialized>` binding throw `ReferenceError: Cannot access 'x' before initialization`.

### Scope of hoisting
- `var` → hoists to the **enclosing function** (or to the script/module top level).
- `function` declarations → same as `var` for sloppy mode; block-scoped in strict mode / ESM.
- `let`/`const`/`class` → hoist to the **enclosing block** (the nearest `{...}`).
- `import` → hoists to the **top of the module**.

### Edge cases (interview traps)
1. **`var` inside a block leaks** — `if (true) { var x = 5; } console.log(x);` → `5`. The `var` belongs to the function, not the block.
2. **`function` inside a block in strict mode** — block-scoped, invisible outside. In sloppy mode, hoisted to the function. Avoid this pattern.
3. **Hoisting precedence** — function decls beat `var` for the same name. Later `var foo = ...` assignment at runtime overwrites. **You cannot redeclare** the same name with `let` in the same scope (SyntaxError at parse).
4. **`typeof` on TDZ binding throws** — only safe for genuinely undeclared identifiers.
5. **ES modules have no `arguments`, no `this === globalThis`, and `var` at top level does NOT attach to `globalThis`** — modules are stricter than scripts.
6. **Circular imports + TDZ** — if A imports from B and B imports from A, the late-loaded module sees the other's bindings in TDZ until evaluation completes. Real-world Node bug source.

## Brute force approach
Rusty candidate: *"Hoisting moves declarations to the top of the file."* This is the textbook one-liner but it's misleading — nothing physically moves. The source code stays the same; the engine just registers bindings during the creation phase. Saying "moves to the top" is fine as shorthand, but you must follow it with the mechanism: "the engine pre-scans declarations and creates bindings before any code runs."

## Optimal approach
A senior answer is structured in three layers:

1. **Mechanism**: two-phase execution per scope (creation → execution). Engine registers bindings during creation.
2. **Per-keyword behavior**: `var` → `undefined`; function decl → full body; `let`/`const`/`class` → TDZ; import → live binding.
3. **Scope of hoisting**: function-scope for `var`; block-scope for `let`/`const`/`class`; module-top for `import`.

Then give a 3-line code example illustrating each.

## Solution (JavaScript)

```js
// All four kinds in one example
import { helper } from './helper.js';   // hoisted to module top

console.log(typeof fnDecl);  // 'function' — fully hoisted
console.log(typeof varX);    // 'undefined' — hoisted, value not assigned
try { console.log(letY); }   // ReferenceError — TDZ
catch (e) { console.log('TDZ for letY'); }
try { new ClassZ(); }        // ReferenceError — TDZ
catch (e) { console.log('TDZ for ClassZ'); }
helper();                    // works — import binding live

function fnDecl() {}
var varX = 10;
let letY = 20;
class ClassZ {}
```

Expected output:
```
function
undefined
TDZ for letY
TDZ for ClassZ
<whatever helper() prints>
```

## Step-by-step dry run

**Module Execution Context — Creation phase**

| Identifier | Stored in            | Initial value         |
|------------|----------------------|-----------------------|
| `helper`   | Module Environment   | `<live binding>` to helper.js export |
| `fnDecl`   | Variable Environment | `<function fnDecl>`   |
| `varX`     | Variable Environment | `undefined`           |
| `letY`     | Lexical Environment  | `<uninitialized>` (TDZ) |
| `ClassZ`   | Lexical Environment  | `<uninitialized>` (TDZ) |

**Execution phase**
1. `console.log(typeof fnDecl)` → `'function'`. Resolution succeeds.
2. `console.log(typeof varX)` → `'undefined'`. Binding holds `undefined`, `typeof undefined === 'undefined'`.
3. `try { console.log(letY) }` → `letY` is in TDZ → `ReferenceError`. Catch prints `'TDZ for letY'`.
4. `try { new ClassZ() }` → same, prints `'TDZ for ClassZ'`.
5. `helper()` → resolves the live import binding, invokes it.
6. `function fnDecl() {}` — no-op at execution.
7. `var varX = 10` — binding now `10`.
8. `let letY = 20` — TDZ ends; binding now `20`.
9. `class ClassZ {}` — TDZ ends; binding now the class.

Note: by the time of step 4, `ClassZ` has not been initialized — `new ClassZ()` throws TDZ, not "not a constructor."

## Important takeaways

**Syntax to memorize**
- **Two-phase model**: creation (hoist) → execution (run).
- `var` → `undefined`. `function` decl → full body. `let`/`const`/`class` → TDZ. `import` → live binding.
- Scope: `var`/`function` to function; `let`/`const`/`class` to block; `import` to module.

**Patterns to reuse**
- When debugging a `ReferenceError`, **first** check whether it's "not defined" (no binding anywhere) or "before initialization" (binding exists, in TDZ). The error messages distinguish them.
- Use `const` everywhere; downgrade to `let` only when reassigning. Never reach for `var` in new code.
- In ESM, never write `var` at the top of a module file — there's no reason to.

**Common mistakes**
- Saying "let isn't hoisted." It is. It just sits in TDZ.
- Confusing function declaration with function expression. Only the **declaration** is fully hoisted.
- Using `typeof x` to probe for a `let`/`const` — throws in TDZ.
- Thinking imports are evaluated where you write them — they execute at module load, top-of-file, regardless of position.

**Related questions**
- TDZ with `let`/`const`
- Function declaration vs expression
- Class hoisting
- Scope chain and the Lexical Environment

## Variants

1. **"Walk me through what happens when this file loads"** — given a 15-line module, the interviewer wants you to recite the creation phase (all bindings, in order) before execution. Practice on real code.

2. **"What's the difference between hoisting in a script and an ES module?"** — Scripts share a global object; modules don't (top-level `var` doesn't attach to `globalThis`, `this` is `undefined`, strict mode is on by default, imports are hoisted as live bindings).

3. **"Predict the output of this `var` + function decl combo"** — `console.log(foo); var foo = 5; function foo(){}` → prints `[Function: foo]` then assigns `5`. Final `foo === 5`.

## Revision notes

> **Hoisting overview — 60 second recap**
> - **Two phases per scope**: creation (hoist) → execution.
> - `var` → hoisted, `undefined`. `function` decl → fully hoisted (body included). `let`/`const`/`class` → hoisted but in **TDZ**. `import` → hoisted to module top (live binding).
> - Scope: `var`/`function` = function-scope. `let`/`const`/`class` = block-scope. `import` = module-scope.
> - In TDZ: any access (including `typeof`) throws `ReferenceError: Cannot access 'x' before initialization`.
> - Function decls **beat** `var` for the same name during creation; runtime assignment overwrites.
> - **Trap:** "let isn't hoisted" is wrong — it IS hoisted, just uninitialized.
> - **Trap:** in ESM, top-level `var` does NOT attach to `globalThis`; modules are strict by default.
