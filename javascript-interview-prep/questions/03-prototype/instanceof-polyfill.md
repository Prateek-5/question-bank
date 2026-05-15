# Implement the `instanceof` operator

## Source
- Canonical "do you understand the prototype chain?" interview question (BFE.dev #19, GreatFrontEnd, every senior JS round).
- MDN reference: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/instanceof

## Why this question matters in interviews
`instanceof` is the litmus test for whether a candidate actually understands the prototype chain or has only memorized the word "prototype." The operator's entire job is to walk `obj.__proto__` and compare each link with `Constructor.prototype`. Writing the polyfill in 8 lines proves you know (a) the difference between `__proto__` (instance link) and `.prototype` (constructor's blueprint), (b) that the chain terminates at `null`, and (c) that the check is **chain membership**, not equality. As a backend engineer you'll use this when implementing duck-typing fallbacks, custom error hierarchies, and ORM model checks.

## Concepts involved

### Syntax to lock in
```js
function myInstanceof(obj, Ctor) {
  if (obj === null || (typeof obj !== 'object' && typeof obj !== 'function')) return false;
  let proto = Object.getPrototypeOf(obj);
  const target = Ctor.prototype;
  while (proto !== null) {
    if (proto === target) return true;
    proto = Object.getPrototypeOf(proto);
  }
  return false;
}
```

### Runtime / engine behavior
- Every object has an internal `[[Prototype]]` slot, exposed via `Object.getPrototypeOf(obj)` (modern) or the legacy `obj.__proto__` accessor.
- A constructor function has a `.prototype` property — the object that gets assigned as `[[Prototype]]` of every instance it creates via `new`.
- `instanceof` walks **up** from the instance's `[[Prototype]]` and asks "is this slot `=== Ctor.prototype`?" The walk stops at `null` (top of chain).
- `Object.create(null)` produces an object with `[[Prototype]] === null` — the chain is one link long.

### Edge cases (these are the interview traps)
1. **`null` input** — `instanceof null` would throw natively, but our polyfill should return `false` for `obj === null`.
2. **Primitives** — `5 instanceof Number` is `false` (primitives are not boxed). Guard with `typeof`.
3. **Functions as left operand** — functions ARE objects, so `function f(){}; f instanceof Function` is `true`. Allow `typeof obj === 'function'` to pass the type guard.
4. **Right operand must be callable** — native `instanceof` throws `TypeError` if RHS isn't a function. Decide whether to mirror or no-op; most interviewers want the throw.
5. **`Symbol.hasInstance`** — ES2015 allows a class to override `instanceof` via `static [Symbol.hasInstance](v) { ... }`. A complete polyfill should honor it (bonus).
6. **Prototype reassignment after construction** — `Object.setPrototypeOf(obj, NewCtor.prototype)` changes the chain mid-life. The polyfill handles it correctly because we walk live.
7. **Cross-realm objects** — across iframes / Node `vm` contexts, two `Array` constructors are distinct. `arrFromOtherRealm instanceof Array` is `false`. Mention if asked about edge cases.
8. **Chain termination** — must check `proto !== null` to avoid infinite loop. `Object.prototype`'s `[[Prototype]]` is `null`.

## Brute force approach
"Compare `obj.constructor === Ctor`." This fails the moment inheritance enters the picture: a `Dog` instance has `constructor === Dog`, but `dog instanceof Animal` must still be `true`. Constructor-equality is one rung; `instanceof` is the whole ladder.

## Optimal approach
Linear walk up the prototype chain comparing each slot with `Ctor.prototype`. O(depth) time, O(1) space. Stop at `null`. That's the entire algorithm — anything longer is over-engineering.

## Solution (JavaScript)

```js
/**
 * Polyfill for the `instanceof` operator.
 * @param {unknown} obj   left operand
 * @param {Function} Ctor right operand (must be callable)
 * @returns {boolean}
 */
function myInstanceof(obj, Ctor) {
  if (typeof Ctor !== 'function') {
    throw new TypeError('Right-hand side of instanceof is not callable');
  }

  // Honor user-defined hook (ES2015+)
  if (typeof Ctor[Symbol.hasInstance] === 'function') {
    return Boolean(Ctor[Symbol.hasInstance](obj));
  }

  // Primitives and null short-circuit to false
  if (obj === null || (typeof obj !== 'object' && typeof obj !== 'function')) {
    return false;
  }

  const target = Ctor.prototype;
  if (target === null || typeof target !== 'object') {
    throw new TypeError('Function has non-object prototype in instanceof check');
  }

  let proto = Object.getPrototypeOf(obj);
  while (proto !== null) {
    if (proto === target) return true;
    proto = Object.getPrototypeOf(proto);
  }
  return false;
}
```

