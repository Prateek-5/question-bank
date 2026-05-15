# `var` hoisting across if-blocks and loops

## Source
- Canonical senior-JS interview problem (BFE.dev, Frontend Masters, "You Don't Know JS: Scope & Closures" Ch. 4).
- MDN reference: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/var

## Why this question matters in interviews
This is the warm-up output-prediction puzzle on senior screens. The interviewer is checking *one* thing: can you reason about JavaScript's **two execution phases** (creation → execution) and the fact that `var` is **function-scoped**, not block-scoped. Get this wrong and the entire downstream conversation about closures, hoisting, and async iteration loses credibility. On the backend, this comes up daily: legacy services that still use `var`, transpiled code paths, and `try/catch` blocks where `var`-declared error info "leaks" out of the block on purpose. Knowing exactly what is hoisted where lets you debug a 10-year-old Express middleware in your sleep.

## Concepts involved

### Syntax to lock in
```js
function f() {
  if (false) {
    var x = 10;   // declaration is hoisted to top of f, assignment is not
  }
  console.log(x); // undefined — not ReferenceError
}
f();
```

### Runtime / engine behavior — the two phases
1. **Creation phase (a.k.a. hoisting):** the engine walks the function body and registers every `var` and function declaration in the **Variable Environment** of the function's *Lexical Environment*. `var` bindings are initialized to `undefined`. Block-level declarations (`let`, `const`, `class`, `function` in strict mode) are registered in a separate **Lexical Environment** record for that block, but in TDZ until reached.
2. **Execution phase:** statements run top-to-bottom. Assignments happen here.

For `var`, the relevant scope record is **the nearest enclosing function or module/script** — never an `if`, `for`, `while`, or bare `{}` block.

