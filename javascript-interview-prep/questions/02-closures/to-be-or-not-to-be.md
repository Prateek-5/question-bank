# To Be Or Not To Be (`expect`)

## Source
- https://leetcode.com/problems/to-be-or-not-to-be/

## Why this question matters in interviews
This problem looks trivial — write `expect(5).toBe(5)` — but it's actually the closure-based foundation of **Jest**, **Jasmine**, **Mocha's `chai`**, and every fluent assertion library on npm. Interviewers like it because in <15 lines you have to demonstrate: closing over a value, returning an **object of methods** that share that value, and choosing between throwing vs returning errors. As a backend engineer, this is the same skeleton you'd use to build any **fluent / builder API** — query builders (Knex), HTTP request builders (supertest), config DSLs. The pattern goes: capture context in closure → expose chainable methods → propagate context.

## Concepts involved

### Syntax to lock in
```js
function expect(val) {
  return {
    toBe(other) {
      if (val !== other) throw new Error("Not Equal");
      return true;
    },
    notToBe(other) {
      if (val === other) throw new Error("Equal");
      return true;
    },
  };
}
```
- Outer captures `val` in its LE.
- Returned object has two methods, both closing over the same LE → both see the same `val`.
- Equality is **strict** (`===`) per the LeetCode spec. This matters: `expect(NaN).toBe(NaN)` returns `false` under `===`, so `notToBe` would *not* throw — surprising, sometimes spec-relevant.

### Lexical environment / what survives
- `LE_outer = { val }`. One LE per `expect(...)` call.
- Two method function objects share `[[Environment]] = LE_outer`.
- Even after `expect(5)` returns, LE_outer is held alive by the returned object — until the caller drops the reference. Typical lifecycle: `expect(x).toBe(y)` — built and discarded inline, garbage collected immediately.

### Why throwing vs returning?
LeetCode wants `toBe` to **throw `"Not Equal"`** and **return `true`** on success. Jest's real `expect` matchers return `undefined` and throw on failure — same shape. The throw-on-failure model lets the test runner catch and report; return-`true` lets you assert in a one-liner if you want.

### Edge cases / interview traps
1. **Strict equality** — `===` not `==`. `expect(0).toBe(-0)` is `true` under `===`; `expect(NaN).toBe(NaN)` is `false`. Jest's real `toBe` uses `Object.is`, which flips both. If the interviewer asks "how would Jest's `toBe` handle `NaN`?", `Object.is(val, other)` is the answer.
2. **Throwing the right type** — spec says `throw "Not Equal"` (a string). Real code uses `new Error(...)`. Match the spec verbatim on LeetCode; in a real-world variant, prefer `Error` (gives stack traces).
3. **Object equality** — `expect({a:1}).toBe({a:1})` is `false` (different references). Asks for `toEqual` (deep) as a variant.
4. **No `this` needed** — methods don't reference `this`, so destructuring is safe: `const { toBe } = expect(5); toBe(5);` works. Contrast with a class where `toBe` would lose `this`.
5. **Chaining** — `.toBe()` returns `true`, not the object. So you can't chain `.toBe(5).notToBe(6)`. If the interviewer asks for chaining, return `this`-equivalent (the same object) instead.

## Brute force approach
"Use a class with `val` as a field and methods that check." Works. But again — the prompt says **return**, not **instantiate**. Class adds a `new` call site, a prototype, and exposes `val` (unless using `#val`). Closure version is tighter and idiomatically JS.

## Optimal approach
Outer function captures `val`. Return an object literal with two methods that close over `val` and throw on mismatch. O(1) memory, O(1) per assertion.

## Solution (JavaScript)

```js
/**
 * @param {string|number|null|undefined} val
 * @return {{ toBe: Function, notToBe: Function }}
 */
var expect = function (val) {
  return {
    toBe(other) {
      if (val !== other) throw "Not Equal";
      return true;
    },
    notToBe(other) {
      if (val === other) throw "Equal";
      return true;
    },
  };
};

// Usage
expect(5).toBe(5);          // true
expect(5).notToBe(6);       // true
try { expect(5).toBe(6); }   catch (e) { console.log(e); } // "Not Equal"
try { expect(5).notToBe(5); } catch (e) { console.log(e); } // "Equal"
```

