# Hoisting and scope inside try/catch blocks

## Source
- Canonical senior-JS interview problem (BFE.dev, "You Don't Know JS: Scope & Closures" Ch. 3, Node error-handling deep dives).
- MDN reference: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/try...catch

## Why this question matters in interviews
The `try`/`catch` block has **three** scoping rules layered on top of each other, and senior interviewers will probe all of them:
1. The `try` block is a regular block — `let`/`const` are block-scoped; `var` escapes to the function.
2. The `catch (err)` parameter has its **own scope** — it's not a `var` in the function. (Pre-ES2019: this was always true. ES2019 added optional catch binding `catch {}`.)
3. The `catch` body is *another* block on top of the catch-param scope — `let` here doesn't collide with the `err` param.

Backend code is full of `try`/`catch` (every async route handler in Express, every DB call). Misunderstanding catch-scoping causes real bugs: declaring `var result` inside `try` and accessing it outside the block "works" by accident; declaring `let result` in the same spot throws. Knowing the rules lets you write production-correct error handling without guessing.

## Concepts involved

### Syntax to lock in
```js
function f() {
  try {
    var a = 1;    // var → escapes try, lives in f's scope
    let b = 2;    // let → block-scoped to try
  } catch (err) { // err is a binding in its OWN scope, not f's
    var c = 3;    // var → escapes both catch-body and catch-param scope to f
    let d = 4;    // let → block-scoped to catch body
  }

  console.log(a); // 1
  console.log(c); // 3 (if catch ran) or undefined (if try succeeded — c never assigned)
  // console.log(b);   // ReferenceError — block-scoped to try
  // console.log(d);   // ReferenceError — block-scoped to catch
  // console.log(err); // ReferenceError — bound in catch's param scope only
}
```

### Runtime / engine behavior — three layered scopes
For a single `try { ... } catch (err) { ... }`:

```
function-scope (VE)
└── try-block scope (LE for let/const inside try)
└── catch-param scope (LE containing only err)
    └── catch-body scope (LE for let/const inside catch body)
```

- `var` declarations anywhere inside try OR catch are hoisted to the **nearest function/module/script** — they live in the function VE, regardless of which block they appear in.
- The `err` parameter is in a scope *between* the function and the catch body. You cannot redeclare `err` with `let` in the catch body (TDZ-collision-style `SyntaxError`), but you *can* redeclare it with `var` — and the `var` shadows the param **only inside the body**, not outside (since the param is in its own scope).
- ES2019's **optional catch binding** lets you write `catch { ... }` (no param) when you don't need the error.
- The error you catch is **always** bound to `err` lazily — engines don't pre-populate it on the creation phase; it's assigned when an exception is thrown into the catch.

### Edge cases (the traps)
1. **`var err` inside catch body** — legal in non-strict; in strict mode it's a `SyntaxError` in some specs (and engines vary). Avoid it.
2. **`let err` inside catch body** — `SyntaxError: Identifier 'err' has already been declared`. The catch param is in an outer scope but `let` in the body sees it as a duplicate.
3. **`var x` inside `try`, accessed *after* the try block** — works and gives the assigned value (if the try ran past the `var x = ...` line) OR `undefined` if the assignment never executed. Common bug source.
4. **Reassigning the catch param** — `catch (err) { err = wrap(err); throw err; }` is fine; the param is mutable.
5. **Async + try/catch** — `try { await p; } catch (err) { ... }` works only for promises *awaited* in that try; sync `.then` chains escape.
6. **Re-throwing from finally** — `finally` is yet another block, with its own `let`/`const` scope. A `return` or `throw` in `finally` overrides the try/catch result.
7. **`var` in finally** — escapes to function scope just like `var` in try/catch.
8. **Optional catch binding (`catch {}`)** — no err scope is created. Useful for "swallow and continue" patterns. ES2019+.

## Brute force approach
"Treat try/catch like one big block." Wrong on two counts: (a) `var` doesn't respect block boundaries, so things "leak" upward in ways that surprise you, and (b) the catch param has its own micro-scope that no other construct has. Treating it as one block leads to "why does `let err` in the catch body throw a `SyntaxError`?" confusion.

## Optimal approach
**Always draw the three-layer diagram.** On the whiteboard:

```
[ function VE: { var hoists from try AND catch }
  [ try LE: { let/const inside try }
  ]
  [ catch-param LE: { err }
    [ catch-body LE: { let/const inside catch body }
    ]
  ]
]
```

For every variable, ask: which layer owns it? Then the output is mechanical.

## Solution (JavaScript)

```js
function trickyCatch() {
  try {
    var a = 1;
    let b = 2;
    throw new Error('boom');
  } catch (err) {
    var c = 3;            // hoisted to function VE
    let d = 4;            // block-scoped to catch body
    console.log(err.message); // 'boom'
    // let err = ...;     // SyntaxError — err already in outer (param) scope
    var err = 'overwrite'; // legal in sloppy mode! shadows param ONLY inside catch body
    console.log(err);     // 'overwrite'
  }

  console.log(a);  // 1   — var a leaked from try
  console.log(c);  // 3   — var c leaked from catch
  console.log(typeof err); // 'undefined' — err is bound to the catch param scope, not function scope
  // console.log(b);  // ReferenceError
  // console.log(d);  // ReferenceError
}

trickyCatch();
```

