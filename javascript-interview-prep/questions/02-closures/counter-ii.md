# Build a counter with `increment / decrement / reset` sharing private state

> **Difficulty:** Easy-Medium   |   **Time:** ~12 min   |   **Prereqs:** [counter.md](./counter.md), [`concepts/closures.md`](../../concepts/closures.md)
>
> **Source:** <a href="https://leetcode.com/problems/counter-ii/" target="_blank" rel="noopener noreferrer">LeetCode 2665 — Counter II</a>

---

## 1. Problem statement

**Signature**
```ts
function createCounter(init: number): {
  increment(): number;   // returns the value AFTER incrementing
  decrement(): number;   // returns the value AFTER decrementing
  reset(): number;       // resets to init and returns init
};
```

**Input / Output examples**

| Setup                       | Sequence of calls                                | Output sequence       |
|-----------------------------|---------------------------------------------------|-----------------------|
| `const c = createCounter(5)` | `increment(); increment(); decrement(); reset(); increment();` | `6, 7, 6, 5, 6`       |
| `const c = createCounter(0)` | `increment(); decrement(); reset();`              | `1, 0, 0`             |
| `const c = createCounter(10); const d = createCounter(10);` | `c.increment(); d.increment();` | `11, 11` (independent) |

**Constraints**
- `increment()` returns the value **after** the increment — first call after `createCounter(init)` returns `init + 1` (pre-increment, not post).
- `reset()` restores the counter to the **original `init`**, even after many mutations.
- All three methods share the *same* private number; mutation by one is visible to the others.
- Two factory calls produce **independent** counters.

---

## 2. Plain-English restatement

The interviewer wants a small object with three methods — `increment`, `decrement`, `reset` — that all secretly read and write the same private number. From the outside there's no way to inspect or assign that number directly; the only doors in are the three methods. Critically, `reset` must remember the *original* starting value, not the current one.

In ~8 lines, this problem extends the single-function `counter.md` pattern to the **object-of-methods** pattern. It's the smallest example of the "revealing module pattern" — the dominant pre-ES6 way of writing encapsulated modules in JavaScript, and still the cleanest way to expose a small API without classes.

---

## 3. Why this matters in interviews

This is the bridge from "single closure" to "object of methods sharing one private state." Interviewers use it to check whether you understand that *multiple* returned functions can share *one* lexical environment on the heap. The same shape underlies Event Emitter, Pub/Sub, LRU Cache, connection-pool handles, and session-stores. As a backend engineer, this is the pattern you reach for when you want a tiny state-holder without dragging in a class.

---

## 4. Mental model

Counter II is a **vault with three buttons**: an "up" button, a "down" button, and a "reset to factory default" button. All three buttons reach into the *same* internal counter; you, the holder of the vault, can only press the buttons — you can't open the vault directly.

```
   createCounter(5)
        │
        ├──► LE: { init: 5, n: 5 }   ← the vault
        │           ▲    ▲
        │           │    └── readable/writable by all 3 methods
        │           │
        │       remembered for reset()
        │
        └──► returns {
                increment: ▢──► reads/writes n
                decrement: ▢──► reads/writes n
                reset:     ▢──► restores n to init
              }
```

One LE on the heap, three function objects pointing at it. Mutations by one method are visible to the others because they're all reading the same slot.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. After `const c = createCounter(5); c.increment();`, what does the call return — `5` or `6`?
> 2. If you wrote `let n = 0;` inside each method instead of in the outer scope, what would `c.increment(); c.increment();` print?
> 3. After many mutations, does `reset()` go back to the *original* `init` or to `0`? What changes in your code to make either work?

---

## 6. Brute force — walked through

### Wrong attempt 1: `let n` inside each method

```js
function createCounter(init) {
  return {
    increment() { let n = init; return ++n; },   // returns init+1 every time
    decrement() { let n = init; return --n; },
    reset() { let n = init; return n; },
  };
}
```

Each method has its **own** `n`. They don't share state — every call starts from `init`. `c.increment(); c.increment();` returns `init+1` twice. Classic blunder under stress.

### Wrong attempt 2: forget to save `init`

```js
function createCounter(init) {
  return {
    increment() { return ++init; },
    decrement() { return --init; },
    reset() { return init = 0; },     // BUG: hardcoded 0, ignores original init
  };
}
```

Here `n` and `init` are the same variable. After mutations, `reset()` has no memory of where to go back to — and the hardcoded `0` is wrong for `createCounter(5)`. You need to **capture `init` separately** so `reset` has something to restore to.

### Wrong attempt 3: a class with public fields

