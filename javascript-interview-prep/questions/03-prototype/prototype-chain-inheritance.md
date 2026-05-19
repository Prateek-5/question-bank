# Prototype chain & inheritance

> **Difficulty:** Medium-Senior   |   **Time:** ~15 min   |   **Prereqs:** [`concepts/prototype.md`](../../concepts/prototype.md)
>
> **Source:** The most fundamental JS conceptual question. Every JS-flavored backend round.

---

## 1. Problem statement

Explain the prototype chain. Distinguish `Foo.prototype`, `instance.__proto__`, and `Object.getPrototypeOf`. Show ES5 and ES6 inheritance.

**Verification examples**

| Operation                                          | Result                                              |
|----------------------------------------------------|------------------------------------------------------|
| `new Foo() instanceof Foo`                          | `true` (chain walk finds `Foo.prototype`)           |
| `Object.getPrototypeOf(instance) === Foo.prototype` | `true`                                               |
| `instance.method()`                                 | walks chain → first match wins                      |
| `class Dog extends Animal` — `d.speak()`           | inherited via chain                                  |
| `Object.create(null)` instance — `obj.toString`    | `undefined` (no chain to Object.prototype)         |

**Constraints**
- Constructors carry `.prototype`; instances point via `__proto__`/`getPrototypeOf`.
- Lookup walks instance → its proto → ... → `null`.
- `instanceof` = "is `Ctor.prototype` on LHS's chain?"
- `extends` wires both instance chain AND static-method chain.

---

## 2. Plain-English restatement

Every object has a hidden link to another object — its prototype. Property lookups walk this chain. Constructors have a `.prototype` property that becomes the prototype of every instance they make via `new`. `instanceof` walks the chain looking for the constructor's prototype.

---

## 3. Why this matters in interviews

Single most fundamental JS question. Filter: can you draw the chain in 60s? Everything else (`this`, polyfills, `class`) depends on this.

---

## 4. Mental model

```
   Three names to distinguish:
   
   Foo.prototype          → object that future instances inherit FROM (lives on the constructor)
   instance.__proto__     → instance's link to Foo.prototype (deprecated accessor)
   Object.getPrototypeOf  → modern way to read the link
   
   Constructor and instance access the SAME object via two names.

   The chain (example):
   d ──▶ Dog.prototype ──▶ Animal.prototype ──▶ Object.prototype ──▶ null
        instance         inherits             inherits             chain root

   Property lookup walks left-to-right; first match wins.
   `null` ends the chain.

   `new Foo(args)`:
   1. Create new object obj.
   2. obj.[[Prototype]] = Foo.prototype.
   3. Foo.apply(obj, args) → run constructor body with this=obj.
   4. Return obj (unless Foo returned an object).
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What is `Object.getPrototypeOf([])`?
> 2. After `Child.prototype = Object.create(Parent.prototype)`, why must you also set `Child.prototype.constructor = Child`?
> 3. What's `Object.create(null)` useful for?

---

## 6. Brute force — walked through

### Wrong attempt 1: `Object.assign` parent properties
Flat snapshot; no live inheritance; `instanceof` lies.

### Wrong attempt 2: `Child.prototype = Parent.prototype`
Aliases — mutating one affects both. Use `Object.create`.

### Wrong attempt 3: forget `constructor` reset
After `Object.create`, `Child.prototype.constructor === Parent`. Reset to `Child`.

---

## 7. The unlocking insight

> **Constructors carry `.prototype`; instances link via `__proto__`/`getPrototypeOf`. Lookup walks the chain. `new` wires `[[Prototype]] = Ctor.prototype`. ES6 `class extends` does this + wires static-method chain (`Sub.__proto__ = Base`).**

Three properties:

1. **Three names for two roles** — constructor's blueprint vs instance's link.
2. **Chain walk** for lookups and `instanceof`.
3. **`new` does 4 things** — create, link prototype, apply, return.

---

## 8. Solution (annotated)

```js
// ES5 dialect — every wire visible
function Animal(name) {
  this.name = name;                                                    // step 1: own state
}
Animal.prototype.speak = function () {                                  // step 2: shared method
  return `${this.name} makes a sound`;
};

function Dog(name, breed) {
  Animal.call(this, name);                                              // step 3: inherit state (super)
  this.breed = breed;
}
Dog.prototype = Object.create(Animal.prototype);                        // step 4: wire prototype chain
Dog.prototype.constructor = Dog;                                        // step 5: restore constructor
Dog.prototype.bark = function () {
  return `${this.name} woofs`;
};

const d = new Dog('rex', 'lab');
d.speak();                                                              // 'rex makes a sound' (inherited)
d.bark();                                                               // 'rex woofs' (own proto)
d instanceof Dog;                                                       // true
d instanceof Animal;                                                    // true (chain walk)
d instanceof Object;                                                    // true

// ES6 class — same machine, sugar syntax
class Animal2 {
  constructor(name) { this.name = name; }
  speak() { return `${this.name} makes a sound`; }
}
class Dog2 extends Animal2 {
  constructor(name, breed) {
    super(name);                                                        // ≡ Animal2.call(this, name)
    this.breed = breed;
  }
  bark() { return `${this.name} woofs`; }
}
```

**Try it yourself**

```js
// Walking the chain
const d = new Dog2('rex', 'lab');
Object.getPrototypeOf(d) === Dog2.prototype;                            // true
Object.getPrototypeOf(Dog2.prototype) === Animal2.prototype;            // true
Object.getPrototypeOf(Animal2.prototype) === Object.prototype;          // true
Object.getPrototypeOf(Object.prototype) === null;                       // true

