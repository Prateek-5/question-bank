# Hoisting

## Intuition first: why does "hoisting" even exist?

> **Mental Model:** Before JavaScript runs your code line-by-line, it does a quick "scouting pass" through the file (or the function, or the block) and writes every variable and function name onto a clipboard. Only after the clipboard is populated does it start running your code from the top. "Hoisting" is the colloquial word for "name appeared on the clipboard before the line that declared it."

Picture a teacher walking into a classroom. *Before* she starts teaching, she calls roll: "Alice — present. Bob — present. Carol — present." Every name is on the attendance sheet. Now she starts the lesson. If, mid-lesson, someone asks "is Bob here?", she doesn't have to look up — she already knows.

JavaScript does the same. The "roll call" is what we call the **creation phase**. Only `var` gets initialized to `undefined` during this phase (think: Bob is on the roll, but his desk is empty). `let`, `const`, `class` get *registered* but not initialized — they exist on the roll, but reading them throws an error until execution reaches their declaration line. That illegal-read window is the **Temporal Dead Zone (TDZ)**.

**Why does this concept exist?** Because early JavaScript wanted you to be able to call a function declared further down in the file. Forward references were considered useful (and Pascal/C-style "declare before use" felt heavy for a scripting language). So the engine pre-scans declarations. Decades later, this convenience has produced its own family of bugs — TDZ, dead-zone references, function-expression-vs-declaration confusion — which are exactly what interviewers test.

### First-principles definition

> **Hoisting** is not a real runtime operation; the engine does *not* literally move your code. What actually happens: when a scope is entered, the engine allocates bindings for every declaration found inside that scope *before* executing the body. The illusion of "moving declarations to the top" is just how it feels from the programmer's perspective.

### Progressive examples — start tiny, end realistic

```js
// 1) Tiniest hoisting — var
console.log(x); // undefined  (NOT ReferenceError!)
var x = 5;

// 2) Same shape with let — explodes
// console.log(y); // ReferenceError: Cannot access 'y' before initialization
let y = 5;

// 3) Function declarations — fully hoisted including the BODY
greet();                  // works — prints "hi"
function greet() { console.log("hi"); }

// 4) Function expression assigned to var — only the var is hoisted
// hello();               // TypeError: hello is not a function
var hello = function () { console.log("hi"); };

// 5) Interview classic — let + class TDZ
// new Foo();             // ReferenceError
class Foo {}
```

By the time you can predict outputs 1–5 in your sleep AND explain *why each one differs*, you're ready for the worked examples below.

## Mental Model

> Picture a two-pass interpreter:
>
> **Pass 1 (Creation):** Walk the scope. Stamp every declaration name onto an environment record. `var` gets a slot containing `undefined`. `function` declarations get a slot containing the actual function object. `let`/`const`/`class` get a slot marked "UNINITIALIZED" — touching this slot throws.
>
> **Pass 2 (Execution):** Run the code top-to-bottom. When execution hits `var x = 5`, only the `= 5` part actually runs (the `var x` part already happened in pass 1). When execution hits `let y = 5`, the slot is flipped from UNINITIALIZED to `5` — and from this line onward, reads succeed.

Every closure/scope question can be answered by asking: "What's on the clipboard? Has the slot been initialized yet?"

## Why interviewers care

Hoisting questions are the **cheapest filter** in JS interviews. In 3 lines of code they can test:
1. Do you separate **declaration** from **initialization**?
2. Do you know that `var`, `let`, `function`, `class` each behave differently?
3. Do you understand **TDZ** and why it exists?
4. Can you predict outputs without running the code?

If you fumble hoisting, you'll likely fumble closures, modules, and circular dependencies — so this 30-second question gives a fast signal.

## Common beginner confusion

- "`var x = 5` is one statement, right?" → Wrong. The engine treats it as two operations: declare `x` (creation phase) and assign `5` (execution phase).
- "`let` isn't hoisted." → False. `let` IS hoisted; the difference is the binding is in the TDZ until the declaration line. Test: `{ console.log(typeof x); let x; }` throws — the very *fact that it throws* (rather than printing `"undefined"`) proves `x` exists in the scope.
- "Hoisting moves code to the top." → No code is moved. The engine just pre-registers names.
- "`function foo(){}` and `var foo = function(){}` are the same." → They are not. The first is fully hoisted (callable above the line); the second is `undefined` above the line.
- "TDZ is just for safety." → Yes, but more concretely: TDZ catches the bug of using a variable before the line where it gains a real value — a bug `var` silently allowed.

