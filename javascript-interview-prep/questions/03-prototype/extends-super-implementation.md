# Implement `extends` + `super` manually (without the `class` keyword)

## Source
- Senior JS interview question — tests whether you understand the two prototype links `extends` installs.
- MDN reference: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/super

## Why this question matters in interviews
Most candidates can write `class Dog extends Animal`. Far fewer can explain that `extends` performs **two** prototype writes — one on the instance side and one on the constructor side. This question separates "memorized the syntax" from "internalized the model." When you implement it manually with `Object.setPrototypeOf`, the interviewer can see whether you understand: (a) how `child.inheritedMethod` finds the parent method, (b) how `Child.inheritedStatic()` finds the parent static, (c) how `super(...)` initializes parent fields, and (d) how `super.method()` calls the parent's override. Backend engineers hit this when extending `EventEmitter`, `Error`, `Readable`, or building custom mongoose model hierarchies.

## Concepts involved

### Syntax to lock in
```js
// What we want to replicate, without using `class`:
//   class B extends A { constructor(...) { super(...); ... }; m() { super.m(); ... } }

function extend(Child, Parent) {
  Object.setPrototypeOf(Child.prototype, Parent.prototype); // instance side
  Object.setPrototypeOf(Child, Parent);                     // constructor (static) side
}

function callSuper(Parent, instance, args) {
  return Parent.call(instance, ...args);                    // = super(...args) in ctor
}

function callSuperMethod(Parent, instance, methodName, args) {
  return Parent.prototype[methodName].call(instance, ...args); // = super.method(...)
}
```

### Runtime / engine behavior
- A constructor function has **two** important slots:
  - `Ctor.prototype` — the object that becomes every instance's `[[Prototype]]`.
  - `[[Prototype]]` of `Ctor` itself — the parent constructor, used for static method lookup.