### Edge cases (the traps)
1. **`var` inside `if(false){}`** — declaration still hoisted; assignment never runs. Result: `undefined`, not `ReferenceError`.
2. **`var` inside a `for` loop** — single binding shared across all iterations. The "setTimeout in a for-loop" closure bug is this.
3. **`var` inside `try`/`catch`** — escapes to the function scope (intentional in legacy code so `err` info survives the block).
4. **Redeclaration** — `var x; var x;` is legal and silently merged. `let x; let x;` is a `SyntaxError`.
5. **Implicit globals via missing `var`** — `function f(){ x = 1; }` creates `x` on `globalThis` in sloppy mode, throws in strict.
6. **Hoisting across modules** — `var` at the top level of an ES module is **not** added to `globalThis` (unlike a classic script).
7. **`var` shadowing a `let` in an inner block** — `SyntaxError` at parse time (you can't `var` a name already in TDZ for the same scope).

## Brute force approach
"Read top-to-bottom and pretend declarations only exist after their line." This is what every junior does. It produces wrong answers for every `var`-in-block puzzle. The brute-force mental model treats JS like C/C++ block scope — but `var` predates block scope. Drop it.

## Optimal approach
**Two-pass mental model.** On every function you read:
1. **Pass 1 (creation):** scan the entire function body. List every `var` name and every `function fname()` declaration. They are pre-initialized in the Variable Environment — `var` to `undefined`, function declarations to the function object.
2. **Pass 2 (execution):** walk statements in order. Reach an assignment? Mutate the existing binding. Reach a `let`/`const`? Initialize the block-scoped binding (it was in TDZ before this line).

Annotate each step with the current `VE` (function-scoped, var bindings) and `LE` (block-scoped, let/const/class bindings).

## Solution (JavaScript)

```js
function demo() {
  console.log(a);          // (1) what prints?
  console.log(b);          // (2) what prints?
  console.log(typeof c);   // (3) what prints?

  if (true) {
    var a = 1;             // var → hoisted to demo's VE
    let b = 2;             // let → block-scoped, in TDZ until this line
    const c = 3;           // const → block-scoped, in TDZ until this line
  }

  console.log(a);          // (4) what prints?
  try {
    console.log(b);        // (5) what prints?
  } catch (e) {
    console.log('b is not defined');
  }

  for (var i = 0; i < 3; i++) { /* loop */ }
  console.log(i);          // (6) what prints?
}

demo();
```

Expected output:
```
undefined           // (1)
ReferenceError      // (2) — but caught? no, this throws BEFORE we reach line 5
```

Wait — line (2) throws synchronously, so lines (3)–(6) never run. The interviewer wants you to **notice** that. Re-order to make it runnable:

```js
function demo() {
  console.log(a);          // (1) undefined  — var a is hoisted
  console.log(typeof b);   // (2) 'undefined' — typeof swallows ReferenceError for undeclared, but here b is in TDZ → ReferenceError still throws
}
```

That's the real trap. `typeof` only swallows `ReferenceError` for **truly undeclared** names; a TDZ name throws regardless.

## Step-by-step dry run

Input (the cleaned-up version):
```js
function demo() {
  console.log(a);                    // line A
  if (true) {
    var a = 1;
    let b = 2;
  }
  console.log(a);                    // line B
  for (var i = 0; i < 2; i++) {}
  console.log(i);                    // line C
}
demo();
```

Trace:

```js
// === Creation phase for demo() ===
// VE: { a: undefined, i: undefined }
// LE (function body):  { } (let/const at block level created lazily)

// === Execution phase ===

// line A: console.log(a)
//   lookup 'a' in VE → undefined
//   prints: undefined

// enter if-block — new LE pushed for this block
//   LE(if-block): { b: <uninitialized, TDZ> }
//   VE still: { a: undefined, i: undefined } (var a does NOT live in the if's LE)

//   var a = 1  →  VE: { a: 1, i: undefined }
//   let b = 2  →  LE(if-block): { b: 2 }

// exit if-block — its LE is popped (b is gone)
//   VE: { a: 1, i: undefined }

// line B: console.log(a) → 1

// for-loop: var i is in demo's VE (NOT the loop's LE), so it's the same `i`
//   after loop: VE: { a: 1, i: 2 }

// line C: console.log(i) → 2
```

Output:
```
undefined
1
2
```

## Important takeaways

**Syntax to memorize**
- `var` lives in the **nearest function or module/script**. Never in a block.
- `let` / `const` / `class` / `function` (strict) live in the **nearest block**.
- During the creation phase, `var` is initialized to `undefined`. `let` / `const` are in **TDZ** until their declaration is reached.

**Patterns to reuse**
- Two-pass model: list hoisted names first, then walk statements. Apply this to every output-prediction puzzle.
- VE/LE annotation: write them down on the whiteboard. Interviewers love seeing the explicit record.

**Common mistakes**
- Saying "var inside `if(false)` is undeclared" — wrong. It's `undefined`.
- Confusing TDZ `ReferenceError` with "undeclared `ReferenceError`" — `typeof` swallows the latter but not the former.
- Thinking `for (var i...)` creates a fresh `i` per iteration — it does not. `let` does (see `let-in-for-loop-binding.md`).

**Backend relevance**
- Legacy `var` in Express middleware leaking error refs upward — sometimes intentional, sometimes a memory leak.
- Transpiled output: Babel often emits `var` for `let` when targeting older runtimes, but with renaming to preserve block semantics. Read the output to debug.

## Variants

1. **`let` in the same shape** — replace every `var` with `let` and re-trace. Each `let` is block-scoped; `console.log(a)` before the block throws `ReferenceError` (TDZ).
2. **`var` in a `switch` block** — `switch` is a single block; `var` in `case 1:` is visible in `case 2:`. Common bug.
3. **`var` redeclared inside a nested function** — only shadows in the inner function; outer scope's `var` is untouched. Asked as a follow-up to test that you understand function-scope boundaries.

## Revision notes

> **var-in-block — 60 second recap**
> - JS has two phases: **creation** (hoist) → **execution** (run).
> - `var`: hoisted to nearest **function / module / script**. Initialized to `undefined`.
> - `let` / `const` / `class`: hoisted to nearest **block**. In **TDZ** until declared.
> - `var` ignores `if`, `for`, `while`, `{}` blocks. Only `function`/module boundaries stop it.
> - `var x` declared inside `if(false){}` still exists as `undefined` in the enclosing function.
> - `for (var i...)`: single `i` shared across iterations. Source of the classic `setTimeout`-in-loop bug.
> - `try { var e; } catch {}`: `e` escapes to function scope.
> - `typeof tdzName` still throws — TDZ overrides `typeof`'s usual `ReferenceError` swallow.
> - Always annotate **VE** (function-scoped vars) and **LE** (block-scoped lets) on a whiteboard.
> - **Trap:** redeclaring `var` is silent; redeclaring `let`/`const` is a `SyntaxError`.
