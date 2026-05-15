# Implement `Array.prototype.last`

## Source
- LeetCode #2619 "Array Prototype Last": https://leetcode.com/problems/array-prototype-last/
- Asked at Stripe, Atlassian and many frontend-leaning backend rounds as a 10-minute warm-up.

## Why this question matters in interviews
This single problem tests three things interviewers love to probe in 10 minutes: **augmenting a built-in prototype**, **`this` binding inside a prototype method**, and **awareness of the "polluting built-ins is a code smell" tradeoff**. As a senior backend engineer you must be able to (a) write the one-liner, (b) explain *why* you'd normally avoid it, and (c) know how to do it *safely* with `Object.defineProperty` so the new method doesn't leak into `for...in` loops or break libraries that monkey-patch the same name. Saying "I'd never do this in prod" is fine; not knowing the mechanics is not.

## Concepts involved

### Syntax to lock in
```js
Array.prototype.last = function () {
  return this.length === 0 ? -1 : this[this.length - 1];
};
[1, 2, 3].last(); // 3
[].last();        // -1
```

### Runtime / engine behavior
- Every value created by `[...]` literal or `new Array(...)` has `Array.prototype` in its prototype chain: `arr -> Array.prototype -> Object.prototype -> null`.
- Method resolution: when you call `arr.last()`, the engine looks at `arr`'s own properties first (none), then `Object.getPrototypeOf(arr)` which is `Array.prototype` — and finds `last` there. `this` inside is the array itself.
- Adding a property directly with assignment (`Array.prototype.last = ...`) creates an **enumerable** property. That means `for (const k in arr)` will now yield `'last'`. This is the *real* reason "don't touch built-ins" is the rule.
- `Object.defineProperty(Array.prototype, 'last', { value: fn, enumerable: false, writable: true, configurable: true })` is the safe form.

### Edge cases (interview traps)
1. **Empty array** — must return `-1` per the problem (not `undefined`). Always check `this.length`.
2. **`this` is the array** — never hard-code a variable name; rely on `this`. Arrow functions would *break* this (they have no own `this`).
3. **Sparse arrays** — `[1, , 3].last()` returns `3`, but `[1, 2, ,].last()` returns `undefined` because the trailing comma creates a hole at index 2 and `length` is 3. Be explicit if asked.
4. **Subclasses** — `class MyArr extends Array {}`. `new MyArr(1,2,3).last()` still works because `MyArr.prototype.__proto__ === Array.prototype`. Show you understand the chain.
5. **`for...in` pollution** — if you do `Array.prototype.last = fn` without `defineProperty`, `for (const i in [1,2,3])` now lists `0, 1, 2, 'last'`. Demonstrate the fix.
6. **Re-augmentation** — running the patch twice should not throw. `writable: true, configurable: true` makes it safe.
7. **Strict mode** — irrelevant here, but `this` inside the method is *always* the array because the call is method-style.

## Brute force approach
"Iterate the whole array until I'm at the last element." Pointless — JS arrays know their length in O(1). The question is really about *where* to put the function and *how* `this` works, not algorithmic complexity.

## Optimal approach
Attach `last` to `Array.prototype` using `Object.defineProperty` so it's non-enumerable. Inside, use `this.length` to detect empty and index `this[this.length - 1]` otherwise. O(1) time, O(1) space.

## Solution (JavaScript)

```js
/**
 * Augment Array.prototype with a `last()` method.
 * Returns the last element, or -1 for empty arrays.
 *
 * Use Object.defineProperty so the new method is NON-ENUMERABLE
 * — this is the production-grade form. A naive
 *   Array.prototype.last = function () { ... }
 * would leak the key into `for...in` over every array.
 */
Object.defineProperty(Array.prototype, 'last', {
  value: function () {
    return this.length === 0 ? -1 : this[this.length - 1];
  },
  writable: true,      // allow re-assignment (re-running the patch)
  configurable: true,  // allow deletion / redefinition
  enumerable: false,   // critical — no for...in leakage
});

// Usage
[1, 2, 3].last();          // 3
['a', 'b'].last();         // 'b'
[].last();                 // -1
new Array(5).fill(0).last(); // 0
```

