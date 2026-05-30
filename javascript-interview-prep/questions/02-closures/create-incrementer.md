# Build an incrementer factory that returns a new sequence value on each call

> **Difficulty:** Easy   |   **Time:** ~5 min   |   **Prereqs:** [counter.md](./counter.md), [`concepts/closures.md`](../../concepts/closures.md)
>
> **Source:** BFE.dev #18 "Counter"; variant of <a href="https://leetcode.com/problems/counter/" target="_blank" rel="noopener noreferrer">LeetCode 2620 — Counter</a>

---

## 1. Problem statement

**Signature**
```ts
function createIncrement(by?: number, start?: number): () => number;
```

**Input / Output examples**

| Setup                           | Sequence of calls          | Output sequence |
|---------------------------------|----------------------------|-----------------|
| `const inc = createIncrement(2)` | `inc(); inc(); inc();`     | `2, 4, 6`       |
| `const inc = createIncrement()`  | `inc(); inc();`            | `1, 2`          |
| `const tick = createIncrement(2, 100)` | `tick(); tick();`     | `102, 104`      |
| `const a = createIncrement(1); const b = createIncrement(10);` | `a(); a(); b(); a();` | `1, 2, 10, 3` (independent) |

**Constraints**
- The returned function takes no arguments and returns the *new* (post-increment) value.
- `by` defaults to 1, `start` defaults to 0 (so the first call returns `by` itself).
- Two factory calls produce **independent** counters with their own private state.

---

## 2. Plain-English restatement

Write a function `createIncrement(by, start)` that returns *another* function. That returned function has a hidden counter inside it. Each time you call the returned function, it bumps the counter by `by` and gives you the new value. Two separate factory calls must produce two independent counters — calling one doesn't affect the other.

This is essentially `counter.md` with a configurable step. The pedagogical purpose is to lock in the factory-closure shape — the smallest reusable building block for ID generators, sequence numbers, retry counters, and rate-limiter tickets.

---

## 3. Why this matters in interviews

`createIncrement` is the **simplest possible factory closure**. Senior interviewers ask it as a 5-minute warmup and then immediately layer follow-ups: "now support `reset()`," "now make `by` per-call," "now expose the current value without mutating." Each follow-up tests whether you really understand how a closure partitions state. Backend uses are everywhere: log-sequence counters, request-ID generators, per-tenant counters, deterministic test fixtures.

---

## 4. Mental model

Picture a **vending machine** with a sticky-note counter on the side. The factory `createIncrement(2)` builds a fresh machine and sticks a `0` on it. Every time you press the button (call the returned function), the machine adds `2` to the sticker, then hands you back the new number. You can't reach inside the machine to change the sticker; you can only press the button. If you order a *second* machine from the factory, it has its own sticker — pressing one machine's button does not bump the other's.

