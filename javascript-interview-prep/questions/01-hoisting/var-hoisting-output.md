# Output prediction: `var` hoisting inside a function

## Source
Canonical senior-JS interview problem. MDN reference: https://developer.mozilla.org/en-US/docs/Glossary/Hoisting

## Why this question matters in interviews
This is the #1 warm-up question on JS-rusty backend candidates. The interviewer doesn't care about the answer — they care whether you can articulate the **two-phase execution model** (creation phase + execution phase) and the **variable environment**. Senior backends often pattern-match `var` to "block-scoped local variable like in Go/Java," which is wrong on both axes (function-scoped + hoisted). If you fumble this, the interviewer assumes you'll fumble closures, TDZ, and async code that follows. Treat it as a 60-second test of your mental model of the engine.

## Concepts involved

### Syntax to lock in
```js
function f() {
  console.log(a);  // undefined — NOT ReferenceError
  var a = 2;
  console.log(a);  // 2
}

var a = 1;
f();
```

### Runtime / engine behavior
- When a function is invoked, the engine creates an **Execution Context** with two sub-records: the **Variable Environment** (for `var` + function decls) and the **Lexical Environment** (for `let`/`const`/`class`).
- **Creation phase**: every `var` declaration in the function body is registered in the Variable Environment and **initialized to `undefined`**. Function declarations get hoisted with their full body. This is "hoisting."
- **Execution phase**: code runs top to bottom. Assignments (`a = 2`) update the binding. Until that assignment executes, `a` holds `undefined`.
- `var` is **function-scoped**, not block-scoped. A `var` inside an `if` / `for` / `{}` block is hoisted to the enclosing function (or to the global object if at module/script top level, but ES modules behave slightly differently — top-level `var` does NOT become a property of `globalThis` in ESM).
- The outer `a = 1` is shadowed inside `f()` because the inner `var a` creates a new binding in the function's VE — and that binding is the one resolved by the scope chain.

### Edge cases (interview traps)
1. **Shadowing happens during creation phase, not assignment** — the inner `a` exists from line 1 of the function, holding `undefined`. The outer `a = 1` is unreachable inside `f`.
2. **Re-declaring `var`** is legal — `var a; var a;` is fine. `let a; let a;` is a `SyntaxError`.
3. **`var` inside a block** still hoists to the function — `if (true) { var x = 5; } console.log(x);` prints `5`.
4. **`typeof` safety** — `typeof undeclaredVar` returns `'undefined'` for truly undeclared identifiers. This is the only safe way to probe existence pre-`let`.
5. **Function-declaration hoisting beats `var`** — if both `function foo(){}` and `var foo` exist, the function wins during creation. A later `foo = 5` overwrites the binding.

## Brute force approach
Rusty candidate's first answer: *"It logs `1` then `2` — because `a` is declared outside."* Wrong. They're thinking lexical-scope-then-shadow, ignoring hoisting. Second guess: *"It throws because `a` isn't defined yet."* Also wrong — that's the `let`/TDZ behavior. The correct mental model needs both pieces: (a) the inner `var` shadows the outer, AND (b) hoisting initializes it to `undefined` before line 1.

## Optimal approach
Mentally split the function body into two passes:

1. **Creation pass** — scan declarations, build the VE. `{ a: undefined }`.
2. **Execution pass** — run statements. First `console.log(a)` reads VE → `undefined`. Then `a = 2` updates VE. Second `console.log(a)` reads VE → `2`.

This 2-pass framework answers every `var`-hoisting question you'll ever see.

## Solution (JavaScript)

```js
var a = 1;

function f() {
  // CREATION PHASE of f's execution context:
  //   VariableEnvironment = { a: undefined }    // inner `var a` hoisted
  //   OuterEnv -> global { a: 1, f: <fn> }
  //
  // EXECUTION PHASE:
  console.log(a);   // reads VE.a -> undefined
  var a = 2;        // declaration was already hoisted; this line only assigns
  console.log(a);   // reads VE.a -> 2
}

f();
// Output:
// undefined
// 2
```

## Step-by-step dry run

Input: the snippet above.

**Global Execution Context — Creation Phase**
| Identifier | Value          |
|------------|----------------|
| `a`        | `undefined`    |
| `f`        | `<function f>` |

**Global Execution Context — Execution Phase**
- `var a = 1;` → global VE becomes `{ a: 1, f: <fn> }`.
- `f();` → push new Execution Context for `f`.

**`f`'s Execution Context — Creation Phase**
| Identifier | Value          |
|------------|----------------|
| `a`        | `undefined`    | (because of `var a = 2` inside)

The scope chain is `f's VE -> global VE`. Lookup for `a` stops at `f`'s VE.

**`f`'s Execution Context — Execution Phase**
- Line `console.log(a)` → look up `a` → finds local `a = undefined` → prints `undefined`.
- Line `var a = 2` → assignment only (declaration already done) → local `a = 2`.
- Line `console.log(a)` → prints `2`.

Pop `f`'s context. Global `a` is still `1`.

## Important takeaways

**Syntax to memorize**
- `var` declarations are hoisted and initialized to `undefined`.
- `var` is **function-scoped**, not block-scoped.
- The inner `var` shadows the outer **from the first line of the function**, not from its declaration line.

**Patterns to reuse**
- The two-phase model (creation → execution) generalizes to every hoisting question.
- The "Variable Environment table" is the right whiteboard artefact when explaining hoisting live.

**Common mistakes**
- Saying "JS hoists the declaration to the top" is technically fine but obscures the mechanism. Say "the engine registers the binding during the creation phase."
- Forgetting that hoisting is **per-function-scope**, not per-block, for `var`.
- Assuming `console.log` before declaration throws — that's the `let`/`const` behavior.

**Related questions**
- TDZ with `let`/`const`
- Function declaration vs expression hoisting
- Loop closure with `var` vs `let`
- `class` hoisting (TDZ)

## Variants

1. **Same code, but change `var` to `let`** — now the first `console.log(a)` throws `ReferenceError: Cannot access 'a' before initialization` (TDZ). Outer `a = 1` is shadowed but inaccessible inside `f`.

2. **Hoisting + parameter** — `function f(a) { console.log(a); var a = 2; console.log(a); } f(7);` prints `7` then `2`. Parameters are initialized BEFORE the function body's `var` re-declarations; `var a` re-declares but doesn't reset to `undefined` (re-declaration without initializer is a no-op).

3. **Hoisting + nested function** — `function f() { console.log(typeof g); var g; function g(){} console.log(typeof g); }` prints `'function'` then `'function'`. Function declarations beat `var` during creation phase.

## Revision notes

> **var hoisting — 60 second recap**
> - Two phases: **creation** (register `var` as `undefined`, hoist `function` fully) → **execution** (run statements).
> - `var` is **function-scoped** (not block).
> - Inner `var` shadows outer from line 1 of the function — the outer binding is invisible inside.
> - Reading a hoisted `var` before assignment → `undefined`. **Never throws.**
> - Whiteboard trick: draw the VE table for each EC.
> - Trap: confusing this with `let`/`const` TDZ behavior (which throws).
> - Output of canonical snippet: `undefined`, then `2`.