## Step-by-step dry run

Input:
```js
class Animal {}
class Dog extends Animal {}
const d = new Dog();

myInstanceof(d, Dog);     // ?
myInstanceof(d, Animal);  // ?
myInstanceof(d, Object);  // ?
myInstanceof(d, Array);   // ?
```

Trace `myInstanceof(d, Animal)`:
- `Ctor` is `Animal` — callable, no `Symbol.hasInstance` override.
- `obj` is `d` — typeof `'object'`, not null. Continue.
- `target = Animal.prototype`.
- Iter 1: `proto = Object.getPrototypeOf(d) === Dog.prototype`. `Dog.prototype !== Animal.prototype`. Climb.
- Iter 2: `proto = Object.getPrototypeOf(Dog.prototype) === Animal.prototype`. Match! Return `true`.

Trace `myInstanceof(d, Object)`:
- Climbs `Dog.prototype → Animal.prototype → Object.prototype`. Match at depth 3. Return `true`.

Trace `myInstanceof(d, Array)`:
- Climbs full chain to `Object.prototype`, then `null`. Loop exits. Return `false`.

Bonus — `myInstanceof(5, Number)`:
- `typeof 5 === 'number'` → fails type guard → returns `false`. Matches native behavior.

## Important takeaways

**Syntax to memorize**
- `Object.getPrototypeOf(x)` over `x.__proto__` — works on `Object.create(null)` instances too.
- Loop condition: `while (proto !== null)`, not `while (proto)` (defends against weird falsy protos — rare but real).
- Cache `Ctor.prototype` in a local before the loop; one property read instead of N.

**Patterns to reuse**
- "Walk a chain until you hit `null`" is the same skeleton as: prototype lookup for property access, scope chain resolution, linked-list traversal, parent-pointer tree walks.
- The two-link mental model (instance `[[Prototype]]` vs constructor `.prototype`) is the foundation for `Object.create`, `extends/super`, and class desugaring questions.

**Common mistakes**
- Comparing `proto === Ctor` instead of `proto === Ctor.prototype`. The chain holds prototype objects, not constructor functions.
- Forgetting the `null` check — infinite loop on a chain that's already exhausted.
- Returning `false` for functions (e.g., `(()=>{}) instanceof Function` should be `true`).
- Skipping `Symbol.hasInstance` — small detail, but classes like `Promise` use it internally for thenable detection.

**Related questions**
- `Object.create` polyfill (constructs a chain)
- `extends`/`super` manual implementation (configures the chain)
- "Why does `[] instanceof Array` return `false` across iframes?" (realm-specific globals)

## Variants

1. **`Symbol.hasInstance` override demo** — "Make a class `Even` such that `5 instanceof Even` is `false` and `4 instanceof Even` is `true`, with no instances ever created." Tests the static hook.

2. **Cross-realm `instanceof`** — "Why does `arr instanceof Array` from another iframe fail? How would you write `isArray` correctly?" Answer: `Array.isArray` checks the internal `[[Class]]` brand, not the chain.

3. **`isPrototypeOf` polyfill** — "Implement `Animal.prototype.isPrototypeOf(d)`." Same walk, but the comparison target is `this` (already a prototype object) instead of `Ctor.prototype`. Highlights that `isPrototypeOf` skips the `.prototype` indirection.

## Revision notes

> **instanceof polyfill — 60 second recap**
> - Walks `Object.getPrototypeOf(obj)` upward, comparing each link with `Ctor.prototype`.
> - Stop on match (`true`) or `null` (`false`).
> - Guard against `null` / primitives on the left (return `false`).
> - Throw `TypeError` if `Ctor` isn't a function.
> - Honor `Ctor[Symbol.hasInstance]` if present (ES2015+ hook).
> - **Two-link rule:** instance side = `[[Prototype]]`; constructor side = `.prototype`. The polyfill bridges them.
> - **Trap:** comparing with `Ctor` instead of `Ctor.prototype`. The chain stores prototype objects.
> - Cross-realm gotcha: each iframe / vm context has its own `Array`, `Object`. Use `Array.isArray` for arrays.