## TL;DR
- **Hoisting = the engine allocates bindings during the "creation phase" of an execution context BEFORE running code line-by-line.**
- `var` is hoisted and initialized to `undefined`. `let`/`const`/`class` are hoisted but NOT initialized — accessing them throws → **Temporal Dead Zone (TDZ)**.
- **Function declarations** are fully hoisted (binding + value). **Function expressions / arrow functions** assigned to `var` hoist only the variable.
- ES Modules: top-level `var`/`function` do NOT pollute global; `import` bindings are hoisted and live (read-only).
- "Hoisting" is a mental model — V8 actually does this via the lexical environment + variable environment created at scope entry.

## Why backend interviewers care
- Backend code runs in long-lived Node processes; subtle TDZ bugs in module init can crash workers at boot.
- Understanding hoisting clarifies module load order, circular dependency hazards, and why `require` (CJS) vs `import` (ESM) behave differently.
- Output-prediction questions on hoisting are the cheapest filter interviewers use to gauge JS depth.

## Core mental model

> **Bridge:** Now that you have the "clipboard" picture, the formal spec terminology below should just feel like the engine's exact recipe for the same idea.

Every execution context (global, function, block for `let`/`const`) goes through two phases:

1. **Creation phase**: the engine scans the scope and registers all declarations. `var` → bound to `undefined`. `function` declarations → bound to the function object. `let`/`const`/`class` → bindings created but marked *uninitialized* (TDZ).
2. **Execution phase**: code runs top-to-bottom.

In V8, this is implemented via two environment records attached to the context: the **VariableEnvironment** (for `var`/function decls) and the **LexicalEnvironment** (for `let`/`const`/block scopes). The TDZ is literally a flag on the binding — reading it before initialization throws `ReferenceError`.

### The hoisting timeline (visual)

```
SOURCE                              CREATION PHASE             EXECUTION PHASE
─────────────────                   ─────────────────          ─────────────────
console.log(a);     ┐               a = undefined              a is undefined → log 'undefined'
console.log(b);     │   roll call → b = <UNINITIALIZED>        read b → ReferenceError (TDZ)
console.log(foo()); │               foo = <fn body>            call foo → "hi"
var a = 1;          │
let b = 2;          │
function foo() {…}  ┘
```

Notice three different fates for three different declaration kinds — same scope, same line numbers, totally different behavior. That's the entire essence of hoisting.

```js
console.log(a); // undefined   ← var hoisted + initialized
console.log(b); // ReferenceError ← let in TDZ
console.log(foo()); // "hi"    ← function decl fully hoisted

var a = 1;
let b = 2;
function foo() { return "hi"; }
```

#### Line-by-line walkthrough

Pretend you're the engine. You enter the global scope.

**Creation phase** (before any line runs):
- See `var a = 1;` → register `a`, set to `undefined`.
- See `let b = 2;` → register `b`, set to `<UNINITIALIZED>`.
- See `function foo() { ... }` → register `foo`, set to the function object itself.