## Step-by-step dry run

Input:
```js
const e = expect(5);
console.log(e.toBe(5));     // expect: true
try { e.toBe(6); } catch (err) { console.log(err); } // expect: "Not Equal"
console.log(e.notToBe(7));  // expect: true
try { e.notToBe(5); } catch (err) { console.log(err); } // expect: "Equal"
```

Trace:
1. `expect(5)` is called.
   - LE_outer created: `{ val: 5 }`.
   - Object literal `{ toBe, notToBe }` is built; both methods carry `[[Environment]] = LE_outer`.
   - Returned and bound to `e`. Outer frame popped; LE_outer retained because `e` references methods that reference it.
2. `e.toBe(5)`:
   - Scope chain lookup of `val` → `LE_outer.val = 5`.
   - `5 !== 5` is `false` → no throw → returns `true`.
3. `e.toBe(6)`:
   - `5 !== 6` is `true` → throws `"Not Equal"`. Caught by outer try/catch; prints `"Not Equal"`.
4. `e.notToBe(7)`:
   - `5 === 7` is `false` → no throw → returns `true`.
5. `e.notToBe(5)`:
   - `5 === 5` is `true` → throws `"Equal"`. Prints `"Equal"`.

All four method calls read **the same `val`** from **the same LE** on the heap.

## Important takeaways

**Syntax to memorize**
- `function expect(val) { return { toBe(o){...}, notToBe(o){...} }; }`.
- Method shorthand in object literal — concise and avoids the `function` keyword.

**Patterns to reuse**
- **Returning an object of methods that all close over the outer's parameters** is the universal "tiny fluent API" pattern. Same as Counter II, Event Emitter, LRU cache, querybuilder.
- This pattern is how Jest's `expect`, Jasmine's matchers, Chai's `chai(...)` all work internally — just with hundreds of matchers and async support.

**Common mistakes**
- Using `==` instead of `===` (spec violation).
- Throwing `new Error("...")` when the spec says `throw "..."` (string). On LeetCode, match the spec to pass tests.
- Forgetting to return `true` on success — some grading harnesses check the return value.
- Adding chaining without being asked — the spec wants `.toBe()` to return `true`, not the object.

**Related questions**
- Counter II (multi-method closure with mutation)
- Event Emitter (multi-method closure over a `listeners` map)
- Currying (chained closures, similar fluent feel)
- "Build a tiny assertion library" — extends this with `.toEqual`, `.toThrow`, `.toBeGreaterThan`, etc.

## Variants

1. **Add `.toEqual(other)`** — deep structural equality. Requires recursive comparison; closure pattern unchanged. Tests your recursion + type-check muscles.

2. **Add `.not` modifier** — Jest-style `expect(5).not.toBe(6)`. Solution: `expect` returns an object that has both the matchers and a `.not` getter returning an inverted matcher set. Now you have **nested closures**: `not.toBe` closes over the outer `val` *and* a "negate" flag. Common follow-up.

3. **Async `.resolves`/`.rejects`** — `await expect(promise).resolves.toBe(5)`. Now matchers return promises. Closure over `val` *and* the pending promise.

## Revision notes

> **expect (To Be Or Not To Be) — 60 second recap**
> - Outer captures `val`; return object `{ toBe, notToBe }`.
> - Both methods close over the **same LE** → both see the same `val`.
> - `toBe(other)`: throw `"Not Equal"` if `val !== other`, else return `true`. Strict equality.
> - `notToBe(other)`: throw `"Equal"` if `val === other`, else return `true`.
> - No `this` — destructuring methods is safe.
> - **Trap:** `==` vs `===`; `NaN !== NaN`; objects compare by reference.
> - **Trap:** spec wants `throw "string"`, not `new Error()` — match the harness.
> - This is the literal skeleton behind Jest's `expect`, Chai's matchers, and every fluent assertion lib.
> - Family: Counter II, Event Emitter, querybuilder — all "object-of-methods sharing closure state."
