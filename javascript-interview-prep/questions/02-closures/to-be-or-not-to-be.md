# Build a tiny `expect(val)` assertion API — `.toBe / .notToBe`

> **Difficulty:** Easy   |   **Time:** ~10 min   |   **Prereqs:** [counter-ii.md](./counter-ii.md), [`concepts/closures.md`](../../concepts/closures.md)
>
> **Source:** <a href="https://leetcode.com/problems/to-be-or-not-to-be/" target="_blank" rel="noopener noreferrer">LeetCode 2704 — To Be Or Not To Be</a>

---

## 1. Problem statement

**Signature**
```ts
function expect(val: unknown): {
  toBe(other: unknown): true;     // throws "Not Equal" if val !== other
  notToBe(other: unknown): true;  // throws "Equal" if val === other
};
```

**Input / Output examples**

| Call                                       | Behaviour                                     |
|--------------------------------------------|------------------------------------------------|
| `expect(5).toBe(5)`                        | returns `true`                                |
| `expect(5).toBe(6)`                        | throws `"Not Equal"`                          |
| `expect(5).notToBe(6)`                     | returns `true`                                |
| `expect(5).notToBe(5)`                     | throws `"Equal"`                              |
| `expect(NaN).toBe(NaN)`                    | throws `"Not Equal"` (`NaN !== NaN` under `===`) |
| `expect({a:1}).toBe({a:1})`                | throws `"Not Equal"` (different references)   |

**Constraints**
- Use **strict equality** (`===`).
- Throw the bare string `"Not Equal"` / `"Equal"`, not an `Error` object (LeetCode harness expects this).
- Return `true` on success.
- Methods share the captured `val` via closure (no `this`).

---

## 2. Plain-English restatement

Write a function `expect(val)` that returns a tiny object with two methods, `toBe` and `notToBe`. Each method takes a second value and compares it strictly to the originally captured `val`. On match-failure for `toBe` (or match-success for `notToBe`) it throws a string; otherwise it returns `true`.

In 12 lines, you're building the closure-based skeleton of every fluent assertion library — Jest's `expect`, Jasmine's matchers, Chai's `chai(...)`. The pattern: capture context in a closure, return an object whose methods all share that context.

---

## 3. Why this matters in interviews

This looks trivial — write `expect(5).toBe(5)` — but in under 15 lines it forces three demonstrations: closing over a value, returning an object of methods that share that value, and choosing between throwing vs returning errors. As a backend engineer, this is the same skeleton you'd reach for to build a query builder (Knex), HTTP request builder (supertest), or config DSL. Capture context in closure → expose chainable methods → propagate context.

---

## 4. Mental model

`expect(val)` opens a **briefcase** containing `val`. The two methods are keys — both can open the briefcase and read `val`, but neither lets you change it or see it from outside. Each method just compares its argument to whatever's inside.

```
   expect(5)
        │
        ├── briefcase:  ┌──────────┐
        │               │  val: 5  │   ← captured at expect-call time
        │               └──────────┘
        │                    ▲
        │                    │ both methods read this slot via closure
        │              ┌────────────────────┐
        └── returns ──▶│  {                 │
                       │    toBe(other)…    │
                       │    notToBe(other)… │
                       │  }                 │
                       └────────────────────┘
```

One LE on the heap, two function objects pointing at it, no `this` involved.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Does `expect(NaN).toBe(NaN)` return `true` or throw? Why?
> 2. Should you throw `"Not Equal"` (a string) or `new Error("Not Equal")`? What does the LeetCode harness expect?
> 3. Will `const { toBe } = expect(5); toBe(5);` work without binding? Why does the closure-based version not need `this`?

---

## 6. Brute force — walked through

### Wrong attempt 1: a class

```js
class Expect {
  constructor(val) { this.val = val; }
  toBe(other) { if (this.val !== other) throw "Not Equal"; return true; }
  notToBe(other) { if (this.val === other) throw "Equal"; return true; }
}
const expect = (v) => new Expect(v);
```

Works mechanically — but the prompt says `expect(...)` should *return* an object, not require `new`. Also `this.val` is publicly mutable (`e.val = 999`), defeating the captured-context idea. And destructuring breaks: `const { toBe } = expect(5); toBe(5)` → `TypeError: Cannot read 'val' of undefined`.

### Wrong attempt 2: `==` instead of `===`

```js
function expect(val) {
  return {
    toBe(other) { if (val != other) throw "Not Equal"; return true; },
    notToBe(other) { if (val == other) throw "Equal"; return true; },
  };
}
```

