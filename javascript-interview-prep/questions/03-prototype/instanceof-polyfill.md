# Polyfill the `instanceof` operator

> **Difficulty:** Easy-Medium   |   **Time:** ~10 min   |   **Prereqs:** [prototype-chain-inheritance.md](./prototype-chain-inheritance.md)
>
> **Source:** BFE.dev #19, GreatFrontEnd. Litmus test for prototype-chain understanding.

---

## 1. Problem statement

`myInstanceof(obj, Ctor)` — return `true` if `Ctor.prototype` is anywhere on `obj`'s prototype chain.

**Verification examples**

```js
class Animal {}
class Dog extends Animal {}
const d = new Dog();

myInstanceof(d, Dog);        // true
myInstanceof(d, Animal);     // true (chain walk)
myInstanceof(d, Object);     // true
myInstanceof(d, Array);      // false
myInstanceof(5, Number);     // false (primitive, not boxed)
myInstanceof(null, Object);  // false (null short-circuits)
```

**Constraints**
- Walk `Object.getPrototypeOf(obj)` upward.
- Compare each link with `Ctor.prototype`.
- Stop on match (true) or `null` (false).
- Handle `Symbol.hasInstance` override.

---

## 2. Plain-English restatement

Walk up the prototype chain from `obj`, asking at each step "is this link `=== Ctor.prototype`?" Stop on match (true) or when the chain ends at `null` (false). Not constructor equality — chain membership.

---

## 3. Why this matters in interviews

Litmus test for understanding the prototype chain. 8 lines proves you know `__proto__` vs `.prototype` and chain mechanics.

---

## 4. Mental model

```
   instanceof = "is Ctor.prototype anywhere on obj's chain?"
   
   obj.__proto__ ──▶ obj.__proto__.__proto__ ──▶ ... ──▶ null
                              ↑
                       compare each step
                       with Ctor.prototype
   
   Stop conditions:
   - Match: return true.
   - Hit null: return false.
   
   `instance.constructor === Ctor` is NOT instanceof — that's just one rung.
   instanceof is the WHOLE LADDER walk.
   
   Symbol.hasInstance:
   - Class can override via static [Symbol.hasInstance](v).
   - Polyfill should honor it before falling back to chain walk.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why is `5 instanceof Number` `false`?
> 2. What's the difference between `obj.constructor === Ctor` and `obj instanceof Ctor`?
> 3. Can a class override `instanceof` behavior?

---

## 6. Brute force — walked through

### Wrong attempt 1: `obj.constructor === Ctor`
Single rung; misses inheritance. `Dog` instance has `constructor === Dog` but `instanceof Animal` is also true.

### Wrong attempt 2: compare `proto === Ctor`
Wrong — chain holds prototype OBJECTS, not constructor functions.

### Wrong attempt 3: no null check
Infinite loop on chain that's exhausted.

---

## 7. The unlocking insight

> **Walk `Object.getPrototypeOf(obj)` upward. Compare each link with `Ctor.prototype`. Stop on match (true) or `null` (false). Honor `Symbol.hasInstance` if defined.**

Three properties:

1. **Chain walk** — not single comparison.
2. **Compare `proto === Ctor.prototype`** — not `Ctor`.
3. **Null termination** — chain ends.

---

## 8. Solution (annotated)

```js
function myInstanceof(obj, Ctor) {
  if (typeof Ctor !== 'function') {
    throw new TypeError('Right-hand side of instanceof is not callable');
  }

  if (typeof Ctor[Symbol.hasInstance] === 'function') {                  // step 1: honor override
    return Boolean(Ctor[Symbol.hasInstance](obj));
  }

  if (obj === null || (typeof obj !== 'object' && typeof obj !== 'function')) {
    return false;                                                        // step 2: primitive/null
  }

  const target = Ctor.prototype;
  if (target === null || typeof target !== 'object') {
    throw new TypeError('Function has non-object prototype');
  }

  let proto = Object.getPrototypeOf(obj);
  while (proto !== null) {                                                // step 3: walk chain
    if (proto === target) return true;
    proto = Object.getPrototypeOf(proto);
  }
  return false;
}
```

**Try it yourself**

```js
class Animal {}
class Dog extends Animal {}
const d = new Dog();

myInstanceof(d, Dog);        // true
myInstanceof(d, Animal);     // true
myInstanceof(d, Object);     // true
myInstanceof(d, Array);      // false
myInstanceof(5, Number);     // false
myInstanceof(null, Object);  // false

