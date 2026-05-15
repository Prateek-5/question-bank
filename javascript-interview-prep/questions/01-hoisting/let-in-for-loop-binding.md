# Per-iteration binding semantics of `let` in for-loops

## Source
- Canonical senior-JS interview problem (LeetCode-style closures puzzle, BFE.dev #28, Frontend Masters "Deep JS Foundations").
- MDN reference: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/for#lexical_declarations_in_the_initialization_block

## Why this question matters in interviews
The "setTimeout in a for-loop" puzzle is the most-asked closure question in the history of JS interviews. The senior twist: explain **mechanically** why the `let` version prints `0 1 2` while the `var` version prints `3 3 3`. The answer is not "let is block-scoped" alone — it's the **per-iteration fresh binding** that ES2015 introduced specifically to fix this pattern. If you can explain how the spec creates a new lexical environment per iteration and copies the previous iteration's value into the next, you've demonstrated mastery of the language semantics, not just lore. Backend angle: Node service workers, batch processors, and async queues where you fire `N` tasks in a loop and need each callback to see *its own* index — this is daily Node code.

## Concepts involved

### Syntax to lock in
```js
// The classic puzzle
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 0);   // 3 3 3
}

for (let i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 0);   // 0 1 2
}
```

### Runtime / engine behavior — the spec's per-iteration binding trick
For `for (let i = 0; cond; step) { body }`, the spec (ECMA-262 §14.7.4.4 *CreatePerIterationEnvironment*) does roughly this:

```
let lastEnv = a new Lexical Environment with binding { i: 0 }
while (cond evaluated in lastEnv) {
  let thisIterEnv = a fresh Lexical Environment cloned from lastEnv
  // body runs with thisIterEnv as the current scope
  body
  // before evaluating `step`, copy `i` from thisIterEnv back into a fresh nextEnv
  let nextEnv = clone(thisIterEnv)
  step evaluated in nextEnv
  lastEnv = nextEnv
}
```

So **each iteration creates a brand-new `i` binding**, initialized to the value `i` had at the end of the previous iteration. Closures created inside the body capture *that iteration's* `i`, not a shared one.

For `var`, there is **one** binding in the enclosing function scope. All closures capture the same binding; by the time the timers fire, the loop has finished and `i` is `3`.

### Edge cases (the traps)
1. **`const` in `for (const x of arr)`** — works fine because `for...of` creates a new binding per iteration *and* never reassigns it.
2. **`for (let i = 0; i < n; i++)` with `i++` after closure creation** — closure already has its iteration's `i`; subsequent `i++` won't change it.
3. **`for-in` / `for-of` with `let`** — also per-iteration. Same fix for the `var` bug.
4. **`for (var ...)` workaround with IIFE** — `(function(j){ setTimeout(...) })(i)` was the pre-ES6 fix. Still seen in legacy code.
5. **`forEach((x) => ...)`** — has *always* given fresh `x` per iteration because each callback invocation creates a new function scope. The `var`-in-`for` bug never applied to `forEach`.
6. **Babel transpilation** — when targeting ES5, Babel emits an IIFE per iteration to emulate `let`'s fresh binding. Inspect the output to convince yourself.
7. **Performance** — per-iteration env creation has measurable overhead. V8 elides it when the body has no closures capturing the loop var. **Don't** prematurely de-`let` to `var`.

## Brute force approach
"Closures share scope, so all three timers see the final `i`." That's correct for `var` and wrong for `let`. The naive "closures share scope" line skips the fresh-binding-per-iteration step. If the interviewer asks "why does `let` work?", answering "because it's block-scoped" is **incomplete** — block-scoping alone wouldn't fix it (there's still only one `i` per loop). The fresh **per-iteration** binding is what fixes it. State that explicitly.

## Optimal approach
**Step through the spec.** For each loop iteration:
1. Clone the previous iteration's lexical environment into a fresh one.
2. Run the body in that fresh env. Any closure created inside the body captures *this* fresh env.
3. Apply the `step` expression in a new clone, becoming the env for the next iteration.

That's the entire mechanism. State it, then show the `0 1 2` output drops out naturally.

## Solution (JavaScript)

```js
// Demonstrate: with `let`, each iteration captures its own i.
function scheduleWithLet() {
  for (let i = 0; i < 3; i++) {
    setTimeout(() => console.log('let:', i), 0);
  }
}

// And the broken version with `var`.
function scheduleWithVar() {
  for (var i = 0; i < 3; i++) {
    setTimeout(() => console.log('var:', i), 0);
  }
}

// The pre-ES6 fix using IIFE — what Babel emits when targeting ES5.
function scheduleWithIIFE() {
  for (var i = 0; i < 3; i++) {
    (function (j) {
      setTimeout(() => console.log('iife:', j), 0);
    })(i);
  }
}

scheduleWithLet();   // let: 0, let: 1, let: 2
scheduleWithVar();   // var: 3, var: 3, var: 3
scheduleWithIIFE();  // iife: 0, iife: 1, iife: 2
```

## Step-by-step dry run

Trace `scheduleWithLet()`:

```js
// === Loop entry ===
// Per spec: create initial LE with { i: 0 } — call it Env0.
// LE(Env0): { i: 0 }

// --- Iteration 1 ---
// CreatePerIterationEnvironment: clone Env0 → Env1
// LE(Env1): { i: 0 }
// Body runs in Env1.
//   setTimeout( () => console.log(i) ) — the arrow closes over Env1.
//   T1 scheduled. T1's [[Environment]] = Env1.
// Step: i++ in Env1 mutates Env1's i to 1.
// But before the next iteration, clone Env1 → Env2 (with i=1) for the cond check.

// --- Iteration 2 ---
// LE(Env2): { i: 1 }
// Body in Env2: setTimeout closes over Env2. T2 scheduled.
// Step: i++ → Env2.i = 2. Clone Env2 → Env3.

// --- Iteration 3 ---
// LE(Env3): { i: 2 }
// setTimeout closes over Env3. T3 scheduled.
// Step: i++ → Env3.i = 3. Clone → Env4 (i=3). Cond fails. Exit.

// === Timers fire (microtask queue empty, task queue drains) ===
// T1 reads i from Env1 → 0   → "let: 0"
// T2 reads i from Env2 → 1   → "let: 1"
// T3 reads i from Env3 → 2   → "let: 2"
```

Now trace `scheduleWithVar()`:

```js
// === Loop entry ===
// VE (function scope of scheduleWithVar): { i: 0 }
// Note: only ONE binding for i, in the function scope. No per-iteration env.

// Iter 1: setTimeout( () => console.log(i) ) — arrow closes over VE.
// Iter 2: same VE.
// Iter 3: same VE.
// Step: i goes 0 → 1 → 2 → 3. Loop exits.

// VE now: { i: 3 }.

// Timers fire. All three read i from the SAME VE → 3 each time.
// Output: "var: 3" × 3.
```

## Important takeaways

**Syntax to memorize**
- `for (let i = 0; ...)` → fresh `i` per iteration. Closures-in-body capture *that iteration's* `i`.
- `for (var i = 0; ...)` → single `i` shared across all iterations. Classic closure bug.
- `for (const x of arr)` and `for (let x of arr)` → also per-iteration. `const` is safe here.

**Patterns to reuse**
- **"Spec-accurate explanation"** — instead of "let is block-scoped", say "ES2015 added CreatePerIterationEnvironment for `for (let ...)` headers specifically to make this pattern work." That phrase wins points.
- **IIFE fix** is the pre-ES6 equivalent. Knowing both shows historical depth.
- **`forEach`** sidesteps the bug because each callback invocation has its own arg binding.

**Common mistakes**
- Saying "block scope fixes it" — incomplete. Block scope + per-iteration cloning is what fixes it.
- Confusing `for...of` semantics with `for(let i;;)` — both work, but for different reasons (`for...of` creates a fresh binding *every iteration* including the first; the C-style `for` clones across the step expression).
- Believing the `let` version has the same memory cost as `var` — it doesn't. V8 only optimizes away the per-iter env when no closure captures `i`.

**Backend relevance**
- Firing N async tasks in a loop where each callback needs *its own* index/payload: always use `let` (or destructure into a `const` inside the body).
- `for (const task of tasks) { await task() }` for sequential awaits — each iteration's `task` is its own binding.

## Variants

1. **Replace `setTimeout` with `Promise.resolve().then`** — same fix (let vs var) applies; demonstrates the bug isn't timer-specific.
2. **`for (let i = 0; i < 3; i++) { const j = i; ... }`** — `const j` inside the body always works regardless of header, because each iteration creates a fresh body scope. Useful when the header has to be `var` for legacy reasons.
3. **`for-of` over an async iterable** — `for (const chunk of asyncIter)` — explain the fresh-binding semantics and why this is safe with concurrent awaits.

## Revision notes

> **let in for-loops — 60 second recap**
> - `for (let i = 0; ...; ...)` creates a **fresh `i` per iteration** via the spec's `CreatePerIterationEnvironment`.
> - `for (var i = 0; ...; ...)` creates **one** `i` in the function scope. All closures share it.
> - The `let` version isn't just "block-scoped" — it's **block-scoped AND cloned each iteration**.
> - Trace mentally as: `Env0 → clone to Env1 → run body → step in Env1 → clone Env1 → Env2 → ...`.
> - Each closure stores `[[Environment]]` pointing at its iteration's env, so timers fire with the captured `i`.
> - Pre-ES6 fix: IIFE — `(function(j){ ... })(i)`. Babel emits this when transpiling.
> - `forEach`/`map`/`for-of` never had this bug — callback args are fresh per invocation.
> - **Trap:** "block scope fixes it" is half-answer. Spec wording is "per-iteration binding".
> - V8 elides per-iter env when the body has no closures over `i` — no premature de-`let`-ing.
> - **Async loops:** use `for (const task of tasks) { await task() }` to keep each iteration's `task` isolated.
