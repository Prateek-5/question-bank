# Encapsulate private state via closures — `createCounter` with hard privacy

> **Difficulty:** Medium   |   **Time:** ~15 min   |   **Prereqs:** [counter-ii.md](./counter-ii.md), [`concepts/closures.md`](../../concepts/closures.md)
>
> **Source:** <a href="https://codedamn.com/news/nodejs/encapsulating-private-data-closures" target="_blank" rel="noopener noreferrer">Codedamn — Encapsulating Private Data with Closures</a>

---

## 1. Problem statement

**Signature**
```ts
function createCounter(): {
  increment(): void;
  decrement(): void;
  getValue(): number;
  reset(): void;
};
```

**Input / Output examples**

| Code                                       | Behaviour                                      |
|--------------------------------------------|------------------------------------------------|
| `const c = createCounter(); c.increment(); c.getValue()` | `1`                                  |
| `c.count`                                  | `undefined` (no public property)              |
| `Object.keys(c)`                           | `['increment', 'decrement', 'getValue', 'reset']` |
| `JSON.stringify(c)`                        | `"{}"` (methods skipped, count invisible)      |
| `const a = createCounter(); const b = createCounter();` | independent state per instance      |
| `const { increment } = c; increment();`    | works — no `this` needed                       |

**Constraints**
- The internal counter must be **unreachable** from outside the returned methods. No `c.count`, no reflective access.
- Each `createCounter()` call must produce an independent instance.
- Methods must be destructure-safe — no `this` dependency.

---

## 2. Plain-English restatement

Build a counter as a *closure-based handle*. The factory returns an object with a few methods, but the underlying number lives inside the factory's lexical scope — not as a property on the returned object, not on the prototype, not anywhere reachable from outside. The only doors in are the methods you expose.

This is the conceptual sibling of `counter-ii.md` framed as an **encapsulation/OOP discussion** rather than a coding puzzle. The interviewer wants to hear you explain *why* this gives you true privacy and *how* it compares to class `#fields`.

---

## 3. Why this matters in interviews

Senior backend interviewers ask this to check whether you understand **why** closures matter at the architecture level: how do you build a stateful object whose internals are *genuinely unreachable* from outside? Pre-ES2022, this was the only way to get private fields. Even today in Node codebases, you'll see closure-based modules for: connection-pool handles, rate-limiter state, session stores, cache layers, plugin sandboxes. Knowing when to reach for a closure vs a class vs a `#field` signals seniority.

---

## 4. Mental model

A **handle** for a sealed jar of marbles. The jar is locked inside a factory; only the handle's buttons can `add a marble`, `remove a marble`, or `count the marbles`. There's no key to the jar itself — no way to peek directly, no way to swap the jar.

```
   createCounter()
        │
        ├── sealed jar:  ┌──────────┐
        │                │ count: 0 │   ← inside the factory's LE; unreachable externally
        │                └──────────┘
        │                     ▲
        │                     │ read/write through closure
        │                ┌──────────────────────────────┐
        └── returns ───▶ │  { increment, decrement,     │
                         │    getValue, reset }          │   ← handle (the only API)
                         └──────────────────────────────┘
   
   c.count;                    → undefined (no property)
   Object.keys(c);             → method names only
   Reflect.ownKeys(c);         → method names only (no count)
   Object.getOwnPropertyNames; → no count
   JSON.stringify(c);          → "{}"  methods skipped, count invisible
```

The closure pins `count` for the lifetime of the handle. Two handles from two factory calls have **two independent LEs** — completely separate jars.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. After `const c = createCounter(); c.increment(); c.count = 999; c.getValue()` — does `getValue` return `1` or `999`? Why?
> 2. If you do `const { increment } = createCounter(); increment();` — does it work? Why doesn't it lose `this` like a class method would?
> 3. What's the memory cost per instance? More or less than a class with the same methods?

---

## 6. Brute force — walked through

### Wrong attempt 1: public property

```js
function createCounter() {
  const obj = { count: 0 };
  obj.increment = () => obj.count++;
  return obj;
}
const c = createCounter();
c.count = 999;       // mutated from outside — privacy gone
c.increment();
c.count;             // 1000
```

`count` is now a public property. Anyone can read or write it. Fails the privacy contract.

### Wrong attempt 2: leading-underscore convention

```js
function createCounter() {
  const obj = { _count: 0 };
  obj.increment = () => obj._count++;
  return obj;
}
```

Convention, not enforcement. `_count` is still readable and writable. Senior interviewers count this as "soft privacy" — useless in adversarial contexts.

### Wrong attempt 3: state inside the method body

```js
function createCounter() {
  return {
    increment() { let count = 0; count++; },   // BUG: fresh count every call
    getValue()  { let count = 0; return count; },
  };
}
```

Each method has its own local `count`. They don't share. Every call resets. The state must live in the **factory** scope, not the method bodies.

### Wrong attempt 4: store on `this` with `class`

```js
class Counter {
  constructor() { this.count = 0; }
  increment() { this.count++; }
}
const c = new Counter();
c.count = 999;       // public; mutable
```

