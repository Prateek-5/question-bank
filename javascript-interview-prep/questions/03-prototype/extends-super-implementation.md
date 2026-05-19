# Implement `extends` + `super` manually

> **Difficulty:** Senior   |   **Time:** ~15 min   |   **Prereqs:** [prototype-chain-inheritance.md](./prototype-chain-inheritance.md), [class-to-prototype-desugar.md](./class-to-prototype-desugar.md)
>
> **Source:** Senior JS interview question. Tests the two prototype links `extends` installs.

---

## 1. Problem statement

Without using `class`, manually wire inheritance + super calls.

**Verification examples**

```js
function extend(Child, Parent) {
  Object.setPrototypeOf(Child.prototype, Parent.prototype);   // instance chain
  Object.setPrototypeOf(Child, Parent);                        // STATIC chain
}

function Animal(name) { this.name = name; }
Animal.prototype.speak = function() { return `${this.name} speaks`; };
Animal.kingdom = function() { return 'Animalia'; };

function Dog(name, breed) {
  Animal.call(this, name);          // = super(name)
  this.breed = breed;
}
extend(Dog, Animal);

const d = new Dog('rex', 'lab');
d.speak();                          // 'rex speaks' (inherited)
Dog.kingdom();                      // 'Animalia' (STATIC chain)
d instanceof Animal;                // true
```

**Constraints**
- `extends` installs TWO prototype writes — instance side AND static side.
- `super(args)` = `Parent.call(this, ...args)` (or `Reflect.construct` for built-ins).
- `super.method()` = `Parent.prototype.method.call(this, ...)`.

---

## 2. Plain-English restatement

`class Child extends Parent` does two things: wires `Child.prototype` to inherit from `Parent.prototype` (so instances find inherited methods), AND wires `Child` itself to inherit from `Parent` (so static methods are inherited too). Most candidates remember the first; forget the second.

---

## 3. Why this matters in interviews

Separates "memorized syntax" from "internalized model." Two prototype links, not one.

---

## 4. Mental model

```
   class Child extends Parent {} does TWO writes:
   
   1. Object.setPrototypeOf(Child.prototype, Parent.prototype)
      → child instances find inherited instance methods.
   
   2. Object.setPrototypeOf(Child, Parent)
      → Child.someStatic() finds Parent's static methods.
   
   super(args) inside constructor:
      Parent.call(this, ...args)  // simple case
      Reflect.construct(Parent, args, new.target)  // built-in subclassing
   
   super.method(args) inside method:
      Parent.prototype.method.call(this, ...args)
   
   NOT this.__proto__.method() — that's wrong for multi-level inheritance.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What does `class Child extends Parent` write besides `Child.prototype.__proto__`?
> 2. Why does `Parent.call(this, ...)` work for `super(...)` in simple cases?
> 3. Why doesn't it work for `Array`/`Error`/`Map`?

---

## 6. Brute force — walked through

### Wrong attempt 1: only set instance chain
`Object.setPrototypeOf(Child.prototype, Parent.prototype)` alone misses static inheritance.

### Wrong attempt 2: `Child.prototype = new Parent()`
Runs Parent constructor at definition time; side effects fire globally.

### Wrong attempt 3: `super.method = this.__proto__.method`
Infinite recursion in multi-level inheritance.

---

## 7. The unlocking insight

> **`extends` does TWO `Object.setPrototypeOf` writes. `super(args)` ≈ `Parent.call(this, args)`. `super.method(args)` = `Parent.prototype.method.call(this, args)`. For built-in subclassing (Array, Error), use `Reflect.construct`.**

Three properties:

1. **TWO prototype writes** — instance + static chains.
2. **`super(args)`** = `Parent.call(this, ...)`.
3. **`super.method`** uses home-object lookup, NOT `this.__proto__`.

---

## 8. Solution (annotated)

```js
function extend(Child, Parent) {
  Object.setPrototypeOf(Child.prototype, Parent.prototype);              // step 1: instance chain
  Object.setPrototypeOf(Child, Parent);                                   // step 2: STATIC chain
}

function Animal(name) { this.name = name; }
Animal.prototype.speak = function() { return `${this.name} speaks`; };
Animal.kingdom = function() { return 'Animalia'; };

function Dog(name, breed) {
  Animal.call(this, name);                                                // step 3: super(name)
  this.breed = breed;
}
Dog.prototype.speak = function() {                                         // step 4: override + super.speak
  const parent = Animal.prototype.speak.call(this);
  return `${parent}; ${this.name} barks`;
};
extend(Dog, Animal);

