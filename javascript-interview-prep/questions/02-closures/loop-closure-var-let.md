# The loop-closure bug — why `var` in a `setTimeout` loop prints the wrong thing

> **Difficulty:** Medium   |   **Time:** ~15 min   |   **Prereqs:** [counter.md](./counter.md), [`concepts/closures.md`](../../concepts/closures.md), [`concepts/hoisting.md`](../../concepts/hoisting.md)
>
> **Source:** Canonical JS interview problem (Frontend Masters, MDN, *You Don't Know JS*).

---

## 1. Problem statement

**The code**
```js
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 0);
}
```

**Input / Output examples**

| Code                                                          | Output      | Why                                          |
|---------------------------------------------------------------|-------------|----------------------------------------------|
| `for (var i = 0; i < 3; i++) setTimeout(() => log(i));`       | `3, 3, 3`   | shared `i` binding, loop ends before timers fire |
| `for (let i = 0; i < 3; i++) setTimeout(() => log(i));`       | `0, 1, 2`   | fresh `i` binding per iteration              |
| `for (var i = 0; i < 3; i++) (function (j) { setTimeout(() => log(j)); })(i);` | `0, 1, 2` | IIFE creates a fresh scope per iteration     |
| `for (var i = 0; i < 3; i++) setTimeout(log.bind(null, i), 0);` | `0, 1, 2`   | `bind` snapshots `i` at bind-time            |
| `[0,1,2].forEach(i => setTimeout(() => log(i)));`             | `0, 1, 2`   | callback parameter `i` is fresh per call     |

**Constraints**
- Predict the output.
- Provide at least two fixes (`let` and IIFE).
- Articulate why closures capture **bindings**, not values.

---

## 2. Plain-English restatement

You have a loop that schedules three `setTimeout`s. Each timer logs the loop variable. The naive expectation — `0, 1, 2` — is wrong with `var`. The actual output is `3, 3, 3`. The interviewer wants you to explain why, then show how to fix it.

The "trick" is that `var` creates **one** variable shared across all loop iterations, and closures don't capture values — they capture references to bindings. By the time the timers fire, the shared variable has reached `3`.

---

## 3. Why this matters in interviews

This is *the* closure question. Every senior interviewer has it in their back pocket. It looks like a three-line trick puzzle but actually tests three deep concepts at once: **`var` is function-scoped** (one binding per function call), **`let` is block-scoped** (a fresh binding per loop iteration), and **closures capture bindings by reference, not values**. Candidates from Java/Go/Python often whiff this because *their* for-loop variables are also "fresh per iteration." If you stumble here, the interviewer immediately suspects every async/callback-heavy code you've ever written is buggy. Getting it crisp — with both fixes and a clean explanation — is the closure equivalent of writing FizzBuzz cleanly.

---

## 4. Mental model

Picture **three runners standing at a sign that says `i = ?`**. The sign is the loop variable. With `var`, there's **one** sign in the whole stadium; every runner reads it at the moment they finally start. With `let`, each runner gets their **own** sign, fixed at the moment the runner was placed.

```
   var i — single shared sign in the stadium:
   
            sign  ─── i: 0 → 1 → 2 → 3   (loop mutates the one sign)
            
            runner₁ scheduled at i=0, fires at end:  reads sign → 3
            runner₂ scheduled at i=1, fires at end:  reads sign → 3
            runner₃ scheduled at i=2, fires at end:  reads sign → 3
   
   ─────────────────────────────────────────────────────────────────
   
   let i — each runner gets their own sign:
   
            iter1: sign₁ ─── i: 0   runner₁ binds to sign₁  →  reads 0
            iter2: sign₂ ─── i: 1   runner₂ binds to sign₂  →  reads 1
            iter3: sign₃ ─── i: 2   runner₃ binds to sign₃  →  reads 2
```

The fix swaps "one shared mutable binding" for "fresh binding per iteration." The spec literally creates a new LE on each iteration when you use `let`.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. With `var i`, do all callbacks fire after the loop finishes, or interleaved with it? (Hint: think about the call stack vs the task queue.)
> 2. With `let i`, what specifically does the engine do at the start of each iteration that makes the bug disappear?
> 3. Why doesn't `[0,1,2].forEach((i) => setTimeout(...))` have the bug, even though `i` is also a loop variable?

---

## 6. Brute force — walked through

### The buggy version

```js
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 0);
}
// Output: 3, 3, 3
```

Step-through:

1. `var i` is **function-scoped** (or global). The declaration hoists to the top of the enclosing scope; there's **one** binding named `i` in memory.
2. The synchronous part of the loop runs:
   - Iteration 1: `i=0`. `setTimeout(cb1, 0)` schedules `cb1` for the next macrotask tick. `i++` → `i=1`.
   - Iteration 2: `i=1`. Schedule `cb2`. `i++` → `i=2`.
   - Iteration 3: `i=2`. Schedule `cb3`. `i++` → `i=3`.
   - Loop condition `3 < 3` is false. Loop exits with `i=3`.
3. All three callbacks have `[[Environment]]` pointing at the **same** enclosing LE — the one with the single `i` binding. They didn't capture `i`'s value at scheduling time; they captured a reference.
4. The call stack drains. The event loop picks up macrotasks. Each callback reads `i` from the shared LE — value is now `3`. All three log `3`.

### Why "use a counter / use `await`" doesn't help

```js
for (var i = 0; i < 3; i++) {
  await Promise.resolve();
  setTimeout(() => console.log(i), 0);
}
```

The `await` doesn't isolate `i`. The shared binding still grows to `3` by the time the timers fire. Adding `Promise.resolve()`, `await`, microtasks — none of them fix the binding-sharing problem.

---

## 7. The unlocking insight

> **Closures capture *bindings* (named slots in a lexical environment), not values. `var` shares one binding across all loop iterations; `let` creates a fresh binding per iteration.**

The ECMAScript spec has a special rule for `for (let i = ...; ...; ...)` loops: at the start of each iteration, the engine creates a **new** lexical environment with a fresh `i` slot, copies the previous iteration's value into it, runs the body, then advances. So callbacks scheduled in iteration 3 close over iteration 3's `i` — a different slot than iteration 2's.

`var` has no such rule. The single `i` lives in the enclosing function's variable environment from the moment the loop starts. Every iteration mutates the same slot. Every closure scheduled during the loop reads the same slot when it eventually fires.

**The IIFE fix replicates the per-iteration-binding manually:**

```js
for (var i = 0; i < 3; i++) {
  (function (j) {
    setTimeout(() => console.log(j), 0);
  })(i);
}
```

The IIFE creates a new function scope per iteration at the moment of invocation. The parameter `j` is a fresh binding per call, initialized to the current `i`. The inner `setTimeout` callback closes over `j` — its iteration's `j` — not the shared `i`. Conceptually, `for (let)` does the same thing more efficiently (no extra call frame).

**TDZ matters:** `let` declarations are hoisted to the top of their block but are in the **temporal dead zone** until initialized. Accessing them early throws `ReferenceError`. For each iteration in a `for (let)`, the new `i` has its own TDZ that closes the moment the iterator advances to the body.

---

## 8. Solution (annotated)

```js
// --- The bug --------------------------------------------------------
for (var i = 0; i < 3; i++) {                        // step 1: ONE `i` binding (function-scoped)
  setTimeout(() => console.log(i), 0);               // step 2: callback closes over the SHARED `i`
}
// Logs: 3, 3, 3 (by the time callbacks fire, loop is done; i = 3)

// --- Fix 1: let (preferred, ES6+) -----------------------------------
for (let i = 0; i < 3; i++) {                        // step 1: fresh `i` binding per iteration
  setTimeout(() => console.log(i), 0);               // step 2: each callback closes over its OWN `i`
}
// Logs: 0, 1, 2

// --- Fix 2: IIFE (pre-ES6 / legacy) ---------------------------------
for (var i = 0; i < 3; i++) {
  (function (j) {                                     // step 1: IIFE creates a new scope per iteration
    setTimeout(() => console.log(j), 0);              // step 2: callback closes over `j` (this iteration's)
  })(i);                                              // step 3: pass current `i` into `j`
}
// Logs: 0, 1, 2

// --- Fix 3 (honourable mention): bind --------------------------------
for (var i = 0; i < 3; i++) {
  setTimeout(console.log.bind(null, i), 0);          // bind snapshots `i` at bind-time
}
// Logs: 0, 1, 2
```

**Try it yourself**

```js
// 'After loop' is printed first because the loop is synchronous; timers wait for the next tick
for (var i = 0; i < 3; i++) setTimeout(() => console.log(i), 0);
console.log('after loop:', i);
// after loop: 3
// 3
// 3
// 3

// forEach doesn't have the bug — callback parameter is fresh per call
[0, 1, 2].forEach((i) => setTimeout(() => console.log(i), 0));
// 0
// 1
// 2
```

---

## 9. Step-by-step dry run

Input:

```js
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 100);
}
console.log('after loop:', i);
```

Values-first trace:

| Phase | Step             | `i`     | Task queue           | Output                |
|-------|------------------|---------|----------------------|-----------------------|
| sync  | iter 1 schedules | `0 → 1` | `[cb1]`              | —                     |
| sync  | iter 2 schedules | `1 → 2` | `[cb1, cb2]`         | —                     |
| sync  | iter 3 schedules | `2 → 3` | `[cb1, cb2, cb3]`    | —                     |
| sync  | post-loop log    | `3`     | (same)               | `after loop: 3`       |
| t=100 | cb1 reads shared `i` | `3` | `[cb2, cb3]`         | `3`                   |
| t=100 | cb2 reads shared `i` | `3` | `[cb3]`              | `3`                   |
| t=100 | cb3 reads shared `i` | `3` | `[]`                 | `3`                   |

With `let i`, three different LEs would exist on the heap by t=100; each `cb` would read its own `i` (0, 1, 2).

---

## 10. Common confusion + traps

1. **"`var` gives me a fresh `i` per iteration."**
   False. That's `let`. `var` is function-scoped; **one** binding shared across all iterations.

2. **"Closures capture values."**
   False. They capture **bindings** (references to slots). The captured value is whatever the slot holds **at the moment the closure runs**, not when it was defined.

3. **"Adding `await` or `Promise.resolve()` fixes it."**
   False. Same shared `i`. The microtask still reads the latest value.

4. **`const` in the for-head breaks.**
   `for (const i = 0; i < 3; i++)` throws on the increment (`i++` reassigns a const). But `for (const x of arr)` works — `x` is a fresh binding per iteration, like `let`.

5. **`forEach`/`map` don't have the bug.**
   The callback parameter is a fresh binding per call. So `[0,1,2].forEach((i) => setTimeout(() => log(i)))` prints `0, 1, 2` correctly even with the variable named `i`.

6. **Confusing the bug with event-loop ordering.**
   The `i = 3` value is fixed *before* any timer fires — the loop is synchronous. It's not a race. The bug is purely about binding sharing.

7. **`var` at module top-level (ES modules).**
   `var` in ES modules does NOT become a property of `globalThis`. It's module-scoped. Same loop bug still applies.

8. **Arrow vs `function`.**
   Irrelevant to the bug. Both capture the enclosing LE. The bug is about *where* `i` lives.

---

## 11. Senior follow-ups & variants

### Variant 1 — Print 1..N with a 1-second delay between each

Combines the closure fix with timer arithmetic.

```js
// Solution A: increasing delays
for (let i = 1; i <= N; i++) {
  setTimeout(() => console.log(i), i * 1000);
}

// Solution B: sequential await
async function printRange(n) {
  for (let i = 1; i <= n; i++) {
    console.log(i);
    await new Promise((r) => setTimeout(r, 1000));
  }
}
```

Solution B uses `for (let)` to avoid the same bug class in an async loop.

### Variant 2 — `Promise.all` on `map` results

The interviewer asks: "Does `[1,2,3].map(async (i) => fetch(i))` have the same bug?" Answer: **No.** The `map` callback parameter `i` is a fresh binding per call. Each async function captures its own `i`. Safe.

### Variant 3 — `var` in `try/catch` in a loop

`catch (e)` *does* have block scope per spec — `e` is per-iteration even inside a `for (var)` loop. Useful trivia for the same problem class.

### Variant 4 — Force the `var` behaviour with `let`

The interviewer flips the question: "Make this `for (let)` loop print `3, 3, 3`." Trick: declare `let i` outside the loop, then use `for (i = 0; ...; ...)` — now `i` is hoisted out of the for-head's block scope.

```js
let i;
for (i = 0; i < 3; i++) setTimeout(() => console.log(i), 0);
// Logs: 3, 3, 3
```

### Variant 5 — The IIFE generalizes

The IIFE trick is the **general mechanism for creating a new scope on demand** — pre-ES6 modules, jQuery plugins, polyfills all used it. Modern JS uses `let`/`const` + blocks, but the principle is the same.

---

## 12. How to think aloud in the interview

> "The output is `3, 3, 3`, not `0, 1, 2`. Reason: `var` is function-scoped, so there's one `i` shared across all iterations. Closures capture bindings, not values — when the timers fire, they all read the latest `i`, which is `3` because the loop has already finished. Three fixes: (1) `let` — spec creates a fresh `i` per iteration; (2) IIFE — manually create a new scope per iteration; (3) `setTimeout(log.bind(null, i), 0)` — `bind` snapshots `i` at bind-time. Preferred: `let`. `forEach` and `map` don't have the bug because the callback parameter is a fresh binding per call. Don't confuse this with the event loop — the bug exists even at `0ms` because the loop is synchronous."

---

## 13. 60-second revision

> - **The bug:** `for (var i = 0; i < N; i++) setTimeout(() => log(i))` prints `N` `N` times. **One `i` binding shared**; loop ends before any callback fires; all callbacks read the final value.
> - **Root cause:** closures capture **bindings**, not values. `var` is function-scoped → one slot.
> - **Fix 1 (preferred):** `let` — spec creates a **fresh per-iteration binding**.
> - **Fix 2 (legacy):** IIFE — `(function (j) { setTimeout(() => log(j)); })(i);` — new scope per iteration.
> - **Fix 3 (cute):** `setTimeout(log.bind(null, i), 0)` — `bind` snapshots `i` at bind-time.
> - **`forEach` / `map` don't have the bug** — callback parameter is fresh per call.
> - **TDZ** matters here: `let` bindings throw on early access (safer than `var`'s `undefined`).
> - **Don't confuse with event-loop ordering:** `i` reaches the final value **before** any callback runs.
> - **Family:** any "closure inside a loop" pattern — async fetches, promise chains, generator yields, React render callbacks.

---

**Related:** [counter.md](./counter.md) · [setinterval-stale-closure.md](./setinterval-stale-closure.md) · [closure-memory-leak-dom.md](./closure-memory-leak-dom.md) · [`05-event-loop/microtask-macrotask-order.md`](../05-event-loop/microtask-macrotask-order.md)

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md), [`concepts/hoisting.md`](../../concepts/hoisting.md)