Mechanically works. But `count` is publicly accessible, and methods now require `this` (so destructuring `const { increment } = c; increment();` throws). The closure version sidesteps both.

---

## 7. The unlocking insight

> **A variable declared inside a function and read/written only by methods returned from that function is invisible to every form of external reflection — no property access, no enumeration, no Reflect API, no prototype walk. It's as private as it gets in JavaScript before ES2022.**

When `createCounter()` runs, the engine creates an LE holding `count = 0`. The returned object's methods all carry `[[Environment]]` pointing at this LE. The variable name `count` exists *only* as a binding inside that LE — there's no entry on the returned object, no symbol-table introspection that exposes it, no `for...in` loop that names it.

Three properties make this useful:

1. **Hard privacy.** As strong as ES2022 `#fields`. Stronger than `Symbol` keys (which `Reflect.ownKeys` exposes). Stronger than `_count` convention (which is just naming).
2. **No `this`.** Methods reference `count` through the scope chain, not through a receiver. So destructuring is safe: `const { increment } = createCounter(); increment();` works.
3. **Per-instance isolation.** Each `createCounter()` call creates a fresh LE — two handles share nothing.

**Trade-offs vs class `#fields`:**

| Aspect | Closure | `class { #field }` | `class { _field }` |
|---|---|---|---|
| Privacy | Hard (no reflective access) | Hard (no reflective access) | Soft (convention) |
| Available since | Always | ES2022 | Always |
| Memory per instance | LE + N function objects | shared prototype + per-instance slot | shared prototype + per-instance slot |
| `this` semantics | Not used | Standard | Standard |
| Destructure-safe | Yes | No (loses `this`) | No |
| `instanceof` checks | No | Yes | Yes |
| Inheritance | Awkward | Standard `extends` | Standard `extends` |

Pick closure for: small handle-style objects, destructure-safe methods, pre-2022 compatibility.
Pick `#field` for: hierarchies, `instanceof` checks, many instances (shared prototype methods = less memory).

---

## 8. Solution (annotated)

```js
function createCounter() {            // step 1: factory call creates a fresh LE
  let count = 0;                       // step 2: private state — lives in factory's LE

  return {                             // step 3: return public API only
    increment() { count += 1; },        // step 4: methods close over `count` via scope chain
    decrement() { count -= 1; },        //         (no `this` involved)
    getValue()  { return count; },
    reset()     { count = 0; },
  };
}
```

**Try it yourself**

```js
const c = createCounter();
c.increment();
c.increment();
c.increment();
console.log(c.getValue());    // 3
c.decrement();
console.log(c.getValue());    // 2
c.reset();
console.log(c.getValue());    // 0

// Privacy proof
console.log(c.count);                       // undefined
console.log(Object.keys(c));                // ['increment','decrement','getValue','reset']
console.log(Object.getOwnPropertyNames(c)); // same
console.log(JSON.stringify(c));             // "{}"
c.count = 999;                              // assignment to a non-existent prop; ignored
console.log(c.getValue());                  // 0  (still 0; assignment didn't reach the closure)

// Destructure-safe — no `this`
const { increment, getValue } = createCounter();
increment(); increment();
console.log(getValue());                    // 2

// Per-instance isolation
const a = createCounter();
const b = createCounter();
a.increment(); a.increment();
b.increment();
console.log(a.getValue(), b.getValue());    // 2  1
```

---

## 9. Step-by-step dry run

Input:

```js
const a = createCounter();
const b = createCounter();
a.increment();
a.increment();
b.increment();
console.log(a.getValue(), b.getValue());
```

Values-first trace:

| Step | Action          | `LE_A.count` | `LE_B.count` | Returns        |
|------|-----------------|--------------|---------------|----------------|
| init | `createCounter()` × 2 | `0`     | `0`           | two handles    |
| 1    | `a.increment()` | `0 → 1`      | `0`           | (undefined)    |
| 2    | `a.increment()` | `1 → 2`      | `0`           | (undefined)    |
| 3    | `b.increment()` | `2`          | `0 → 1`       | (undefined)    |
| 4    | `a.getValue()`  | `2`          | `1`           | `2`            |
|      | `b.getValue()`  | `2`          | `1`           | `1`            |

Two LEs on the heap, two `count` slots, no cross-contamination.

<details>
<summary><b>Engine internals (click to expand)</b></summary>

Each `createCounter()` call creates an LE record holding `count`. The four method functions are *fresh* function objects per call — each carries `[[Environment]]` pointing at its own LE.

This is a memory cost vs class: with a class, methods live on the prototype (one copy shared). With closures, methods are per-instance. For 100k counters, the closure version allocates 400k function objects vs the class version's 4 (on the prototype). Usually negligible at small N; can matter at scale.

</details>

---

## 10. Common confusion + traps

1. **Declaring state as a property of the returned object.**
   ```js
   return { count: 0, increment() { ... } };
   ```
   `count` is now public. Fails privacy.

2. **Declaring state inside a method body.**
   Each method gets its own `count`. Mutations don't share.