const d = new Dog('rex', 'lab');
d.speak();                                                                 // 'rex speaks; rex barks'
Dog.kingdom();                                                              // 'Animalia' (via static chain)
d instanceof Animal;                                                        // true
```

**Try it yourself**

```js
// Subclassing built-ins needs Reflect.construct
function MyArray() {
  return Reflect.construct(Array, arguments, MyArray);                     // <- new.target
}
Object.setPrototypeOf(MyArray.prototype, Array.prototype);
Object.setPrototypeOf(MyArray, Array);

const a = new MyArray(1, 2, 3);
a instanceof MyArray;                                                       // true
a instanceof Array;                                                         // true
a.length;                                                                   // 3
```

---

## 9. Step-by-step dry run

```
extend(Dog, Animal):
  Object.setPrototypeOf(Dog.prototype, Animal.prototype)
    → Dog.prototype.__proto__ = Animal.prototype
  Object.setPrototypeOf(Dog, Animal)
    → Dog.__proto__ = Animal

new Dog('rex', 'lab'):
  obj = Object.create(Dog.prototype)
  Dog.apply(obj, ['rex', 'lab']):
    Animal.call(this, 'rex'):  // super
      obj.name = 'rex'
    obj.breed = 'lab'
  return obj

d.speak():
  Walk: d → Dog.prototype.speak found.
  Invoke with this=d:
    Animal.prototype.speak.call(this) → 'rex speaks'
    return 'rex speaks; rex barks'

Dog.kingdom():
  Walk: Dog own? No. Dog.__proto__ = Animal own? YES → Animal.kingdom.
  Invoke → 'Animalia'.
  ← static chain at work!
```

---

## 10. Common confusion + traps

1. **Forget static chain** — `Child.staticMethod` won't find `Parent.staticMethod`.
2. **`Child.prototype = new Parent()`** — pre-ES5 anti-pattern; runs ctor at definition.
3. **`super.method = this.__proto__.method`** — wrong for multi-level (infinite recursion).
4. **`Object.setPrototypeOf` deopt** — fine at module init; avoid in hot paths.
5. **Built-in subclassing** — `Array.call(this)` fails; use `Reflect.construct`.
6. **`Error` subclass** — loses stack; use `Error.captureStackTrace`.
7. **Re-pin `constructor`** if you reassign Child.prototype.

---

## 11. Senior follow-ups & variants

### Variant 1 — `Reflect.construct` for built-ins
`new.target` controls which prototype is installed. Required for `Array`, `Error`, `Map`.

### Variant 2 — Symbol.species
Subclass methods returning instances use `this.constructor[Symbol.species]`.

### Variant 3 — Multi-level inheritance
A ← B ← C. `super.m` in C must look up from C.prototype's home, not `this.__proto__`.

### Variant 4 — Mixin pattern
Multiple inheritance via `Object.assign(Target.prototype, ...mixins)`.

### Variant 5 — Class fields desugar
Public fields become assignments in constructor; private fields use WeakMap.

---

## 12. How to think aloud

> "`class Child extends Parent` does TWO prototype writes — most candidates remember only one. (1) `Object.setPrototypeOf(Child.prototype, Parent.prototype)` so child INSTANCES find inherited instance methods. (2) `Object.setPrototypeOf(Child, Parent)` so `Child.someStatic()` finds Parent's STATIC methods. Inside constructor: `super(args)` is `Parent.call(this, ...args)` for simple cases, `Reflect.construct(Parent, args, new.target)` for built-in subclassing (Array, Error, Map ignore `this` in normal call). Inside method: `super.method(args)` is `Parent.prototype.method.call(this, ...args)`. NOT `this.__proto__.method` — that recurses infinitely in multi-level inheritance because home-object lookup is from the method's defining class. Trap: forget static chain; use new Parent() at definition; build-in subclassing without Reflect.construct."

---

## 13. 60-second revision

> - **`extends`** = TWO `setPrototypeOf` writes.
> - **Instance chain:** `Child.prototype.__proto__ = Parent.prototype`.
> - **Static chain:** `Child.__proto__ = Parent`.
> - **`super(args)`** ≈ `Parent.call(this, ...args)`; built-ins need `Reflect.construct`.
> - **`super.method(args)`** = `Parent.prototype.method.call(this, ...args)`.
> - **Home-object lookup** — NOT `this.__proto__.method`.
> - **`Object.setPrototypeOf` deopts** — fine at init; avoid hot paths.
> - **Trap:** forget static chain; pre-ES5 `Child.prototype = new Parent()`; built-in subclass without Reflect.construct.

---

**Related:** [prototype-chain-inheritance.md](./prototype-chain-inheritance.md) · [class-to-prototype-desugar.md](./class-to-prototype-desugar.md) · [reflect-construct-vs-new.md](./reflect-construct-vs-new.md) · [polyfill-new.md](./polyfill-new.md)

**Concept primer:** [`concepts/prototype.md`](../../concepts/prototype.md)
