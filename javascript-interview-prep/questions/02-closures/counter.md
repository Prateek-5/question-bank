# Build a counter factory that retains private state across calls

> **Difficulty:** Easy   |   **Time:** ~10 min   |   **Prereqs:** [`concepts/closures.md`](../../concepts/closures.md)
>
> **Source:** [LeetCode 2620 — Counter](https://leetcode.com/problems/counter/)

---

## 1. Problem statement

**Signature**
```ts
function createCounter(n: number): () => number;
```

**Input / Output examples**

| Call                     | Subsequent calls of the returned function | Output sequence |
|--------------------------|--------------------------------------------|-----------------|
| `const c = createCounter(10); c(); c(); c();` | three calls | `10, 11, 12` |
| `const c = createCounter(0); c(); c();`       | two calls   | `0, 1`       |
| `const c = createCounter(-5); c();`           | one call    | `-5`         |
| `const a = createCounter(0); const b = createCounter(0); a(); a(); b();` | mixed | `a → 0, 1`, `b → 0` (independent) |

**Constraints**
- `createCounter` returns a function (not a value, not a class instance).
- Every fresh call to `createCounter(n)` must produce an **independent** counter — two counters from two factory calls share *nothing*.
- The very first call to the returned function must give back `n` itself (not `n+1`).

---

## 2. Plain-English restatement

The interviewer hands you a function `createCounter(n)` and asks you to make it return *another* function. Every time *that* returned function is called, it gives you back the next integer in sequence, starting from `n`. Two separate factory calls must produce two independent counters that don't see each other.

In ~10 lines, this problem forces you to demonstrate the single most important closure pattern in JavaScript: **a function that keeps private state alive across calls**.

---

## 3. Why this matters in interviews

This is the second-most-asked warm-up after debounce. The same shape appears all over production code: request-ID generators, sequence numbers, retry counters, connection-pool tickets, rate-limiter token counts, idempotency keys. Interviewers also use it as a springboard for follow-ups — "now add reset," "now make it private without closures," "now compare with `#field`." Doing this one cleanly signals strong fundamentals; tripping on it signals you may struggle with later closure-heavy questions.

---

## 4. Mental model

Imagine a **safety-deposit vault** that holds a single number. The factory `createCounter(n)` opens a fresh vault, places `n` inside, and hands you a special key — the returned function. Every time you turn the key, it does two things in one motion: shows you the current number, then bumps it by 1. The vault itself is unreachable except through the key. If you call the factory again, you get a *different* vault and a *different* key.

```
   createCounter(10)
        │
        ├── allocates a fresh slot:  ┌───────────┐
        │                            │  n = 10   │   ← the "vault"
        │                            └───────────┘
        │                                  ▲
        │                                  │ closes over (reads/writes)
        │                            ┌───────────┐
        └── returns ───────────────▶ │  () => …  │   ← the key (returned function)
                                     └───────────┘

   c(); c(); c();
   ↓    ↓    ↓
   10   11   12   (each call reads → returns → increments the SAME vault)
```

The vault survives on the heap *for as long as the key (returned function) is still reachable*. That survival mechanism is what JavaScript calls a **closure**.

---

## 5. Try it yourself first

> **Predict the answers before reading on:**
>
> 1. If you call `createCounter(0)` twice and run each result once, what does each one return?
> 2. Should you use `return n++` or `return ++n`? What does each produce on the **first** call?
> 3. Could you implement this without a closure — using only an outer global variable? What goes wrong?

(Don't peek. Even a 5-second guess locks in the lesson when you read the explanation below.)

---

## 6. Brute force — walked through

### Attempt 1: store the count on a global

```js
let n = 0;
function createCounter() {
  return function () { return n++; };
}
```

What's wrong? Two callers of `createCounter()` share the **same** global `n`. The problem statement requires independent counters; this fails the very last row of the I/O table:

```js
const a = createCounter();
const b = createCounter();
a();    // 0
a();    // 1
b();    // 2  ← BUG: b leaked through a's state
```

Reject the global-counter approach in five seconds. The lesson: we need **per-instance isolation**.

### Attempt 2: a class with a public field

```js
class Counter {
  constructor(n) { this.n = n; }
  inc() { return this.n++; }
}
```

Two problems. First, the prompt asks for a *function*, not a class — the contract is `c()`, not `c.inc()`. Second, `this.n` is publicly mutable from the outside: `c.n = 999`. The "private state" requirement is broken.

### Attempt 3: the parameter `n` itself becomes the private slot

```js
function createCounter(n) {
  return function () { return n++; };
}
```

This works. Why? It's the unlocking insight in section 7.

---

## 7. The unlocking insight

> **Every function call creates a fresh local environment, and a returned inner function keeps that environment alive on the heap.**

When you call `createCounter(10)`, JavaScript creates a fresh **lexical environment (LE)** — a small record holding one slot: `n = 10`. The inner function defined inside `createCounter`'s body captures a reference to this LE (the spec calls it `[[Environment]]`). Even after `createCounter` returns and its stack frame is popped, the LE survives on the heap *because the returned inner function still points at it*.

Three consequences fall out of this:

1. **Privacy.** `n` is not a property of any object you can name; it's a slot inside a lexical environment that is reachable only via the inner function. There is no `.n` accessor, no `Reflect.ownKeys`, no `Object.getOwnPropertyNames` — nothing exposes it. Stronger than class `this.n`, equivalent to ES2022 `#n`, and the closure pattern predates `#` by 20 years.
2. **Mutation by reference.** Inside the inner function, `n++` doesn't capture a snapshot of `n = 10`; it captures a *binding* to the slot in the LE. Reading and writing both go through that binding, so every call sees and updates the same number.
3. **Independence per factory call.** Each invocation of `createCounter` creates a *new* LE — a separate vault with its own `n`. Two counters from two factory calls share nothing because there's nothing to share: they don't even refer to the same LE.

That's the entire trick. Everything else — the choice of post-increment, the edge cases — falls out of these three properties.

---

## 8. Solution (annotated)

```js
function createCounter(n) {                // step 1: outer function holds the private slot `n`
                                            //         each call creates a fresh LE with n in it
  return function () {                      // step 2: inner function closes over the LE above
                                            //         (it has [[Environment]] = outer's LE)
    return n++;                             // step 3: post-increment — RETURNS current n,
                                            //         THEN bumps n by 1 inside the same LE
  };
}
```

**Try it yourself**

```js
const c = createCounter(10);
console.log(c());   // 10
console.log(c());   // 11
console.log(c());   // 12

const a = createCounter(0);
const b = createCounter(0);
console.log(a());   // 0
console.log(a());   // 1
console.log(b());   // 0  ← independent vault
```

---

## 9. Step-by-step dry run

Input:

```js
const c = createCounter(10);
c(); c(); c();
```

Values-first trace:

| Step | Action          | `n` in closure (before → after) | Returned |
|------|-----------------|----------------------------------|----------|
| init | `createCounter(10)` | (created with `10`)          | the inner function `c` |
| 1    | `c()`           | `10 → 11`                       | `10`     |
| 2    | `c()`           | `11 → 12`                       | `11`     |
| 3    | `c()`           | `12 → 13`                       | `12`     |

<details>
<summary><b>Engine internals (click to expand)</b></summary>

1. `createCounter(10)` pushes a frame; the engine creates `LE_outer = { n: 10 }`.
2. The `function () { ... }` literal creates a function object whose `[[Environment]]` points at `LE_outer`.
3. `createCounter` returns. Its frame pops. `LE_outer` would be GC'd, but the returned function still holds a reference — so it stays on the heap.
4. Each `c()` pushes a new `LE_inner` with parent `LE_outer`. The `n++` expression looks up `n` via the scope chain, finds it in `LE_outer`, reads it (returns it), then writes back `n + 1` to the same slot.
5. `LE_inner` is popped after each call. `LE_outer` persists as long as `c` does.

</details>

---

## 10. Common confusion + traps

1. **"`return n++` vs `return ++n`" — off-by-one if you pick the wrong one.**
   Post-increment (`n++`) returns the current value *then* increments. Pre-increment (`++n`) increments first *then* returns. The problem requires the very first call to return `n` itself, so post-increment is correct. With `++n`, the first call would return `n + 1` — off by one.

2. **"The inner function freezes `n` at creation time." False.**
   The inner function captures the *binding*, not a snapshot. Every read goes through the live slot in the outer LE. That's why mutation works at all.

3. **"Two counters from `createCounter()` with the same `n` share state." False.**
   Each factory call creates a brand-new LE. Two separate LEs, two separate `n` slots. Independent vaults.

4. **Memory leak via long-lived closure.**
   The outer LE lives as long as the returned function is reachable. For a counter, that's a single number — tiny. But if you accidentally captured a 50 MB cache in the same LE, *that* would stay in memory too. Senior follow-up: closures pin everything in scope, not just the variables you mention by name in the body (engine-specific; modern V8 is smart enough to prune unused captures but don't rely on it).

5. **`this` is unused — don't introduce it.**
   The inner function doesn't reference `this`. Writing `this.n++` would either throw in strict mode (no `this`) or create a global property in sloppy mode. The whole point is to avoid `this` entirely.

6. **Re-declaring `n` inside the inner function — resets on every call.**
   ```js
   return function () { var n = 0; return n++; };  // BUG: always returns 0
   ```
   The inner `var n` shadows the outer; every call gets a fresh `n = 0`. Subtle, but fatal.

---

## 11. Senior follow-ups & variants

### Variant 1 — `createCounter(n, step)` (step argument)

```js
function createCounter(n, step = 1) {
  return function () { const out = n; n += step; return out; };
}
```

Same pattern, two slots in the LE. Note we can't use `n++` anymore since `step` may not be 1; we explicitly save the return value, then mutate.

### Variant 2 — Counter II: `{ inc, dec, reset }`

The interviewer extends the question. Now the factory returns an *object* with three methods, all closing over the same `n`:

```js
function createCounter(init) {
  let n = init;
  return {
    inc:   () => ++n,                 // returns the value AFTER increment
    dec:   () => --n,
    reset: () => { n = init; return n; },
  };
}
```

This is the **closure-based module pattern** — a single closure hosts multiple operations that share private state. Every JS library before ES6 used this. Pre-ES6 jQuery, Underscore, and Node's `module.exports` patterns all reduce to this shape.

### Variant 3 — Closure vs class `#field`

The interviewer asks: "rewrite this with a class using true privacy."

```js
class Counter {
  #n;
  constructor(n) { this.#n = n; }
  next() { return this.#n++; }
}
const c = new Counter(10);
c.next(); c.next();   // 10, 11
```

Tradeoffs to discuss aloud:

- **Closure**: lighter (no prototype overhead), predates `#` by 20 years, simpler to reason about for one-off factories, the methods are per-instance (more memory per counter).
- **Class `#`**: methods live on the prototype (one copy, less memory across many instances), supports inheritance, debuggable in DevTools (the `#n` field shows in the inspector under the special private-fields panel), uses `this`.

For a single counter, prefer closure (less ceremony). For "I'll have 100k counter instances" or "I want to extend Counter," prefer class.

### Variant 4 — Counter with `peek`

Return `{ next, peek }` where `peek` reads without incrementing. Sets up Counter II naturally.

```js
function createCounter(init) {
  let n = init;
  return { next: () => n++, peek: () => n };
}
```

---

## 12. How to think aloud in the interview

> "Right — `createCounter` takes a number and returns a function. The returned function, when called, should give back the current value and then increment for next time. The two-factory-calls case tells me each counter must be independent — so I can't use a global. The natural answer is a closure: outer holds `n`, inner returns and post-increments. Post-increment, not pre-increment, because the first call should return `n` itself. Two factory calls give two LEs, so they're independent automatically — I get that for free. Let me write it... [writes 3 lines]. Privacy: `n` is unreachable from outside the inner function, which is stronger than a public class field. If they ask for follow-ups, I'd reach for an object-of-methods to add `reset` and `peek` — same closure pattern, just exposing multiple operations."

---

## 13. 60-second revision

> - **Pattern:** `function outer(n) { return function () { return n++; }; }`
> - The outer call's lexical environment **persists on the heap** because the returned function holds a reference (`[[Environment]]`).
> - Each `createCounter()` call creates a **fresh** LE → independent counters automatically.
> - **Use post-increment** `n++` so the first call returns the initial value.
> - **Privacy:** `n` is unreachable externally. Stronger than `this.n`; equivalent to `#n`.
> - **Trap:** `++n` instead of `n++` is an off-by-one.
> - **Trap:** declaring `var n` inside the inner — resets on every call.
> - **Memory:** the closure pins whatever's in scope; keep an eye on inadvertently captured large objects.
> - **Family:** ID generators, `once(fn)`, `memoize`, debounce timerId, throttle lastCall, module pattern.

---

**Related:** [counter-ii.md](./counter-ii.md) · [create-incrementer.md](./create-incrementer.md) · [closure-vs-private-class-field-comparison.md](./closure-vs-private-class-field-comparison.md)

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md)