// Symbol.hasInstance override
class Even {
  static [Symbol.hasInstance](v) { return typeof v === 'number' && v % 2 === 0; }
}
myInstanceof(4, Even);       // true (no instance ever created)
myInstanceof(5, Even);       // false
```

---

## 9. Step-by-step dry run

```
myInstanceof(d, Animal):

  Ctor = Animal (function ✓).
  Symbol.hasInstance on Animal? No.
  obj = d (typeof 'object', not null) — pass guard.
  target = Animal.prototype.

  Walk:
    proto = Object.getPrototypeOf(d) = Dog.prototype.
    proto === Animal.prototype? No.
    proto = Object.getPrototypeOf(Dog.prototype) = Animal.prototype.
    proto === Animal.prototype? YES. Return true.

myInstanceof(d, Object):
  target = Object.prototype.
  Walk: Dog.prototype → Animal.prototype → Object.prototype (match). True.

myInstanceof(d, Array):
  target = Array.prototype.
  Walk full chain to Object.prototype, then null. No match. False.

myInstanceof(5, Number):
  typeof 5 === 'number' → primitive guard fails → return false.

Symbol.hasInstance override:
  myInstanceof(4, Even):
    Even[Symbol.hasInstance] is a function.
    Call Even[Symbol.hasInstance](4) → 4 % 2 === 0 → true.
    Return true.
```

---

## 10. Common confusion + traps

1. **Compare `proto === Ctor`** — chain holds prototype OBJECTS.
2. **Forget `null` check** — infinite loop.
3. **Return false for functions** — functions ARE objects (`fn instanceof Function` true).
4. **Skip `Symbol.hasInstance`** — Promise uses it.
5. **Primitives** — `5 instanceof Number` is false (not boxed).
6. **Cross-realm objects** — `arr instanceof Array` false across iframes/vm.
7. **Constructor equality vs instanceof** — different (single rung vs walk).

---

## 11. Senior follow-ups & variants

### Variant 1 — `Symbol.hasInstance` demo
`class Even { static [Symbol.hasInstance](v) { ... } }`. No instance needed.

### Variant 2 — Cross-realm
Different iframes have different `Array` constructors. Use `Array.isArray` for arrays.

### Variant 3 — `isPrototypeOf` polyfill
`Animal.prototype.isPrototypeOf(d)` — same walk, no `.prototype` indirection.

### Variant 4 — `Object.create(null)` instance
Chain has 1 link (`null`); `instanceof Object` is false.

### Variant 5 — `Object.setPrototypeOf` mid-life
Polyfill handles dynamically; walks live chain.

---

## 12. How to think aloud

> "`instanceof` is a CHAIN WALK, not a single comparison. Walk `Object.getPrototypeOf(obj)` upward, comparing each link with `Ctor.prototype`. Stop on match (return true) or `null` (return false). Guard against primitives/null up front. Honor `Symbol.hasInstance` (ES2015+) if defined — classes can override instanceof. Compare with `Ctor.prototype`, NOT `Ctor` — the chain holds prototype OBJECTS, not constructor functions. `obj.constructor === Ctor` is just one rung; instanceof is the whole ladder. Cross-realm gotcha: different iframes have different `Array`/`Object` constructors. For arrays specifically use `Array.isArray`. Trap: comparing with Ctor instead of Ctor.prototype; missing null check (infinite loop); returning false for functions (they ARE objects)."

---

## 13. 60-second revision

> - **Walk** `Object.getPrototypeOf(obj)` upward.
> - **Compare** each link with `Ctor.prototype` (NOT `Ctor`).
> - **Stop:** match → true; `null` → false.
> - **Honor `Symbol.hasInstance`** if defined (Promise uses it).
> - **Primitives:** `5 instanceof Number` is false.
> - **Cross-realm:** different constructors per realm; use `Array.isArray`.
> - **Two-link rule:** instance side = `[[Prototype]]`; constructor side = `.prototype`.
> - **Trap:** compare with Ctor; no null check; return false for functions.

---

**Related:** [prototype-chain-inheritance.md](./prototype-chain-inheritance.md) · [polyfill-new.md](./polyfill-new.md) · [object-create-polyfill.md](./object-create-polyfill.md) · [class-to-prototype-desugar.md](./class-to-prototype-desugar.md)

**Concept primer:** [`concepts/prototype.md`](../../concepts/prototype.md)
