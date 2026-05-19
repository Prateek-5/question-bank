# Desugar `class` → prototype-based code

> **Difficulty:** Senior   |   **Time:** ~15 min   |   **Prereqs:** [prototype-chain-inheritance.md](./prototype-chain-inheritance.md), [extends-super-implementation.md](./extends-super-implementation.md)
>
> **Source:** "Do you actually understand classes?" question. TC39 walkthroughs, BFE.dev.

---

## 1. Problem statement

Show that ES6 `class` is sugar over constructor + prototype. Desugar a class with constructor, instance methods, static methods, `extends`, and `super`.

**Verification examples**

```js
// ES6 class
class Animal {
  constructor(name) { this.name = name; }
  speak() { return this.name + ' makes a sound'; }
  static kingdom() { return 'Animalia'; }
}
class Dog extends Animal {
  constructor(name, breed) {
    super(name);
    this.breed = breed;
  }
  speak() {
    return super.speak() + '; ' + this.name + ' barks';
  }
}

// Desugared
function Animal(name) { this.name = name; }
Animal.prototype.speak = function() { return this.name + ' makes a sound'; };
Animal.kingdom = function() { return 'Animalia'; };

function Dog(name, breed) {
  Animal.call(this, name);
  this.breed = breed;
}
Object.setPrototypeOf(Dog.prototype, Animal.prototype);
Object.setPrototypeOf(Dog, Animal);
Dog.prototype.speak = function() {
  return Animal.prototype.speak.call(this) + '; ' + this.name + ' barks';
};
```

**Constraints**
- Class methods are **non-enumerable** by default; assigned `.prototype.x` is enumerable.
- `class` body is always strict mode.
- Class declarations are TDZ-hoisted (not fully hoisted like function decls).

---

## 2. Plain-English restatement

`class Foo { method() {} }` translates to: define a `function Foo(){}` constructor; put `method` on `Foo.prototype`. `extends Parent` wires `Foo.prototype.__proto__ = Parent.prototype` AND `Foo.__proto__ = Parent`. `super(args)` is `Parent.call(this, args)`. `super.method(args)` is `Parent.prototype.method.call(this, args)`.

---

## 3. Why this matters in interviews

Tests whether class syntax knowledge is grounded in mechanics. Probes Babel-output readability + pre-ES6 codebase fluency.

---

## 4. Mental model

```
   class Foo {
     constructor() {}
     method() {}
     static staticMethod() {}
   }
   
   becomes:
   
   function Foo() {}
   Foo.prototype.method = function() {};
   Foo.staticMethod = function() {};
   
   class Bar extends Foo {
     constructor() { super(); }
     method() { super.method(); }
   }
   
   becomes:
   
   function Bar() { Foo.call(this); }
   Object.setPrototypeOf(Bar.prototype, Foo.prototype);  // instance chain
   Object.setPrototypeOf(Bar, Foo);                       // STATIC chain
   Bar.prototype.method = function() {
     Foo.prototype.method.call(this);
   };
   
   Class methods are non-enumerable; Object.defineProperty does this in real Babel output.
   class body is implicit 'use strict'.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Where do instance methods live in the desugar?
> 2. What does `extends` do that single inheritance assignment doesn't?
> 3. Is `super()` before `this` required in the desugar?

---

## 6. Brute force — walked through

### Wrong attempt 1: "class is a class"
Misses that it's syntactic sugar; can't write Babel output.

### Wrong attempt 2: only set instance chain
Forgets static chain — `Bar.staticMethod` won't find Foo's.

### Wrong attempt 3: `super` = `this.__proto__`
Multi-level inheritance breaks (infinite recursion).

---

## 7. The unlocking insight

> **Class = constructor function + methods on `.prototype` + static methods on the function. `extends` = TWO `setPrototypeOf`s (instance + static chains). `super(args)` = `Parent.call(this, args)`. `super.method(args)` = `Parent.prototype.method.call(this, args)`. Class methods are non-enumerable by default.**

Three properties:

1. **Methods on `.prototype`** — instance methods.
2. **Static on constructor** — `Foo.staticMethod`.
3. **`extends` = 2 chain writes** — instance + static.

---

## 8. Solution (annotated)

```js
// Class
class Animal {
  constructor(name) { this.name = name; }
  speak() { return `${this.name} makes a sound`; }
  static kingdom() { return 'Animalia'; }
}

// Desugar:
function Animal(name) { this.name = name; }                              // step 1: constructor

Object.defineProperty(Animal.prototype, 'speak', {                       // step 2: non-enumerable method
  value: function() { return `${this.name} makes a sound`; },
  writable: true, configurable: true, enumerable: false,
});

Animal.kingdom = function() { return 'Animalia'; };                       // step 3: static

class Dog extends Animal {
  constructor(name, breed) { super(name); this.breed = breed; }
  speak() { return `${super.speak()}; ${this.name} barks`; }
}

