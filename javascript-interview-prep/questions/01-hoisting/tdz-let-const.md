# Temporal Dead Zone with `let` / `const`

## Source
Canonical senior-JS interview problem. MDN reference: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/let#temporal_dead_zone_tdz

## Why this question matters in interviews
Backend engineers coming from typed languages assume "declared but unassigned" means `null`/`undefined`. JS broke that mental model with `let`/`const` in ES6, and interviewers love testing whether you know **why** it throws (not just *that* it throws). The TDZ is also load-bearing for every modern JS codebase — every Node service, every Next.js handler, every ESM file uses `let`/`const`. Failing to explain TDZ flags you as someone who hasn't kept up since the `var` era. Bonus: TDZ behavior is the foundation for understanding `class` hoisting and import hoisting, which often follow as the next question.

## Concepts involved

### Syntax to lock in
```js
console.log(x);        // ReferenceError: Cannot access 'x' before initialization
let x = 5;

console.log(typeof y); // ReferenceError (NOT 'undefined')
let y = 5;

{
  // TDZ for `z` starts here, at the top of this block
  // ...any access here throws
  let z = 1;           // TDZ ends here — binding is initialized
  console.log(z);      // 1
}
```

### Runtime / engine behavior
- `let`, `const`, and `class` declarations **are hoisted** — the binding is registered in the **Lexical Environment** of the enclosing block during the creation phase. This is a common myth-buster: candidates often say "let isn't hoisted." It is. It's just not **initialized**.
- The binding exists in an **uninitialized** state from the start of its block until the line where the declaration runs. That window is the **Temporal Dead Zone**.
- Any read or write to the binding during the TDZ throws `ReferenceError: Cannot access 'x' before initialization`.
- `typeof` is **not** a safe-probe for `let`/`const` — it also throws. This is different from `var`/undeclared identifiers, where `typeof undeclared === 'undefined'`.
- `let`/`const` are **block-scoped**. `var` is function-scoped. A `let` inside `if`/`for`/`{}` is invisible outside the block.
- `const` requires an initializer at declaration (`const x;` is a `SyntaxError`). `let` does not.

### Edge cases (interview traps)
1. **TDZ is temporal, not spatial** — it's about *time of execution*, not source position. `function f() { return x; } let x = 5; f();` works because by the time `f` runs, the TDZ has ended.
2. **`typeof` trap** — `typeof maybeDeclared` is the classic existence check, but it throws on `let`/`const` in TDZ. Use `try/catch` or a sentinel pattern instead.
3. **`for` loop fresh binding** — `for (let i = 0; i < 3; i++)` creates a **new `i`** per iteration. This is why closures over `let` in loops behave correctly (vs the `var` bug).
4. **Switch case TDZ** — a `let` declared in one `case` lives in the whole `switch` block. Accessing it from an earlier case is a TDZ error. Wrap each case in `{}` to scope safely.
5. **Redeclaration** — `let x; let x;` is a **SyntaxError** at parse time, not runtime. Same scope only.
6. **Global `let`/`const`** — at the top level of a script, they do NOT become properties of `globalThis` (unlike `var`).