// Object.create(null) for clean dictionaries
const dict = Object.create(null);
dict.foo = 1;
dict.toString;                                                          // undefined (no chain!)
// Safe for user-controlled keys (no proto pollution).

// Arrow functions have no prototype
const arrow = () => {};
arrow.prototype;                                                        // undefined
// new arrow() → TypeError (not a constructor)
```

---

## 9. Step-by-step dry run

```
const d = new Dog('rex', 'lab')

new Dog(...) steps:
  1. obj = {} (fresh object)
  2. obj.[[Prototype]] = Dog.prototype
  3. Dog.apply(obj, ['rex', 'lab']):
       Animal.call(this='obj', 'rex'):
         obj.name = 'rex'
       obj.breed = 'lab'
  4. return obj

Property lookups on d:

d.bark():
  d own? no
  Dog.prototype own? YES → return Dog.prototype.bark
  invoke with this=d → 'rex woofs'

d.speak():
  d own? no
  Dog.prototype own? no
  Animal.prototype own? YES → return Animal.prototype.speak
  invoke with this=d → 'rex makes a sound'

d.toString():
  walks all the way to Object.prototype → toString → '[object Object]'

d.zzz:
  walks to null → returns undefined (doesn't throw)

instanceof check:
  d instanceof Animal:
    Object.getPrototypeOf(d) === Animal.prototype? No (it's Dog.prototype).
    Object.getPrototypeOf(Dog.prototype) === Animal.prototype? YES. Return true.
```

---

## 10. Common confusion + traps

1. **`Child.prototype = Parent.prototype`** — aliases; use `Object.create`.
2. **Forget `constructor` reset** after Object.create.
3. **Confuse `Foo.prototype` (parent-to-be) with `Foo.__proto__`** (Foo's own proto = `Function.prototype`).
4. **`new` with arrow function** — TypeError (no `.prototype`).
5. **`for...in` walks chain** — includes inherited enumerable; use `Object.keys`.
6. **`Object.create(null)` lacks `toString`** — feature, not bug.
7. **Shadowing** — `instance.x = ...` creates own prop; doesn't mutate proto.

---

## 11. Senior follow-ups & variants

### Variant 1 — Implement `instanceof`
Walk `Object.getPrototypeOf(obj)` looking for `Ctor.prototype`. See [instanceof-polyfill.md](./instanceof-polyfill.md).

### Variant 2 — Implement `Object.create`
`function fakeCreate(p){ function F(){}; F.prototype=p; return new F(); }`. Crockford pattern.

### Variant 3 — Mixin pattern
`Object.assign(Target.prototype, Mixin1, Mixin2)` — combine multiple sources.

### Variant 4 — Static methods
`class Foo { static bar() {} }` — `bar` on `Foo` itself, not `Foo.prototype`. Two chains (instance + constructor).

### Variant 5 — `Object.create(null)` for dictionaries
Safe maps; no `__proto__`/`toString` collisions with user keys.

---

## 12. How to think aloud

> "Three names: `Foo.prototype` on the constructor (the blueprint for instances), `instance.__proto__` (deprecated accessor), `Object.getPrototypeOf(instance)` (modern way to read the link). Instance's link and constructor's prototype property are the SAME object. Lookup walks the chain: instance → its proto → its proto's proto → ... → null; first match wins. `new Foo(args)` does 4 things: create obj, wire `obj.[[Prototype]] = Foo.prototype`, call `Foo.apply(obj, args)`, return obj (unless constructor explicitly returned an object). ES5 inheritance: `Child.prototype = Object.create(Parent.prototype); Child.prototype.constructor = Child; Parent.call(this, ...)` in Child's constructor. ES6 `class extends` desugars to this + wires the static-method chain via `Sub.__proto__ = Base`. `instanceof` walks the chain looking for `Ctor.prototype`. `Object.create(null)` makes prototype-less objects — safe for user-keyed maps. Arrow functions have no `.prototype` → can't be `new`'d. Trap: `Child.prototype = Parent.prototype` aliases; forgetting `constructor` reset."

---

## 13. 60-second revision

> - **Three names:** `Foo.prototype` (on constructor), `instance.__proto__` (deprecated), `Object.getPrototypeOf` (modern).
> - **Chain walk** for lookups and `instanceof`. First match wins.
> - **`new` does 4 things:** create, wire proto, apply, return.
> - **ES5 inherit:** `Child.prototype = Object.create(Parent.prototype); .constructor = Child` + `Parent.call(this, ...)`.
> - **ES6 `class extends`** = ES5 + static chain.
> - **`instanceof`** = "is `Ctor.prototype` on LHS chain?"
> - **`Object.create(null)`** for prototype-less dictionaries.
> - **Arrow functions** have no `.prototype` (can't be `new`'d).
> - **Trap:** `Child.prototype = Parent.prototype` (aliases); forgetting `constructor` reset; confusing `Foo.prototype` with `Foo.__proto__`.

---

**Related:** [this-keyword-nodejs.md](./this-keyword-nodejs.md) · [polyfill-new.md](./polyfill-new.md) · [instanceof-polyfill.md](./instanceof-polyfill.md) · [class-to-prototype-desugar.md](./class-to-prototype-desugar.md) · [object-create-polyfill.md](./object-create-polyfill.md)

**Concept primer:** [`concepts/prototype.md`](../../concepts/prototype.md)