3. **Using leading-underscore convention.**
   `_count` is readable and writable. Soft privacy = no privacy.

4. **Adding a setter on `value` "for convenience."**
   ```js
   set value(v) { count = v; }
   ```
   You've just leaked the private slot. If you want external write, add an explicit method (e.g., `setValue(v)`) — even then, consider whether you really need it.

5. **`JSON.stringify` returns `"{}"`.**
   Methods are skipped by `JSON.stringify`; `count` is invisible. If serialization matters, add a `toJSON()` method that returns a plain snapshot.

6. **Memory pinning by accident.**
   ```js
   function createCounter() {
     const huge = new Array(1e7);    // unused but captured
     let count = 0;
     return { increment() { count++; } };
   }
   ```
   `huge` is retained alongside `count` because the closure pins everything in scope (V8 sometimes prunes via escape analysis but not reliably). Keep factory scopes lean.

7. **`instanceof` doesn't work.**
   Closures aren't constructors. If callers need `instanceof Counter`, you need a class (or a tag-on-the-object workaround).

8. **Hot-path performance at scale.**
   For 1M counters, the per-instance method allocation adds up. Class with shared prototype methods wins. For ≤1000 instances, no measurable difference.

---

## 11. Senior follow-ups & variants

### Variant 1 — Add subscriptions (observable counter)

```js
function createCounter() {
  let count = 0;
  const listeners = new Set();
  function emit() { for (const l of listeners) l(count); }
  return {
    increment() { count++; emit(); },
    decrement() { count--; emit(); },
    reset()     { count = 0; emit(); },
    getValue()  { return count; },
    subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn); },
  };
}
```

Same closure pattern, larger scope (count + listeners). The skeleton scales to Pub/Sub, Event Emitter, observable stores.

### Variant 2 — Rewrite with `class { #count }`

```js
class Counter {
  #count = 0;
  increment() { this.#count++; }
  decrement() { this.#count--; }
  getValue()  { return this.#count; }
  reset()     { this.#count = 0; }
}
```

Discuss aloud:
- **Privacy** is identical.
- **Memory**: class shares methods on the prototype — wins at scale.
- **Destructuring** breaks for the class (`const { increment } = new Counter(); increment();` throws).
- **`instanceof`** works for the class, not the closure.
- **Inheritance** is straightforward with class, awkward with closures.

### Variant 3 — `WeakMap`-keyed privacy for class-like patterns

A middle-ground for environments where `#fields` aren't available but you want class ergonomics:

```js
const _state = new WeakMap();
class Counter {
  constructor() { _state.set(this, { count: 0 }); }
  increment() { _state.get(this).count++; }
  getValue()  { return _state.get(this).count; }
}
```

`_state` is module-scoped. Outside the module, no one can fish entries out (you'd need a reference to `_state` itself). Plus methods are on the prototype, so memory is class-like.

### Variant 4 — Augmenting with `Object.freeze`

```js
function createCounter() {
  let count = 0;
  const api = Object.freeze({
    increment() { count++; },
    getValue() { return count; },
  });
  return api;
}
```

`Object.freeze(api)` prevents external code from monkey-patching the returned object (`c.increment = () => {}`). The closure already protects `count`; freezing protects the API surface.

---

## 12. How to think aloud in the interview

> "True privacy in JS comes from one of three things: closures, `#private` class fields (ES2022), or `WeakMap`-keyed state (the pre-2022 class alternative). For a small handle, closures are the simplest — declare `let count` in the factory, return methods that close over it. State is unreachable: no `c.count`, no `Object.keys(c).count`, no reflection. As a bonus, no `this` is needed, so destructuring is safe. Trade-offs vs class `#fields`: closures cost per-instance method allocation (vs prototype-shared); class `#` supports `instanceof` and inheritance more naturally. I'd pick closure for: lightweight handles, destructure-safe APIs, plugin sandboxes. Class for: hierarchies, many instances, anything where `instanceof` matters."

---

## 13. 60-second revision

> - **Pattern:** outer declares `let state`; returns object of methods that close over it.
> - **Privacy** is reflection-proof: no property, no enumeration, no Reflect access. Equivalent to `#fields`.
> - **No `this`** — destructuring is safe.
> - **Per-instance**: each factory call creates a fresh LE — handles share nothing.
> - **vs `class { #x }`**: privacy identical; closures are destructure-safe; classes are `instanceof`-able and inheritance-friendly.
> - **vs `_count`**: convention only — not privacy.
> - **Memory:** closures pin everything in scope; keep factory bodies lean.
> - **Trap:** state as a property of the returned object; state inside a method body; setter on the value.
> - **Family:** Counter II, Event Emitter, LRU Cache, plugin sandboxes — all revealing-module pattern.

---

**Related:** [counter-ii.md](./counter-ii.md) · [module-pattern-iife.md](./module-pattern-iife.md) · [closure-vs-private-class-field-comparison.md](./closure-vs-private-class-field-comparison.md) · [factory-with-injected-deps.md](./factory-with-injected-deps.md)

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md)