## Step-by-step dry run

Input:
```js
const arr = [10, 20, 30];
arr.last();
```

Trace the prototype walk:
1. Engine evaluates `arr.last` — it asks: does `arr` have an own property named `last`? `Object.getOwnPropertyNames(arr) === ['0','1','2','length']`. **No.**
2. Engine follows `Object.getPrototypeOf(arr)` → `Array.prototype`. Does it have `last`? **Yes** (we defined it). Return that function.
3. The function is invoked **method-style**: `arr.last()`. Inside the call, `this === arr`.
4. `this.length === 3` → not zero → return `this[3 - 1] === this[2] === 30`.

Now check `for...in` leakage with **and without** `defineProperty`:
```js
Array.prototype.foo = function () {};                                   // enumerable
Object.defineProperty(Array.prototype, 'bar', { value: () => {}, enumerable: false });

for (const k in [1, 2, 3]) console.log(k);
// '0', '1', '2', 'foo'    <-- foo leaks! bar does not.
```

This is exactly why the safe form matters.

## Important takeaways

**Syntax to memorize**
- `Object.defineProperty(Array.prototype, 'name', { value, writable: true, configurable: true, enumerable: false })`.
- Use `function () {}` not `() => {}` — arrows have no `this` binding.
- `this.length === 0 ? -1 : this[this.length - 1]`.

**Patterns to reuse**
- The pattern of "non-enumerable method on a prototype" is exactly how every native method (`push`, `map`, `filter`) is defined. Run `Object.getOwnPropertyDescriptor(Array.prototype, 'map')` and you'll see `enumerable: false`.
- Same pattern works for `String.prototype`, `Function.prototype`, `Object.prototype` — though `Object.prototype` pollution is far more dangerous (affects every object).

**Common mistakes**
- Plain assignment `Array.prototype.last = fn` — leaks into `for...in`.
- Writing an arrow function — `this` becomes the surrounding scope, not the array.
- Returning `undefined` for empty arrays — read the spec carefully (`-1` here).
- Forgetting `configurable: true` — second run of the script throws on overwrite.

**Why interviewers ask this**
- It separates candidates who know "JS has prototypes" from those who know **how** prototype lookup and property descriptors actually work.

## Variants

1. **`Array.prototype.first`** — same pattern, `this[0]` (or `-1` if empty).
2. **`Array.prototype.groupBy(fn)`** — LeetCode #2631. Returns an object keyed by `fn(item)` mapping to arrays. Tests the same prototype-augmentation skill plus reduce-style iteration.
3. **Polyfill `Array.prototype.flat(depth)`** without recursion. Same harness, different algorithm — see the recursion bucket.
4. **`Object.prototype.has(key)`** — same mechanic on `Object.prototype`. Interviewer follow-up: "Why is this much more dangerous?" Because it pollutes *every* object including the empty `{}` literals you use as maps.

## Revision notes

> **Array.prototype.last — 60 second recap**
> - Add via `Object.defineProperty(Array.prototype, 'last', { value: fn, enumerable: false, writable: true, configurable: true })`.
> - Inside the method, `this` is the array (method-style call).
> - Use `function`, NOT arrow — arrows have no own `this`.
> - Empty array → return `-1` (problem-specific), otherwise `this[this.length - 1]`.
> - Plain assignment leaks into `for...in`; `enumerable: false` is mandatory.
> - Method lookup walks `arr -> Array.prototype -> Object.prototype -> null`.
> - Mention "in production we'd prefer a free function `last(arr)` or a util module; prototype augmentation breaks library boundaries."
> - All native methods (`map`, `filter`, `push`) are themselves non-enumerable on `Array.prototype` — same template.
> - **Trap:** arrow function + augmenting prototype = broken `this`. Don't.
