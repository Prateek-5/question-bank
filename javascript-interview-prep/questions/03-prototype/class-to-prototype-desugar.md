# Desugar an ES6 `class` into prototype-based code

## Source
- Classic "do you actually understand classes?" interview question (TC39 spec walkthroughs, You Don't Know JS, BFE.dev).
- MDN reference: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Classes

## Why this question matters in interviews
`class` in ES6 is **syntactic sugar over the constructor + prototype pattern**. Senior interviews probe this because candidates who only learned `class` syntax often can't explain (a) where instance methods live, (b) how `extends` wires up both the instance chain and the static chain, (c) what `super(...)` actually does. Writing the desugared equivalent proves you can read Babel output, debug `__proto__` issues, and understand why method-stealing (`Array.prototype.slice.call`) works at all. Backend engineers see this when integrating with code that predates `class` (mongoose models, old EventEmitter subclasses, pre-ES6 libraries).

## Concepts involved

### Syntax to lock in
```js
// ES6 class
class Animal {
  constructor(name) { this.name = name; }
  speak() { console.log(this.name + ' makes a sound'); }
  static kingdom() { return 'Animalia'; }
}

class Dog extends Animal {
  constructor(name, breed) {
    super(name);                   // <- must be before `this`
    this.breed = breed;
  }
  speak() {                        // override
    super.speak();                 // call parent
    console.log(this.name + ' barks');
  }
}

// Desugared:
function Animal(name) { this.name = name; }
Animal.prototype.speak = function () { console.log(this.name + ' makes a sound'); };
Animal.kingdom = function () { return 'Animalia'; };

function Dog(name, breed) {
  Animal.call(this, name);         // = super(name)
  this.breed = breed;
}
Object.setPrototypeOf(Dog.prototype, Animal.prototype);  // instance-side chain
Object.setPrototypeOf(Dog, Animal);                       // static-side chain

Dog.prototype.speak = function () {
  Animal.prototype.speak.call(this);                       // = super.speak()
  console.log(this.name + ' barks');
};
```

### Runtime / engine behavior
- A `class` declaration creates a function (the constructor) **plus** a `.prototype` object holding the instance methods (non-enumerable!). Static methods live on the constructor function itself.
- `extends` does **two** prototype writes — this is the headline insight:
  1. `Object.setPrototypeOf(Child.prototype, Parent.prototype)` — so `child.instanceMethod` resolves via the chain.
  2. `Object.setPrototypeOf(Child, Parent)` — so `Child.staticMethod` falls through to `Parent.staticMethod`.
- `super(...)` in a constructor is **`Parent.call(this, ...)`** (or `Reflect.construct` for derived classes — see edge cases).
- `super.method(...)` in a method is **`Parent.prototype.method.call(this, ...)`**. The lookup is from the *home object* of the calling method, not from `this.__proto__` — this matters for deep hierarchies.
- Class methods are non-enumerable by default; assigning `Foo.prototype.bar = ...` makes `bar` enumerable. Tiny lie in the desugar, but it's the interviewer's "extra credit" question.

### Edge cases (these are the interview traps)
1. **`super` before `this`** — in a derived constructor, accessing `this` before `super(...)` throws `ReferenceError`. The desugar with `Parent.call(this, ...)` doesn't reproduce this exactly (because `this` already exists in a regular function). The spec-accurate version uses `Reflect.construct(Parent, args, new.target)` so that the parent constructs `this`.
2. **`new.target`** — preserved across `super` calls. A naive `Parent.call(this, ...)` desugar loses `new.target`; `Reflect.construct` preserves it.
3. **Two chains, not one** — beginners think `extends` only sets `Child.prototype.__proto__`. The static-side chain (`Child.__proto__ === Parent`) is just as important — it's why `class Foo extends Map {}` lets you call `Foo.groupBy(...)` if `Map.groupBy` exists.
4. **Method enumerability** — desugared methods set via assignment are enumerable; class methods aren't. `Object.defineProperty(Dog.prototype, 'speak', { value: fn, enumerable: false, writable: true, configurable: true })` is the faithful version.
5. **`super.method` is lexically bound** — `super` looks up via the *method's home object*, not `this`. Moving a method between classes (or extracting it) breaks `super`. Worth mentioning.
6. **Extending built-ins** — `class MyArray extends Array {}` works in ES2015+ engines; the pre-ES6 desugar with `Array.call(this)` does NOT — `Array.call(this)` ignores `this` and returns a new array. Real subclassing of built-ins requires `Reflect.construct`.
7. **Static block (ES2022)** — `static { ... }` runs at class definition time. Desugars to an IIFE on the constructor function right after the static methods are attached.
8. **Private fields (`#x`)** — not pure desugar; they use a WeakMap-equivalent internal slot. Mention if asked.

## Brute force approach
"Use `Child.prototype = new Parent()`." This was the pre-ES5 pattern. It runs the parent's constructor **at class definition time** (wrong — it should run per-instance), and any side effects in `Parent` happen once globally. Also sets `Child.prototype.constructor` to `Parent`. Drop it.

## Optimal approach
- Constructor function for the class body.
- Instance methods on `Ctor.prototype` via `Object.defineProperty` (non-enumerable).
- Static methods on `Ctor` itself.
- For `extends`: `Object.setPrototypeOf` for **both** the prototype side and the constructor side.
- For `super(...)`: `Reflect.construct(Parent, args, new.target)` (spec-accurate) or `Parent.call(this, ...)` (good-enough for interviews).
- For `super.method(...)`: `Object.getPrototypeOf(Child.prototype).method.call(this, ...)`.

## Solution (JavaScript)

```js
// Spec-accurate desugar of:
//   class Animal { constructor(name) { this.name = name; } speak() { ... } static kingdom() { ... } }
//   class Dog extends Animal { constructor(name, breed) { super(name); this.breed = breed; }
//                              speak() { super.speak(); ... } }

function Animal(name) {
  this.name = name;
}
Object.defineProperty(Animal.prototype, 'speak', {
  value: function () { console.log(this.name + ' makes a sound'); },
  writable: true, configurable: true, enumerable: false,
});
Object.defineProperty(Animal, 'kingdom', {
  value: function () { return 'Animalia'; },
  writable: true, configurable: true, enumerable: false,
});

function Dog(name, breed) {
  // Equivalent of `super(name)` — Reflect.construct preserves new.target
  // and (for built-in parents) lets the parent allocate `this`.
  const self = Reflect.construct(Animal, [name], new.target || Dog);
  self.breed = breed;
  return self;
}

// Two prototype links — the headline of `extends`:
Object.setPrototypeOf(Dog.prototype, Animal.prototype); // instance chain
Object.setPrototypeOf(Dog, Animal);                     // static chain

Object.defineProperty(Dog.prototype, 'speak', {
  value: function () {
    // Equivalent of `super.speak()`:
    Object.getPrototypeOf(Dog.prototype).speak.call(this);
    console.log(this.name + ' barks');
  },
  writable: true, configurable: true, enumerable: false,
});

// Usage
const d = new Dog('Rex', 'Lab');
d.speak();              // 'Rex makes a sound' then 'Rex barks'
Dog.kingdom();          // 'Animalia' — found via static chain on Dog.__proto__ === Animal
d instanceof Dog;       // true
d instanceof Animal;    // true — walks Dog.prototype → Animal.prototype
```

## Step-by-step dry run

Input: `const d = new Dog('Rex', 'Lab'); d.speak();`

Trace `new Dog('Rex', 'Lab')`:
- `new Dog(...)` allocates `this` (initially `Dog.prototype`-linked) and runs the body.
- `Reflect.construct(Animal, ['Rex'], Dog)` — runs `Animal` as a constructor with `new.target = Dog`. Returns a fresh object with `[[Prototype]] = Dog.prototype` and `name = 'Rex'`.
- `self.breed = 'Lab'`.
- Body returns `self` (explicit return from constructor overrides the default `this`).
- Net: `d = { name: 'Rex', breed: 'Lab' }`, chain `Dog.prototype → Animal.prototype → Object.prototype → null`.

Trace `d.speak()`:
- Lookup: `d.speak` → not own → walk chain → `Dog.prototype.speak` (the override). Call with `this = d`.
- Inside: `Object.getPrototypeOf(Dog.prototype).speak` → `Animal.prototype.speak`. `.call(d)` → logs `'Rex makes a sound'`.
- Then `console.log(d.name + ' barks')` → `'Rex barks'`.

Trace `Dog.kingdom()`:
- `Dog.kingdom` — not own on `Dog` → static chain: `Dog.__proto__ === Animal` → `Animal.kingdom` → call → returns `'Animalia'`. Demonstrates the static-side chain.

## Important takeaways

**Syntax to memorize**
- Class methods → `Ctor.prototype.method`, non-enumerable.
- Static methods → `Ctor.method`, non-enumerable.
- `extends` ⇒ **two** `Object.setPrototypeOf` calls (instance side + constructor side).
- `super(...)` ⇒ `Reflect.construct(Parent, args, new.target)` (or `Parent.call(this, ...)` for simple cases).
- `super.method(...)` ⇒ `Object.getPrototypeOf(homeObject).method.call(this, ...)`.

**Patterns to reuse**
- The "two chains" mental model unlocks `Array.from`, `Promise.resolve`, `Symbol.species` — all live on the constructor's static chain.
- `Reflect.construct` + `new.target` is the magic that lets `class MyArray extends Array {}` work. Worth memorizing.

**Common mistakes**
- Setting `Child.prototype = new Parent()` — runs the parent constructor at definition time (wrong) and pollutes `Child.prototype` with parent's own properties.
- Forgetting `Object.setPrototypeOf(Child, Parent)` — `Child.staticMethod()` won't fall through to `Parent.staticMethod()`.
- Using `this.__proto__.method.call(this)` for `super` — breaks in multi-level inheritance because `this.__proto__` is always `Dog.prototype`, infinite loop.
- Assigning `Dog.prototype.speak = fn` and calling it "desugared" — methods are now enumerable, breaking `for...in` iteration.

**Related questions**
- `instanceof` polyfill (walks the chain `extends` builds)
- Polyfill `new` (sets `[[Prototype]]` to `Ctor.prototype`)
- "What does Babel emit for `class extends`?" (the answer is this exact desugar)

## Variants

1. **Subclass a built-in** — "Desugar `class MyArray extends Array {}`." Forces `Reflect.construct` because `Array.call(this)` ignores `this` and allocates a new array.

2. **Mixin pattern** — "How do you do multiple inheritance in JS?" Answer: function-returning-class mixins like `Serializable(Loggable(Base))`. Each mixin returns `class extends Base { ... }`.

3. **Private fields** — "Desugar `class { #count = 0; inc() { this.#count++; } }`." Hand-wavy answer: a `WeakMap<instance, fieldValue>` per private field, keyed by the instance.

## Revision notes

> **class → prototype desugar — 60 second recap**
> - `class` = constructor function + `.prototype` holding non-enumerable instance methods + statics on the function.
> - `extends` ⇒ **two** prototype links: `Object.setPrototypeOf(Child.prototype, Parent.prototype)` AND `Object.setPrototypeOf(Child, Parent)`.
> - `super(...)` ⇒ `Reflect.construct(Parent, args, new.target)` (preserves `new.target`).
> - `super.method()` ⇒ `Object.getPrototypeOf(homeObject).method.call(this, ...)` — NOT `this.__proto__`.
> - Methods set via `defineProperty` (non-enumerable), not assignment.
> - **Trap:** forgetting the static-side chain — `Child.staticInherited()` silently fails.
> - **Trap:** `super` is lexically bound to the home object; extracting methods breaks `super`.
> - Subclassing built-ins requires `Reflect.construct`; `Parent.call(this)` won't work.
