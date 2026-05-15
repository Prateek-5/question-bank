# Function expression vs declaration inside `if` / `else`

## Source
- Canonical senior-JS interview problem (BFE.dev, "JavaScript: The Good Parts" Ch. 4, V8 / SpiderMonkey legacy notes).
- MDN reference: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/function

## Why this question matters in interviews
Senior interviewers love this trap because it exposes whether the candidate understands the **difference between a Function Declaration (FD) and a Function Expression (FE)** at parse time, *and* whether they know about the **Annex B legacy semantics** for "Function-in-Block" (FiB). It's the single most-cited "browser vs Node vs strict mode" quirk in the language. On the backend, this matters when:
- Refactoring legacy Express handlers that conditionally redefine helpers.
- Reading transpiled output (Babel/SWC often rewrites FiB to FE assigned to a `var`).
- Debugging "the function exists at the top of the file but is `undefined` here" issues in CommonJS code.

If you ever see `if (cond) { function foo() {} }` in production code, **it's a bug waiting to happen**. The interviewer wants you to spot that.

## Concepts involved

### Syntax to lock in
```js
// Function Declaration — hoisted fully (name + body)
function foo() {}

// Function Expression — only the variable is hoisted (as var → undefined, or TDZ for let/const)
const foo = function () {};
const bar = function named() {};   // Named Function Expression

// Function-in-Block (FiB) — the ambiguous case
if (true) {
  function baz() {}                // FD inside a block — semantics differ across modes!
}
```

### Runtime / engine behavior
- **Function Declaration at top level of a function/module/script:** fully hoisted. Both the binding *and* the function object are created during the creation phase. You can call `foo()` before its `function foo(){}` line.
- **Function Expression:** the *variable* is hoisted by `var`/`let`/`const` rules. The function object is created on the right-hand side **at execution time**, when the assignment runs. Calling it before the assignment line gives `TypeError: foo is not a function` (if `var`) or `ReferenceError` (if `let`/`const`).
- **Function-in-Block:** the messy case.
  - **Strict mode / ES modules:** `function baz(){}` inside a block is **block-scoped**. It's hoisted to the top of the *block*, not the function. Outside the block, `baz` is undefined.
  - **Sloppy mode (legacy script, no `"use strict"`):** "Annex B.3.3" legacy semantics kick in — the function is *also* hoisted to the enclosing function scope as `var baz = undefined`, and the assignment happens when control enters the block. The behavior differs across engines historically; modern V8 follows Annex B.
  - **Node CommonJS modules** run in a function wrapper but are **not** automatically strict. ES modules **are** strict.

### Edge cases (the traps)
1. **`if (cond) { function foo() {} } else { function foo() {} }`** — in sloppy mode both `foo` declarations exist; the one that runs assigns to the outer `var foo`. In strict mode both are block-scoped and neither leaks out.
2. **Named Function Expression's name** — `const x = function bar(){};` exposes `bar` only *inside* the function body, not outside. Old IE8 leaked `bar` to the enclosing scope (don't rely on it; the bug shipped in millions of pages).
3. **Hoisting precedence** — a function declaration and a `var` with the same name: the function declaration "wins" during hoisting, but a later `var x = 1` assignment overwrites the binding.
4. **Arrow function inside `if`** — `const fn = () => {}` is just a `const` declaration; arrow functions are *expressions*, never declarations. No FiB quirk.
5. **Functions in `switch` / `try` / `catch`** — same FiB rules apply.
6. **Reading transpiled code** — Babel emits `var foo = function() {}` for top-level `function` declarations when it can prove there's no `arguments` reliance, to dodge FiB. If you see this, it's intentional.

## Brute force approach
"I'll just assume the function is defined wherever I see `function name(){}`." This works for top-level FDs but completely fails for FiB. The naive reader claims `baz` is callable outside the `if` — wrong in strict mode, accidentally right in sloppy mode, and the answer flips based on a `"use strict"` line at the top of the file. Drop this mental model.

## Optimal approach
**Three-question decision tree** for every function-y thing you see:
1. **Is it a Function Declaration or Function Expression?** FD = `function name() {}` as a *statement*. FE = anything appearing in an expression context (RHS of `=`, argument to a call, parenthesized).
2. **Is it at the top level of a function/module/script, or inside a block?** Top-level → fully hoisted. Inside a block → FiB rules.
3. **Strict or sloppy?** ES modules and `"use strict"` files: block-scoped, no leak. Sloppy classic scripts: Annex B.3.3 legacy hoist-and-assign.

## Solution (JavaScript)

```js
// File: example.js  (sloppy mode — classic script, no "use strict")

console.log(typeof foo);   // (1) ?
console.log(typeof bar);   // (2) ?
console.log(typeof baz);   // (3) ?

if (true) {
  function foo() { return 'foo'; }   // FD inside block → Annex B.3.3
}

var bar = function () { return 'bar'; };

if (false) {
  function baz() { return 'baz'; }   // FD inside block that never runs
}

console.log(typeof foo);   // (4) ?
console.log(typeof baz);   // (5) ?
```