**Execution phase** (now run top-to-bottom):
- `console.log(a)` → look up `a` → `undefined`. Print "undefined".
- `console.log(b)` → look up `b` → marker says UNINITIALIZED → throw `ReferenceError`.
- (If we'd gotten past line 2:) `foo()` → already a function → returns `"hi"`.

Function declarations are special because their *value* is hoisted, not just the name. Function expressions (`var f = function(){}`) only hoist the `var` binding (= undefined) — calling `f()` before the line throws TypeError.

Classes are hoisted but TDZ'd, so `new Foo()` before the `class Foo {}` line throws ReferenceError — unlike functions.

### Comparison table — who hoists what?

| Declaration             | Name in scope before line? | Value before line? | Reading before line | Calling before line |
|-------------------------|---------------------------|--------------------|---------------------|---------------------|
| `var x = 1`             | yes                       | `undefined`        | ok → `undefined`    | TypeError (not fn)  |
| `let x = 1`             | yes                       | UNINITIALIZED      | ReferenceError (TDZ)| ReferenceError      |
| `const x = 1`           | yes                       | UNINITIALIZED      | ReferenceError (TDZ)| ReferenceError      |
| `function foo() {}`     | yes                       | the function       | ok                  | ok                  |
| `class Foo {}`          | yes                       | UNINITIALIZED      | ReferenceError (TDZ)| ReferenceError      |
| `var f = function(){}`  | yes (as var)              | `undefined`        | ok → `undefined`    | TypeError           |
| `let f = () => {}`      | yes                       | UNINITIALIZED      | ReferenceError (TDZ)| ReferenceError      |

This single table answers ~80% of all hoisting interview questions.

## Syntax cheat sheet
```js
// var: hoisted, initialized to undefined, function-scoped
console.log(x); // undefined
var x = 5;

// let/const: hoisted but TDZ until declaration line
// console.log(y); // ReferenceError
let y = 5;
const z = 6;

// function declaration: fully hoisted
greet(); // works
function greet() { console.log("hi"); }

// function expression: only var is hoisted
// sayHi();        // TypeError: sayHi is not a function
var sayHi = function() {};

// arrow on let: TDZ
// say();          // ReferenceError
let say = () => {};

// class: hoisted but TDZ
// new Foo();      // ReferenceError
class Foo {}

// Block scope for let/const/class; var ignores blocks
{
  var leaks = 1;  // accessible outside
  let stays = 2;  // block-scoped
}
console.log(leaks); // 1
// console.log(stays); // ReferenceError

// var redeclaration allowed; let/const not
var a = 1; var a = 2; // ok
let b = 1; // let b = 2; // SyntaxError

// for-loop binding: var shares one binding; let creates one per iter
for (var i = 0; i < 3; i++) setTimeout(() => console.log(i)); // 3 3 3
for (let j = 0; j < 3; j++) setTimeout(() => console.log(j)); // 0 1 2

// typeof on TDZ var still throws (unlike undeclared)
// typeof undeclared; // "undefined"
// typeof tdzVar;     // ReferenceError
let tdzVar;
```

## Edge cases & interview traps
1. **`typeof` on a TDZ variable throws** — but `typeof` on a truly undeclared identifier returns `"undefined"`.
2. **Function declaration inside `if`** — pre-ES6 hoisted to enclosing function; in strict mode/ESM, block-scoped. Don't rely on it.
3. **`var` redeclaration is silent**; `let` redeclaration is a `SyntaxError` at parse time.
4. **Hoisting order**: function decls hoist *after* `var` bindings, so a same-named function decl wins over `var x;` at creation.
5. **`let` in `for`-loop creates a new binding per iteration** — fixes the classic closure-over-loop bug.
6. **TDZ applies even to `let x = x;`** — the right-hand `x` is accessed before init → throws.
7. **Classes are NOT hoisted like functions** — TDZ until declaration line.
8. **`var` declared inside a `try/catch` parameter shadows** the catch binding in weird ways pre-ES2019.
9. **`function` inside a function is hoisted to the enclosing function scope**, not the block.
10. **CJS `require`** runs the module top-to-bottom synchronously — circular requires return a partial `module.exports`. Hoisting of `function` decls means they're available before the require returns.
11. **ESM `import`** bindings are hoisted to the top of the module and are *live*; reassigning the import throws.
12. **`var` at module top-level in ESM is NOT a global** — unlike scripts where `var x` becomes `globalThis.x`.
13. **Arrow assigned to `const` before use** throws ReferenceError, not TypeError — different signal in stack traces.
14. **Destructuring with `let { a } = obj` is TDZ'd** the same way — `a` doesn't exist until the line runs.
    ```js
    const obj = { a: 1 };
    // console.log(a); // ReferenceError — a is in TDZ
    let { a } = obj;
    ```

## Interview worked examples

> **How to use this section:** For each example, predict the output first, *then* speak the "I'd say" out loud as if to an interviewer. The reasoning script matters as much as the answer.

### Example 1 — Predict the output (var hoisting)
**Asked as:** "What does this print? `console.log(foo); var foo = 'bar'; console.log(foo);`"

**How to think aloud:** "Three things go through my head: (1) is `foo` declared with var, let, or const? var. (2) Is there a creation phase? Yes. (3) What's the var initialized to in the creation phase? `undefined`. So the first log sees undefined, then the assignment runs, then the second log sees 'bar'."

I'd say: "var is hoisted to the top of the function/module scope and initialized to undefined during the creation phase. So the first log sees the binding but not its value yet. Only when execution reaches the assignment does foo become 'bar'."

```js
console.log(foo); // undefined  — binding exists, value not yet assigned
var foo = "bar";
console.log(foo); // "bar"
```

**Common candidate mistake:** Saying the first log throws ReferenceError (confusing `var` with `let`). Or saying it prints `"bar"` (forgetting that `var foo = 'bar'` is TWO operations executed at different times).

**What the interviewer is testing:** Do you separate "declaration hoisting" from "initialization"?
**Sharp follow-up they often ask:** "What changes if you replace `var` with `let`?" → first log throws ReferenceError (TDZ).

### Example 2 — `typeof` on a TDZ variable
**Asked as:** "Is `typeof x` always safe? Predict: `typeof x; let x = 1;`"

**How to think aloud:** "Old wisdom: `typeof` is safe even on undeclared things. New wrinkle: TDZ. If the variable is declared *somewhere in this scope* with let/const/class, then from the top of the scope to the declaration line, it's in TDZ — and TDZ reads throw, even via typeof. The trick is knowing that 'declared with let' does NOT mean 'undeclared.'"

I'd say: "`typeof` is safe on truly undeclared names — returns 'undefined'. But here `x` IS declared as let, so it sits in the TDZ from the start of the block until the `let x = 1` line. Reading it, even via typeof, throws."

```js
typeof undeclared;  // "undefined" — safe
// typeof x;        // ReferenceError — x is declared but in TDZ
let x = 1;
```

**Common candidate mistake:** Assuming `typeof` is *always* safe. The whole point of TDZ is that even peeking at the type throws.

**What the interviewer is testing:** TDZ exists for `let`/`const`/`class` from scope start, not from the line.
**Sharp follow-up they often ask:** "What about `class Foo {}`? Same TDZ rule."

### Example 3 — Function declaration vs expression
**Asked as:** "Why does this work for one and not the other?"

**How to think aloud:** "Function declaration `function greet() {}` is special — both name AND body are on the clipboard before execution starts. Function expression `var sayHi = function () {}` is just a var assignment to a function value; only the `var sayHi` is on the clipboard (as `undefined`). Calling `undefined()` throws TypeError, not ReferenceError — that distinction matters."

I'd say: "Function declarations hoist both the name and the function value. Function expressions assigned to `var` only hoist the `var` binding as undefined — calling undefined throws TypeError."

```js
greet();        // "hi" — function decl fully hoisted
function greet() { console.log("hi"); }

// sayHi();     // TypeError: sayHi is not a function
var sayHi = function () { console.log("hi"); };
```

**Common candidate mistake:** Saying the second case throws ReferenceError. The variable IS bound (to undefined). The error you get is TypeError — "undefined is not a function."

**What the interviewer is testing:** Function decl vs function expression hoisting asymmetry.
**Sharp follow-up they often ask:** "What if `sayHi` is on `let` or `const`?" → ReferenceError instead of TypeError, signalling TDZ vs undefined.

### Example 4 — `let` in `for` + `setTimeout` (the classic)
**Asked as:** "What does each loop print?"

**How to think aloud:** "Two ingredients: hoisting (or specifically, scope of `i`) and timer queue. With `var`, there's one `i`. The loop runs to completion, `i` becomes 3, *then* the three timers fire and all read 3. With `let`, the spec says each iteration of the for-loop gets a FRESH binding — so three separate `j`s, captured by three separate closures."

I'd say: "With `var`, all three closures share one binding `i`, which is 3 by the time the timers fire. With `let`, the spec creates a fresh `i` binding per iteration, so each closure captures its own."

```js
for (var i = 0; i < 3; i++) setTimeout(() => console.log(i)); // 3 3 3
for (let j = 0; j < 3; j++) setTimeout(() => console.log(j)); // 0 1 2
```

**Common candidate mistake:** Saying "the async nature messes up `i`." Wrong cause — the cause is *binding sharing*. Even synchronously stored callbacks show the bug.

**What the interviewer is testing:** Per-iteration binding semantics of `let` in `for` headers.
**Sharp follow-up they often ask:** "Fix the var version without using let." → wrap body in IIFE `(function(j){ setTimeout(...); })(i)`.

### Example 5 — Class hoisting
**Asked as:** "Will this run? `new Foo(); class Foo {}`"

**How to think aloud:** "Class looks like function syntactically but is a TDZ binding semantically. I'm going to look for the declaration form — `class Foo {}` — and assume TDZ. So `new Foo()` above it throws ReferenceError (not TypeError, not undefined — ReferenceError, which is the TDZ signal)."

I'd say: "No — classes are hoisted but TDZ-locked until the declaration line, unlike function declarations. The `new Foo()` call sits in the TDZ window and throws ReferenceError."

```js
// new Foo();          // ReferenceError: Cannot access 'Foo' before initialization
class Foo { constructor() { this.x = 1; } }
new Foo();             // works
```

**Common candidate mistake:** Saying classes hoist like functions because the syntax looks similar. They don't. The spec deliberately put them in TDZ.

**What the interviewer is testing:** Whether you know class differs from function in hoisting.
**Sharp follow-up they often ask:** "Why did the designers choose TDZ for class?" → Catch bugs early; avoid the foot-gun of partial constructor before fields.

### Example 6 — Function declaration inside `if`
**Asked as:** "Is this code portable? `if (true) { function bar() {} } bar();`"

**How to think aloud:** "This is one of the few JS questions where the answer is genuinely 'it depends on the mode.' Historically, browsers hoisted function declarations out of blocks to enclosing function scope. The spec now says: in strict mode and ESM, block-scope it. So `bar()` outside the block is unreliable — production code should never depend on this."

I'd say: "Pre-ES6 / sloppy mode in some engines, `bar` leaked to the function scope. In strict mode and ESM (and per spec), function declarations inside blocks are block-scoped — so `bar()` outside the block throws. Treat this as undefined behavior in production."

```js
"use strict";
if (true) { function bar() { return 1; } }
// bar(); // ReferenceError in strict mode
```

**Common candidate mistake:** Confidently saying "works fine" or "throws every time." The honest answer is "depends on strict mode / module type, so don't write code like this."

**What the interviewer is testing:** Awareness of strict mode block-scoped function declarations.
**Sharp follow-up they often ask:** "How would you reliably declare bar conditionally?" → assign a function expression to a `let` declared outside the block.

## Common machine-coding patterns
- **Output prediction with var/let mix** — when used: warm-up rounds. Sketch: `console.log(x); var x = 1; let y;` predict outputs.
- **Loop closure fix using `let`** — when used: async callbacks inside loops. Sketch:
  ```js
  for (let i = 0; i < n; i++) queue.push(() => i);
  ```
- **IIFE to avoid `var` leakage** — when used: legacy code, sandboxing. Sketch:
  ```js
  (function() { var private = 1; })();
  ```
- **Function declaration vs expression for circular deps** — when used: CJS modules referencing each other. Hoisted `function` decls survive partial loads; `module.exports = () => ...` assignments don't.

## Backend-specific notes
In Node, every CommonJS file is wrapped in a function `(function(exports, require, module, __filename, __dirname){ ... })`, so module top-level `var` is function-scoped — never global. Circular `require` returns whatever `module.exports` looked like at the point of re-entry; if you rely on a hoisted function declaration that was assigned to `module.exports` *after* the require, the partial export bites you. Defensive pattern: `module.exports.fn = function fn(){}` instead of `module.exports = { fn }` at the bottom.

In ESM (`.mjs` / `"type": "module"`), imports are statically resolved and hoisted — the engine builds the dependency graph before executing any module body, so circular ESM works better than circular CJS, but live bindings means you read the *current* value, not the value at import time.

## 60-second revision (day-before)
```text
┌──────────────────────────────────────────────────────────┐
│ HOISTING — DAY-BEFORE CRAM                               │
├──────────────────────────────────────────────────────────┤
│ • var: hoisted, = undefined, function-scoped, redeclare ok│
│ • let/const/class: hoisted + TDZ (ReferenceError)        │
│ • function decl: hoisted with VALUE; can call above line │
│ • function expr / arrow: only var name hoisted           │
│ • typeof TDZ → throws; typeof undeclared → "undefined"   │
│ • for(let): new binding per iter → closure-loop fix      │
│ • Classes: TDZ, NOT function-style hoisted               │
│ • ESM: imports hoisted + live + read-only                │
│ • CJS: top-down sync; circular → partial module.exports  │
│ • let x = x → TDZ on RHS → throws                        │
│ • Function decl beats var of same name in creation phase │
└──────────────────────────────────────────────────────────┘
```