```js
class Counter {
  constructor(init) { this.init = init; this.n = init; }
  increment() { return ++this.n; }
  // ...
}
```

Works mechanically. But `this.n` is publicly mutable (`c.n = 999`) and the prompt asks for a *function*, not a class. Closure version gives smaller surface area and true privacy.

---

## 7. The unlocking insight

> **One outer LE can be shared by many returned functions — each becomes a method on the public API, all reading and writing the same private slots.**

Inside `createCounter(init)`, we declare two slots: `init` (preserved for `reset`) and `n` (the live counter). We then return an object literal whose values are three function expressions. All three functions are *defined inside the same outer call*, so all three have `[[Environment]]` pointing at the **same** LE. When `increment()` mutates `n`, the next `decrement()` reads the mutated value because they share the slot, not a copy.

This is the **revealing module pattern**: outer function declares private state, returns an object whose methods are the public API. The pattern is also destructuring-safe — `const { increment } = createCounter(5);` still works, because `increment` doesn't depend on `this` to find its state; the state lives in the captured LE.

Two design choices fall out:

- **Pre-increment (`++n`) vs post-increment (`n++`).** The spec says the first `increment()` after `createCounter(init)` returns `init+1`. So pre-increment. (Counter I uses post-increment — re-read each spec carefully.)
- **Capture `init` separately.** Don't conflate `init` and `n`. Keep `init` immutable in the LE so `reset` can restore from it.

---

## 8. Solution (annotated)

```js
var createCounter = function (init) {           // step 1: outer holds two private slots
  let n = init;                                  // step 2: `n` is the live counter (mutable)
                                                  //         `init` stays as the original (immutable)
  return {                                       // step 3: return an object of three methods
    increment() { return ++n; },                  // step 4: pre-increment — bump THEN return
    decrement() { return --n; },                  // step 5: same pattern, the other direction
    reset()     { return (n = init); },           // step 6: restore n to original; assignment
                                                  //         expression returns the new value
  };
};
```

**Try it yourself**

```js
const c = createCounter(5);
console.log(c.increment());   // 6
console.log(c.increment());   // 7
console.log(c.decrement());   // 6
console.log(c.reset());       // 5
console.log(c.increment());   // 6

// Destructuring-safe (no `this` needed)
const { increment, reset } = createCounter(0);
console.log(increment());     // 1
console.log(increment());     // 2
console.log(reset());         // 0
```

---

## 9. Step-by-step dry run

Input:

```js
const c = createCounter(5);
c.increment(); c.increment(); c.decrement(); c.reset(); c.increment();
```

Values-first trace:

| Step | Method called   | `n` (before → after) | Returned |
|------|-----------------|----------------------|----------|
| init | `createCounter(5)` | LE = `{init: 5, n: 5}` | the methods object |
| 1    | `c.increment()` | `5 → 6`              | `6`      |
| 2    | `c.increment()` | `6 → 7`              | `7`      |
| 3    | `c.decrement()` | `7 → 6`              | `6`      |
| 4    | `c.reset()`     | `6 → 5`              | `5`      |
| 5    | `c.increment()` | `5 → 6`              | `6`      |

All three methods read and wrote the **same `n` slot** in the **same LE** on the heap. `init` was never touched after creation.

<details>
<summary><b>Engine internals (click to expand)</b></summary>

1. `createCounter(5)` is called. Engine creates `LE_outer = { init: 5, n: 5 }`.
2. The object literal `{ increment, decrement, reset }` is built. Each method is a function expression whose `[[Environment]] = LE_outer`.
3. The object is returned. The outer frame pops; `LE_outer` would be GC'd, but three function objects still reference it via `[[Environment]]`, so it stays on the heap.
4. Each method invocation creates its own `LE_inner` whose parent is `LE_outer`. Variable lookups for `n` and `init` walk one step up to `LE_outer`.
5. `LE_outer` is alive as long as any of the three returned methods are reachable.

</details>

---

## 10. Common confusion + traps

1. **Pre-increment vs post-increment — spec mismatch.**
   Counter II requires `++n` (pre-increment). Counter I requires `n++` (post-increment). Mixing them up is the most common silent bug. Re-read the spec each time.

2. **`reset` must restore the original `init`.**
   You need to capture `init` separately and never mutate it. Don't write `n = 0` in `reset` — the spec passes non-zero `init`. The expression `(n = init)` both assigns and returns the new value.

3. **All methods must share state.**
   The classic blunder: declaring `let n` *inside* each method instead of in the outer scope. Each method now has its own counter. Mutations don't propagate.