Spec violation. `expect(0).toBe(false)` would pass under `==`, fail under `===`. LeetCode's harness uses strict equality.

### Wrong attempt 3: throw an `Error` object

```js
toBe(other) { if (val !== other) throw new Error("Not Equal"); return true; }
```

Production-correct (gives a stack trace), but the LeetCode test harness checks `catch (e) → e === "Not Equal"`. With `new Error(...)`, `e` is an Error object — the string comparison fails. Match the spec verbatim on LeetCode; prefer `Error` in real code.

---

## 7. The unlocking insight

> **A closure-captured value plus an object of methods is the smallest fluent-API skeleton in JavaScript.**

`expect(val)` creates a fresh LE holding `val`. Returning an object whose methods are function expressions defined inside that LE means **every method has `[[Environment]]` pointing at the same LE** — they all read the same `val` slot through the scope chain. There's no `this`, no field exposure, no class machinery. Just one captured slot shared by two methods.

Three properties fall out:

1. **Destructuring is safe.** `const { toBe } = expect(5); toBe(5)` works because `toBe` doesn't need `this` to find `val` — it reads via closure. Compare with a class, where the same destructure loses the receiver and throws.
2. **The captured value is read-only from the outside.** There's no `.val` to set, no key in `Object.keys(...)`, no `Reflect.ownKeys(...)` exposing it. Even within the methods, neither needs to mutate `val`.
3. **Each `expect(...)` call** creates a fresh LE — multiple briefcases don't interfere. `expect(5).toBe(5); expect(6).toBe(6);` runs cleanly.

The same skeleton scales: Jest's real `expect` has 70+ matchers, async support (`.resolves`/`.rejects`), and a `.not` modifier — all reachable from this base shape by closing over additional flags.

---

## 8. Solution (annotated)

```js
var expect = function (val) {                  // step 1: outer captures `val` in its LE
  return {                                      // step 2: return an object literal with two methods
    toBe(other) {                                // step 3: strict-equality check; throw string on mismatch
      if (val !== other) throw "Not Equal";
      return true;
    },
    notToBe(other) {                             // step 4: inverse — throw if they DO match
      if (val === other) throw "Equal";
      return true;
    },
  };
};
```

**Try it yourself**

```js
console.log(expect(5).toBe(5));        // true
console.log(expect(5).notToBe(6));     // true

try { expect(5).toBe(6); }      catch (e) { console.log(e); }   // "Not Equal"
try { expect(5).notToBe(5); }   catch (e) { console.log(e); }   // "Equal"
try { expect(NaN).toBe(NaN); }  catch (e) { console.log(e); }   // "Not Equal" (NaN !== NaN)

// Destructuring-safe (no `this`)
const { toBe } = expect(42);
console.log(toBe(42));                  // true
```

---

## 9. Step-by-step dry run

Input:

```js
const e = expect(5);
e.toBe(5);
try { e.toBe(6); } catch (err) { console.log(err); }
e.notToBe(7);
try { e.notToBe(5); } catch (err) { console.log(err); }
```

Values-first trace:

| Step | Call          | Captured `val` | Comparison      | Outcome             |
|------|---------------|----------------|------------------|---------------------|
| init | `expect(5)`   | LE = `{val: 5}` | —                | returns the methods object |
| 1    | `e.toBe(5)`   | `5`            | `5 !== 5` → false | returns `true`      |
| 2    | `e.toBe(6)`   | `5`            | `5 !== 6` → true  | throws `"Not Equal"` |
| 3    | `e.notToBe(7)`| `5`            | `5 === 7` → false | returns `true`      |
| 4    | `e.notToBe(5)`| `5`            | `5 === 5` → true  | throws `"Equal"`    |

All four calls read the **same `val` slot** in the **same LE** on the heap.

---

## 10. Common confusion + traps

1. **Strict equality vs loose equality.**
   Use `===`/`!==`, not `==`/`!=`. The spec is explicit. `expect(0).toBe('')` is `false` under strict; `true` under loose. Don't change the operator without permission.

2. **`NaN` quirks.**
   `NaN !== NaN` is `true` under `===`, so `expect(NaN).toBe(NaN)` *throws* "Not Equal." Jest's real `toBe` uses `Object.is`, which treats `NaN === NaN` and `-0 !== +0`. If the interviewer asks "how would Jest handle this?", say `Object.is(val, other)`.

3. **Object equality is by reference.**
   `expect({a:1}).toBe({a:1})` throws because the two literals are different objects. For deep equality, use `toEqual` (a variant).