```
   createIncrement(2)
        │
        ├── new "machine":  ┌──────────┐
        │                   │ count: 0 │   ← sticker (private slot)
        │                   │ by: 2    │   ← configured at factory time
        │                   └──────────┘
        │                         ▲
        │                         │ reads + writes via closure
        │                   ┌──────────────┐
        └── returns ──────▶ │  () => …     │   ← the button
                            └──────────────┘

   inc(); inc(); inc();
   ↓      ↓      ↓
   2      4      6   (each press: count += by, then return count)
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. After `const inc = createIncrement(); inc(); inc();`, what does each call return?
> 2. If you call `createIncrement(2)` twice and call each result once, what do you get back from each? Do they share state?
> 3. Should the increment happen *before* returning or *after*? Hint: the first call after `createIncrement(2)` should return `2`, not `0`.

---

## 6. Brute force — walked through

### Wrong attempt 1: a global counter

```js
let count = 0;
function createIncrement(by = 1) {
  return function () { count += by; return count; };
}
```

What's wrong? Two callers of `createIncrement()` share the same `count`. Two factory calls leak into each other — fails the independence requirement. Reject.

### Wrong attempt 2: `let count` inside the returned function

```js
function createIncrement(by = 1) {
  return function () {
    let count = 0;        // BUG: fresh `count` every call
    count += by;
    return count;
  };
}
```

The inner `let count = 0` resets on every invocation. `inc(); inc(); inc();` returns `by, by, by` — the counter never advances. Classic blunder under stress.

### Wrong attempt 3: stash on the returned function as a property

```js
function createIncrement(by = 1) {
  const fn = function () { fn.count += by; return fn.count; };
  fn.count = 0;
  return fn;
}
```

Works, but exposes mutable state externally: anyone can write `inc.count = 999`. Closure version gives true privacy.

---

## 7. The unlocking insight

> **The mutable counter slot must live in the factory's scope, not the inner function's body. That's what makes it survive across calls and stay private from the outside.**

When you call `createIncrement(by, start)`, the engine creates a fresh LE holding three slots: `by`, `start`, and `count` (initialized to `start`). The inner function is defined inside that LE, so its `[[Environment]]` points there. Every call to the returned function reads `count` and `by` through the closure, mutates `count` in place, and returns the new value. The slot survives because the returned function still references its LE.

The same insight powers the "decorated function" pattern: if you want to add helper methods like `.reset()` and `.value()` to the returned function, you define them in the *same* factory scope. They all close over the same LE, so they all see the same `count`. This is the same mechanism `counter-ii.md` uses for object-of-methods — just attached to a function instead of an object.

---

## 8. Solution (annotated)

```js
function createIncrement(by = 1, start = 0) {     // step 1: factory takes step + starting value
  let count = start;                                // step 2: private slot lives in factory LE

  function inc() {                                  // step 3: the button (the returned function)
    count += by;                                    //         bump count by `by`
    return count;                                   //         return the new value
  }

  inc.reset = () => { count = start; };             // step 4: decorate with `.reset()` — shares closure
  inc.value = () => count;                          // step 5: decorate with `.value()` — read-only peek

  return inc;                                       // step 6: hand out the button
}
```

**Try it yourself**

```js
const a = createIncrement(1);
const b = createIncrement(10);
console.log(a(), a(), a());   // 1 2 3
console.log(b(), b());         // 10 20
console.log(a.value());        // 3  (a is independent of b)

a.reset();
console.log(a());              // 1  (back to start)

const tick = createIncrement(2, 100);
console.log(tick(), tick());   // 102 104
```

---

## 9. Step-by-step dry run

Input:

```js
const tick = createIncrement(2, 100);
tick(); tick(); tick.reset(); tick();
```

Values-first trace:

| Step | Action          | LE state                          | Returned   |
|------|-----------------|------------------------------------|------------|
| init | `createIncrement(2, 100)` | `{by: 2, start: 100, count: 100}` | the `inc` function |
| 1    | `tick()`        | `count: 100 → 102`                | `102`      |
| 2    | `tick()`        | `count: 102 → 104`                | `104`      |
| 3    | `tick.reset()`  | `count: 104 → 100`                | `undefined` |
| 4    | `tick()`        | `count: 100 → 102`                | `102`      |

<details>
<summary><b>Engine internals (click to expand)</b></summary>

1. `createIncrement(2, 100)` creates `LE_outer = { by: 2, start: 100, count: 100 }`.
2. The `inc` function is defined; its `[[Environment]] = LE_outer`. So are the arrow functions `inc.reset` and `inc.value` — all three share the same LE.
3. `inc` (with its attached methods) is returned. Outer frame pops; `LE_outer` survives on the heap because `tick` references it (and so do `tick.reset` and `tick.value`).
4. Each invocation reads/writes `count` through `[[Environment]]` → `LE_outer`. Mutations persist between calls because they're all touching the same slot.
5. A separate `createIncrement(10)` would create *its own* `LE_outer'`, completely independent — that's the factory isolation guarantee.

</details>

---

## 10. Common confusion + traps

1. **Declaring `let count` inside the inner function — resets every call.**
   The slot has to live in the **factory** scope. Inside the inner, every call starts from `0` again.

2. **Forgetting to capture `start` separately if you want `reset()`.**
   If you reuse `count` and don't preserve `start`, your reset has nothing to restore to. Keep both.