4. **No `this` needed.**
   The methods don't reference `this`. That's a *feature*: destructuring is safe (`const { increment } = createCounter(5); increment();` works). With `this.n`, the same destructure breaks because `this` is now undefined at the call site.

5. **Memory pinning.**
   The returned object retains the LE. Stashing the object in a long-lived global (e.g., module scope) keeps the closure — and anything it captures — alive forever. For a counter holding two numbers that's fine; for one closing over a 50 MB blob it isn't.

6. **Exposing `n` via a getter.**
   Adding a `get n()` accessor defeats the privacy promise. If callers need a peek, expose `peek()` explicitly — see Variant 1.

---

## 11. Senior follow-ups & variants

### Variant 1 — Add `peek()` (read without mutation)

A common follow-up: "let callers see the current value without changing it."

```js
function createCounter(init) {
  let n = init;
  return {
    increment() { return ++n; },
    decrement() { return --n; },
    reset()     { return (n = init); },
    peek()      { return n; },   // read-only access; no mutation
  };
}
```

This formalizes the privacy contract — the only ways in are the methods you choose to expose.

### Variant 2 — Bounded counter

`createCounter(init, { min, max })` — clamp or throw on out-of-range. Tests whether you can layer validation without breaking the encapsulation.

```js
function createCounter(init, { min = -Infinity, max = Infinity } = {}) {
  let n = init;
  const guard = (v) => Math.min(max, Math.max(min, v));
  return {
    increment() { return n = guard(n + 1); },
    decrement() { return n = guard(n - 1); },
    reset()     { return (n = init); },
  };
}
```

### Variant 3 — Event-driven counter

Every mutation fires a callback. Mash this with Event Emitter — the closure now captures both `n` and a `listeners` array.

```js
function createCounter(init) {
  let n = init;
  const listeners = [];
  const emit = (kind) => listeners.forEach((l) => l({ kind, value: n }));
  return {
    increment() { ++n; emit('inc'); return n; },
    decrement() { --n; emit('dec'); return n; },
    reset()     { n = init; emit('reset'); return n; },
    subscribe(fn) { listeners.push(fn); return () => listeners.splice(listeners.indexOf(fn), 1); },
  };
}
```

### Variant 4 — Class equivalent with `#private`

The interviewer says: "now rewrite with a class using true privacy."

```js
class Counter {
  #init; #n;
  constructor(init) { this.#init = init; this.#n = init; }
  increment() { return ++this.#n; }
  decrement() { return --this.#n; }
  reset()     { return (this.#n = this.#init); }
}
```

Discuss aloud:
- **Closure version**: per-instance methods (more memory across many counters), but destructuring-safe and no `this`.
- **Class version**: methods on the prototype (one copy, lower memory at scale), supports `extends`, but `this`-bound — destructuring breaks unless you `bind` first.
- For a one-off counter, prefer closure (less ceremony). For "I'll have 100k counter instances" or "subclassable counter," prefer class.

---

## 12. How to think aloud in the interview

> "I need three methods that share private state. The natural shape is an outer function declaring `let n = init` (plus keep `init` separately for `reset`), and returning an object with three method shorthands. All three close over the same LE, so they share `n` automatically. Pre-increment, not post — first `increment()` after `createCounter(5)` should return `6`. `reset()` does `n = init`; the assignment expression returns the assigned value, which is what we want. I'll skip `this` entirely — that makes the methods destructuring-safe. For follow-ups: peek (read-only), bounded (validation), event-driven (subscribe + emit). The pattern is the revealing module — same shape as Event Emitter, LRU, Pub/Sub."

---

## 13. 60-second revision

> - **Pattern:** outer captures `init` + `let n = init`; returns `{ increment, decrement, reset }`.
> - All three methods have `[[Environment]] = outer LE` — they share the **same** `n` slot.
> - **Pre**-increment `++n` for Counter II. (Post-increment `n++` for Counter I — easy to mix up.)
> - **`reset` needs the original `init`** — capture it explicitly; never overwrite it.
> - **No `this`** — destructuring methods off the returned object remains safe.
> - **Trap:** declaring `let n` inside each method → each has its own counter.
> - **Trap:** writing `n = 0` in reset instead of `n = init`.
> - **Family:** revealing module pattern → Event Emitter, Pub/Sub, LRU Cache, To-Be-Or-Not-To-Be.

---

**Related:** [counter.md](./counter.md) · [to-be-or-not-to-be.md](./to-be-or-not-to-be.md) · [closure-as-state-machine.md](./closure-as-state-machine.md) · [closure-vs-private-class-field-comparison.md](./closure-vs-private-class-field-comparison.md)

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md)