## Brute force approach
Rusty candidate: *"`let` isn't hoisted, that's why you get an error — the variable doesn't exist yet."* Wrong. The binding **does** exist (which is exactly why you get a *ReferenceError-with-a-specific-message* and not the same error you'd get for a truly undeclared identifier). Saying "not hoisted" reveals you don't know the mechanism. The right framing is: hoisted but uninitialized → access during the uninitialized window throws.

## Optimal approach
Think in three states for any binding:

1. **Not declared** — identifier doesn't exist in any reachable scope. Access throws `ReferenceError: x is not defined`. `typeof` returns `'undefined'`.
2. **Declared but in TDZ** — binding exists, holds the internal "uninitialized" marker. Any access throws `ReferenceError: Cannot access 'x' before initialization`. `typeof` also throws.
3. **Initialized** — normal read/write semantics.

`var` skips state 2 (goes straight from "not declared" → "initialized to undefined" during creation).
`let`/`const`/`class` go through all three states.

## Solution (JavaScript)

```js
// Demonstrate all three states
function demo() {
  // BLOCK START — Lexical Environment created.
  // Bindings present: { x: <uninitialized>, y: <uninitialized> }
  // (let/const are hoisted but in TDZ)

  try {
    console.log(typeof x);   // throws ReferenceError — TDZ
  } catch (e) {
    console.log('TDZ trap:', e.message);
  }

  let x = 10;                 // TDZ for x ENDS here
  const y = 20;               // TDZ for y ENDS here

  console.log(x, y);          // 10 20 — normal access

  console.log(typeof notDeclared); // 'undefined' — never declared, safe
}

demo();
```

## Step-by-step dry run

**Block entry — Creation phase (Lexical Environment)**
| Identifier | State            |
|------------|------------------|
| `x`        | `<uninitialized>` (TDZ) |
| `y`        | `<uninitialized>` (TDZ) |

**Execution phase**

- Line `console.log(typeof x)` → engine resolves `x` in current LE → finds binding in `<uninitialized>` state → throws `ReferenceError: Cannot access 'x' before initialization`. **`typeof` does NOT shield you here** because the engine has to resolve the binding to determine its type, and resolution itself throws for TDZ.
- `catch (e)` → prints `TDZ trap: Cannot access 'x' before initialization`.
- Line `let x = 10` → binding `x` transitions from `<uninitialized>` to `10`. TDZ for `x` ends.
- Line `const y = 20` → same for `y`. TDZ for `y` ends.
- Line `console.log(x, y)` → both bindings initialized → prints `10 20`.
- Line `console.log(typeof notDeclared)` → identifier not in any scope. Per spec, `typeof` on an undeclared identifier returns `'undefined'` without throwing (this is the historical safe-probe pattern). Prints `'undefined'`.

## Important takeaways

**Syntax to memorize**
- `let`/`const`/`class` are **hoisted but uninitialized**.
- TDZ runs from the start of the enclosing block to the declaration line.
- `const` requires an initializer; you cannot declare and assign later.
- `let` is reassignable. `const` is not (but `const` objects are mutable — `const arr = []; arr.push(1)` is fine).

**Patterns to reuse**
- The three-state model (`not declared` / `TDZ` / `initialized`) lets you predict any output-order question.
- Default to `const` everywhere; downgrade to `let` only when reassigning. Never use `var` in new code.

**Common mistakes**
- Saying "let is not hoisted" (wrong — it's hoisted but in TDZ).
- Using `typeof` to safe-probe a `let` (throws). Only works for undeclared identifiers.
- Putting `let` declarations after their first use, assuming hoisting will save you — it won't.
- Confusing TDZ (`ReferenceError: Cannot access 'x' before initialization`) with not-defined (`ReferenceError: x is not defined`). Different errors → different root causes.

**Related questions**
- `var` hoisting and the two-phase model
- Function vs class declaration hoisting
- Loop closure: `var` bug vs `let` per-iteration binding
- ES module import hoisting (also TDZ-ish for circular imports)

## Variants

1. **TDZ inside default parameters** — `function f(a = b, b) {}` then `f()` throws because `b`'s TDZ extends to the parameter list and `a`'s default reads `b` before its initializer. Reversing them (`function f(b, a = b)`) works.

2. **Class TDZ** — `new Foo(); class Foo {}` throws TDZ error. Function decls would not. Tests whether you know `class` behaves like `let`, not like `function`.

3. **Circular import TDZ** — in ESM, if module A imports `x` from B while B imports from A, accessing `x` before B's evaluation completes throws TDZ. Real production gotcha in large monorepos.

## Revision notes

> **TDZ / let-const — 60 second recap**
> - `let`/`const`/`class` ARE hoisted — just **uninitialized** until their declaration line runs.
> - That uninitialized window = **Temporal Dead Zone**. Any access (read, write, even `typeof`) throws `ReferenceError`.
> - Three states: not-declared / TDZ / initialized. `var` skips TDZ. `let`/`const`/`class` traverse all three.
> - Block-scoped (not function-scoped). Top-level `let`/`const` do NOT attach to `globalThis`.
> - `const` requires initializer; objects under `const` are still mutable.
> - **Trap:** `typeof x` is NOT safe for `let` in TDZ — only safe for genuinely undeclared identifiers.
> - **Trap:** TDZ error message is *"Cannot access 'x' before initialization"* — distinct from *"x is not defined"*. Know both.