// Desugar:
function Dog(name, breed) {
  Animal.call(this, name);                                                // step 4: super(name)
  this.breed = breed;
}
Object.setPrototypeOf(Dog.prototype, Animal.prototype);                   // step 5: instance chain
Object.setPrototypeOf(Dog, Animal);                                       // step 6: STATIC chain
Object.defineProperty(Dog.prototype, 'speak', {
  value: function() {
    return `${Animal.prototype.speak.call(this)}; ${this.name} barks`;    // step 7: super.speak
  },
  writable: true, configurable: true, enumerable: false,
});
```

**Try it yourself**

```js
const d = new Dog('rex', 'lab');
d.speak();                                                                 // 'rex makes a sound; rex barks'
Dog.kingdom();                                                              // 'Animalia' (via static chain)
d instanceof Animal;                                                        // true

// Class methods non-enumerable
for (const k in d) console.log(k);                                          // 'name', 'breed' (NOT 'speak')

// Assigned to prototype directly = enumerable
class Foo {}
Foo.prototype.method = function() {};
for (const k in new Foo()) console.log(k);                                  // 'method' (enumerable!)
```

---

## 9. Step-by-step dry run

```
class Dog extends Animal { ... }

Desugar:
  function Dog(...) { Animal.call(this, ...); ... }
  Object.setPrototypeOf(Dog.prototype, Animal.prototype)  // instance
  Object.setPrototypeOf(Dog, Animal)                       // STATIC
  Methods on Dog.prototype (non-enumerable).

new Dog('rex', 'lab'):
  obj = Object.create(Dog.prototype)
  Dog.apply(obj, ['rex', 'lab']):
    Animal.call(this, 'rex'):  // super(name)
      obj.name = 'rex'
    obj.breed = 'lab'
  return obj

d.speak():
  Walk: d → Dog.prototype.speak found → invoke.
  Inside: Animal.prototype.speak.call(this) → 'rex makes a sound'
  Return 'rex makes a sound; rex barks'.

Dog.kingdom():
  Walk: Dog own? no. Dog.__proto__ = Animal → Animal.kingdom.
  Static chain enables this.
```

---

## 10. Common confusion + traps

1. **Methods become enumerable in desugar** — class methods are non-enumerable; use `defineProperty`.
2. **Forget static chain** — `Bar.staticMethod` won't find `Foo.staticMethod`.
3. **`super` before `this`** — class enforces; desugar with `Parent.call(this, ...)` doesn't.
4. **`Reflect.construct` for built-ins** — `class extends Array {}` needs it; `Parent.call(this)` fails.
5. **Private fields desugar via WeakMap** — Babel output is more complex.
6. **Class body strict mode** — implicit; desugar should preserve.
7. **`new.target`** in constructors — `Reflect.construct` preserves; plain apply doesn't.

---

## 11. Senior follow-ups & variants

### Variant 1 — Private fields
`#x` desugars to a WeakMap or symbol property.

### Variant 2 — Class fields
Public fields = assignments in constructor; `#private` = WeakMap.

### Variant 3 — `super.method` home-object
Uses defining class's prototype, NOT `this.__proto__`.

### Variant 4 — `Reflect.construct` for built-in subclassing
`class MyArr extends Array {}` requires `Reflect.construct(Array, args, new.target)`.

### Variant 5 — Class as expression
`const C = class {};` — same desugar; class expression.

---

## 12. How to think aloud

> "Class is syntactic sugar over constructor + prototype. Constructor body → plain function. Instance methods → `Foo.prototype.method`. Static methods → `Foo.staticMethod`. `extends Parent` does TWO `setPrototypeOf` writes: `Foo.prototype.__proto__ = Parent.prototype` (instance chain — for inherited instance methods) AND `Foo.__proto__ = Parent` (static chain — for inherited static methods). `super(args)` = `Parent.call(this, ...args)` for simple cases; `Reflect.construct(Parent, args, new.target)` for built-ins (Array, Error). `super.method(args)` = `Parent.prototype.method.call(this, ...args)`. Class methods are NON-ENUMERABLE by default (`defineProperty` in real Babel output). Class body is implicit strict mode. Trap: forget static chain; treat super as `this.__proto__`; build-in subclassing without Reflect.construct."

---

## 13. 60-second revision

> - **Class = constructor + `.prototype` methods + static on function.**
> - **`extends`** = TWO `setPrototypeOf`s (instance + static chains).
> - **`super(args)`** = `Parent.call(this, ...)` (or `Reflect.construct`).
> - **`super.method(args)`** = `Parent.prototype.method.call(this, ...)`.
> - **Class methods non-enumerable** by default.
> - **Class body always strict.**
> - **TDZ-hoisted** (NOT fully hoisted like fn decls).
> - **Trap:** forget static chain; `super` as `this.__proto__`; built-in subclass.

---

**Related:** [extends-super-implementation.md](./extends-super-implementation.md) · [prototype-chain-inheritance.md](./prototype-chain-inheritance.md) · [reflect-construct-vs-new.md](./reflect-construct-vs-new.md) · [`01-hoisting/class-hoisting.md`](../01-hoisting/class-hoisting.md)

**Concept primer:** [`concepts/prototype.md`](../../concepts/prototype.md)