The `var err` inside catch is the subtle one. In sloppy mode it's legal and creates a `var err` in the function VE *as well as* shadowing the param inside the body. In strict mode some engines still allow this; others reject it. Either way, **don't write it.**

## Step-by-step dry run

```js
// === Creation phase for trickyCatch() ===
// Scan body for var decls anywhere (including inside try/catch/finally):
// VE: { a: undefined, c: undefined, err: undefined }   (yes, var err from the catch body too)
// Function declarations: none.

// === Execution phase ===

// enter try-block
//   LE(try): { b: <TDZ> }
//   var a = 1   → VE: { a: 1, c: undefined, err: undefined }
//   let b = 2   → LE(try): { b: 2 }
//   throw new Error('boom')

// throw → unwind to catch
//   exit try LE. b is gone.

// create catch-param LE: { err: <Error 'boom'> }
//   create catch-body LE: { d: <TDZ> }

//   var c = 3      → VE: { a:1, c:3, err: undefined }
//   let d = 4      → catch-body LE: { d: 4 }
//   console.log(err.message)   → reads err from param LE → 'boom'

//   var err = 'overwrite'
//     Tricky: the `var err` hoist went to VE (so VE.err: undefined was created at creation).
//     The assignment runs HERE. But there's ALSO a binding `err` in the param LE.
//     In sloppy mode, assignment to `err` writes to the NEAREST `err` in scope chain → the param LE.
//     (Some engines instead annex-B this to VE.err. V8 follows: assignment hits param.)
//     Result: param LE.err = 'overwrite'. VE.err stays undefined.

//   console.log(err) → 'overwrite' (reads from param LE — same binding just assigned)

// exit catch-body LE, exit catch-param LE.

// console.log(a)        → VE.a = 1
// console.log(c)        → VE.c = 3
// console.log(typeof err)
//   Now param LE is gone. Lookup walks to VE.err → undefined.
//   typeof undefined = 'undefined'.
```

Output:
```
boom
overwrite
1
3
undefined
```

The last line is the senior trap: `err` *appears* visible because of the `var err` hoist, but it's `undefined` because the assignment hit the catch param, not the VE binding.

## Important takeaways

**Syntax to memorize**
- `try`, `catch`-param, and `catch`-body are **three separate scopes** for `let`/`const`. `var` ignores all three and escapes to the function.
- The catch param `err` is **not** a function-scoped binding. It disappears once you leave the catch.
- ES2019 optional catch: `try { ... } catch { ... }` if you don't need the error object.

**Patterns to reuse**
- For "did this try succeed and what's the value?" pattern, declare `let result` **before** the try block:
  ```js
  let result;
  try { result = compute(); } catch (e) { result = fallback; }
  ```
  Avoids the `var`-escapes-and-might-be-undefined trap.
- Always `console.error(err)` (or log structured) **inside** catch. Outside the catch, `err` is gone.

**Common mistakes**
- Declaring `let result` inside try and reading it after — `ReferenceError`.
- Using `var` and assuming the assignment ran when it might not have (because the throw happened first).
- Thinking `catch (err) { let err = ... }` is legal — it's a `SyntaxError`.
- Trying to "rename" the catch param via `var err = ...` inside the body — works in sloppy mode but writes to the param, not the function scope. Subtle bug.

**Backend relevance**
- Express handlers: `try { const data = await db.query(...) } catch (err) { res.status(500).send(...) }`. The `data` is block-scoped — that's correct. Don't lift it out with `var`.
- AsyncLocalStorage / async-hooks context propagation: the `err` arg in catch is the same instance you can attach context to before re-throwing.
- Re-throwing wrapped errors: `catch (err) { throw new HttpError(500, err.message, { cause: err }) }` — uses ES2022 `cause`.

## Variants

1. **`finally` block scope** — add `finally { var f = 1; let g = 2; }`. Show that `f` escapes to function, `g` doesn't. Show that `return` inside `finally` overrides try/catch return.
2. **Optional catch binding** — refactor to `try { ... } catch { logSwallow() }`. When is this acceptable (telemetry/swallow patterns) vs forbidden (silent failure)?
3. **Async try/catch** — `try { await promise } catch (err)` works; `try { promise.then(...) } catch (err)` does not (the promise rejection escapes the try). Common bug.

## Revision notes

> **try/catch hoisting — 60 second recap**
> - **Three scopes** stack: function VE > try LE > catch-param LE > catch-body LE.
> - `var` anywhere inside try/catch/finally → hoisted to the **function VE**.
> - `let`/`const` → block-scoped to whichever of the three blocks contains them.
> - `catch (err)` — `err` is in its **own param scope**, not the function. Gone after the catch.
> - `let err` inside catch body → `SyntaxError` (duplicate binding with param).
> - `var err` inside catch body → legal sloppy, writes to the **param**, not the VE. Subtle.
> - ES2019: `catch { }` — optional binding, no err scope.
> - **Pattern:** declare result variables with `let` *before* the try block, assign inside.
> - **Async trap:** sync try/catch around `.then(...)` chains catches *nothing* — only `await`-ed rejections.
> - `finally` can override try/catch via `return`/`throw`. `var` in finally also escapes.
> - ES2022 `Error({ cause })` — preserve causal chain when re-throwing wrapped errors.