3. **Negative or zero `by` — should work.**
   `createIncrement(-1)` is a decrementer. `createIncrement(0)` returns `0` (or `start`) forever. Don't add unrequested validation.

4. **Float `by` accumulates IEEE-754 error.**
   `createIncrement(0.1)` after 10 calls yields `0.9999999999999999`. Mention if asked about decimals; the fix is integer math or `Number.EPSILON` tolerance.

5. **Concurrent callers — single-threaded JS is safe.**
   The closure-bump-and-return is one synchronous operation; no race. Inside a Worker thread sharing a `SharedArrayBuffer`, you'd need `Atomics.add`.

6. **Attaching methods exposes them but not the slot.**
   `inc.reset()` works, but `inc.count` is `undefined` — there's no property by that name. The slot is in the closure, not on the function object. That's the privacy guarantee.

---

## 11. Senior follow-ups & variants

### Variant 1 — Step overridable per call

The interviewer asks: "let callers pass a step to override the default."

```js
function createIncrement(defaultBy = 1, start = 0) {
  let count = start;
  return function (by = defaultBy) {
    count += by;
    return count;
  };
}
const inc = createIncrement(1);
inc();       // 1
inc(5);      // 6  (one-off override)
inc();       // 7  (back to default)
```

### Variant 2 — Capped / cycling incrementer

`createIncrement(1, 0, { max: 10, onOverflow: 'throw' | 'cycle' | 'clamp' })`.

```js
function createIncrement(by = 1, start = 0, { max = Infinity, onOverflow = 'throw' } = {}) {
  let count = start;
  return function () {
    count += by;
    if (count > max) {
      if (onOverflow === 'throw') throw new RangeError(`count exceeded ${max}`);
      if (onOverflow === 'cycle') count = start + (count - max - 1);
      if (onOverflow === 'clamp') count = max;
    }
    return count;
  };
}
```

### Variant 3 — `{ increment, decrement, reset, value }` object form

This is the bridge to `counter-ii.md` — same factory scope, expose multiple operations.

```js
function createCounter(init) {
  let n = init;
  return {
    increment() { return ++n; },
    decrement() { return --n; },
    reset() { return (n = init); },
    value() { return n; },
  };
}
```

### Variant 4 — Atomic for SharedArrayBuffer

For worker-shared counters, swap the local variable for an `Int32Array` view over a `SharedArrayBuffer`:

```js
function createSharedIncrement(sab, slot, by = 1) {
  const view = new Int32Array(sab);
  return function () { return Atomics.add(view, slot, by) + by; };
}
```

`Atomics.add` returns the *old* value, so we add `by` again to return the new value. Senior bonus — mention only if asked.

---

## 12. How to think aloud in the interview

> "Factory closure: outer holds `count`, inner does `count += by; return count`. Two factory calls give two independent LEs, so they don't share state — that's the whole point. Slot must live in the outer scope; declaring it inside the inner resets every call. If they ask for `reset()`, I attach a method on the returned function — same closure, same slot. If they want `value()` for read-only access, same trick. For per-call step override, the inner takes an optional parameter that defaults to the factory-time `by`. For shared-memory counters across workers, swap to `Atomics.add` over a typed-array view of `SharedArrayBuffer`."

---

## 13. 60-second revision

> - **Pattern:** `function createIncrement(by, start) { let count = start; return () => (count += by, count); }`
> - The slot **must** live in the factory scope, not in the inner function body.
> - Each `createIncrement()` call = a fresh LE = independent counter.
> - **Trap:** declaring `let count` inside the inner — resets every call.
> - **Decorated-function pattern:** attach `.reset()` and `.value()` to the returned function; they share the closure.
> - **Family:** `once`, `counter-ii`, debounce/throttle, ID generators, retry counters.
> - For shared-memory across workers: `Atomics.add` on a typed-array view of `SharedArrayBuffer`.

---

**Related:** [counter.md](./counter.md) · [counter-ii.md](./counter-ii.md) · [once-with-cached-return.md](./once-with-cached-return.md) · [allow-one-function-call.md](./allow-one-function-call.md)

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md)