- `Object.setPrototypeOf(child, parent)` updates the internal `[[Prototype]]` slot. Engines deoptimize on this — avoid in hot paths.
- Property lookup is uniform: when you write `Child.foo`, JS first checks `Child`'s own props, then walks `Child.__proto__`. Same for instances. The "two chains" exist because constructors are objects too.
- `super(...)` semantics: in a class, it allocates `this` via the parent constructor (using `new.target` so the child's prototype is still installed). In manual code, `Parent.call(this, ...args)` is the practical equivalent for simple cases.

### Edge cases (these are the interview traps)
1. **Forgetting the static chain** — most common bug. `Object.setPrototypeOf(Child.prototype, Parent.prototype)` alone misses `Child.parentStatic()`.
2. **`Child.prototype = Object.create(Parent.prototype)`** — pre-ES6 pattern. Works for the instance chain but clobbers `Child.prototype.constructor` (now points to `Parent`) and **doesn't** set the static chain. Always re-pin `Child.prototype.constructor = Child` if you use this pattern.
3. **`Object.setPrototypeOf` deopt** — engines see this as "shape change," disable inline caches for affected objects. Fine at module init, terrible inside per-request handlers.
4. **`super.method` is NOT `this.__proto__.method`** — common mistake. In multi-level inheritance (`A ← B ← C`), if `C.m` calls `super.m`, `this.__proto__` is always `C.prototype`, leading to infinite recursion. The correct lookup is from the method's *home object* (`Object.getPrototypeOf(homeObject)`).
5. **`Reflect.construct` for built-ins** — to subclass `Array`, `Error`, `Map`, `Parent.call(this, ...)` fails (these constructors ignore `this`). Use `Reflect.construct(Parent, args, new.target)`.
6. **`Error` subclasses** — `class MyError extends Error {}` loses stack traces unless you call `Error.captureStackTrace(this, this.constructor)` (V8-specific) or set `this.name = 'MyError'`. Worth mentioning.
7. **Symbol.species** — when a subclass method returns a new instance (e.g., `Array.prototype.map`), the engine consults `this.constructor[Symbol.species]` to decide the constructor. Subtle, but relevant for built-in subclassing.

## Brute force approach
"Use `Child.prototype = new Parent()`." Runs the parent constructor at definition time (with no arguments — likely throws), and any side effects (DB connection, file open) happen once globally instead of per-instance. The pre-ES5 hack that everyone moved away from.

## Optimal approach
Two `Object.setPrototypeOf` calls — done. Call `Parent.call(this, ...args)` inside `Child` to mimic `super(...)`. For built-in parents or precise spec semantics, use `Reflect.construct`. Re-pin `constructor` if needed for `instance.constructor === Child` checks.

## Solution (JavaScript)

```js
/**
 * Manually wire up inheritance, replicating what `class Child extends Parent` does.
 * @param {Function} Child
 * @param {Function} Parent
 */
function inherit(Child, Parent) {
  if (typeof Parent !== 'function' && Parent !== null) {
    throw new TypeError('Class extends value is not a constructor or null');
  }
  // Instance-side chain — instances of Child inherit Parent's prototype methods
  Object.setPrototypeOf(Child.prototype, Parent === null ? null : Parent.prototype);
  // Constructor-side chain — Child inherits Parent's static methods
  Object.setPrototypeOf(Child, Parent === null ? Function.prototype : Parent);
  // Re-pin constructor (it was reset when we touched the prototype object)
  Object.defineProperty(Child.prototype, 'constructor', {
    value: Child, writable: true, configurable: true, enumerable: false,
  });
}

// ---- Example use ----

function Animal(name) {
  this.name = name;
}
Animal.prototype.speak = function () {
  console.log(this.name + ' makes a sound');
};
Animal.kingdom = function () { return 'Animalia'; };

function Dog(name, breed) {
  // super(name) — for built-ins, swap to Reflect.construct
  Animal.call(this, name);
  this.breed = breed;
}
inherit(Dog, Animal);

// Override + super.method()
Dog.prototype.speak = function () {
  // super.speak() — look up via the home object, not this.__proto__
  Object.getPrototypeOf(Dog.prototype).speak.call(this);
  console.log(this.name + ' barks');
};

const rex = new Dog('Rex', 'Lab');
rex.speak();             // 'Rex makes a sound' then 'Rex barks'
rex instanceof Dog;      // true
rex instanceof Animal;   // true
Dog.kingdom();           // 'Animalia' — found via static chain
rex.constructor === Dog; // true (because we re-pinned it)
```

## Step-by-step dry run

Input: `const rex = new Dog('Rex', 'Lab'); rex.speak(); Dog.kingdom();`

Setup state after `inherit(Dog, Animal)`:
- `Dog.prototype.__proto__ === Animal.prototype` (instance chain).
- `Dog.__proto__ === Animal` (static chain).
- `Dog.prototype.constructor === Dog` (re-pinned).

Trace `new Dog('Rex', 'Lab')`:
- `new` creates `obj = {}`, sets `obj.__proto__ = Dog.prototype`, calls `Dog.call(obj, 'Rex', 'Lab')`.
- Inside `Dog`: `Animal.call(obj, 'Rex')` → sets `obj.name = 'Rex'`. Then `obj.breed = 'Lab'`.
- `obj` is returned implicitly. `rex = { name: 'Rex', breed: 'Lab' }` with chain to `Dog.prototype → Animal.prototype → Object.prototype`.

Trace `rex.speak()`:
- `rex.speak`: not own → `Dog.prototype.speak` (the override). Call with `this = rex`.
- `Object.getPrototypeOf(Dog.prototype).speak` → `Animal.prototype.speak`. `.call(rex)` → logs `'Rex makes a sound'`.
- Then `console.log(rex.name + ' barks')` → `'Rex barks'`.

Trace `Dog.kingdom()`:
- Property lookup on `Dog`. Not own. Walk `Dog.__proto__` → `Animal`. Found `kingdom`. Call with `this = Dog`. Returns `'Animalia'`.
- This is the static-chain payoff. Without `Object.setPrototypeOf(Dog, Animal)`, this would throw `Dog.kingdom is not a function`.

## Important takeaways

**Syntax to memorize**
- TWO links every time:
  - `Object.setPrototypeOf(Child.prototype, Parent.prototype)` — instances inherit methods.
  - `Object.setPrototypeOf(Child, Parent)` — constructor inherits statics.
- `super(...)` ≈ `Parent.call(this, ...args)` for simple cases; `Reflect.construct(Parent, args, new.target)` for built-ins.
- `super.method(...)` ≈ `Object.getPrototypeOf(homeObject).method.call(this, ...args)`. The home object is `Child.prototype` for instance methods, `Child` for static methods.

**Patterns to reuse**
- The two-link rule generalizes: any time you "extend" something in JS, ask "what's the instance-side chain?" and "what's the static-side chain?"
- `Object.setPrototypeOf` at module init is fine; never in hot paths (deopt).

**Common mistakes**
- Setting only the instance-side chain — `Dog.parentStatic()` silently breaks.
- Using `this.__proto__.method.call(this)` for `super.method` — infinite loop in 3+ level hierarchies.
- Forgetting `Child.prototype.constructor = Child` after replacing `Child.prototype` — `instance.constructor` lies.
- Calling `Parent.call(this, ...)` when `Parent` is a built-in (`Array`, `Error`, `Map`) — the parent ignores `this` and returns a new instance. Use `Reflect.construct`.

**Related questions**
- Class-to-prototype desugar (this is the same question framed differently)
- `instanceof` polyfill (walks the instance-side chain you just built)
- "Why doesn't `class MyArray extends Array {}` work in pre-ES6 desugar?" (answer: `Reflect.construct` required)

## Variants

1. **Diamond inheritance / mixin** — "How would you compose multiple parents?" JS doesn't support multiple inheritance directly; use function-returning-class mixins: `function Serializable(Base) { return class extends Base { ... } }`.

2. **`Reflect.construct` for built-ins** — "Subclass `Error` manually so stack traces work." Use `Reflect.construct(Error, [msg], new.target)`; assign `this.name = 'MyError'`; call `Error.captureStackTrace(this, MyError)` for V8.

3. **Lazy super setup** — "Defer `inherit(Child, Parent)` until first instantiation." Wrap the constructor: on first `new`, run inherit then call the real ctor. Avoids the `Object.setPrototypeOf` deopt at module load if classes are rarely used.

## Revision notes

> **extends/super manual — 60 second recap**
> - `extends` installs **two** prototype links — instance side (`Child.prototype → Parent.prototype`) and static side (`Child → Parent`).
> - `super(...args)` in constructor → `Parent.call(this, ...args)` (or `Reflect.construct` for built-ins).
> - `super.method(...)` → `Object.getPrototypeOf(homeObject).method.call(this, ...)`. Home object, NOT `this.__proto__`.
> - Re-pin `Child.prototype.constructor = Child` if you replace the prototype object.
> - `Object.setPrototypeOf` is a deopt — fine at init, terrible in hot paths.
> - **Trap:** forgetting the static chain — inherited statics silently break.
> - **Trap:** `this.__proto__.method` for super → infinite recursion in 3-level hierarchies.
> - Built-in parents (`Array`, `Error`, `Map`) require `Reflect.construct` + `new.target`.