In **sloppy mode** the answers are:
```
(1) 'undefined'   // foo exists as var (Annex B), but not yet assigned
(2) 'undefined'   // var bar hoisted but not assigned
(3) 'undefined'   // baz exists as var (Annex B), not yet assigned (and never will be)
(4) 'function'    // foo got assigned when control entered the if-block
(5) 'undefined'   // if(false) never executed → baz stays undefined
```

In **strict mode / ES module** the same file produces:
```
(1) 'undefined'   // foo is block-scoped; doesn't exist at outer scope yet — but `typeof` swallows ReferenceError for undeclared names, so 'undefined'
(2) 'undefined'   // var bar hoisted but not assigned
(3) 'undefined'   // baz is block-scoped, never declared outside the block
(4) 'undefined'   // foo is block-scoped — invisible here
(5) 'undefined'   // same — baz block-scoped, invisible here
```

## Step-by-step dry run

Take the sloppy-mode trace:

```js
// === Creation phase (sloppy mode, classic script) ===
// Annex B.3.3 effect: function decls inside blocks get a `var` binding in the enclosing function scope too.
// VE (script scope): { foo: undefined, bar: undefined, baz: undefined }
// (foo and baz from Annex B var-hoisting; bar from the explicit var)

// === Execution phase ===

// line: console.log(typeof foo)
//   foo is undefined → prints 'undefined'

// line: console.log(typeof bar)
//   bar is undefined → 'undefined'

// line: console.log(typeof baz)
//   baz is undefined → 'undefined'

// enter if(true) block:
//   inside the block, FD foo is fully hoisted to top of BLOCK
//   AND, at the point control enters the block, Annex B copies the
//   block-scoped foo into the outer var foo.
//   VE: { foo: <fn>, bar: undefined, baz: undefined }

// exit if-block. var foo retains the assignment.

// line: var bar = function () { ... }
//   VE: { foo: <fn>, bar: <fn>, baz: undefined }

// if(false) — block never entered → baz remains undefined.

// line: console.log(typeof foo) → 'function'
// line: console.log(typeof baz) → 'undefined'
```

For **strict mode** the difference is: Annex B.3.3 is disabled. The `function foo` and `function baz` declarations stay strictly inside their blocks. No outer `var foo` / `var baz` exists. After the file runs, `typeof foo` is `'undefined'` because `typeof` doesn't throw on undeclared names.

## Important takeaways

**Syntax to memorize**
- `function name() {}` as a **statement** = Function Declaration. Fully hoisted (name + body).
- `function name() {}` as an **expression** (RHS, arg, parens) = Function Expression. Only the variable binding hoists.
- FiB (function-in-block) = legacy footgun. **Don't write it.** Use `const x = function() {}` or an arrow.

**Patterns to reuse**
- "What's the binding form, what's the scope, what's the mode" — apply this three-question filter to every `function` you see.
- For conditional helpers, always use an expression: `const helper = cond ? fnA : fnB;`. Predictable in strict and sloppy.

**Common mistakes**
- Assuming `if (cond) function foo(){}` block-scopes the same way everywhere. It doesn't — sloppy vs strict diverge.
- Forgetting that ES modules and classes are *always* strict. CommonJS modules are not.
- Thinking the *name* of a Named Function Expression is visible outside the function. It isn't (except in old IE).

**Backend relevance**
- Express middleware that conditionally re-declares a helper function inside `if (env === 'dev')` will break differently in `node --use-strict` vs plain Node.
- Code targeting Node 18+ ES modules can assume strict; CJS code can't.

## Variants

1. **Add `"use strict"` and ask for the diff** — interviewer wants you to recite Annex B.3.3 vs strict block-scoping.
2. **Top-level `function foo(){}` vs `var foo = function(){}`** — when called before the line, FD works; FE throws `TypeError: foo is not a function` (var) or `ReferenceError` (let/const).
3. **Hoisting precedence with same name** — `function foo(){}` followed by `var foo;` — does `foo` exist? Yes, the FD wins (the `var foo` declaration without initializer does **not** overwrite). Add `var foo = 1` and now `foo === 1` after that line.

## Revision notes

> **Function expression vs declaration in conditionals — 60 second recap**
> - **FD** (`function foo(){}` as a statement) → fully hoisted: name + body, callable before the line.
> - **FE** (`const x = function(){}` etc.) → only the **variable** hoists; body assigned on execution.
> - **FiB** = function inside a block. Outcome depends on mode:
>   - **Strict / ES module:** block-scoped. Invisible outside the block.
>   - **Sloppy classic script:** Annex B.3.3 — also creates an outer `var name`, assigned when control enters the block.
> - **Arrow functions** are expressions only — never FDs, no FiB quirk.
> - **Named Function Expression**'s name (`function bar` in `const x = function bar(){}`) is visible *only inside* the function body.
> - **`typeof` swallows** `ReferenceError` for undeclared names, but **not** for TDZ.
> - **Babel** rewrites FiB to `var name = function(){}` to avoid the mode-dependency — read transpiled output if confused.
> - **Trap:** `if (false) function foo(){}` in sloppy mode still creates an outer `var foo = undefined`.
> - **Rule of thumb:** never write FDs inside blocks. Use FEs or arrows.