4. **Throw a string, not an Error (on LeetCode).**
   The harness checks `catch (e) → e === "Not Equal"`. With `new Error(...)`, `e` is an object — strict comparison fails. Match the spec verbatim on LeetCode; in production prefer `new Error(...)` for stack traces.

5. **Forgetting to return `true`.**
   Some graders check the return value. `if (cond) throw; return true;` is the canonical shape.

6. **Trying to chain.**
   `.toBe(5)` returns `true`, not the object. So `.toBe(5).notToBe(6)` throws `TypeError: cannot read 'notToBe' of true`. If chaining is asked for, return the methods object (or `this`-equivalent) instead.

---

## 11. Senior follow-ups & variants

### Variant 1 — Add `.toEqual` (deep equality)

```js
function expect(val) {
  return {
    toBe(other) { if (val !== other) throw "Not Equal"; return true; },
    notToBe(other) { if (val === other) throw "Equal"; return true; },
    toEqual(other) {
      if (!deepEqual(val, other)) throw "Not Equal";
      return true;
    },
  };
}
function deepEqual(a, b) {
  if (a === b) return true;
  if (typeof a !== 'object' || typeof b !== 'object' || a === null || b === null) return false;
  const ka = Object.keys(a), kb = Object.keys(b);
  if (ka.length !== kb.length) return false;
  return ka.every((k) => deepEqual(a[k], b[k]));
}
```

Real assertion libraries also handle Date, Map, Set, RegExp, and cycles — see `memoize-with-deep-equality.md`.

### Variant 2 — Jest-style `.not` modifier

`expect(5).not.toBe(6)` should pass. This requires **nested closures**: the outer captures `val`, the `.not` getter returns a *new* matcher set that inverts the throw conditions.

```js
function expect(val) {
  const positive = {
    toBe(other) { if (val !== other) throw "Not Equal"; return true; },
    notToBe(other) { if (val === other) throw "Equal"; return true; },
  };
  const negated = {
    toBe(other) { if (val === other) throw "Not (Not Equal)"; return true; },
    notToBe(other) { if (val !== other) throw "Not (Equal)"; return true; },
  };
  return { ...positive, not: negated };
}
```

Senior follow-up: chain modifiers like `.not.toBe`. Closure-over-flag + factory of matcher sets generalizes.

### Variant 3 — Async `.resolves` / `.rejects`

```js
function expect(val) {
  const sync = { toBe(other) { if (val !== other) throw "Not Equal"; return true; } };
  const resolves = {
    async toBe(other) {
      const v = await val;
      if (v !== other) throw "Not Equal";
      return true;
    },
  };
  return { ...sync, resolves };
}
await expect(Promise.resolve(5)).resolves.toBe(5);
```

Now `val` may be a Promise, and `.resolves.toBe(5)` awaits then compares. Closure over a pending promise.

### Variant 4 — Custom matcher registry

Real Jest lets you `expect.extend({ toBeWithinRange(received, min, max) {...} })`. That's a closure over a global matcher registry; each `expect(...)` builds an object from the registry by binding `val` into each matcher.

---

## 12. How to think aloud in the interview

> "Closure over `val`, return an object with two methods. Both methods close over the same `val` slot — they read it via the scope chain, no `this` involved. `toBe` throws `"Not Equal"` (string, per spec) on mismatch; `notToBe` throws `"Equal"` if they match. Both return `true` on success. Strict equality, so `NaN !== NaN` and object refs aren't equal — call those out for the interviewer. No chaining because `.toBe()` returns `true`, not the object. If they ask for follow-ups: `.toEqual` (deep), `.not` (factory of negated matchers via nested closures), `.resolves`/`.rejects` (async)."

---

## 13. 60-second revision

> - **Pattern:** outer captures `val`; return object literal `{ toBe, notToBe }`.
> - Both methods close over the **same LE** → both see the same `val`.
> - **Strict equality** (`===`) per spec; `Object.is` if interviewer asks for Jest semantics.
> - **`toBe(other)`**: throw `"Not Equal"` if `val !== other`, else return `true`.
> - **`notToBe(other)`**: throw `"Equal"` if `val === other`, else return `true`.
> - No `this` → destructuring is safe.
> - **Trap:** `==` vs `===`; `NaN !== NaN`; objects compare by reference.
> - **Trap:** `throw new Error(...)` instead of `throw "..."` — LeetCode harness fails.
> - **Family:** Jest `expect`, Chai matchers, Jasmine, querybuilder, fluent assertion libs.

---

**Related:** [counter-ii.md](./counter-ii.md) · [private-data-counter.md](./private-data-counter.md) · [module-pattern-iife.md](./module-pattern-iife.md)

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md)
