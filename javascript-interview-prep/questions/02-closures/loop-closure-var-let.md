# Loop Closure Bug: `var` vs `let` in `setTimeout`

## Source
- Canonical JavaScript interview problem (asked at every JS-heavy interview; appears in You-Don't-Know-JS, Frontend Masters, MDN, and codedamn write-ups).
- Reference: `canonical://closures/loop-var-let`

## Why this question matters in interviews
This is **the** closure question. Every senior interviewer has it in their back pocket. It looks like a 3-line trick puzzle but actually tests three deep concepts at once: **`var` is function-scoped** (one binding per function call), **`let` is block-scoped** (a *fresh* binding per loop iteration), and **closures capture bindings by reference, not values**. Backend candidates who got fluent on Java/Go/Python often whiff this because Java's for-loop variable is also "fresh per iteration." JS's `var` isn't. If you stumble here, the interviewer immediately suspects every async/callback-heavy code you've ever written is buggy. Getting this crisp — with both fixes (`let` and IIFE) and a clean explanation of the per-iteration TDZ — is the closure equivalent of writing FizzBuzz cleanly.

## Concepts involved

### The buggy code
```js
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 0);
}
// Output: 3, 3, 3   (not 0, 1, 2)
```

### Why it prints `3, 3, 3` — the lexical environment view
1. `var i` is **function-scoped** (or global-scoped if at the top level). The `var` declaration is hoisted to the top of the enclosing function and shares **one single binding** across the entire loop. There is exactly **one `i`** in memory.
2. The loop runs synchronously:
   - Iteration 1: `i=0`. `setTimeout(cb1, 0)` schedules `cb1` to fire on the next macrotask tick. `i++` → `i=1`.
   - Iteration 2: `i=1`. `setTimeout(cb2, 0)` schedules `cb2`. `i++` → `i=2`.
   - Iteration 3: `i=2`. `setTimeout(cb3, 0)` schedules `cb3`. `i++` → `i=3`.
   - Loop condition `i<3` is now false. Loop exits with `i=3`.
3. All three callbacks (`cb1`, `cb2`, `cb3`) are arrow functions whose `[[Environment]]` points at the **same enclosing LE** — the one that holds the **one** `i` binding. They didn't capture `i`'s value at scheduling time; they captured a reference to the binding.
4. The call stack drains. The event loop now picks up macrotasks. Each callback runs and **reads `i` from the shared LE**. The current value is `3`. So all three log `3`.

This is the canonical "closures close over variables, not values" demonstration.

### Fix 1 — `let` (preferred, ES6+)
```js
for (let i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 0);
}
// Output: 0, 1, 2
```

#### Why `let` fixes it — per-iteration binding + TDZ
- The `for (let i = ...; ...; ...)` syntax has a **special rule** in the ECMAScript spec: a fresh `i` binding is created **once per iteration**, in the block scope of the loop body.
- Before each iteration's body runs, the engine:
  1. Reads the *previous* iteration's `i`.
  2. Creates a brand-new lexical environment for this iteration with its own `i` slot.
  3. Copies the previous value into the new slot.
  4. Runs the loop body (which can now bind closures to *this* iteration's `i`).
  5. After the body, evaluates the increment `i++` against the *new* binding.
- Each `setTimeout` callback's `[[Environment]]` points to *that iteration's* LE — a distinct slot per iteration. When the callbacks fire, each reads its own `i`. So you get `0, 1, 2`.
- The **TDZ (temporal dead zone)** is relevant because `let` declarations are not hoisted to the top of the block in the readable sense — accessing `i` before the `let i = ...` line throws `ReferenceError`. Inside a `for (let)` loop, each iteration's binding has its own TDZ from the start of the iteration until initialization.

### Fix 2 — IIFE (Immediately Invoked Function Expression) — the pre-ES6 way
```js
for (var i = 0; i < 3; i++) {
  (function (j) {
    setTimeout(() => console.log(j), 0);
  })(i);
}
// Output: 0, 1, 2
```
- The IIFE creates a **new function scope per iteration** at the moment it's invoked.
- The parameter `j` is a fresh binding per call, initialized to the current value of `i`.
- The inner `setTimeout` callback closes over `j` — that iteration's `j`, not the shared `i`.
- Conceptually this is what the engine does for you automatically when you write `for (let ...)` — except the engine does it more efficiently (no extra function call frame).

### Edge cases / interview traps
1. **`var` at the top of a script** — same problem, just at global scope (or module scope). `i` lives on `globalThis` (in scripts) or the module's TDZ-aware top-level LE.
2. **`forEach` doesn't have the bug** — `[0,1,2].forEach(i => setTimeout(() => console.log(i), 0))` prints `0,1,2` even with `var` because the callback parameter `i` is a fresh binding per call. The bug is specific to *for-loops with shared variables*.
3. **`const` in a for-loop** — `for (const i = 0; i < 3; i++)` throws because the increment tries to reassign. But `for (const x of arr)` works — each iteration's `x` is a fresh binding (same per-iteration semantics as `let`).
4. **Arrow vs `function`** — irrelevant to the bug. Both capture the enclosing LE. The bug is about *where* `i` lives, not about `this`.
5. **Why this matters for async/await** — the same bug bites with `await` in a `for (var)` loop. Use `let`.
6. **Performance** — per-iteration binding has a tiny cost. In hot inner loops, V8 optimizes it away. Don't manually downgrade to `var` for "perf."

### TDZ — temporal dead zone, briefly
- `let` and `const` declarations are hoisted to the top of their block, **but not initialized**. Accessing them before the `let`/`const` line throws `ReferenceError` — that gap is the TDZ.
- For a `for (let i = ...; ...; ...)` loop, each iteration's `i` binding has its own TDZ that closes at the moment of initialization.
- TDZ is what makes `let`/`const` safer than `var` (which silently gives you `undefined`).

## Brute force approach
The "buggy" version above is the brute attempt — and the bug surprises everyone who's worked in C/Java/Python first. Reject it not because it's slow but because it's *wrong*.

## Optimal approach
Use `let`. The engine creates a fresh per-iteration binding for free; closures attached to each iteration see that iteration's value. If you can't use `let` (legacy ES5 codebase), wrap the body in an IIFE that takes the loop variable as a parameter.

## Solution (JavaScript)

```js
// --- The bug (avoid) -----------------------------------------------
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log("var:", i), 0);
}
// Logs: var: 3, var: 3, var: 3

// --- Fix 1: let (preferred) ----------------------------------------
for (let i = 0; i < 3; i++) {
  setTimeout(() => console.log("let:", i), 0);
}
// Logs: let: 0, let: 1, let: 2

// --- Fix 2: IIFE (pre-ES6 / legacy environments) -------------------
for (var i = 0; i < 3; i++) {
  (function (j) {
    setTimeout(() => console.log("iife:", j), 0);
  })(i);
}
// Logs: iife: 0, iife: 1, iife: 2

// --- Fix 3 (honorable mention): bind ------------------------------
for (var i = 0; i < 3; i++) {
  setTimeout(console.log.bind(null, "bind:", i), 0);
}
// Logs: bind: 0, bind: 1, bind: 2
// Works because `bind` snapshots the args at bind-time.
```

## Step-by-step dry run

Input:
```js
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 100);
}
console.log("after-loop:", i);
```

Trace:
1. `var i` hoisted to enclosing function/global scope. **One `i` binding** in the LE.
2. **Synchronous phase (call stack):**
   - Iteration 1: `i=0`. `setTimeout` registers `cb1` to fire after 100ms. Task queue: `[cb1]`. `i++` → `i=1`.
   - Iteration 2: `i=1`. `setTimeout(cb2, 100)`. Task queue: `[cb1, cb2]`. `i++` → `i=2`.
   - Iteration 3: `i=2`. `setTimeout(cb3, 100)`. Task queue: `[cb1, cb2, cb3]`. `i++` → `i=3`.
   - Loop condition `3<3` false → loop exits.
   - `console.log("after-loop:", i)` prints `after-loop: 3`.
3. **Synchronous phase ends. Stack empties.** Event loop checks task queue.
4. ~100ms later, timers expire (all three were scheduled with `t=100`, fire in order):
   - `cb1` runs: looks up `i` via scope chain → finds the **single** `i` in the enclosing LE → value is `3`. Logs `3`.
   - `cb2` runs: same lookup → `3`. Logs `3`.
   - `cb3` runs: same lookup → `3`. Logs `3`.

Output order:
```
after-loop: 3
3
3
3
```

Now swap `var` for `let`:
- Iteration 1: a **fresh LE_iter1** is created with its own `i = 0`. `cb1` binds `[[Environment]] = LE_iter1`.
- Iteration 2: **fresh LE_iter2** with `i = 1`. `cb2` binds to it.
- Iteration 3: **fresh LE_iter3** with `i = 2`. `cb3` binds to it.
- When the callbacks fire, each reads `i` from its own LE → `0, 1, 2`. Three independent slots on the heap.

## Important takeaways

**Syntax to memorize**
- `var` is function-scoped → one binding shared across all iterations.
- `let` in a `for` head → fresh binding per iteration (special spec rule).
- IIFE: `(function (j) { ... })(i)` — manual per-iteration scope.
- `.bind(null, value)` — snapshots `value` at bind-time.

**Patterns to reuse**
- "Make sure each closure captures its own copy of the loop variable" — comes up with `setTimeout`, `addEventListener`, async DB calls in a loop, `Promise.all(items.map(async ...))`, generator yield in a loop.
- The IIFE trick is the **general mechanism for creating a new scope on demand** — pre-ES6 modules, jQuery plugins, polyfills all used it.

**Common mistakes**
- Assuming `var` gives you a fresh `i` per iteration (false; that's `let`).
- Thinking closures capture *values* (false; they capture *bindings*).
- "Fixing" it by adding `await` or `Promise.resolve()` — doesn't help, same shared `i`.
- Using `const` in the for-head — fails on the increment.
- Confusing the bug with the event-loop ordering (the `i=3` value is fixed *before* any callback runs — not a race).

**Related questions**
- "Predict the output: setTimeout vs Promise.then vs queueMicrotask in a loop" (event-loop bucket)
- "Print 1..5 with a 1-second delay between each" (classic follow-up; needs `let` + setTimeout offsets, or sequential await)
- `var` hoisting / TDZ questions (hoisting bucket)
- Closures in Counter / once / debounce (same capture-by-reference mechanic, deliberate this time)

## Variants

1. **Print 1..N with a 1-second delay between each** — combines this concept with timer arithmetic. Two solutions: (a) `let i` + `setTimeout(() => log(i), i * 1000)`, or (b) async function with `await sleep(1000)` in a `for (let)` loop.

2. **`map` returning promises, then `Promise.all`** — interviewer asks "do I have the same bug?" Show that the `map` callback parameter is a fresh binding per call (like `forEach`), so `[1,2,3].map(async i => fetch(i))` is safe — *no* bug.

3. **`var` in a try/catch in a loop** — `catch (e)` *does* have block scope (per spec) so `e` is per-iteration even without `let`. Useful trivia.

4. **The reverse trick** — interviewer writes `for (let i = ...)` and asks how to *force* the buggy `var` behavior. Answer: declare `let i` outside the loop, then use `for (i = 0; ...; ...)`.

## Revision notes

> **loop closure var/let — 60 second recap**
> - **The bug:** `for (var i = 0; i < N; i++) setTimeout(() => log(i))` prints `N` `N` times. One `i` binding shared across all iterations; loop finishes before any callback runs; all callbacks read the final `i`.
> - **Root cause:** closures capture **bindings** (slots in an LE), not values. `var` is function-scoped → one slot.
> - **Fix 1 (preferred):** `let` — spec creates a **fresh per-iteration binding** in the loop's block scope. Each callback closes over its own slot.
> - **Fix 2 (legacy):** IIFE — `(function (j) { setTimeout(() => log(j)); })(i);` — manually creates a new function scope per iteration.
> - **Fix 3 (cute):** `setTimeout(log.bind(null, i), 0)` — `bind` snapshots `i` at bind-time.
> - **forEach/map don't have the bug** — callback parameter is fresh per call.
> - **TDZ** matters here: `let` bindings hit the TDZ before initialization → throws on early access (safer than `var`'s `undefined`).
> - **Don't confuse with event-loop ordering:** the `i=N` value is fixed *before* the event loop runs any callback.
> - Family: any "closure inside a loop" pattern — async fetches, promise chains, generator yields.
